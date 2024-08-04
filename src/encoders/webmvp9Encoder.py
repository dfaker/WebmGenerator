
import os
import logging
import subprocess as sp
import datetime
import time

from ..encodingUtils import getFreeNameForFileAndLog
from ..encodingUtils import logffmpegEncodeProgress
from ..encodingUtils import isRquestCancelled

from ..webmGeneratorUi import RELEASE_NUMVER

from ..optimisers.nelderMead import encodeTargetingSize as encodeTargetingSize_nelder_mead
from ..optimisers.linear     import encodeTargetingSize as encodeTargetingSize_linear

def encoder(inputsList, outputPathName,filenamePrefix, filtercommand, options, totalEncodedSeconds, totalExpectedEncodedSeconds, statusCallback,requestId=None,encodeStageFilter='null',globalOptions={},packageglobalStatusCallback=print,startEndTimestamps=None):
  
  audoBitrate = 8
  try:
    audoBitrate = int(float(options.get('audioRate','8')))
  except Exception as e:
    print(e)

  audoBitrate = int(audoBitrate)*1024

  audio_mp  = 8
  video_mp  = 1024*1024
  initialBr = globalOptions.get('initialBr',16777216)
  dur       = totalExpectedEncodedSeconds-totalEncodedSeconds

  if options.get('maximumSize') == 0.0:
    sizeLimitMax = float('inf')
    sizeLimitMin = float('-inf')
    initialBr    = globalOptions.get('initialBr',16777216)
  else:
    sizeLimitMax = options.get('maximumSize')*1024*1024
    sizeLimitMin = sizeLimitMax*(1.0-globalOptions.get('allowableTargetSizeUnderrun',0.25))
    targetSize_guide =  (sizeLimitMin+sizeLimitMax)/2
    initialBr        = ( ((targetSize_guide)/dur) - ((audoBitrate / 1024 / audio_mp)/dur) )*8

  print('allowableTargetSizeUnderrun',globalOptions.get('allowableTargetSizeUnderrun'))
  print('sizeLimitMax',sizeLimitMax)
  print('sizeLimitMin',sizeLimitMin)

  videoFileName,logFilePath,filterFilePath,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'webm', requestId)

  def encoderStatusCallback(text,percentage,**kwargs):
    statusCallback(text,percentage,**kwargs)
    packageglobalStatusCallback(text,percentage)

  def encoderFunction(br, passNumber, passReason, passPhase=0, requestId=None, widthReduction=0.0, bufsize=None, cqMode=False):
    
    ffmpegcommand=[]
    ffmpegcommand+=['ffmpeg' ,'-y']

    s,e = None,None
    if startEndTimestamps is not None:
        s,e = startEndTimestamps
        ffmpegcommand+=['-ss', str(s)]
        ffmpegcommand+=inputsList
        ffmpegcommand+=['-to', str(e-s)]
    else:
        ffmpegcommand+=inputsList

    if widthReduction>0.0:
      encodefiltercommand = filtercommand+',[outv]{encodeStageFilter},scale=iw*(1-{widthReduction}):ih*(1-{widthReduction}):flags=bicubic[outvfinal]'.format(encodeStageFilter=encodeStageFilter,widthReduction=widthReduction)
    else:
      encodefiltercommand = filtercommand+',[outv]{encodeStageFilter},null[outvfinal]'.format(encodeStageFilter=encodeStageFilter)

    if options.get('audioChannels') == 'No audio':
      encodefiltercommand+=',[outa]anullsink'

    with open(filterFilePath,'wb') as filterFile:
      filterFile.write(encodefiltercommand.encode('utf8'))

    targetWidth = 0
    targetHeight = 0
    
    try:
      widthCmd = ['ffmpeg']+inputsList+['-filter_complex_script',filterFilePath,'-frames:v','1','-f','null','-']
      proc = sp.Popen(widthCmd,stdout=sp.PIPE,stderr=sp.PIPE)
      outs,errs = proc.communicate()
      for errLine in errs.split(b'\n'):
        for errElem in [x.strip() for x in errLine.split(b',')]:
          if b'x' in errElem:
            try:
              w,h = errElem.split(b' ')[0].split(b'x')
              w=int(w)
              h=int(h)
              targetWidth = w
              targetHeight = h
            except:
              pass
    except Exception as e:
      print(e)

    tileColumns  = 0

    if not options.get('disableVP9Tiling',False):
      if targetWidth >= 960:
        tileColumns = 1
      if targetWidth >= 1920:
        tileColumns = 2
      if targetWidth >= 3840:
        tileColumns = 3

    print('VP9 targetWidth:',targetWidth)
    print('VP9 tileColumns:',tileColumns)
      
    if options.get('audioChannels') == 'No audio':
      ffmpegcommand+=['-filter_complex_script',filterFilePath]
      ffmpegcommand+=['-map','[outvfinal]']
    elif 'Copy' in options.get('audioChannels',''):
      ffmpegcommand+=['-filter_complex_script',filterFilePath]
      ffmpegcommand+=['-map','[outvfinal]','-map','a:0']
    else:
      ffmpegcommand+=['-filter_complex_script',filterFilePath]
      ffmpegcommand+=['-map','[outvfinal]','-map','[outa]']

    if passPhase==1:
      ffmpegcommand+=['-pass', '1', '-passlogfile', logFilePath ]
    elif passPhase==2:
      ffmpegcommand+=['-pass', '2', '-passlogfile', logFilePath ]

    if bufsize is None:
      bufsize = 3000000
      if sizeLimitMax != 0.0 and not cqMode:
        bufsize = str(min(2000000000.0,br*2))

    threadCount = globalOptions.get('encoderStageThreads',4)
    metadataSuffix = globalOptions.get('titleMetadataSuffix',' WmG')
    
    crf = 4
    if cqMode:
      crf = br
      br = 0

    audioCodec = ["-c:a","libopus"]
    if 'Copy' in options.get('audioChannels',''):
      audioCodec = []



    if startEndTimestamps is None:
        ffmpegcommand+=["-shortest", "-copyts"
                       ,"-start_at_zero", "-c:v","libvpx-vp9"] + audioCodec + [
                        "-stats","-pix_fmt","yuv420p"
                       ,"-threads", str(threadCount)
                       ,"-auto-alt-ref", "6", "-lag-in-frames", "25"]
    else:
        ffmpegcommand+=["-c:v","libvpx-vp9"] + audioCodec + [
                        "-stats","-pix_fmt","yuv420p"
                       ,"-threads", str(threadCount)
                       ,"-auto-alt-ref", "6", "-lag-in-frames", "25"]

    if not cqMode:
      #ffmpegcommand += ["-bufsize", str(bufsize)]
      pass

    if passPhase==1:
      pass
    else:
      ffmpegcommand += ['-speed', '1']

    if options.get('forceBestDeadline',False):
      ffmpegcommand+=["-quality","best"]
    else:
      ffmpegcommand+=["-quality","good"]

    ffmpegcommand+=['-psnr', '-row-mt', '1', '-tile-columns', str(tileColumns), "-tile-rows", "0"
                   ,"-arnr-maxframes", "7","-arnr-strength", "5"
                   ,"-aq-mode", "0", "-tune-content", "film", "-enable-tpl", "1", "-frame-parallel", "0"
                   ,"-metadata", 'Title={}'.format(filenamePrefix.replace('-','-') + metadataSuffix) ]
    

    qmaxOverride = 50
    useQmax=False
    try:
      temp = options.get('qmaxOverride',-1)
      if temp >= 0:
        qmaxOverride = temp
        useQmax=True
    except Exception as e:
      print(e)


    if sizeLimitMax == 0.0:
      if useQmax:
        ffmpegcommand+=["-b:v","0","-qmin","0","-qmax",str(qmaxOverride),"-crf"  ,str(crf)]
      else:
        ffmpegcommand+=["-b:v","0","-crf"  ,str(crf)]

    else:
      if useQmax:
        ffmpegcommand+=["-b:v",str(br),"-qmin","0","-qmax",str(qmaxOverride)]
      else:
        ffmpegcommand+=["-b:v",str(br)]

      if cqMode:
        ffmpegcommand+=["-crf", str(crf)]

    bitRateControl = options.get('bitRateControl','Average')

    if not useQmax and sizeLimitMax > 0.0:
      if bitRateControl == 'Limit Maximum':
        ffmpegcommand+=['-maxrate' ,str(br)]
      elif bitRateControl == 'Constant':
        ffmpegcommand+=['-minrate', str(br), '-maxrate' ,str(br)]

    if 'No audio' in options.get('audioChannels','') or passPhase==1:
      ffmpegcommand+=["-an"]    
    elif 'Stereo' in options.get('audioChannels',''):
      ffmpegcommand+=["-ac","2"]    
      ffmpegcommand+=["-ar",'48k']
      ffmpegcommand+=["-b:a",str(audoBitrate)]
    elif 'Mono' in options.get('audioChannels',''):
      ffmpegcommand+=["-ac","1"]
      ffmpegcommand+=["-ar",'48k']
      ffmpegcommand+=["-b:a",str(audoBitrate)]
    elif 'Copy' in options.get('audioChannels',''):
      ffmpegcommand+=["-c:a","copy"]
    else:
      ffmpegcommand+=["-an"]  

    ffmpegcommand+=["-sn"]

    if passPhase==1:
      ffmpegcommand += ['-f', 'null', os.devnull]
    else:
      ffmpegcommand += [tempVideoFilePath]

    logging.debug("Ffmpeg command: {}".format(' '.join(ffmpegcommand)))

    print("Ffmpeg command: {}".format(' '.join(ffmpegcommand)))

    proc = sp.Popen(ffmpegcommand,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
    
    if cqMode:
      encoderStatusCallback(None,None, lastEncodedCRF=crf, lastEncodedSize=None, lastBuff=0, lastWR=widthReduction)
    else:
      encoderStatusCallback(None,None, lastEncodedBR=br, lastEncodedSize=None, lastBuff=bufsize, lastWR=widthReduction)
      

    psnr, returnCode = logffmpegEncodeProgress(proc,'Pass {} {} {}'.format(passNumber,passReason,tempVideoFilePath),totalEncodedSeconds,totalExpectedEncodedSeconds,encoderStatusCallback,passNumber=passPhase,requestId=requestId,tempVideoPath=tempVideoFilePath,options=options)
    if isRquestCancelled(requestId):
      return 0, psnr, returnCode
    if passPhase==1:
      return 0, psnr, returnCode
    else:
      finalSize = os.stat(tempVideoFilePath).st_size
      encoderStatusCallback(None,None,lastEncodedSize=finalSize)
      return finalSize, psnr, returnCode

  encoderFunction.supportsCRQMode=True
  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds)

  minimumPSNR = 0.0
  try:
    minimumPSNR = float(options.get('minimumPSNR',0.0))
  except:
    pass


  optimiser = encodeTargetingSize_linear
  if  'Nelder-Mead' in options.get('optimizer'):
    optimiser = encodeTargetingSize_nelder_mead

  finalFilenameConfirmed = optimiser(encoderFunction=encoderFunction,
                      tempFilename=tempVideoFilePath,
                      outputFilename=videoFilePath,
                      initialDependentValue=initialBr,
                      twoPassMode=True,
                      allowEarlyExitWhenUndersize=globalOptions.get('allowEarlyExitIfUndersized',True),
                      sizeLimitMin=sizeLimitMin,
                      sizeLimitMax=sizeLimitMax,
                      maxAttempts=globalOptions.get('maxEncodeAttempts',6),
                      dependentValueMaximum=options.get('maximumBitrate',0),
                      requestId=requestId,
                      minimumPSNR=minimumPSNR,
                      optimiserName=options.get('optimizer'),
                      options=options,
                      globalOptions=globalOptions)

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds )
  
  encoderStatusCallback('Encoding complete '+videoFilePath,1,finalFilename=finalFilenameConfirmed)
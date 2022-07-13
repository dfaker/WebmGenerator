
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

def encoder(inputsList, outputPathName,filenamePrefix, filtercommand, options, totalEncodedSeconds, totalExpectedEncodedSeconds, statusCallback,requestId=None,encodeStageFilter='null',globalOptions={},packageglobalStatusCallback=print):
  
  audoBitrate = 8
  for abr in ['48','64','96','128','192']:
    if abr in options.get('audioChannels',''):
      audoBitrate = int(abr)*1024

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

  videoFileName,logFilePath,filterFilePath,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'webm', requestId)

  def encoderStatusCallback(text,percentage,**kwargs):
    statusCallback(text,percentage,**kwargs)
    packageglobalStatusCallback(text,percentage)

  def encoderFunction(br, passNumber, passReason, passPhase=0, requestId=None, widthReduction=0.0, bufsize=None):
    
    ffmpegcommand=[]
    ffmpegcommand+=['ffmpeg' ,'-y']
    ffmpegcommand+=inputsList

    if widthReduction>0.0:
      encodefiltercommand = filtercommand+',[outv]{encodeStageFilter},scale=iw*(1-{widthReduction}):ih*(1-{widthReduction}):flags=bicubic[outvfinal]'.format(encodeStageFilter=encodeStageFilter,widthReduction=widthReduction)
    else:
      encodefiltercommand = filtercommand+',[outv]{encodeStageFilter},null[outvfinal]'.format(encodeStageFilter=encodeStageFilter)

    if options.get('audioChannels') == 'No audio':
      encodefiltercommand+=',[outa]anullsink'

    with open(filterFilePath,'wb') as filterFile:
      filterFile.write(encodefiltercommand.encode('utf8'))

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
              targetHeight = max(h,w)
            except:
              pass
    except Exception as e:
      print(e)

    tileColumns  = 0

    if 'No Tile' not in  options.get('outputFormat',''):
      if targetHeight >= 960:
        tileColumns = 1
      if targetHeight >= 1920:
        tileColumns = 2
      if targetHeight >= 3840:
        tileColumns = 3

    print('VP9 targetHeight:',targetHeight)
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
      if sizeLimitMax != 0.0:
        bufsize = str(min(2000000000.0,br*2))

    threadCount = globalOptions.get('encoderStageThreads',4)
    metadataSuffix = globalOptions.get('titleMetadataSuffix',' WmG')
    

    audioCodec = ["-c:a","libopus"]
    if 'Copy' in options.get('audioChannels',''):
      audioCodec = []

    ffmpegcommand+=["-shortest", "-copyts"
                   ,"-start_at_zero", "-c:v","libvpx-vp9"] + audioCodec + [
                    "-stats","-pix_fmt","yuv420p","-bufsize", str(bufsize)
                   ,"-threads", str(threadCount)
                   ,"-auto-alt-ref", "6", "-lag-in-frames", "25"]


    if passPhase==1:
      pass
    else:
      ffmpegcommand += ['-speed', '1']

    if 'BEST' in  options.get('outputFormat','').upper():
      ffmpegcommand+=["-quality","best"]
    else:
      ffmpegcommand+=["-quality","good"]

    ffmpegcommand+=['-psnr', '-row-mt', '1', '-tile-columns', str(tileColumns), "-tile-rows", "0"
                   ,"-arnr-maxframes", "7","-arnr-strength", "5"
                   ,"-aq-mode", "0", "-tune-content", "film", "-enable-tpl", "1", "-frame-parallel", "0"
                   ,"-metadata", 'Title={}'.format(filenamePrefix.replace('-','-') + metadataSuffix) 
                   ,"-metadata", 'WritingApp=WebmGenerator {}'.format(RELEASE_NUMVER)
                   ,"-metadata", 'DateUTC={}'.format(datetime.datetime.utcnow().isoformat() ) ]
    
    if sizeLimitMax == 0.0:
      ffmpegcommand+=["-b:v","0","-qmin","0","-qmax","20","-crf"  ,'4']
    else:
      ffmpegcommand+=["-b:v",str(br),"-qmin","0","-qmax","20","-crf"  ,'4']

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
    proc = sp.Popen(ffmpegcommand,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
    encoderStatusCallback(None,None, lastEncodedBR=br, lastEncodedSize=None, lastBuff=bufsize, lastWR=widthReduction)
    psnr, returnCode = logffmpegEncodeProgress(proc,'Pass {} {} {}'.format(passNumber,passReason,tempVideoFilePath),totalEncodedSeconds,totalExpectedEncodedSeconds,encoderStatusCallback,passNumber=passPhase,requestId=requestId)
    if isRquestCancelled(requestId):
      return 0, psnr, returnCode
    if passPhase==1:
      return 0, psnr, returnCode
    else:
      finalSize = os.stat(tempVideoFilePath).st_size
      encoderStatusCallback(None,None,lastEncodedSize=finalSize)
      return finalSize, psnr, returnCode

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds)

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
                      optimiserName=options.get('optimizer'))

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds )
  
  encoderStatusCallback('Encoding complete '+videoFilePath,1,finalFilename=finalFilenameConfirmed)
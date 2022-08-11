
import os
import logging
import subprocess as sp

from ..encodingUtils import getFreeNameForFileAndLog
from ..encodingUtils import logffmpegEncodeProgress
from ..encodingUtils import isRquestCancelled

from ..optimisers.nelderMead import encodeTargetingSize as encodeTargetingSize_nelder_mead
from ..optimisers.linear     import encodeTargetingSize as encodeTargetingSize_linear

def encoder(inputsList, outputPathName,filenamePrefix, filtercommand, options, totalEncodedSeconds, totalExpectedEncodedSeconds, statusCallback,requestId=None,encodeStageFilter='null',globalOptions={},packageglobalStatusCallback=print):
  
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

  videoFileName,logFilePath,filterFilePath,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'mp4', requestId)

  def encoderStatusCallback(text,percentage,**kwargs):
    statusCallback(text,percentage,**kwargs)
    packageglobalStatusCallback(text,percentage)

  def encoderFunction(br,passNumber,passReason,passPhase=0, requestId=None,widthReduction=0.0,bufsize=None, cqMode=False):
    
    ffmpegcommand=[]
    ffmpegcommand+=['ffmpeg' ,'-y']
    ffmpegcommand+=inputsList



    if widthReduction>0.0:
      encodefiltercommand = filtercommand+',[outv]scale=iw*(1-{widthReduction}):ih*(1-{widthReduction}):flags=bicubic[outvfinal]'.format(widthReduction=widthReduction)
    else:
      encodefiltercommand = filtercommand+',[outv]null[outvfinal]'.format(widthReduction=widthReduction)

    if options.get('audioChannels') == 'No audio':
      encodefiltercommand+=',[outa]anullsink'

    with open(filterFilePath,'wb') as filterFile:
      filterFile.write(encodefiltercommand.encode('utf8'))

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

    presetNum = 8
    try:
      presetNum = options.get('svtav1Preset',8)
    except Exception as e:
      print(e)


    ffmpegcommand+=["-shortest", "-slices", "8", "-copyts"
                   ,"-start_at_zero", "-c:v","libsvtav1"] + audioCodec + [
                    "-stats","-pix_fmt","yuv420p","-bufsize", str(bufsize)
                   ,"-threads", str(threadCount),"-crf"  ,'25','-g', '300'
                   ,'-psnr','-cpu-used','0','-row-mt', '1',  '-preset', str(presetNum)
                   ,"-metadata", 'title={}'.format(filenamePrefix.replace('-',' -') + metadataSuffix) ]
    
    if sizeLimitMax == 0.0:
      ffmpegcommand+=["-b:v","0","-qmin","0","-qmax","10"]
    else:
      ffmpegcommand+=["-b:v",str(br)]

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
    psnr, returnCode = logffmpegEncodeProgress(proc,'Pass {} {} {}'.format(passNumber,passReason,tempVideoFilePath),totalEncodedSeconds,totalExpectedEncodedSeconds,encoderStatusCallback,passNumber=passPhase,requestId=requestId,tempVideoPath=tempVideoFilePath,options=options)
    if isRquestCancelled(requestId):
      return 0, psnr, returnCode
    if passPhase==1:
      return 0, psnr, returnCode
    else:
      finalSize = os.stat(tempVideoFilePath).st_size
      encoderStatusCallback(None,None,lastEncodedSize=finalSize)
      return finalSize, psnr, returnCode

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds)

  encoderFunction.supportsCRQMode=False
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
                      optimiserName=options.get('optimizer'),
                      options=options,
                      globalOptions=globalOptions)

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds )
  
  encoderStatusCallback('Encoding complete '+videoFilePath,1,finalFilename=finalFilenameConfirmed)
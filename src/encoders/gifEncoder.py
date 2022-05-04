
import os
import logging
import subprocess as sp

from ..encodingUtils import getFreeNameForFileAndLog
from ..encodingUtils import logffmpegEncodeProgress
from ..encodingUtils import isRquestCancelled

from ..optimisers.nelderMead import encodeTargetingSize as encodeTargetingSize_nelder_mead
from ..optimisers.linear     import encodeTargetingSize as encodeTargetingSize_linear

def encoder(inputsList, outputPathName,filenamePrefix, filtercommand, options, totalEncodedSeconds, totalExpectedEncodedSeconds, statusCallback,encodeStageFilter='null',requestId=None,globalOptions={},packageglobalStatusCallback=print):

  if options.get('maximumSize') == 0.0:
    sizeLimitMax = float('inf')
    sizeLimitMin = float('-inf')
  else:
    sizeLimitMax = options.get('maximumSize')*1024*1024
    sizeLimitMin = sizeLimitMax*(1.0-globalOptions.get('allowableTargetSizeUnderrun',0.25))

  videoFileName,logFilePath,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'gif', requestId)

  def encoderStatusCallback(text,percentage,**kwargs):
    statusCallback(text,percentage,**kwargs)
    packageglobalStatusCallback(text,percentage)

  def encoderFunction(width,passNumber,passReason,passPhase=0,requestId=None,widthReduction=0.0,bufsize=None):

    giffiltercommand = filtercommand+',[outv]scale=w=iw*sar:h=ih,setsar=sar=1/1,scale=\'max({}\\,min({}\\,iw)):-1\':flags=area,split[pal1][outvpal],[pal1]palettegen=stats_mode=diff[plt],[outvpal][plt]paletteuse=dither=floyd_steinberg:[outvgif],[outa]anullsink'.format(0,width)

    ffmpegcommand=[]
    ffmpegcommand+=['ffmpeg' ,'-y']
    ffmpegcommand+=inputsList
    ffmpegcommand+=['-filter_complex',giffiltercommand]
    ffmpegcommand+=['-map','[outvgif]']
    ffmpegcommand+=["-vsync", 'passthrough'
                   ,"-shortest" 
                   ,"-copyts"
                   ,"-start_at_zero"
                   ,"-stats"
                   ,"-an"
                   ,'-psnr'
                   ,"-sn",tempVideoFilePath]

    encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds)

    proc = sp.Popen(ffmpegcommand,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
    psnr, returnCode = logffmpegEncodeProgress(proc,'Pass {} {} {}'.format(passNumber,passReason,videoFileName),totalEncodedSeconds,totalExpectedEncodedSeconds,encoderStatusCallback,passNumber=0,requestId=requestId)
    if isRquestCancelled(requestId):
      return 0, psnr, returnCode
    finalSize = os.stat(tempVideoFilePath).st_size
    encoderStatusCallback(None,None,lastEncodedSize=finalSize)
    return finalSize, psnr, returnCode

  initialWidth = options.get('maximumWidth',1280)

  optimiser = encodeTargetingSize_linear
  if  'Nelder-Mead' in options.get('optimizer'):
    optimiser = encodeTargetingSize_nelder_mead

  finalFilenameConfirmed = optimiser(encoderFunction=encoderFunction,
                      tempFilename=tempVideoFilePath,
                      outputFilename=videoFilePath,
                      initialDependentValue=initialWidth,
                      sizeLimitMin=sizeLimitMin,
                      sizeLimitMax=sizeLimitMax,
                      allowEarlyExitWhenUndersize=globalOptions.get('allowEarlyExitIfUndersized',True),
                      maxAttempts=globalOptions.get('maxEncodeAttemptsGif',10),
                      dependentValueName='Width',
                      dependentValueMaximum=options.get('maximumWidth',0),
                      requestId=requestId,
                      optimiserName=options.get('optimizer'))

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds )
  encoderStatusCallback('Encoding complete '+videoFilePath,1,finalFilename=finalFilenameConfirmed)
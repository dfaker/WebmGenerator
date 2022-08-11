
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

  videoFileName,logFilePath,filterFilePath,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'png', requestId)

  def encoderStatusCallback(text,percentage,**kwargs):
    statusCallback(text,percentage,**kwargs)
    packageglobalStatusCallback(text,percentage)

  def encoderFunction(width,passNumber,passReason,passPhase=0,requestId=None,widthReduction=0.0,bufsize=None, cqMode=False):

    giffiltercommand = filtercommand+',[outv]scale=w=iw*sar:h=ih,setsar=sar=1/1,scale=\'max({}\\,min({}\\,iw)):-1\':flags=area[outvgif],[outa]anullsink'.format(0,width)

    with open(filterFilePath,'wb') as filterFile:
      filterFile.write(giffiltercommand.encode('utf8'))

    ffmpegcommand=[]
    ffmpegcommand+=['ffmpeg' ,'-y']
    ffmpegcommand+=inputsList
    ffmpegcommand+=['-plays', '0']
    ffmpegcommand+=['-filter_complex_script',filterFilePath]
    ffmpegcommand+=['-map','[outvgif]']
    ffmpegcommand+=["-vsync", 'passthrough'
                   ,"-shortest" 
                   ,"-copyts"
                   ,"-start_at_zero"
                   ,"-stats"
                   ,"-an"
                   ,'-psnr'
                   ,"-f","apng"
                   ,"-sn",tempVideoFilePath]

    encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds)

    proc = sp.Popen(ffmpegcommand,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
    psnr, returnCode = logffmpegEncodeProgress(proc,'Pass {} {} {}'.format(passNumber,passReason,videoFileName),totalEncodedSeconds,totalExpectedEncodedSeconds,encoderStatusCallback,passNumber=0,requestId=requestId,tempVideoPath=tempVideoFilePath,options=options)
    if isRquestCancelled(requestId):
      return 0, psnr, returnCode
    finalSize = os.stat(tempVideoFilePath).st_size
    encoderStatusCallback(None,None,lastEncodedSize=finalSize)
    return finalSize, psnr, returnCode

  initialWidth = options.get('maximumWidth',1280)

  encoderFunction.supportsCRQMode=False
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
                      optimiserName=options.get('optimizer'),
                      globalOptions=globalOptions)

  encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds )
  encoderStatusCallback('Encoding complete '+videoFilePath,1,finalFilename=finalFilenameConfirmed)
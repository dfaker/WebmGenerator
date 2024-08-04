
import os
import logging
import subprocess as sp

from ..ffmpegInfoParser import getVideoInfo

from math import sqrt

from ..encodingUtils import getFreeNameForFileAndLog
from ..encodingUtils import logffmpegEncodeProgress
from ..encodingUtils import isRquestCancelled

from ..optimisers.nelderMead import encodeTargetingSize as encodeTargetingSize_nelder_mead
from ..optimisers.linear     import encodeTargetingSize as encodeTargetingSize_linear

def encoder(inputsList, outputPathName,filenamePrefix, filtercommand, options, totalEncodedSeconds, totalExpectedEncodedSeconds, statusCallback,encodeStageFilter='null',requestId=None,globalOptions={},packageglobalStatusCallback=print,startEndTimestamps=None):

  if options.get('maximumSize') == 0.0:
    sizeLimitMax = float('inf')
    sizeLimitMin = float('-inf')
  else:
    sizeLimitMax = options.get('maximumSize')*1024*1024
    sizeLimitMin = sizeLimitMax*(1.0-globalOptions.get('allowableTargetSizeUnderrun',0.25))

  intervideoFileName,interlogFilePath, interfilterFilePath, intertempVideoFilePath, intervideoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'mp4', requestId)
  videoFileName,logFilePath,filterFilePath,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(filenamePrefix, 'gif', requestId)

  def encoderStatusCallback(text,percentage,**kwargs):
    statusCallback(text,percentage,**kwargs)
    packageglobalStatusCallback(text,percentage)

  def encoderFunction(width,passNumber,passReason,passPhase=0,requestId=None,widthReduction=0.0,bufsize=None, cqMode=False):


    gifFPSLimit=''
    if options.get('forceGifFPS',True):
      gifFPSLimit='fps=18,'

    giffiltercommand = filtercommand+',[outv]scale=w=iw*sar:h=ih,setsar=sar=1/1[outvgif],[outa]anullsink'


    with open(interfilterFilePath,'wb') as filterFile:
      filterFile.write(giffiltercommand.encode('utf8'))

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

    ffmpegcommand+=['-filter_complex_script',interfilterFilePath]
    ffmpegcommand+=['-map','[outvgif]']
    ffmpegcommand+=['-pix_fmt', 'yuv444p' 
                   ,'-f', "yuv4mpegpipe"
                   ,'-strict', '-1'
                   ,"-sn",'-']

    encoderStatusCallback('Encoding final '+videoFileName,(totalEncodedSeconds)/totalExpectedEncodedSeconds)

    proc = sp.Popen(ffmpegcommand,stderr=sp.DEVNULL,stdin=sp.DEVNULL,stdout=sp.PIPE)
    proc2 = sp.Popen(['gifski', '-o', tempVideoFilePath, '--extra', '--width', str(width), '-'],stdin=sp.PIPE)

    psnr, returnCode = logffmpegEncodeProgress(proc,'Pass {} {} {}'.format(passNumber,passReason,videoFileName),totalEncodedSeconds,totalExpectedEncodedSeconds,encoderStatusCallback,framesink=proc2,passNumber=0,requestId=requestId,tempVideoPath=tempVideoFilePath,options=options)

    encoderStatusCallback('Encoding gifski '+videoFileName,0.80)


    encoderStatusCallback('Encoding gifski final'+videoFileName,0.9)

    psnr,returnCode = 100,0

    if isRquestCancelled(requestId):
      return 0, psnr, returnCode

    finalSize = os.stat(tempVideoFilePath).st_size
    encoderStatusCallback(None,None,lastEncodedSize=finalSize)

    encoderStatusCallback('Encoding gifski final'+videoFileName,0.95)

    return finalSize, psnr, returnCode

  initialWidth = options.get('maximumWidth',1280) 

  print('initialWidth',initialWidth)
  print('inputsList',inputsList)
  try:
    if len(inputsList) == 2:
        vi = getVideoInfo(inputsList[1])

        if options.get('forceGifFPS',True):
            vi.fps = 18

        area = sizeLimitMax/(vi.duration*vi.fps)
        print('area',area)
        tw = int(sqrt(area*(vi.width/vi.height)))
        th = int(sqrt(area*(vi.height/vi.width)))
        initialWidth = int(max(tw,th)*1.2)
        print('TARGET WIDTH',initialWidth)
  except Exception as e:
    print('TARGET WIDTH Exception',e)

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
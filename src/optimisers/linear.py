

import shutil
import logging

from ..encodingUtils import isRquestCancelled

def encodeTargetingSize(encoderFunction,tempFilename,outputFilename,initialDependentValue,sizeLimitMin,sizeLimitMax,maxAttempts,twoPassMode=False,dependentValueName='BR',requestId=None,minimumPSNR=0.0,optimiserName=''):

  val = initialDependentValue
  targetSizeMedian = (sizeLimitMin+sizeLimitMax)/2
  smallestFailedOverMaximum=None
  largestFailedUnderMinimum=None
  passCount=0
  lastFailReason=''
  passReason='Initial Pass'
  lastpsnr = None
  psnrAdjusted=False
  widthReduction = 0.0
  while 1:
    val=int(val)
    passCount+=1

    if isRquestCancelled(requestId):
      return

    if twoPassMode:
      passReason='Stats Pass {} {}'.format(passCount+1,lastFailReason)
      _         = encoderFunction(val,passCount,passReason,passPhase=1,requestId=requestId,widthReduction=widthReduction)
      passReason='Encode Pass {} {}'.format(passCount+1,lastFailReason)
      finalSize,lastpsnr = encoderFunction(val,passCount,passReason,passPhase=2,requestId=requestId,widthReduction=widthReduction)
    else:
      passReason='Encode Pass {} {}'.format(passCount+1,lastFailReason)
      finalSize,lastpsnr = encoderFunction(val,passCount,passReason,requestId=requestId,widthReduction=widthReduction)

    if isRquestCancelled(requestId):
      return

    adjustval = True
    if lastpsnr is not None and lastpsnr < minimumPSNR and (widthReduction+0.1)<=1.0:
      widthReduction+=0.1
      maxAttempts += passCount
      adjustval=False
      psnrAdjusted=True
      lastFailReason = 'PSNR under {} ({}), resetting at smaller dimensions'.format(minimumPSNR,lastpsnr)
    elif sizeLimitMin<finalSize<sizeLimitMax or ( (not psnrAdjusted) and passCount==1 and finalSize<sizeLimitMax) or passCount>maxAttempts:
      shutil.move(tempFilename,outputFilename)
      return outputFilename
    elif finalSize<sizeLimitMin:
      lastFailReason = 'File too small, {} increase'.format(dependentValueName)
      if largestFailedUnderMinimum is None or val>largestFailedUnderMinimum:
        largestFailedUnderMinimum=val
    elif finalSize>sizeLimitMax:
      lastFailReason = 'File too large, {} decrease'.format(dependentValueName)
      if smallestFailedOverMaximum is None or val<smallestFailedOverMaximum:
        smallestFailedOverMaximum=val
    logging.debug("Encode complete {}:{} finalSize:{} targetSizeMedian:{}".format(dependentValueName,val,finalSize,targetSizeMedian))

    if adjustval:
      val =  val * (1/(finalSize/targetSizeMedian))
      if largestFailedUnderMinimum is not None and smallestFailedOverMaximum is not None:
        val = (largestFailedUnderMinimum+smallestFailedOverMaximum)/2
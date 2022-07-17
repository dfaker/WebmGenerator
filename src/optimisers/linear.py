

import shutil
import logging

from ..encodingUtils import isRquestCancelled

def encodeTargetingSize(encoderFunction,tempFilename,outputFilename,initialDependentValue,sizeLimitMin,sizeLimitMax,maxAttempts,allowEarlyExitWhenUndersize=True,twoPassMode=False,dependentValueName='BR',dependentValueMaximum=0,requestId=None,minimumPSNR=0.0,optimiserName='',options={},globalOptions={}):

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

  print('------')
  print('dependentValueMaximum',dependentValueMaximum)
  print('val',val)
  print('------')

  while 1:
    val=int(val)
    passCount+=1

    if dependentValueMaximum is not None and dependentValueMaximum > 0:
      val = min(val,dependentValueMaximum)

    if isRquestCancelled(requestId):
      return

    if twoPassMode:
      passReason='Stats Pass {} {}'.format(passCount+1,lastFailReason)
      _         = encoderFunction(val,passCount,passReason,passPhase=1,requestId=requestId,widthReduction=widthReduction)
      passReason='Encode Pass {} {}'.format(passCount+1,lastFailReason)
      finalSize,lastpsnr,returnCode = encoderFunction(val,passCount,passReason,passPhase=2,requestId=requestId,widthReduction=widthReduction)
    else:
      passReason='Encode Pass {} {}'.format(passCount+1,lastFailReason)
      finalSize,lastpsnr,returnCode = encoderFunction(val,passCount,passReason,requestId=requestId,widthReduction=widthReduction)

    if isRquestCancelled(requestId):
      return

    adjustval = True

    widthReductionFactor = globalOptions.get('defaultPSNRWidthReductionFactor',0.5)

    if lastpsnr is not None and lastpsnr < minimumPSNR and (widthReduction+widthReductionFactor)<=1.0:
      widthReduction+=widthReductionFactor
      maxAttempts += passCount
      adjustval=False
      psnrAdjusted=True
      lastFailReason = 'PSNR under {} ({}), resetting at smaller dimensions'.format(minimumPSNR,lastpsnr)
      continue
    elif returnCode == 1:
      return
    elif sizeLimitMin<finalSize<sizeLimitMax or ( (not psnrAdjusted) and allowEarlyExitWhenUndersize and passCount==1 and finalSize<sizeLimitMax) or passCount>maxAttempts:
      shutil.move(tempFilename,outputFilename)
      return outputFilename
    elif finalSize<sizeLimitMin:
      lastFailReason = 'File too small {:.2%}, {} increase'.format(finalSize/sizeLimitMin,dependentValueName)
      if largestFailedUnderMinimum is None or val>largestFailedUnderMinimum:
        largestFailedUnderMinimum=val
    elif finalSize>sizeLimitMax:
      lastFailReason = 'File too large {:.2%}, {} decrease'.format(finalSize/sizeLimitMax,dependentValueName)
      if smallestFailedOverMaximum is None or val<smallestFailedOverMaximum:
        smallestFailedOverMaximum=val
    logging.debug("Encode complete {}:{} finalSize:{} targetSizeMedian:{}".format(dependentValueName,val,finalSize,targetSizeMedian))



    if adjustval:
      val =  val * (1/(finalSize/targetSizeMedian))
      if largestFailedUnderMinimum is not None and smallestFailedOverMaximum is not None:
        val = (largestFailedUnderMinimum+smallestFailedOverMaximum)/2


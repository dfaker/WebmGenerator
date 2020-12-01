

import shutil
import math
import numpy as np
import copy

def nelder_mead(f, x_start,x_upper=None,x_lower=None,extra_args={},
                step=0.1, no_improve_thr=10e-6,
                no_improv_break=10, max_iter=0,
                alpha=1., gamma=2., rho=-0.5, sigma=0.5, min_iter_before_acceptable=3):
  '''
      @param f (function): function to optimize, must return a scalar score
          and operate over a numpy array of the same dimensions as x_start
      @param x_start (numpy array): initial position
      @param step (float): look-around radius in initial step
      @no_improv_thr,  no_improv_break (float, int): break after no_improv_break iterations with
          an improvement lower than no_improv_thr
      @max_iter (int): always break after this number of iterations.
          Set it to 0 to loop indefinitely.
      @alpha, gamma, rho, sigma (floats): parameters of the algorithm
          (see Wikipedia page for reference)
      return: tuple (best parameter array, best score)
  '''

  # init

  def contstrain(x,lower,upper):
    if lower is not None and upper is not None:
      return np.minimum(np.maximum(x, lower),upper)
    return x

  lastEncodeParams = None

  assert(len(step)==len(x_start))

  dim = len(x_start)
  x_start = contstrain(x_start, x_lower, x_upper)
  prev_best,isAcceptable = f(x_start,**extra_args)
  lastEncodeParams = x_start

  no_improv = 0
  res = [[x_start, prev_best]]

  for i in range(dim):
    x = copy.copy(x_start)
    x[i] = x[i] + step[i]
    x = contstrain(x, x_lower, x_upper)
    score,isAcceptable = f(x,**extra_args)
    lastEncodeParams = x
    res.append([x, score])

  # simplex iter
  iters = 0
  while 1:
    # order
    res.sort(key=lambda x: x[1])
    best = res[0][1]

    # break after max_iter
    if max_iter and iters >= max_iter:
        print(lastEncodeParams,res[0])
        if (lastEncodeParams == res[0][0]).all():
          return res[0]
        else:
          f(res[0],**extra_args)
          return res[0]
    iters += 1

    if best < prev_best - no_improve_thr:
        no_improv = 0
        prev_best = best
    else:
        no_improv += 1

    if no_improv >= no_improv_break:
      print(lastEncodeParams,res[0])
      if (lastEncodeParams == res[0][0]).all():
        return res[0]
      else:
        f(res[0])
        return res[0]

    # centroid
    x0 = [0.] * dim
    for tup in res[:-1]:
        for i, c in enumerate(tup[0]):
            x0[i] += c / (len(res)-1)

    # reflection
    xr = x0 + alpha*(x0 - res[-1][0])
    xr = contstrain(xr, x_lower, x_upper)
    rscore,isAcceptable = f(xr,**extra_args)
    lastEncodeParams = xr
    if isAcceptable and iters >= min_iter_before_acceptable:
      return xr
    if res[0][1] <= rscore < res[-2][1]:
        del res[-1]
        res.append([xr, rscore])
        continue

    # expansion
    if rscore < res[0][1]:
        xe = x0 + gamma*(x0 - res[-1][0])
        xe = contstrain(xe, x_lower, x_upper)
        escore,isAcceptable = f(xe,**extra_args)
        lastEncodeParams = xe
        if isAcceptable and iters >= min_iter_before_acceptable:
          return xe
        if escore < rscore:
            del res[-1]
            res.append([xe, escore])
            continue
        else:
            del res[-1]
            res.append([xr, rscore])
            continue

    # contraction
    xc = x0 + rho*(x0 - res[-1][0])
    xc = contstrain(xc, x_lower, x_upper)
    cscore,isAcceptable = f(xc,**extra_args)
    lastEncodeParams = xc
    if isAcceptable and iters >= min_iter_before_acceptable:
      return xc
    if cscore < res[-1][1]:
        del res[-1]
        res.append([xc, cscore])
        continue

    # reduction
    x1 = res[0][0]
    nres = []
    for tup in res:
        redx = x1 + sigma*(tup[0] - x1)
        redx = contstrain(redx, x_lower, x_upper)
        score,isAcceptable = f(redx,**extra_args)
        lastEncodeParams = redx
        if isAcceptable and iters >= min_iter_before_acceptable:
          return xc
        nres.append([redx, score])
    res = nres


def encodeTargetingSize(encoderFunction,tempFilename,outputFilename,initialDependentValue,sizeLimitMin,sizeLimitMax,maxAttempts,twoPassMode=False,dependentValueName='BR',requestId=None,minimumPSNR=0.0,optimiserName='Nelder-Mead - Early Exit'):
  val = initialDependentValue
  targetSizeMedian = (sizeLimitMin+sizeLimitMax)/2
  smallestFailedOverMaximum=None
  largestFailedUnderMinimum=None
  passCount=0
  lastFailReason=''
  passReason='Initial Pass'
  widthReduction = 0.0


  if minimumPSNR > 0.0:
    min_iter_before_acceptable = 3
    
    x_start  = np.array([initialDependentValue,0.0])
    x_upper = np.array([initialDependentValue*1.9,0.9])
    x_lower = np.array([initialDependentValue/2,0.0])

    x_step   = [initialDependentValue*0.1,0.01]
    x_argNames = {'argNames':['br','wr']}
  elif 'Exhaustive' in optimiserName:
    min_iter_before_acceptable = float('inf')
    max_iter = 0

    x_start = np.array([initialDependentValue,0.0,initialDependentValue*2])
    x_upper = np.array([initialDependentValue*1.9,0.9,initialDependentValue*2])
    x_lower = np.array([initialDependentValue/2,0.0,initialDependentValue/5])

    x_step  = [initialDependentValue*0.1,0.01,initialDependentValue*0.1]
    x_argNames = {'argNames':['br','wr','buf']}
  else:
    min_iter_before_acceptable = 1
    
    x_start = np.array([initialDependentValue])
    x_upper = np.array([initialDependentValue*1.9])
    x_lower = np.array([initialDependentValue/2])

    x_step  = [initialDependentValue*0.1]
    x_argNames = {'argNames':['br']}

  max_iter = 15
  if 'Exhaustive' in optimiserName:
    min_iter_before_acceptable = float('inf')
    max_iter = 0

  def encodeOptimizationWrapper(x,argNames=None):
    nonlocal passCount

    passCount+=1

    widthReduction = 0.0
    buff=None
    bitrate=0.0


    if argNames == ['br']:
      bitrate = x[0]
      widthReduction=0.0
      buff=None
    elif argNames == ['br','wr']:
      bitrate = x[0]
      widthReduction=x[1]
      buff=None
    elif argNames == ['br','wr','buf']:
      bitrate = x[0]
      widthReduction=x[1]
      buff=x[2]

    
    if widthReduction >= 0.9:
      widthReduction = 0.9
    elif widthReduction <= 0.0:
      widthReduction = 0.0

    bitrate = int(bitrate)
    widthReduction = round(widthReduction,3)

    if buff is not None:
      buff=int(buff)

    if twoPassMode:
      passReason='Nelder-Mead Stats Pass {} {}'.format(passCount+1,lastFailReason)
      _         = encoderFunction(bitrate,passCount,passReason,passPhase=1,requestId=requestId,widthReduction=widthReduction,bufsize=buff)
      passReason='Nelder-Mead Encode Pass {} {}'.format(passCount+1,lastFailReason)
      finalSize,lastpsnr = encoderFunction(bitrate,passCount,passReason,passPhase=2,requestId=requestId,widthReduction=widthReduction,bufsize=buff)
    else:
      passReason='Nelder-Mead Encode Pass {} {}'.format(passCount+1,lastFailReason)
      finalSize,lastpsnr = encoderFunction(bitrate,passCount,passReason,requestId=requestId,widthReduction=widthReduction,bufsize=buff)

    try:
      if lastpsnr is not None and lastpsnr != float('inf'):
        psnrScore           = (52-lastpsnr)/52
      elif lastpsnr == float('inf'):
        psnrScore = 0.0
      else:
        psnrScore = 1

      widthReductionScore = widthReduction

      sizeScore           = abs(finalSize-sizeLimitMax)/sizeLimitMax
      if finalSize > sizeLimitMax:
        sizeScore  = abs(abs(finalSize-sizeLimitMax)/sizeLimitMax)*100
      bitrateScore = (initialDependentValue*2)/bitrate

      score = psnrScore+widthReductionScore+sizeScore+bitrateScore
    except Exception as e:
      print(e)
      score = float('inf')



    print("Optimzation pass complete - score: {} bitrate:{} widthReduction:{}  finalSize:{}  psnr:{}  ".format(score,bitrate,widthReduction,finalSize,lastpsnr))

    isAcceptable = (sizeLimitMin<finalSize<=sizeLimitMax and lastpsnr is not None and lastpsnr > minimumPSNR ) 

    return score,isAcceptable
    

  x = nelder_mead(encodeOptimizationWrapper, x_start, x_upper=x_upper, x_lower=x_lower, step=x_step, extra_args=x_argNames, max_iter=15, min_iter_before_acceptable=min_iter_before_acceptable)
  shutil.move(tempFilename,outputFilename)
  return outputFilename
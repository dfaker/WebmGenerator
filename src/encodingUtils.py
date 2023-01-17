

import threading
import os
import logging
from datetime import datetime
import math
from collections import deque

filesPlannedForCreation = set()
fileExistanceLock = threading.Lock()

cancelledEncodeIds = set()

def isRquestCancelled(requestId):
  global cancelledEncodeIds
  return requestId in cancelledEncodeIds or -1 in cancelledEncodeIds

packageglobalStatusCallback=print

def idfunc(s):return s

getShortPathName = idfunc

try:
  import win32api
  getShortPathName=win32api.GetShortPathName
except Exception as e:
  logging.error("win32api getShortPathName Exception", exc_info=e)

def cleanFilenameForFfmpeg(filename):
  return getShortPathName(os.path.normpath(filename))

def cancelCurrentEncodeRequest(requestId):
  global cancelledEncodeIds
  cancelledEncodeIds.add(requestId)


bit_depths = {
"yuv420p": 8, "yuyv422": 8, "rgb24": 8, "bgr24": 8, "yuv422p": 8, "yuv444p": 8, "yuv410p": 8, 
"yuv411p": 8, "gray": 8, "monow": 1, "monob": 1, "pal8": 8, "yuvj420p": 8, "yuvj422p": 8, 
"yuvj444p": 8, "uyvy422": 8, "uyyvyy411": 8, "bgr8": 3, "bgr4": 1, "bgr4_byte": 1, "rgb8": 2, 
"rgb4": 1, "rgb4_byte": 1, "nv12": 8, "nv21": 8, "argb": 8, "rgba": 8, "abgr": 8, "bgra": 8, 
"gray16be": 16, "gray16le": 16, "yuv440p": 8, "yuvj440p": 8, "yuva420p": 8, "rgb48be": 16, 
"rgb48le": 16, "rgb565be": 5, "rgb565le": 5, "rgb555be": 5, "rgb555le": 5, "bgr565be": 5, 
"bgr565le": 5, "bgr555be": 5, "bgr555le": 5, "vaapi": 0, "yuv420p16le": 16, 
"yuv420p16be": 16, "yuv422p16le": 16, "yuv422p16be": 16, "yuv444p16le": 16, 
"yuv444p16be": 16, "dxva2_vld": 0, "rgb444le": 4, "rgb444be": 4, "bgr444le": 4, 
"bgr444be": 4, "ya8": 8, "bgr48be": 16, "bgr48le": 16, "yuv420p9be": 9, "yuv420p9le": 9, 
"yuv420p10be": 10, "yuv420p10le": 10, "yuv422p10be": 10, "yuv422p10le": 10, 
"yuv444p9be": 9, "yuv444p9le": 9, "yuv444p10be": 10, "yuv444p10le": 10, "yuv422p9be": 9, 
"yuv422p9le": 9, "gbrp": 8, "gbrp9be": 9, "gbrp9le": 9, "gbrp10be": 10, "gbrp10le": 10, 
"gbrp16be": 16, "gbrp16le": 16, "yuva422p": 8, "yuva444p": 8, "yuva420p9be": 9, 
"yuva420p9le": 9, "yuva422p9be": 9, "yuva422p9le": 9, "yuva444p9be": 9, "yuva444p9le": 9, 
"yuva420p10be": 10, "yuva420p10le": 10, "yuva422p10be": 10, "yuva422p10le": 10, 
"yuva444p10be": 10, "yuva444p10le": 10, "yuva420p16be": 16, "yuva420p16le": 16, 
"yuva422p16be": 16, "yuva422p16le": 16, "yuva444p16be": 16, "yuva444p16le": 16, 
"vdpau": 0, "xyz12le": 12, "xyz12be": 12, "nv16": 8, "nv20le": 10, "nv20be": 10, "rgba64be": 16, 
"rgba64le": 16, "bgra64be": 16, "bgra64le": 16, "yvyu422": 8, "ya16be": 16, "ya16le": 16, 
"gbrap": 8, "gbrap16be": 16, "gbrap16le": 16, "qsv": 0, "mmal": 0, "d3d11va_vld": 0, "cuda": 0, 
"0rgb": 8, "rgb0": 8, "0bgr": 8, "bgr0": 8, "yuv420p12be": 12, "yuv420p12le": 12, 
"yuv420p14be": 14, "yuv420p14le": 14, "yuv422p12be": 12, "yuv422p12le": 12, 
"yuv422p14be": 14, "yuv422p14le": 14, "yuv444p12be": 12, "yuv444p12le": 12, 
"yuv444p14be": 14, "yuv444p14le": 14, "gbrp12be": 12, "gbrp12le": 12, 
"gbrp14be": 14, "gbrp14le": 14, "yuvj411p": 8, "bayer_bggr8": 2, "bayer_rggb8": 2, 
"bayer_gbrg8": 2, "bayer_grbg8": 2, "bayer_bggr16le": 4, "bayer_bggr16be": 4, 
"bayer_rggb16le": 4, "bayer_rggb16be": 4, "bayer_gbrg16le": 4, "bayer_gbrg16be": 4, 
"bayer_grbg16le": 4, "bayer_grbg16be": 4, "xvmc": 0, "yuv440p10le": 10, "yuv440p10be": 10, 
"yuv440p12le": 12, "yuv440p12be": 12, "ayuv64le": 16, "ayuv64be": 16, "videotoolbox_vld": 0, 
"p010le": 10, "p010be": 10, "gbrap12be": 12, "gbrap12le": 12, "gbrap10be": 10, "gbrap10le": 10, 
"mediacodec": 0, "gray12be": 12, "gray12le": 12, "gray10be": 10, "gray10le": 10, "p016le": 16, 
"p016be": 16, "d3d11": 0, "gray9be": 9, "gray9le": 9, "gbrpf32be": 32, "gbrpf32le": 32, "gbrapf32be": 32, 
"gbrapf32le": 32, "drm_prime": 0, "opencl": 0, "gray14be": 14, "gray14le": 14, "grayf32be": 32, 
"grayf32le": 32, "yuva422p12be": 12, "yuva422p12le": 12, "yuva444p12be": 12, "yuva444p12le": 12, 
"nv24": 8, "nv42": 8, "vulkan": 0, "y210be": 10, "y210le": 10, "x2rgb10le": 10, "x2rgb10be": 10, 
"x2bgr10le": 10, "x2bgr10be": 10, "p210be": 10, "p210le": 10, "p410be": 10, "p410le": 10, "p216be": 16, 
"p216le": 16, "p416be": 16, "p416le": 16, "vuya": 8, "rgbaf16be": 16, "rgbaf16le": 16, "vuyx": 8, 
"p012le": 12, "p012be": 12, "y212be": 12, "y212le": 12, "xv30be": 10, "xv30le": 10, "xv36be": 12, 
"xv36le": 12, "rgbf32be": 32, "rgbf32le": 32, "rgbaf32be": 32, "rgbaf32le": 32
}

def getFreeNameForFileAndLog(filenamePrefix, extension, initialFileN=1):

  try:
    fileN=int(initialFileN)
  except Exception as e:
    print(e)
    fileN=1

  with fileExistanceLock:
    while True:
      
      videoFileName = '{}_{}.{}'.format(filenamePrefix, fileN, extension)
      outLogFilename = 'encoder_{}.log'.format(fileN)
      outFilterFilename = 'filters_{}.txt'.format(fileN)

      logFilePath        = os.path.join('tempVideoFiles', outLogFilename)
      tempVideoFilePath  = os.path.join('tempVideoFiles', videoFileName)
      filterFilePath     = os.path.join('tempVideoFiles', outFilterFilename)
      videoFilePath      = os.path.join('finalVideos', videoFileName)
      

      if not os.path.exists(tempVideoFilePath) and not os.path.exists(filterFilePath) and not os.path.exists(videoFilePath) and not os.path.exists(logFilePath) and videoFileName not in filesPlannedForCreation:
        filesPlannedForCreation.add(videoFileName)
        return videoFileName, logFilePath, filterFilePath, tempVideoFilePath, videoFilePath

      fileN+=1

def logffmpegEncodeProgress(proc, processLabel, initialEncodedSeconds, totalExpectedEncodedSeconds, statusCallback, passNumber=0, requestId=None, tempVideoPath=None, options={}):
  currentEncodedTotal=0
  psnr = None
  ln=b''
  logging.debug('Encode Start')

  earlyExitOnLowPSNR    = options.get('earlyPSNRWidthReduction', False)
  
  minimumPSNR           = -1
  try:
    minimumPSNR           = int(float(options.get('minimumPSNR', -1)))
  except:
    pass

  earlyPSNRWindowLength = options.get('earlyPSNRWindowLength', 5)
  earlyPSNRSkip         = options.get('earlyPSNRSkipSamples', 5)
  psnrSamplesSkipped    = 0

  psnrQ = deque([], max(2, earlyPSNRWindowLength))
  psnrAve = None
  outputSeen = False
  bpp = 8
  bit_depth_set = False
  while 1:
    try:
      if isRquestCancelled(requestId):
        proc.kill()
        outs,  errs = proc.communicate()
        return 0, 0
      c = proc.stderr.read(1)
      if len(c)==0:
        break
      if c == b'\r':

        if b'Output ' in ln:
            outputSeen = True

        print(ln)
        for p in ln.split(b' '):

          if b'Video:' in ln and b'Stream' in ln and outputSeen and not bit_depth_set:
            for key,v_depth in bit_depths.items():
                if key.encode('utf8') in ln:
                    bit_depth_set = True
                    bpp = v_depth
                    print('------------bpp',key,bpp)

          if b'*:' in p:
            try:
              tpsnr = float(p.split(b':')[-1]) 
              if (not math.isnan(tpsnr)) and tpsnr != float('inf'):
                psnr = tpsnr

                if psnrSamplesSkipped > earlyPSNRSkip:
                  psnrQ.append(psnr)
                
                psnrSamplesSkipped+=1

                if len(psnrQ) == earlyPSNRWindowLength and earlyExitOnLowPSNR:
                  psnrAve = sum(psnrQ)/earlyPSNRWindowLength
                  print('psnrAve', psnrAve, minimumPSNR, psnrQ)

                  if psnrAve is not None and psnrAve < minimumPSNR:

                    proc.kill()
                    outs,  errs = proc.communicate()
                    statusCallback('Rolling PSNR too Low '+processLabel, 0, lastEncodedPSNR=psnr, encodeStage='PSNR Too Low', pix_fmt=bpp,  encodePass='PSNR {} ({} samples)'.format(psnrAve, earlyPSNRWindowLength) )
                    return psnrAve, 1

            except Exception as e:
              logging.error("Encode capture psnr Exception", exc_info=e)
          if b'time=' in p:
            try:
              pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'), '%H:%M:%S.%f')
              currentEncodedTotal = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
              if currentEncodedTotal>0:
                if passNumber == 0:
                  statusCallback('Encoding '+processLabel, (currentEncodedTotal+initialEncodedSeconds)/totalExpectedEncodedSeconds, lastEncodedPSNR=psnr, pix_fmt=bpp, encodeStage='Encoding Final',  encodePass='Single Pass Mode')
                elif passNumber == 1:
                  statusCallback('Encoding '+processLabel, ((currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds, lastEncodedPSNR=psnr, pix_fmt=bpp, encodeStage='Encoding Final',  encodePass='Two Pass Mode Pass 1' )
                elif passNumber == 2:

                  sizeNow = None

                  print(tempVideoPath)
                  try:
                    if tempVideoPath is not None:
                      sizeNow = os.stat(tempVideoPath).st_size
                  except Exception as sze:
                    print(sze)

                  statusCallback('Encoding '+processLabel, ( ((totalExpectedEncodedSeconds-initialEncodedSeconds)/2) + (currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds, lastEncodedPSNR=psnr, encodeStage='Encoding Final', currentSize=sizeNow,  encodePass='Two Pass Mode Pass 2' )

            except Exception as e:
              logging.error("Encode progress Exception", exc_info=e)
        ln=b''
      ln+=c
    except Exception as e:
      logging.error("Encode progress Exception", exc_info=e)

  outs,  errs = proc.communicate()

  if proc.returncode == 1:
    statusCallback('Encode Failed '+processLabel, 1, lastEncodedPSNR=psnr, encodeStage='Encode Failed',  encodePass='Error code {}'.format(proc.returncode) )

  if passNumber == 0:
    statusCallback('Complete '+processLabel, (currentEncodedTotal+initialEncodedSeconds)/totalExpectedEncodedSeconds, lastEncodedPSNR=psnr )
  elif passNumber == 1:
    statusCallback('Complete '+processLabel, ((currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds, lastEncodedPSNR=psnr )
  elif passNumber == 2:
    statusCallback('Complete '+processLabel, ( ((totalExpectedEncodedSeconds-initialEncodedSeconds)/2) + (currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds, lastEncodedPSNR=psnr )
  
  return psnr, proc.returncode
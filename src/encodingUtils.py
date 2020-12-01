

import threading
import os
import logging
from datetime import datetime

filesPlannedForCreation = set()
fileExistanceLock = threading.Lock()

cancelledEncodeIds = set()

def isRquestCancelled(requestId):
  global cancelledEncodeIds
  return requestId in cancelledEncodeIds

packageglobalStatusCallback=print

def idfunc(s):return s

getShortPathName = idfunc

try:
  import win32api
  getShortPathName=win32api.GetShortPathName
except Exception as e:
  logging.error("win32api getShortPathName Exception",exc_info=e)

def cleanFilenameForFfmpeg(filename):
  return getShortPathName(os.path.normpath(filename))

def cancelCurrentEncodeRequest(requestId):
  global cancelledEncodeIds
  cancelledEncodeIds.add(requestId)


def getFreeNameForFileAndLog(filenamePrefix,extension):
  fileN=0
  with fileExistanceLock:
    while 1:
      fileN+=1
      videoFileName = '{}_WmG_{}.{}'.format(filenamePrefix,fileN,extension)
      outLogFilename = 'encoder_{}.log'.format(fileN)
      
      logFilePath        = os.path.join('tempVideoFiles',outLogFilename)
      tempVideoFilePath  = os.path.join('tempVideoFiles',videoFileName)
      videoFilePath      = os.path.join('finalVideos',videoFileName)

      if not os.path.exists(tempVideoFilePath) and not os.path.exists(videoFilePath) and not os.path.exists(logFilePath) and videoFileName not in filesPlannedForCreation:
        filesPlannedForCreation.add(videoFileName)
        return videoFileName,logFilePath,tempVideoFilePath,videoFilePath

def logffmpegEncodeProgress(proc,processLabel,initialEncodedSeconds,totalExpectedEncodedSeconds,statusCallback,passNumber=0,requestId=None):
  currentEncodedTotal=0
  psnr = None
  ln=b''
  while 1:
    try:
      if isRquestCancelled(requestId):
        proc.kill()
        outs, errs = proc.communicate()
        return
      c = proc.stderr.read(1)
      if len(c)==0:
        break
      if c == b'\r':
        for p in ln.split(b' '):
          if b'*:' in p:
            print(ln)
            try:
              tpsnr = float(p.split(b':')[-1]) 
              if not math.isnan(tpsnr) and tpsnr != float('inf'):
                psnr = tpsnr
            except:
              pass
          if b'time=' in p:
            try:
              pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
              currentEncodedTotal = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
              if currentEncodedTotal>0:
                if passNumber == 0:
                  statusCallback('Encoding '+processLabel,(currentEncodedTotal+initialEncodedSeconds)/totalExpectedEncodedSeconds,lastEncodedPSNR=psnr,encodeStage='Encoding Final', encodePass='Single Pass Mode')
                elif passNumber == 1:
                  statusCallback('Encoding '+processLabel,((currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds,lastEncodedPSNR=psnr,encodeStage='Encoding Final', encodePass='Two Pass Mode Pass 1' )
                elif passNumber == 2:
                  statusCallback('Encoding '+processLabel,( ((totalExpectedEncodedSeconds-initialEncodedSeconds)/2) + (currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds,lastEncodedPSNR=psnr,encodeStage='Encoding Final', encodePass='Two Pass Mode Pass 2' )
            except Exception as e:
              logging.error("Encode progress Exception",exc_info=e)
        ln=b''
      ln+=c
    except Exception as e:
      logging.error("Encode progress Exception",exc_info=e)
  if passNumber == 0:
    statusCallback('Complete '+processLabel,(currentEncodedTotal+initialEncodedSeconds)/totalExpectedEncodedSeconds,lastEncodedPSNR=psnr )
  elif passNumber == 1:
    statusCallback('Complete '+processLabel,((currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds,lastEncodedPSNR=psnr )
  elif passNumber == 2:
    statusCallback('Complete '+processLabel,( ((totalExpectedEncodedSeconds-initialEncodedSeconds)/2) + (currentEncodedTotal/2)+initialEncodedSeconds)/totalExpectedEncodedSeconds,lastEncodedPSNR=psnr )
  return psnr
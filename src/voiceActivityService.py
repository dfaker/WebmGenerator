
from queue import Queue,Empty,Full
import subprocess as sp
import threading
from .encodingUtils import cleanFilenameForFfmpeg
import numpy as np

try:
  import webrtcvad
except Exception as e:
  webrtcvad=None
  print(e)

from collections import deque


def zero_crossing_rate(frame):
  count = len(frame)
  count_zero = np.sum(np.abs(np.diff(np.sign(frame)))) / 2
  return np.float64(count_zero) / np.float64(count - 1.0)


class VoiceActivityService():


  def __init__(self,globalStatusCallback=print,globalOptions={}):
    self.globalStatusCallback = globalStatusCallback
    self.voiceDetectRequestQueue = Queue()
    self.globalOptions=globalOptions

    self.enabled = False
    if webrtcvad is not None:
      self.enabled=True


    def processFaceRequests():
      if webrtcvad is not None:
        while 1:
          fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,zcrMin,zcrMax = self.voiceDetectRequestQueue.get()

          usezcr = zcrMin!=-1 or zcrMax!=-1

          positiveMode = True
          if condidenceStart < 0:
            condidenceStart = abs(condidenceStart)
            condidenceEnd   = abs(condidenceEnd)
            positiveMode=False


          self.globalStatusCallback('Starting voice activity scan',0)

          condidenceStart = condidenceStart/100
          condidenceEnd = condidenceEnd/100
          
          try:

            print(fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,condidenceStart,condidenceEnd)

            vad = webrtcvad.Vad(int(aggresiveness))


            filename = fileName
            sample_rate = 48000 
            frame_duration = int(float(sampleLength))
            windowLength = float(windowLength)

            proc = sp.Popen(['ffmpeg.exe', '-i', cleanFilenameForFfmpeg(filename), '-ac', '1','-ar', str(sample_rate), '-acodec', 'pcm_s16le', '-f', 'wav', '-'],stdout=sp.PIPE,stderr=sp.DEVNULL,bufsize=10**8)

            n=0

            sampleWindowLength = int(windowLength*(1000/frame_duration))
            sampqueue = deque([],sampleWindowLength)

            zcrqueue = deque([0],sampleWindowLength)

            readLen = int(2*(sample_rate*frame_duration/1000))

            ranges = []

            startTS=None
            endTS=None

            while 1:
              n+=1
              p = proc.stdout.read(readLen)
              if len(p)<readLen:
                break

              if n%100==0:
                start = (n-sampleWindowLength)*(frame_duration/1000)
                self.globalStatusCallback('Running voice activity scan',start/totalDuration)

              if usezcr:
                audio_array = np.frombuffer(p, dtype="int16")
                zcr = zero_crossing_rate(audio_array)
                zcrqueue.append(zcr)

              if vad.is_speech(p, sample_rate):
                sampqueue.append(1.0)
              else:
                sampqueue.append(0.0)

              if len(sampqueue) >= sampleWindowLength:
                start = (n-sampleWindowLength)*(frame_duration/1000)
                end   = (n)*(frame_duration/1000)
                mean = sum(sampqueue)/len(sampqueue)

                meanzcr = (sum(zcrqueue)/len(zcrqueue))*100
                zrcPass = meanzcr==0 or ((zcrMin == -1 or meanzcr>=zcrMin) and (zcrMax == -1 or meanzcr<=zcrMax))
                
                if positiveMode:
                  if zrcPass and mean >= condidenceStart and startTS is None:
                    startTS=start
                    endTS=end
                  elif zrcPass and mean >= condidenceEnd and startTS is not None and endTS is not None and endTS >= start-bridgeDistance:
                    endTS=end
                  elif mean < condidenceEnd and startTS is not None and endTS is not None and endTS <= start-bridgeDistance:
                    if endTS-startTS>=minimimDuration:
                      callback(filename,startTS,timestampEnd=endTS,kind='Cut')
                    startTS=None
                    endTS=None
                else:
                  if zrcPass and mean <= condidenceStart and startTS is None and zrcPass:
                    startTS=start
                    endTS=end
                  elif zrcPass and mean <= condidenceEnd and startTS is not None and endTS is not None and endTS >= start-bridgeDistance:
                    endTS=end
                  elif mean > condidenceEnd and startTS is not None and endTS is not None and endTS <= start-bridgeDistance:
                    if endTS-startTS>=minimimDuration:
                      callback(filename,startTS,timestampEnd=endTS,kind='Cut')
                    startTS=None
                    endTS=None

            if startTS is not None and endTS is not None:
              if endTS-startTS>=minimimDuration:
                callback(filename,startTS,timestampEnd=endTS,kind='Cut')
              startTS=None
              endTS=None

          except Exception as e:
            print(e)

        self.globalStatusCallback('Voice activity scan complete',1)
        self.voiceDetectRequestQueue.task_done()

    self.voiceWorkerThread = threading.Thread(target=processFaceRequests,daemon=True)
    self.voiceWorkerThread.start()

  def scanForVoiceActivity(self,fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,zcrMin,zcrMax):
    print(fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,zcrMin,zcrMax)
    self.voiceDetectRequestQueue.put((fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,zcrMin,zcrMax))

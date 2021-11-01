
from queue import Queue,Empty,Full
import subprocess as sp
import threading
from .encodingUtils import cleanFilenameForFfmpeg

import webrtcvad
from collections import deque

class VoiceActivityService():


  def __init__(self,globalStatusCallback=print,globalOptions={}):
    self.globalStatusCallback = globalStatusCallback
    self.voiceDetectRequestQueue = Queue()
    self.globalOptions=globalOptions


    def processFaceRequests():

      while 1:
        fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,condidenceStart,condidenceEnd = self.voiceDetectRequestQueue.get()

        self.globalStatusCallback('Starting voice activity scan',0)

        condidenceStart = condidenceStart/100
        condidenceEnd = condidenceEnd/100
        
        try:

          print(fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,condidenceStart,condidenceEnd)

          vad = webrtcvad.Vad(int(aggresiveness))


          filename = fileName
          sample_rate = 48000 
          frame_duration = int(float(sampleLength))

          windowLength = int(windowLength)

          proc = sp.Popen(['ffmpeg.exe', '-i', cleanFilenameForFfmpeg(filename), '-ac', '1','-ar', str(sample_rate), '-acodec', 'pcm_s16le', '-f', 'wav', '-'],stdout=sp.PIPE,stderr=sp.DEVNULL,bufsize=10**8)

          n=0

          sampleWindowLength = int(windowLength*(1000/frame_duration))
          sampqueue = deque([],sampleWindowLength)
          readLen = 2*int(sample_rate*frame_duration/1000)
          print(sampleWindowLength)

          ranges = []

          startTS=None
          while 1:
            n+=1
            p = proc.stdout.read(readLen)
            if len(p)<readLen:
              break

            if n%100==0:
              start = (n-sampleWindowLength)*(frame_duration/1000)
              self.globalStatusCallback('Running voice activity scan',start/totalDuration)

            if vad.is_speech(p, sample_rate):
              sampqueue.append(1.0)
            else:
              sampqueue.append(0.0)

            if len(sampqueue) >= sampleWindowLength:
              start = (n-sampleWindowLength)*(frame_duration/1000)
              end   = (n)*(frame_duration/1000)
              mean = sum(sampqueue)/len(sampqueue)

              print(mean)
              if mean >= condidenceStart and startTS is None:
                startTS=start
              if mean < condidenceEnd and startTS is not None:
                if end-startTS>=minimimDuration:
                  callback(filename,startTS,timestampEnd=end,kind='Cut')
                  print('mpv "{f}" --start={s} -ab-loop-a={s} -ab-loop-b={e}'.format(f=filename,s=startTS,e=end) )
                startTS=None

        except Exception as e:
          print(e)

        self.globalStatusCallback('Voice activity scan complete',1)
        self.voiceDetectRequestQueue.task_done()

    self.voiceWorkerThread = threading.Thread(target=processFaceRequests,daemon=True)
    self.voiceWorkerThread.start()

  def scanForVoiceActivity(self,fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,condidenceStart,condidenceEnd):
    print(fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,condidenceStart,condidenceEnd)
    self.voiceDetectRequestQueue.put((fileName,totalDuration,callback,sampleLength,aggresiveness,windowLength,minimimDuration,condidenceStart,condidenceEnd))

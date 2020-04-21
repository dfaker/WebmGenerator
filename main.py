import sys
import os
import mimetypes
import random
import time
import mpv
import cv2
import numpy as np

import subprocess as sp
from win32api import GetSystemMetrics

from datetime import datetime
import tqdm
import multiprocessing as mp

workers=1
maxWidth = 1280
imshape = (100,GetSystemMetrics(0)-10,3)
targetSize_max = 4194304
targetSize_min = 4100000
audio_mp = 8
video_mp = 1024
crf=4
default_span=30.0
logo = 'logo.png'
threads = 2
font = cv2.FONT_HERSHEY_SIMPLEX 

  
files = []


args = sys.argv[1:]


def monitorFFMPEGProgress(proc,desc,a,b):
  with tqdm.tqdm(total=abs(a-b),ascii=True) as pbar:
    lastTs=0.0
    pbar.set_description('Encoding (Starting)')
    ln=b''
    while 1:
      c = proc.stderr.read(1)
      if len(c)==0:
        break
      if c == b'\r':
        for p in ln.split(b' '):
          if b'time=' in p:
            pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
            total_seconds = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
            if total_seconds>0:
              pbar.set_description('Encoding (Actual)')
            pbar.update(total_seconds-lastTs)
            lastTs=total_seconds
        ln=b''
      ln+=c

def processWorker(q):
  while 1:
    filter,(src,s,e),(cw,ch,cx,cy) = q.get()

    s = max(0,s)
    dur = abs(s-e)

    br = int( ((3.8*video_mp)/dur) - ((32 / audio_mp)/dur) ) *8

    cropCmd = ''
    if cx!=0 and cy !=0 and cw!=0 and ch!=0:
      cropCmd = 'crop={}:{}:{}:{},'.format(cw,ch,cx,cy)

    brmult=1

    os.path.exists('out') or os.mkdir('out')
    if filter is not None:
      os.path.exists(os.path.join('out',filter)) or os.mkdir(os.path.join('out',filter))
    os.path.exists('temp') or os.mkdir('temp')

    if filter is not None:
      outFilename=os.path.join('out',filter,os.path.splitext(os.path.basename(src))[0]+'.'+str(int(s))+'.'+str(int(e))+".webm")
      tempname = os.path.join('temp',os.path.splitext(os.path.basename(src))[0]+'.'+str(int(s))+'.'+str(int(e))+".webm")
    else:
      outFilename=os.path.join('out',os.path.splitext(os.path.basename(src))[0]+'.'+str(int(s))+'.'+str(int(e))+".webm")
      tempname = os.path.join('temp',os.path.splitext(os.path.basename(src))[0]+'.'+str(int(s))+'.'+str(int(e))+".webm")


    print('Queue Size:',q.qsize())
    print('Current File:',outFilename)
    print('Range',s,e)
    
    attempt=0
    while 1:
      attempt+=1
      print('Processing Pass 1 attempt',attempt)
      cmd = ["ffmpeg"
             ,"-y" 
             ,"-i"    , src 
             ,"-i"    , logo
             ,"-ss"   , str(s) 
             ,"-to"   , str(e)
             ,"-c:v"  ,"libvpx" 
             ,"-stats"
             ,"-bufsize", "3000k"
             ,"-threads", str(threads)
             ,"-quality", "best" 
             ,"-auto-alt-ref", "1" 
             ,"-lag-in-frames", "16" 
             ,"-slices", "8"
             ,"-passlogfile", tempname+".log"
             ,"-cpu-used", "0"

             ,"-crf"  ,str(crf)
             ,"-b:v"  ,str(br*brmult)+'K' 
             ,"-ac"   ,"1" 
             ,"-an"

             ,"-filter_complex", "[0:v] "+cropCmd+"scale='min("+str(maxWidth)+"\\,iw):-1' [v0],[v0][1:v] overlay='5:sin(5)'"

             ,"-pass" ,"1" 
             ,"-f"    ,"webm" 
             ,tempname]

      proc = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)
      proc.communicate()

      cmd = ["ffmpeg"
             ,"-y" 
             ,"-i"    , src 
             ,"-i"    , logo
             ,"-ss"   , str(s) 
             ,"-to"   , str(e)
             ,"-c:v"  ,"libvpx" 
             ,"-stats"
             ,"-bufsize", "3000k"
             ,"-threads", str(threads)
             ,"-quality", "best" 
             ,"-auto-alt-ref", "1" 
             ,"-lag-in-frames", "16" 
             ,"-slices", "8"
             ,"-passlogfile", tempname+".log"
             ,"-cpu-used", "0"

             ,"-crf"  ,str(crf) 
             ,"-b:v"  ,str(br*brmult)+'K'
             ,"-ac"   ,"1"            
             ,"-c:a"  ,"libvorbis"
             ,"-b:a"  ,"32k"  
             ,"-filter_complex", "[0:v] "+cropCmd+"scale='min("+str(maxWidth)+"\\,iw):-1' [v0],[v0][1:v] overlay='5:5'"
             ,"-pass" ,"2"
             ,tempname]

      proc = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)
      monitorFFMPEGProgress(proc,'Encoding:',s,e)
      proc.communicate()

      finalSize = os.stat(tempname).st_size

      if targetSize_min<finalSize<targetSize_max or (finalSize<targetSize_max and attempt>10):
        print("Complete.")
        os.rename(tempname,outFilename)
        break
      else:        
        if finalSize<targetSize_min:
          print("File size too small",finalSize,targetSize_min-finalSize)
        elif finalSize>targetSize_max:
          print("File size too large",finalSize,finalSize-targetSize_max)
        brmult= brmult+(1.0-(finalSize/(targetSize_max*0.999) ))
    q.task_done()


filters=[]

if __name__ == '__main__':
  """mp.set_start_method('spawn')"""
  q = mp.JoinableQueue()
  pl = []
  for _ in range(workers):
    p = mp.Process(target=processWorker, args=(q,),daemon=True)
    p.start()
    pl.append(p)

  for arg in args:
    if os.path.isfile(arg):
      g = mimetypes.guess_type(arg)
      if g is not None and g[0] is not None and 'video' in g[0]:
        files = [(None,arg) ]
    elif os.path.isdir(arg):
      for r,dl,fl in os.walk(arg):
        for f in fl:
          p = os.path.join(r,f)
          g = mimetypes.guess_type(p)
          if g is not None and g[0] is not None and 'video' in g[0]:
            if len(filters)==0:
              print('Added',p)
              files.append((None,p))
            else:
              for f in filters:
                if f.upper() in p.upper():
                  print('filter',f,'Added',p)
                  files.append((f,p))
                  break
    else:
      filters.append(arg)
      print('Added filter',arg)

  random.shuffle(files)

  
  breakAllLoop = False

  for filter,src in files:

    if breakAllLoop:
      break

    breakLoop = False

    while 1:
      if breakLoop:
        break

      player = mpv.MPV(input_default_bindings=True, osc=True)
      player.loop_playlist = 'inf'
      player.mute = 'yes'
      player.speed = 2
      cw,ch,cx,cy=0,0,0,0
      total_duration=None
      current_time=None
      selected=False
      span=default_span
      keydown=False
      posa=posb=None
      xSelectionPos=None

      player.command('load-script','easycrop.lua')
      player.play(src)
      player.autofit_larger=min(1280,maxWidth)
      player.geometry='100%:50%'
      seeker = np.zeros(imshape,np.uint8)

      def updateScrollImage(mouseX):
        global seeker
        seeker[:,:,:] = 0
        if mouseX is not None:
          
          spanDur = (span/total_duration)*imshape[1]
          seeker[:,max(mouseX-int(spanDur//2),0):min(mouseX+int(spanDur//2),imshape[1]),:]=(0,100,0)
          seeker[:,mouseX,:]=255
        if total_duration is not None and current_time is not None:
          seeker[:, min(max(int(imshape[1]*(current_time/total_duration)),0),imshape[1]-1),: ] = (0,255,0)

        seeker[:25,:,:] = (0,90,0)
        cv2.putText(seeker, 'Queue Current [Q]', (5,15), font, 0.3, (50,255,50), 1, cv2.LINE_AA) 
        cv2.rectangle(seeker, (0,0),(97,24), (50,255,50), 1) 



        cv2.putText(seeker, 'Next File [E]', (150-35,15), font, 0.3, (50,255,50), 1, cv2.LINE_AA) 
        cv2.rectangle(seeker, (140-35,0),(217-35,24), (50,255,50), 1)

        cv2.putText(seeker, 'End File Selection [R]', (250-50,15), font, 0.3, (50,255,50), 1, cv2.LINE_AA) 
        cv2.rectangle(seeker, (240-50,0),(360-50,24), (50,255,50), 1)

        if mouseX is not None:
         cv2.putText(seeker, 'Start: {:01.2f}s End: {:01.2f}s Dur:{:01.2f}s'.format(((mouseX/imshape[1])*total_duration)-span,((mouseX/imshape[1])*total_duration)+span,span ), 
                     (320,15), font, 0.3, (0,255,0), 1, cv2.LINE_AA) 

        cv2.putText(seeker, 'Click or drag here to select time frame, scroll mouse to change duration, press C in player window to crop video or clear crop.', 
                   (5,95), font, 0.3, (0,255,0), 1, cv2.LINE_AA) 

      @player.message_handler('easycrop')
      def luaHandler(w,h,x,y):
        global cw,ch,cx,cy
        cw,ch,cx,cy = int(w),int(h),int(x),int(y)

      def setValues(state,key):
        global player,selected,breakLoop,breakAllLoop
        if state=='d-' and key in ('q','e','r'):
          player.terminate()
          selected=True
          del player
          if key == 'e':
            breakLoop=True
          if key == 'r':
            breakLoop=True
            breakAllLoop=True

      def click(event, x, y, flags, param):
        global keydown,total_duration,posa,posb,span,xSelectionPos

        if event == cv2.EVENT_LBUTTONDOWN:

          if 0<y<24:
            if 0 < x < 97:
              setValues('d-','q')
              return
            elif 140-35 < x < 217-35:
              setValues('d-','e')
              return
            elif 240-50 < x < 360-50:
              setValues('d-','r')
              return 

        if event in (cv2.EVENT_LBUTTONDOWN,cv2.EVENT_LBUTTONUP):
          keydown = event==cv2.EVENT_LBUTTONDOWN

        if event==cv2.EVENT_MOUSEWHEEL:
          incVal = 0.1
          if keydown:
            incVal = 1.0
          if flags>0:
            span+=incVal
          else:
            span-=incVal
          span = max(1,span)

          if total_duration is not None:
            xSelectionPos=x
            localDur = (x/imshape[1])*total_duration
            posa = max(localDur-(span/2),0)
            posb = min(localDur+(span/2),total_duration)
            player.ab_loop_a=posa
            player.ab_loop_b=posb
            player.command('seek', posb-1, 'absolute', 'exact')
            updateScrollImage(xSelectionPos)

        if keydown:
          xSelectionPos=x
          if total_duration is not None:
            xSelectionPos=x
            localDur = (x/imshape[1])*total_duration
            posa = localDur-(span/2)
            posb = localDur+(span/2)
            player.ab_loop_a=posa
            player.ab_loop_b=posb
            player.command('seek', posb-1, 'absolute', 'exact')
            updateScrollImage(xSelectionPos)
      


      player.register_key_binding("q", setValues)
      player.register_key_binding("e", setValues)
      player.register_key_binding("r", setValues)
      player.register_key_binding("CLOSE_WIN", setValues)

      @player.property_observer('time-pos')
      def time_observer(_name, value):
        global total_duration,current_time
        current_time=value
        if total_duration is None:
          total_duration = player.duration
        updateScrollImage(xSelectionPos)  

      cv2.namedWindow("seeker")
      cv2.imshow("seeker",seeker)
      cv2.setMouseCallback("seeker", click)

      while not selected:
        cv2.imshow("seeker",seeker)
        k = cv2.waitKey(1)
        if k in (ord('q'),ord('e')):
          setValues('d-',chr(k))

        
      cv2.destroyAllWindows()


      if not breakLoop and posa is not None and posb is not None:
        q.put( (filter,(src,posa,posb),(cw,ch,cx,cy)) )

      if breakLoop:
        break
  q.join()
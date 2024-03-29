
import tkinter as tk
import tkinter.ttk as ttk
import os
import datetime
import threading
from math import floor
import time
import logging
from threading import Lock

import subprocess as sp
import numpy as np
import math

from contextlib import contextmanager

class AbstractContextManager:

  def __init__(self):
    pass

  def __enter__(self):
    pass

  def __exit__(self ,type, value, traceback):
    pass

@contextmanager
def acquire_timeout(lock, timeout):
  result = lock.acquire(timeout=timeout)
  yield result
  if result:
    lock.release()

jumpRemovelock = Lock()

def format_timedelta(value, time_format="{days} days, {hours2}:{minutes2}:{seconds:02.2F}"):

    if hasattr(value, 'seconds'):
        seconds = value.seconds + value.days * 24 * 3600
    else:
        seconds = value

    seconds_total = seconds

    minutes = int(floor(seconds / 60))
    minutes_total = minutes
    seconds -= minutes * 60

    if hasattr(value, 'microseconds'):
      seconds += (value.microseconds/1000000)
      seconds = round(seconds,2)

    hours = int(floor(minutes / 60))
    hours_total = hours
    minutes -= hours * 60

    days = int(floor(hours / 24))
    days_total = days
    hours -= days * 24

    years = int(floor(days / 365))
    years_total = years
    days -= years * 365

    return time_format.format(**{
        'seconds': seconds,
        'seconds2': str(seconds).zfill(2),
        'minutes': minutes,
        'minutes2': str(minutes).zfill(2),
        'hours': hours,
        'hours2': str(hours).zfill(2),
        'days': days,
        'years': years,
        'seconds_total': seconds_total,
        'minutes_total': minutes_total,
        'hours_total': hours_total,
        'days_total': days_total,
        'years_total': years_total,
    })


def debounce(wait_time,max_gap):
    def decorator(function):
        def debounced(*args, **kwargs):
            def call_function():
                debounced._timer = None
                debounced._last_call = time.time()
                return function(*args, **kwargs)

            if debounced._timer is not None:
                debounced._timer.cancel()

            if debounced._last_call is not None and abs(time.time()-debounced._last_call)>=max_gap:
              function(*args, **kwargs)
              debounced._last_call = time.time()
            else:
              debounced._timer = threading.Timer(wait_time, call_function)
              debounced._timer.start()
        debounced._last_call = time.time()
        debounced._timer = None
        return debounced

    return decorator

audioProcessingSampleRate = 4000
realtimeAudoProcessing = True



def detectBeats(audio_samples, sample_rate, window_length_secs=10, n_peaks=3):
    return []

class TimeLineSelectionFrameUI(ttk.Frame):



  def __init__(self, master, controller, globalOptions={}, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.controller = controller
    self.globalOptions=globalOptions

    self.seekSpeedNormal = self.globalOptions.get("seekSpeedNormal",1)
    self.seekSpeedFast   = self.globalOptions.get("seekSpeedFast",2)
    self.seekSpeedSlow   = self.globalOptions.get("seekSpeedSlow",0.1)

    self.grid_rowconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=1)
    self.grid_columnconfigure(0, weight=1)

    self.timeline_canvas = tk.Canvas(self,width=200, height=150, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=0,column=0,sticky="nesw")

    """
    self.controlsFrame = ttk.Frame(self)
    self.controlsFrame.grid(row=1,column=0,sticky="nesw")

    self.startLabel = ttk.Label(self.controlsFrame,text='Start:')
    self.startLabel.grid(row=0,column=0,sticky="nesw")
    
    self.startSpin = ttk.Spinbox(self.controlsFrame)
    self.startSpin.grid(row=0,column=1,sticky="nesw")
    """

    self.timeline_canvas_popup_menu = tk.Menu(self, tearoff=0)

    self.timeline_canvas_popup_menu.add_command(label="Add new subclip",command=self.canvasPopupAddNewSubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Add new subclip to interest marks",command=self.canvasPopupAddNewSubClipToInterestMarksCallback)

    self.timeline_canvas_popup_menu.add_separator()

    self.timeline_canvas_popup_menu.add_command(label="Delete subclip",command=self.canvasPopupRemoveSubClipCallback)
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Clone subclip",command=self.canvasPopupCloneSubClipCallback)

    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Copy subclip timestamps",command=self.canvasPopupCopySubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Paste subclip timestamps",command=self.canvasPopupPasteSubClipCallback)


    self.timeline_canvas_popup_menu.add_command(label="Expand subclip to interest marks",command=self.canvasPopupExpandSublcipToInterestMarksCallback)

    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Add new interest mark",command=self.canvasPopupAddNewInterestMarkCallback)
    self.timeline_canvas_popup_menu.add_separator()


    self.perfectLoopMenu = tk.Menu(self, tearoff=0)


    
    self.perfectLoopMenu.add_command(label="Move Center on highest inter-frame difference to Start",command=lambda : self.canvasPopupReCenterOnInterFrameDistance('start'))
    self.perfectLoopMenu.add_command(label="Move Center on highest inter-frame difference to Middle",command=lambda : self.canvasPopupReCenterOnInterFrameDistance('mid'))
    self.perfectLoopMenu.add_command(label="Move Center on highest inter-frame difference to End",command=lambda : self.canvasPopupReCenterOnInterFrameDistance('end'))

    self.perfectLoopMenu.add_separator()

    self.perfectLoopMenu.add_command(label="Improve this loop moving the ends at most {}%".format(self.globalOptions.get('loopNudgeLimit1',1)),command=self.canvasPopupFindLowestError1s)
    self.perfectLoopMenu.add_command(label="Improve this loop moving the ends at most {}%".format(self.globalOptions.get('loopNudgeLimit2',2)),command=self.canvasPopupFindLowestError2s)
    
    self.perfectLoopMenu.add_separator()
    self.perfectLoopMenu.add_command(label="Find best loop between {} and {}s centered here".format(  self.globalOptions.get('loopSearchLower1',2), self.globalOptions.get('loopSearchUpper1',3)),command=self.canvasPopupFindContainingLoop3s)
    self.perfectLoopMenu.add_command(label="Find best loop between {} and {}s  centered here".format( self.globalOptions.get('loopSearchLower2',3), self.globalOptions.get('loopSearchUpper2',6)),command=self.canvasPopupFindContainingLoop6s)



    self.timeline_canvas_popup_menu.add_cascade(label="Loop tools",  menu=self.perfectLoopMenu)
    
    self.timeline_canvas_popup_menu.add_separator()

    self.timeline_canvas_popup_menu.add_command(label="Edit subclip",command=self.canvasPopupRangeProperties)

    self.rangePropertiesEntry = self.timeline_canvas_popup_menu.index(tk.END) 

    self.timeline_canvas_popup_menu.add_command(label="Find Similar Sounds",command=self.canvasPopupSimilarSounds)
    
    self.similarSoundsEntry = self.timeline_canvas_popup_menu.index(tk.END) 



    self.timeline_canvas_last_right_click_x=None
    self.timeline_canvas_last_right_click_range=None

    self.timeline_canvas.bind("<Button-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<Button-3>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-3>", self.timelineMousePress)
    self.timeline_canvas.bind("<Button-2>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-2>", self.timelineMousePress)
    self.timeline_canvas.bind("<Enter>", self.timelineMousePress)
    self.timeline_canvas.bind("<Leave>", self.timelineMousePress)
    self.timeline_canvas.bind("<Motion>", self.timelineMousePress)

    self.timeline_canvas.bind("<MouseWheel>", self.timelineMousewheel)

    self.timeline_canvas.bind('<Configure>',self.reconfigure)

    self.timeline_canvas.focus_set()
    self.timeline_canvas.bind('<Left>',  self.keyboardLeft)
    self.timeline_canvas.bind('<Right>', self.keyboardRight)
    self.timeline_canvas.bind('<space>', self.keyboardSpace)
    
    self.timeline_canvas.bind('v',       self.keyboardTempSection)
    self.timeline_canvas.bind('c',       self.keyboardCutatTime)
    self.timeline_canvas.bind('m',       self.keyboardMergeatTime)
    self.timeline_canvas.bind('b',       self.keyboardBlockAtTime)
    self.timeline_canvas.bind('d',       self.keyboardRemoveBlockAtTime)

    self.timeline_canvas.bind('V',       self.keyboardTempSection)
    self.timeline_canvas.bind('C',       self.keyboardCutatTime)
    self.timeline_canvas.bind('M',       self.keyboardMergeatTime)
    self.timeline_canvas.bind('B',       self.keyboardBlockAtTime)
    self.timeline_canvas.bind('D',       self.keyboardRemoveBlockAtTime)

    self.timeline_canvas.bind("q",        lambda x: self.controller.jumpClips(-1))
    self.timeline_canvas.bind("e",        lambda x: self.controller.jumpClips(1))
    self.timeline_canvas.bind("Q",        lambda x: self.controller.jumpClips(-1))
    self.timeline_canvas.bind("E",        lambda x: self.controller.jumpClips(1))
    self.timeline_canvas.bind("r",        lambda x: self.controller.randomClip())
    self.timeline_canvas.bind("R",        lambda x: self.controller.randomClip())
    self.timeline_canvas.bind("<Control-f>",  lambda x: self.controller.search(0))
    self.timeline_canvas.bind("f",        lambda x: self.controller.fastSeek())
    self.timeline_canvas.bind("<Control-r>",  lambda x:self.controller.searchrandom(0))
    self.timeline_canvas.bind("<Control-a>",  lambda x: self.controller.addFullClip())
    self.timeline_canvas.bind("<Control-A>",  lambda x: self.controller.addFullClip())


    self.timeline_canvas.bind(",",        self.stepBackwards)
    self.timeline_canvas.bind(".",        self.stepForwards)

    self.timeline_canvas.bind("y",        self.acceptAndRandomJump)
    self.timeline_canvas.bind("u",        self.rejectAndRandomJump)


    self.timelineZoomFactor=1.0
    self.dragPreviewPos=0.1
    self.dragPreviewMode='abs'
    self.currentZoomRangeMidpoint=0.5

    self.tempRangePreviewDurationLabel = self.timeline_canvas.create_text(0, 0, text='',fill="#69bfdb")
    self.tempRangePreview = self.timeline_canvas.create_rectangle(0,0,0,0,fill="#113a47",width=1,outline="#69bfdb", dash=(1, 1, 2, 3, 5, 8))

    self.randRangePreview = self.timeline_canvas.create_rectangle(0,0,0,0,fill="#461147",width=1,outline="#ca56cc")

    

    self.canvasSeekPointer    = self.timeline_canvas.create_line(0, 0, 0, self.timeline_canvas.winfo_height(),fill="white")

    self.canvasTimestampLabel = self.timeline_canvas.create_text(0, 0, text='',fill="white")

    self.targetTrim=0.25
    self.defaultSliceDuration=10.0
    
    self.handleWidth=10
    self.handleHeight=30
    self.midrangeHeight=20
    self.miniMidrangeHeight=7

    self.canvasRegionCache = {}
    self.timeline_mousedownstate={}
    self.tickmarks=[]
    self.uiDirty=1
    self.clickTarget=None
    self.lastClickedRange=None

    self.rangeHeaderBG = self.timeline_canvas.create_rectangle(0,0,20,0,fill="#3F3F7F")
    self.rangeHeaderActiveRange = self.timeline_canvas.create_rectangle(0,0,0,0,fill="#9E9E9E")
    
    self.rangeHeaderActiveMid = self.timeline_canvas.create_line(0,0,0,0,fill="#4E4E4E")

    self.rangeHeaderClickStart=None

    self.previewBG = self.timeline_canvas.create_rectangle(0,0,0,0,fill="#353535",width=1,outline="white")

    self.canvasHeaderSeekPointer = self.timeline_canvas.create_line(0, 0, 0,0,fill="white")
    self.lastSeek=None

    self.resumeplaybackTimer=None

    self.lastClickedEndpoint = None
    self.framesRequested = False
    self.previewFrames = {}
    self.dirtySelectionRanges = set()

    self.generateWaveImages = False
    self.generateMotionImages = False

    self.lastFilenameForAudioToBytesRequest = None
    self.audioByteValuesReadLock = threading.Lock()
    self.audioByteValues        = []
    self.beats                  = []
    self.latestAudioByteDecoded = 0
    self.completedAudioByteDecoded = False
    self.audioToBytesThread     = None
    self.generateWaveStyle      = 'GENERAL'

    self.lastWavePicSectionsRequested = None
    self.waveAsPicSections            = []
    self.waveAsPicImage               = None
    self.wavePicSectionsThread        = None

    self.tempRangeStart=None

    self.timeline_canvas.coords(self.canvasSeekPointer, -100,45+55,-100,0 )
    self.timeline_canvas.coords(self.canvasTimestampLabel,-100,45+45)
    self.timeline_canvas.delete('previewFrame')
    self.timeline_canvas.delete('fileSpecific')
    self.timeline_canvas.delete('ticks')
    self.uiDirty=1
    self.uiUpdateLock = threading.RLock()
    self.clipped=None

    self.frameRate = None
    self.initialShiftStart = 'Start'

    self.image_handle_left_base = tk.PhotoImage(file = os.path.join("resources",'slider_left_base.gif'))
    self.image_handle_right_base = tk.PhotoImage(file = os.path.join("resources",'slider_right_base.gif'))

    self.image_handle_left_light = tk.PhotoImage(file = os.path.join("resources",'slider_left_light.gif'))
    self.image_handle_right_light = tk.PhotoImage(file = os.path.join("resources",'slider_right_light.gif'))
    self.lastRandomSubclipPos = -1

    self.hoverRID = None
    self.previewRID = None
    self.previewRIDRequested = False
    self.startImg = None
    self.endImg = None

    self.lastSpectraStart = None 
    self.lastSpectraZoomFactor = None
    self.SpectraImage = None


    try:
        self.prefade0 = tk.PhotoImage(file=".\\resources\\prefade0.png")
        self.prefade1 = tk.PhotoImage(file=".\\resources\\prefade1.png")
    except:
        pass

  def stepBackwards(self,e):
    self.controller.stepBackwards()

  def stepForwards(self,e):
    self.controller.stepForwards()

  def acceptAndRandomJump(self,e):

    ctrl  = (e.state & 0x4) != 0
    if ctrl:
        self.controller.randomClip()
        return

    target = self.controller.fastSeek(centerAfter=True)
    
    if self.lastRandomSubclipPos is not None:
      self.keyboardBlockAtTime(e,pos=self.lastRandomSubclipPos,abonly=False)
    
    self.keyboardBlockAtTime(e,pos=target,abonly=True)

    self.lastRandomSubclipPos = target
    

    self.setUiDirtyFlag()
    self.controller.requestAutoconvert()
    print('Exit acceptAndRandomJump')



  def rejectAndRandomJump(self,e):
    target = self.controller.fastSeek(centerAfter=True)
    self.keyboardBlockAtTime(e,pos=target,abonly=True)
    self.lastRandomSubclipPos = target


  def correctMouseXPosition(self,x):

    self.event_generate('<Motion>', warp=True, 
                                x=int(x),
                                y=int(self.winfo_height()-3)

                                )

  def getCurrentlySelectedRegion(self):
    start = self.tempRangeStart
    pos = self.controller.getCurrentPlaybackPosition()
    if start != None and pos != None and pos != start:
      a,b = sorted([start,pos])
      return a,b 
    return None,None

  def processFileAudioToBytes(self,filename,totalDuration,style='SPEECH'):
    print('processFileAudioToBytes ENTRY')
    import subprocess as sp
    sampleRate = audioProcessingSampleRate
    if self.generateWaveStyle == 'SPEECH':
      proc = sp.Popen(['ffmpeg', '-i', filename,  '-ac', '1', '-filter:a', 'arnndn=resources/speechModel/model.rnnn,loudnorm=I=-16:TP=-1.5:LRA=11,aresample={}:async=1'.format(sampleRate), '-map', '0:a', '-c:a', 'pcm_u8', '-f', 'data', '-'],stdout=sp.PIPE,stderr=sp.DEVNULL)
    elif self.generateWaveStyle == 'VOICE':
      proc = sp.Popen(['ffmpeg', '-i', filename,  '-ac', '1', '-filter:a', 'arnndn=resources/voiceModel/model.rnnn,loudnorm=I=-16:TP=-1.5:LRA=11,aresample={}:async=1'.format(sampleRate), '-map', '0:a', '-c:a', 'pcm_u8', '-f', 'data', '-'],stdout=sp.PIPE,stderr=sp.DEVNULL)
    else:
      proc = sp.Popen(['ffmpeg', '-i', filename,  '-ac', '1', '-filter:a', 'compand,highpass=f=200,lowpass=f=3000,aresample={}:async=1'.format(sampleRate), '-map', '0:a', '-c:a', 'pcm_u8', '-f', 'data', '-'],stdout=sp.PIPE,stderr=sp.DEVNULL)
    self.audioByteValues=np.ones((int(totalDuration*sampleRate)),np.uint8)*127
    n=0
    self.completedAudioByteDecoded = False
    while 1:
      if self.audioToBytesThreadKill:
        break
      n+=1
      l = proc.stdout.read(1)
      if len(l)==0:
        break
      self.audioByteValuesReadLock.acquire()
      if n==1:
        self.audioByteValues=np.ones((int(totalDuration*sampleRate)),np.uint8)*127
      try:
        self.audioByteValues[n-1] = int.from_bytes(l, "little")
        self.latestAudioByteDecoded = n/sampleRate
      except Exception as e:
        print(e)

      if realtimeAudoProcessing and n%(sampleRate*50)==0 and n > 1:
        self.beats = detectBeats(self.audioByteValues, sampleRate)#, window_size_ms=50, smoothing_window_ms=50, threshold_factor=1.5, merge_window_ms=100)

      self.audioByteValuesReadLock.release()
    proc.communicate()

    self.beats = detectBeats(self.audioByteValues, sampleRate)#, window_size_ms=50, smoothing_window_ms=50, threshold_factor=1.5, merge_window_ms=100)

    if self.audioToBytesThreadKill:
      self.audioToBytesThreadKill=False
      return

    self.completedAudioByteDecoded = True
    self.audioToBytesThreadKill=False
    self.audioToBytesThread = None

  def generateImageSections(self,filename,startpc,endpc,totalDuration,outputWidth):
    print('generateImageSections')
    args = (filename,startpc,endpc,totalDuration,outputWidth)

    completeOnLastPass=False
    while 1:
      startTS = totalDuration*startpc
      endTS   = totalDuration*endpc

      self.audioByteValuesReadLock.acquire()
      if self.completedAudioByteDecoded:
        completeOnLastPass = True

      tempsamples = np.array(self.audioByteValues,np.uint8)
      #tempsamples = self.audioByteValues

      self.audioByteValuesReadLock.release()

      if args != self.lastWavePicSectionsRequested:
        return


      background = np.ones((40,outputWidth,1),np.uint8)*30
      

      indSt = int(math.floor(len(tempsamples)*(startTS / totalDuration )))
      indEn = int(math.floor(len(tempsamples)*(endTS   / totalDuration )))

      indDistance = indEn-indSt
 
      for x in range(0,outputWidth):
        xPc = x/outputWidth
        xnPc = min((x+1)/outputWidth,1.0)
        samp0 = int(indSt+(xPc*indDistance))
        samp1 = int(indSt+(xnPc*indDistance))
        try:
          sampleszMax = tempsamples[samp0:samp1].max()
          sampleszMax = int((sampleszMax/255)*40)
          sampleszMin = tempsamples[samp0:samp1].min()-1
          sampleszMin = int((sampleszMin/255)*40)
          background[sampleszMin:sampleszMax,x,0]=200
          
          for b in self.beats:
            if samp0 < b <= samp1:
                background[0:255,x,0]=255

        except Exception as e:
          print('Audio spectra norm Exception',e)
        if args != self.lastWavePicSectionsRequested:
          return

      picdata = 'P6\n{w} {h}\n255\n'.format(w=outputWidth,h=40)
      for row in background:
        rowdata = []
        for dtum in row:
          if dtum[0] == 255:
            rowdata.append('{c}{b}{b}'.format(c=chr(255),b=chr(20)))
          elif dtum[0] > 30:
            rowdata.append('{c}{c}{b}'.format(c=chr(int(dtum[0]*0.8)),b=chr(int(dtum[0]))))
          else:
            rowdata.append('{c}{c}{c}'.format(c=chr(int(dtum[0]))))

        picdata += ''.join(rowdata)

      self.timeline_canvas.delete('waveAsPicImage')

      if args != self.lastWavePicSectionsRequested:
        return

      self.waveAsPicImage = tk.PhotoImage(data=picdata)
      canvasimg = self.timeline_canvas.create_image(0,45+20+20,image=self.waveAsPicImage,anchor='nw',tags='waveAsPicImage')
      self.timeline_canvas.lower(canvasimg)
      
      time.sleep(0.1)

      if self.completedAudioByteDecoded and not completeOnLastPass:
        completeOnLastPass = True
        continue

      if completeOnLastPass:
        self.wavePicSectionsThread = None
        return

  def generateImageSections(self,filename,startpc,endpc,totalDuration,outputWidth):
    args = (filename,startpc,endpc,totalDuration,outputWidth)

    completeOnLastPass=False
    while 1:
        startTS = totalDuration*startpc
        endTS   = totalDuration*endpc

        if self.lastSpectraStart is not None and self.SpectraImage is not None:
            if self.lastSpectraStart != startTS and self.lastSpectraZoomFactor == self.timelineZoomFactor:
                oldx = self.secondsToXcoord(self.lastSpectraStart)
                self.timeline_canvas.coords(self.SpectraImage,oldx,45)

        #self.audioByteValuesReadLock.acquire()
        if self.completedAudioByteDecoded:
            completeOnLastPass = True

        indSt = int(math.floor(len(self.audioByteValues)*(startTS / totalDuration )))
        indEn = int(math.floor(len(self.audioByteValues)*(endTS   / totalDuration )))

        tempsamples = np.array(self.audioByteValues[indSt:indEn],np.uint8)
  
        #self.audioByteValuesReadLock.release()

        if args != self.lastWavePicSectionsRequested:
            return

        proc = sp.Popen(['ffmpeg', '-y',  '-f', 'u8', '-i', 'pipe:0', '-filter_complex', "{visStyle}".format(
            start=startTS,
            end=endTS,
            padto=totalDuration,
            width=outputWidth,
            visStyle="showspectrumpic=s={width}x120:legend=0:fscale=lin:scale=cbrt".format(

                width=outputWidth
                )
            ), '-c:v', 'ppm', '-f', 'rawvideo', '-'],stdout=sp.PIPE,stdin=sp.PIPE)

        outs,errs = proc.communicate(input = tempsamples.tobytes())        

        if args != self.lastWavePicSectionsRequested:
            return

        if self.waveAsPicImage is None:
            self.waveAsPicImage = tk.PhotoImage(data=outs)
        else:
            self.waveAsPicImage.config(data=outs)

        if self.SpectraImage is None:
            self.SpectraImage = self.timeline_canvas.create_image(0,45,image=self.waveAsPicImage,anchor='nw',tags='waveAsPicImage')
            self.timeline_canvas.lower(self.SpectraImage)
        else:
            self.timeline_canvas.coords(self.SpectraImage,0,45)


        self.lastSpectraStart = startTS 
        self.lastSpectraZoomFactor = self.timelineZoomFactor


        time.sleep(0.1)

        if self.completedAudioByteDecoded and not completeOnLastPass:
            completeOnLastPass = True
            continue

        if completeOnLastPass:
            self.wavePicSectionsThread = None
            return

  def clearCurrentlySelectedRegion(self):
    self.tempRangeStart=None
    self.updateCanvas()

  def keyboardMergeatTime(self,e):
    if self.tempRangeStart is not None:
      a,b = sorted([self.tempRangeStart,self.controller.getCurrentPlaybackPosition()])
      overlappingRanges=[]
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      for rid,(s,e) in list(ranges):
        if a<=s<=b or a<=e<=b:
          overlappingRanges.append( (s,e,rid) )
      if len(ranges)>1:
        overlappingRanges = sorted(overlappingRanges)
        finalend = overlappingRanges[-1][1]
        for s,e,rid in overlappingRanges[1:]:
          self.controller.removeSubclip((s+e)/2)
        self.tempRangeStart=None
        self.controller.updatePointForClip(self.controller.getcurrentFilename(),overlappingRanges[0][2],'e',finalend)
        self.setUiDirtyFlag(specificRID=overlappingRanges[0][2])


  def keyboardCutatTime(self,e):
    mid = self.controller.getCurrentPlaybackPosition()
    selectedRange = None
    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
    for rid,(s,e) in list(ranges):
      if s<mid<e:
        selectedRange=rid
        break
    if selectedRange is not None:
      mid = self.roundToNearestFrame(mid)
      self.controller.updatePointForClip(self.controller.getcurrentFilename(),selectedRange,'e',mid)
      self.controller.addNewSubclip(mid,e,seekAfter=False)
      self.setUiDirtyFlag(specificRID=selectedRange)
      self.updateCanvas(withLock=False)

  def keyboardRemoveBlockAtTime(self,e,pos=None):
    self.timeline_canvas.coords(self.randRangePreview,0,0,0,0)

    if self.tempRangeStart is not None:
      if pos is None:
        pos = self.controller.getCurrentPlaybackPosition()

      a,b = sorted([self.tempRangeStart,pos])

      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      for rid,(s,e) in list(ranges):
        if a<=s<=b and a<=e<=b:
          self.controller.removeSubclip((s+e)/2)
          self.setUiDirtyFlag(specificRID=rid)
      self.tempRangeStart=None

      #self.updateCanvas()
    else:
      mid = self.controller.getCurrentPlaybackPosition()
      self.controller.removeSubclip(mid)
      #self.updateCanvas()

  def keyboardBlockAtTime(self,e,pos=None,abonly=False):
    
    ctrl  = (e.state & 0x4) != 0
    if ctrl:
      return

    if pos is None:
        pos = self.controller.getCurrentPlaybackPosition()

    if pos is not None:
      pre = self.defaultSliceDuration*0.5
      post = self.defaultSliceDuration*0.5
      a,b = self.roundToNearestFrame(pos-pre),self.roundToNearestFrame(pos+post)
      if abonly:
        ax,bx = self.secondsToXcoord(a),self.secondsToXcoord(b),
        self.timeline_canvas.coords(self.randRangePreview,ax,140,bx,150)

        self.hoverRID='V'
        self.previewRID='V'

        self.blockx0=ax
        self.blockx1=bx
        self.blocks0=a
        self.blocks1=b

        self.requestRIDHoverPreviews(self.previewRID)
        self.previewRIDRequested=True

        self.controller.setAB( a,b,seekAfter=False )
      else:
        self.controller.addNewSubclip( a,b,seekAfter=False )
      
  def startTempSelection(self,startOverride=None):
    if startOverride is not None:
      self.tempRangeStart = startOverride
    else:
      self.tempRangeStart = self.controller.getCurrentPlaybackPosition()

  def endTempSelection(self):
      a,b = self.tempRangeStart, self.controller.getCurrentPlaybackPosition()
      a,b = self.roundToNearestFrame(a),self.roundToNearestFrame(b)
      if a != b:
        self.controller.addNewSubclip(a,b,seekAfter=False)
      self.tempRangeStart=None
      self.updateCanvas()
      self.setUiDirtyFlag()

  def keyboardTempSection(self,e):
    if self.tempRangeStart is None:
      self.startTempSelection()
    else:
      self.endTempSelection()

  def keyboardSpace(self,e):
    self.controller.playPauseToggle()

  def recenterZoomView(self):
    pospc = self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
    timelineWidth = self.winfo_width()
    startpc = self.xCoordToSeconds(0)/self.controller.getTotalDuration()
    endpc   = self.xCoordToSeconds(timelineWidth)/self.controller.getTotalDuration()

    if pospc <= startpc or pospc >= endpc:
        self.currentZoomRangeMidpoint = pospc
        self.centerTimelineOnCurrentPosition()

  def keyboardRight(self,e):
    pos = self.controller.getCurrentPlaybackPosition()
    shift = (e.state & 0x1) != 0
    ctrl  = (e.state & 0x4) != 0

    self.timeline_canvas.coords(self.randRangePreview,0,0,0,0)


    if self.lastClickedEndpoint is not None:
      self.incrementEndpointPosition(self.seekSpeedSlow if ctrl and shift else self.seekSpeedFast if shift else self.seekSpeedNormal,*self.lastClickedEndpoint)
    else:
      if ctrl and shift:
        self.controller.seekRelative(self.seekSpeedSlow)
      elif shift:
        self.controller.seekRelative(self.seekSpeedFast)
      elif ctrl:    
        ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
        nextTarget=None
        for rid,(sts,ens) in sorted(ranges,key=lambda x:x[1][0])[::-1]:
          if sts > pos:
            nextTarget = (sts+ens)/2
        if nextTarget is not None:
          self.seekto(nextTarget)
        else:
          self.controller.seekRelative(self.seekSpeedNormal)
      else:
        self.controller.seekRelative(self.seekSpeedNormal)
    self.recenterZoomView()


  def keyboardLeft(self,e):
    pos = self.controller.getCurrentPlaybackPosition()
    shift = (e.state & 0x1) != 0
    ctrl  = (e.state & 0x4) != 0

    self.timeline_canvas.coords(self.randRangePreview,0,0,0,0)


    if self.lastClickedEndpoint is not None:
      self.incrementEndpointPosition(-self.seekSpeedSlow if ctrl and shift else -self.seekSpeedFast if shift else -self.seekSpeedNormal,*self.lastClickedEndpoint)
    else:
      if ctrl and shift:
        self.controller.seekRelative(-self.seekSpeedSlow)
      elif shift:
        self.controller.seekRelative(-self.seekSpeedFast)
      elif ctrl:      
        ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
        nextTarget=None
        for rid,(sts,ens) in sorted(ranges,key=lambda x:x[1][1]):
          if ens < pos:
            nextTarget = (sts+ens)/2
        if nextTarget is not None:
          self.seekto(nextTarget)
        else:
          self.controller.seekRelative(-self.seekSpeedNormal)
      else:
        self.controller.seekRelative(-self.seekSpeedNormal)
    self.recenterZoomView()


  def incrementEndpointPosition(self,increment,markerrid,pos):
    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
    for rid,(sts,ens) in ranges:
      if rid == markerrid:
        newTs = 0

        self.controller.pause()
        try:
            self.resumeplaybackTimer.cancel()
        except(AttributeError):
            pass
        if self.globalOptions.get('autoResumeAfterSeek',True):
            self.resumeplaybackTimer = threading.Timer(0.8, self.controller.play)
            self.resumeplaybackTimer.start()

        if pos == 's':
          startTarget = self.roundToNearestFrame(sts+(increment*0.05))
          self.clipped=self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,startTarget)
          self.setUiDirtyFlag(specificRID=rid)
          self.seekto(startTarget)
        elif pos == 'e':
          endTarget = self.roundToNearestFrame(ens+(increment*0.05))
          self.clipped=self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,endTarget)
          self.setUiDirtyFlag(specificRID=rid)
          self.seekto(endTarget-0.001)
        break

  def setDragPreviewPos(self,value,mode):
    self.dragPreviewPos = value
    self.dragPreviewMode = mode

  def reconfigure(self,e):
    self.setUiDirtyFlag()
    if self.controller.getTotalDuration() is not None:
      self.updateCanvas(withLock=False)

  def resetForNewFile(self):
    self.timelineZoomFactor=1.0
    self.currentZoomRangeMidpoint=0.5
    self.tempRangeStart=None
    self.canvasRegionCache={}
    self.controller.requestTimelinePreviewFrames(None,None,None,None,None,self.frameResponseCallback)
    self.framesRequested = False;
    self.timeline_canvas.coords(self.canvasSeekPointer, -100,45+55,-100,0 )
    self.timeline_canvas.coords(self.canvasTimestampLabel,-100,45+45)
    self.timeline_canvas.coords(self.tempRangePreview,0,0,0,0)
    self.timeline_canvas.coords(self.randRangePreview,0,0,0,0)

    self.timeline_canvas.coords(self.tempRangePreviewDurationLabel,0,0)
    self.previewFrames = {}
    self.timeline_canvas.delete('previewFrame')
    self.timeline_canvas.delete('waveAsPicImage')
    self.timeline_canvas.delete('fileSpecific')
    self.timeline_canvas.delete('ticks')
    self.timeline_canvas.delete('hoverFrame')
    self.generateWaveImages = False
    self.generateMotionImages = False
    self.audioToBytesThreadKill=True
    self.audioToBytesThread=None
    self.completedAudioByteDecoded = False
    self.frameRate = None
    self.lastRandomSubclipPos = None

    self.setUiDirtyFlag()

  def updateFrameRate(self,fps):
    print('########FPS!!!',fps)
    self.frameRate = fps

  @staticmethod
  def pureGetClampedCenterPosAndRange(totalDuration,zoomFactor,currentMidpoint):

    outputDuration = totalDuration*(1/zoomFactor)
    minPercent     = (1/zoomFactor)/2
    center         = min(max(minPercent,currentMidpoint),1-minPercent)
    lowerRange     = (totalDuration*center)-(outputDuration/2)
    return outputDuration,center,lowerRange

  def getClampedCenterPosAndRange(self,update=True,negative=False):

    result  = self.pureGetClampedCenterPosAndRange(self.controller.getTotalDuration(),
                                                   self.timelineZoomFactor,
                                                   self.currentZoomRangeMidpoint)
    
    outputDuration,center,lowerRange = result
    if update:
      self.currentZoomRangeMidpoint=center

    return center,lowerRange,outputDuration

  def roundToNearestFrame(self,seconds):
    if self.frameRate is not None:
      rem = seconds%(1/self.frameRate)
      return seconds - rem
    return seconds

  def secondsToXcoord(self,seconds,update=True,negative=False):
    try:
      center,rangeStart,duration = self.getClampedCenterPosAndRange(update=update,negative=negative)
      return (((seconds-rangeStart))/duration)*self.winfo_width()
    except Exception as e:
      logging.error('Seconds to x coord Exception',exc_info=e)
      return 0

  def xCoordToSeconds(self,xpos,update=True,negative=False):
    try:
      center,rangeStart,duration = self.getClampedCenterPosAndRange(update=update,negative=negative)
      seconds = rangeStart+( (xpos/self.winfo_width())*duration )
      return self.roundToNearestFrame(seconds)
    except Exception as e:
      logging.error('x coord to seconds Exception',exc_info=e)
      return 0

  def timelineMousewheel(self,e):    
      ctrl  = (e.state & 0x4) != 0
      shift = (e.state & 0x1) != 0
      alt   = (e.state & 0x20000) != 0

      self.timeline_canvas.coords(self.randRangePreview,0,0,0,0)

      if e.y<20:

        factor = 0.10
        if shift:
          factor=0.25
        if ctrl:
          factor=1

        if e.delta>0:
          self.currentZoomRangeMidpoint += factor/self.timelineZoomFactor
          self.setUiDirtyFlag()
          return
        else:
          self.currentZoomRangeMidpoint -= factor/self.timelineZoomFactor
          self.setUiDirtyFlag()
          return

      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())

      rangeHit=False
      for rid,(sts,ens) in ranges:
        st=self.secondsToXcoord(sts)
        en=self.secondsToXcoord(ens)
        if st-self.handleWidth<=e.x<=en+self.handleWidth and e.y>self.winfo_height()-(self.midrangeHeight+10):
          rangeHit = True
          targetSeconds = (sts+ens)/2
          
          jumpspeed = 0.01
          print(shift,alt)
          if shift:
            jumpspeed = 0.1

          if alt:
            jumpspeed = 1.0

          if shift and alt:
            jumpspeed = 10.0

          if e.delta>0:
            targetSeconds+= jumpspeed
          else:
            targetSeconds-= jumpspeed

          self.controller.pause()
          try:
              self.resumeplaybackTimer.cancel()
          except(AttributeError):
              pass
          if self.globalOptions.get('autoResumeAfterSeek',True):
              self.resumeplaybackTimer = threading.Timer(0.8, self.controller.play)
              self.resumeplaybackTimer.start()
          targetSeconds = self.roundToNearestFrame(targetSeconds)
          self.clipped=self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,'m',targetSeconds)
          self.setUiDirtyFlag(specificRID=rid)


          newX=self.secondsToXcoord(targetSeconds)
          qw = int((en-st)/4)

          if qw < 3:
            qw = 0

          if ((st+en)/2) > e.x:
            # Closer to End
            newX-=qw
            if self.dragPreviewMode == 'abs':
                dragoffset = self.dragPreviewPos
            else:
                dragoffset = (ens-sts)*(self.dragPreviewPos/100)

            if ctrl:
              self.controller.seekTo( ((targetSeconds+((ens-sts)/2))) - dragoffset )
            else:
              self.controller.seekTo( ((targetSeconds-((ens-sts)/2))) + dragoffset )
          else:
            # Closer to Start
            newX+=qw

            if self.dragPreviewMode == 'abs':
                dragoffset = self.dragPreviewPos
            else:
                dragoffset = (ens-sts)*(self.dragPreviewPos/100)

            if ctrl:
              self.controller.seekTo( ((targetSeconds-((ens-sts)/2))) + dragoffset )
            else:
              self.controller.seekTo( ((targetSeconds+((ens-sts)/2))) - dragoffset )
          
          self.correctMouseXPosition(newX)
          break

      if shift and not rangeHit:
          if e.delta>0:
              if ctrl and shift:
                self.controller.seekRelative(+self.seekSpeedSlow)
              else:
                self.controller.seekRelative(+self.seekSpeedFast)
              self.currentZoomRangeMidpoint= self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
              self.setUiDirtyFlag()

          else:
              if ctrl and shift:
                self.controller.seekRelative(-self.seekSpeedSlow)
              else:
                self.controller.seekRelative(-self.seekSpeedFast)
              self.currentZoomRangeMidpoint= self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
              self.setUiDirtyFlag()


      elif not rangeHit:

        newZoomFactor = self.timelineZoomFactor
        if e.delta>0:
          newZoomFactor *= 1.5 if ctrl else 1.01
          self.setUiDirtyFlag()
        else:
          newZoomFactor *= 0.666 if ctrl  else 0.99
          self.setUiDirtyFlag()
        
        maxzoom = 150
        try:
            maxzoom = int(self.controller.getTotalDuration())
        except:
            pass

        newZoomFactor = min(max(1,newZoomFactor),maxzoom)
        



        if newZoomFactor == self.timelineZoomFactor:
          self.currentZoomRangeMidpoint= self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
          return

        newZoomRangeMidpoint= self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
        self.currentZoomRangeMidpoint = (self.currentZoomRangeMidpoint+newZoomRangeMidpoint)/2

        self.timelineZoomFactor=newZoomFactor

  @debounce(0.1,0.5)
  def seekto(self,seconds):
    if self.lastSeek is not None and abs(self.lastSeek-seconds)<0.001:
      return
    else:
      self.lastSeek=seconds
    self.controller.seekTo(seconds)

  def requestRIDPreviewCallback(self,filename,timestamp,frameWidth,frameData):
    
    offset = self.handleWidth

    if self.hoverRID == 'V':
        ridfilename = self.controller.getcurrentFilename()
        ridend = self.blocks0
        ridstart = self.blocks1
        offset=0
    else:
        ridfilename,ridend,ridstart = self.controller.controller.videoManager.getDetailsForRangeId(self.hoverRID)
    


    timelineHeight = self.winfo_height()

    if ridstart == timestamp:
        self.startImg = tk.PhotoImage(data=frameData)
        st=self.secondsToXcoord(ridstart)
        iml = self.timeline_canvas.create_image(st+offset,timelineHeight,image=self.startImg,anchor='sw',tags='hoverFrame hoverFramestart')
        #iml = self.timeline_canvas.create_image(st+offset+self.startImg.width() ,timelineHeight,image=self.prefade0,anchor='se',tags='hoverFrame hoverFramestart')

    if ridend == timestamp:
        self.endImg   = tk.PhotoImage(data=frameData)
        en=self.secondsToXcoord(ridend)
        iml = self.timeline_canvas.create_image(en-offset,timelineHeight,image=self.endImg,anchor='se',tags='hoverFrame hoverFrameend')
        #iml = self.timeline_canvas.create_image(en-offset-self.startImg.width(),timelineHeight,image=self.prefade1,anchor='sw',tags='hoverFrame hoverFrameend')

    print(filename,timestamp,frameWidth)


  def requestRIDHoverPreviews(self,rid,pos='m'):
    if self.globalOptions.get('generateRIDHoverPreviews',False):
        
        if rid == 'V':
            ridfilename = self.controller.getcurrentFilename()
            ridend = self.blocks0
            ridstart = self.blocks1
        else:
            ridfilename,ridend,ridstart = self.controller.controller.videoManager.getDetailsForRangeId(self.hoverRID)
        
        timelineHeight = self.winfo_height()

        self.controller.requestRIDHoverPreviews(rid,
                                                (timelineHeight*2,50),
                                                self.requestRIDPreviewCallback,
                                                start=ridstart,
                                                end=ridend
                                                )

  def timelineMousePress(self,e):
    
    if e.type in (tk.EventType.ButtonPress,tk.EventType.ButtonRelease):
        self.timeline_canvas.coords(self.randRangePreview,0,0,0,0)

    if not self.controller.getIsPlaybackStarted():
      self.timeline_canvas.config(cursor="no")
      return    

    enableDraggableHint=False
    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())

    if e.y<20:
      enableDraggableHint=True
    elif self.clickTarget is not None:
      enableDraggableHint=True
    elif e.y>self.winfo_height()-self.handleHeight:
      for rid,(sts,ens) in ranges:
        st=self.secondsToXcoord(sts)
        en=self.secondsToXcoord(ens)

        if (st<e.x<en and e.y>self.winfo_height()-self.midrangeHeight) or (st-self.handleWidth<e.x<en+self.handleWidth and e.y>self.winfo_height()-self.miniMidrangeHeight):
          enableDraggableHint=True
        elif st-self.handleWidth<e.x<st+2:
          enableDraggableHint=True
        elif en-2<e.x<en+self.handleWidth:
          enableDraggableHint=True
        if enableDraggableHint:
          break

    if enableDraggableHint:
        self.timeline_canvas.config(cursor="sb_h_double_arrow")
    else:
        self.timeline_canvas.config(cursor="crosshair")


    ctrl  = (e.state & 0x4) != 0



    self.timeline_canvas.focus_set()

    if e.type in (tk.EventType.ButtonPress,):
      self.lastClickedEndpoint=None
      self.timelineMousePressOffset=0

      if ctrl and self.tempRangeStart is None:
        ctrl_seconds = self.xCoordToSeconds(e.x)
        self.startTempSelection(startOverride=ctrl_seconds)


    if self.clickTarget is None:
            
        if e.type == tk.EventType.Motion or e.type == tk.EventType.ButtonRelease:
          if e.y>20:
            for rid,(sts,ens) in ranges:
              st=self.secondsToXcoord(sts)
              en=self.secondsToXcoord(ens)
              if (st-self.handleWidth)<e.x<(en+self.handleWidth):
                self.hoverRID = rid
                break
            else:
              self.hoverRID = None
          else:
            self.hoverRID = None

        if self.hoverRID != self.previewRID:
            self.previewRID = self.hoverRID
            if not self.previewRIDRequested:
                self.requestRIDHoverPreviews(self.previewRID)
                self.previewRIDRequested = True
            if self.hoverRID is None:
                self.timeline_canvas.delete('hoverFrame')
                self.previewRIDRequested = False



    if e.type in (tk.EventType.ButtonPress,tk.EventType.ButtonRelease):
      self.timeline_mousedownstate[e.num] = e.type == tk.EventType.ButtonPress

      if (e.num==1 and e.y<20) or e.num==2:
        self.rangeHeaderClickStart= self.currentZoomRangeMidpoint-(e.x/self.winfo_width())

      elif e.num==1 and e.y>self.winfo_height()-self.handleHeight:
        targetFound=None

        for rid,(sts,ens) in ranges:
          st=self.secondsToXcoord(sts)
          en=self.secondsToXcoord(ens)

          if (st<e.x<en and e.y>self.winfo_height()-self.midrangeHeight) or (st-self.handleWidth<e.x<en+self.handleWidth and e.y>self.winfo_height()-self.miniMidrangeHeight):
            self.tempRangeStart=None
            self.clickTarget = (rid,'m',sts,ens)
            
            if ((st+en)/2) > e.x:
                self.initialShiftStart = 'End'
            else:
                self.initialShiftStart = 'Start'

            self.setUiDirtyFlag(specificRID=rid)
            self.timelineMousePressOffset = ((st+en)/2)-e.x
            self.controller.pause()
            targetFound=rid
            break
          elif st-self.handleWidth<e.x<st+2:
            self.tempRangeStart=None
            self.clickTarget = (rid,'s',sts,ens)
            self.setUiDirtyFlag(specificRID=rid)
            self.lastClickedEndpoint=(rid,'s')
            self.timelineMousePressOffset = st-e.x
            self.controller.pause()
            targetFound=rid
            break
          elif en-2<e.x<en+self.handleWidth:
            self.tempRangeStart=None
            self.clickTarget = (rid,'e',sts,ens)
            self.setUiDirtyFlag(specificRID=rid)
            self.lastClickedEndpoint=(rid,'e')
            self.timelineMousePressOffset = en-e.x
            self.controller.pause()
            targetFound=rid
            break

        if targetFound is None and self.lastClickedRange is not None:
          self.setUiDirtyFlag(specificRID=self.lastClickedRange)
          self.lastClickedRange=None
        elif targetFound is not None and self.lastClickedRange != targetFound:
          self.setUiDirtyFlag(specificRID=self.lastClickedRange)
          self.lastClickedRange=targetFound
          self.setUiDirtyFlag(specificRID=targetFound)


    if e.type in (tk.EventType.ButtonRelease,) and e.num in (1,2):
      if self.tempRangeStart is not None:
        self.endTempSelection()

      if self.clickTarget is not None:
        rid,pos,os,oe = self.clickTarget
        if pos == 'e':
          self.controller.seekTo( os )

        self.hoverRID = rid
        self.previewRID = self.hoverRID
        if self.hoverRID is not None:
            self.requestRIDHoverPreviews(self.hoverRID,pos=pos)
            self.previewRIDRequested=True

      self.clickTarget = None
      self.rangeHeaderClickStart=None
      if self.globalOptions.get('autoResumeAfterSeek',True):
        self.controller.play()


    if self.timeline_mousedownstate.get(2,False):
      if self.rangeHeaderClickStart is not None:
        self.currentZoomRangeMidpoint = (e.x/self.winfo_width())+self.rangeHeaderClickStart
        self.setUiDirtyFlag()

    if self.timeline_mousedownstate.get(1,False):
      if self.clickTarget is None:
        if self.rangeHeaderClickStart is not None:
          self.currentZoomRangeMidpoint = ((e.x)/self.winfo_width())+self.rangeHeaderClickStart
          self.setUiDirtyFlag()
        else:          
          seconds = self.xCoordToSeconds(e.x)
          self.controller.pause()
          self.seekto(seconds)
          #self.controller.updateStatus('Seeking to {}s'.format(seconds))

          if e.x>self.winfo_width()-2:
            self.currentZoomRangeMidpoint+=0.001
          if e.x<2:
            self.currentZoomRangeMidpoint-=0.001

          if ctrl and self.tempRangeStart is None:
            self.startTempSelection()

          if (not ctrl) and self.tempRangeStart is not None:
            self.endTempSelection()

      if self.clickTarget is not None:
        rid,pos,os,oe = self.clickTarget

        targetSeconds = self.xCoordToSeconds(e.x+self.timelineMousePressOffset)
        targetSeconds = self.roundToNearestFrame(targetSeconds)
        self.setUiDirtyFlag(specificRID=rid,withLock=False)
        self.clipped=self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,targetSeconds)
        self.setUiDirtyFlag(specificRID=rid,withLock=False)
        if pos == 's':
          self.controller.seekTo( targetSeconds )
        elif pos == 'e':
          self.controller.seekTo( targetSeconds-0.001 )
        elif pos == 'm':

          if self.dragPreviewMode == 'abs':
            dragoffset = self.dragPreviewPos
          else:
            dragoffset = (oe-os)*(self.dragPreviewPos/100)

          if self.initialShiftStart == 'End':
            if ctrl:
              targetSeconds = targetSeconds+((oe-os)/2)
              self.controller.seekTo( targetSeconds-dragoffset )
            else:
              targetSeconds = targetSeconds-((oe-os)/2)
              self.controller.seekTo( targetSeconds+dragoffset )
          else:
            if ctrl:
              targetSeconds = targetSeconds-((oe-os)/2)
              self.controller.seekTo( targetSeconds+dragoffset )
            else:
              targetSeconds = targetSeconds+((oe-os)/2)
              self.controller.seekTo( targetSeconds-dragoffset )

    if e.type == tk.EventType.ButtonPress:
      if e.num==3:      
        self.timeline_canvas_last_right_click_x=e.x
        self.timeline_canvas_last_right_click_range=None

        ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
        mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
        lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
        upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
        for rid,(st,et) in list(ranges):
          if st<mid<et:
            self.timeline_canvas_last_right_click_range = rid
            break
          if lower<et<upper or lower<st<upper:
            self.timeline_canvas_last_right_click_range = rid
            break

        if self.timeline_canvas_last_right_click_range is None:
          self.timeline_canvas_popup_menu.entryconfigure(self.rangePropertiesEntry, state='disabled')
          self.timeline_canvas_popup_menu.entryconfigure(self.similarSoundsEntry, state='disabled')
            
        else:
          self.timeline_canvas_popup_menu.entryconfigure(self.rangePropertiesEntry, state='normal')
          self.timeline_canvas_popup_menu.entryconfigure(self.similarSoundsEntry, state='normal')

        self.timeline_canvas_popup_menu.tk_popup(e.x_root,e.y_root)

  def frameResponseCallback(self,filename,timestamp,frameWidth,frameData):
    previewData = tk.PhotoImage(data=frameData)
    if filename == self.controller.getcurrentFilename():
      previewName = ('previewFrame',timestamp)

      if previewName in self.canvasRegionCache:
        self.timeline_canvas.itemconfig(self.canvasRegionCache[previewName],image=previewData, anchor='n',tags='previewFrame')
      self.previewFrames[timestamp] = (frameWidth,previewData)

  def requestFrames(self,filename,startTime,Endtime,timelineWidth,frameWidth):
    self.framesRequested=self.controller.requestTimelinePreviewFrames(filename,startTime,Endtime,frameWidth,timelineWidth,self.frameResponseCallback)

  def centerTimelineOnCurrentPosition(self):
    seekpc = self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
    self.currentZoomRangeMidpoint = seekpc
    self.setUiDirtyFlag()

  def updateCanvas(self,withLock=False):
    
    if withLock:
      updateLock = acquire_timeout(self.uiUpdateLock,0.1)
    else:
      updateLock = AbstractContextManager()

    with updateLock:

      canvasUpdated = False

      if self.controller.getcurrentFilename() is None or self.controller.getTotalDuration() is None:
        return

      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      timelineWidth = self.winfo_width()
      timelineHeight = self.winfo_height()
      
      if self.uiDirty>0:
        self.timeline_canvas.coords(self.rangeHeaderBG,0, 0, timelineWidth, 20)

      startpc = self.xCoordToSeconds(0)/self.controller.getTotalDuration()
      endpc   = self.xCoordToSeconds(timelineWidth)/self.controller.getTotalDuration()

      if self.tempRangeStart is not None:
        a = self.tempRangeStart
        b = self.controller.getCurrentPlaybackPosition()
        d = abs(b-a)
        #a,b = sorted([a,b])
        a = self.secondsToXcoord(a)
        b = self.secondsToXcoord(b)
        self.timeline_canvas.coords(self.tempRangePreview,a,110,b,150)

        self.timeline_canvas.coords(self.tempRangePreviewDurationLabel,(a+b)//2,102)
        self.timeline_canvas.itemconfig(self.tempRangePreviewDurationLabel,text=format_timedelta(datetime.timedelta(seconds=d),'{hours_total}:{minutes2}:{seconds:02.2F}') )
      else:
        self.timeline_canvas.coords(self.tempRangePreview,0,0,0,0)
        self.timeline_canvas.coords(self.tempRangePreviewDurationLabel,0,0)
        self.timeline_canvas.itemconfig(self.tempRangePreviewDurationLabel,text="")

      if self.uiDirty>0 and self.generateWaveImages:

        if self.audioToBytesThread is None and not self.completedAudioByteDecoded: 
          self.audioToBytesThread = threading.Timer(0.0, self.processFileAudioToBytes,args=(self.controller.controller.getcurrentFilename(),self.controller.getTotalDuration()))

          self.audioToBytesThreadKill=False
          self.audioToBytesThread.daemon=True
          self.audioToBytesThread.start()

        newWaveAsPicRequest = (self.controller.controller.getcurrentFilename(),startpc,endpc,self.controller.getTotalDuration(),timelineWidth)

        if self.lastWavePicSectionsRequested != newWaveAsPicRequest:
          if self.wavePicSectionsThread is not None:
            self.wavePicSectionsThread.cancel()
            self.wavePicSectionsThread = None
          self.wavePicSectionsThread = threading.Timer(0.0, self.generateImageSections,args=newWaveAsPicRequest)
          self.wavePicSectionsThread.daemon=True
          self.lastWavePicSectionsRequested = newWaveAsPicRequest
          self.wavePicSectionsThread.start()

      for ts,(frameWidth,frameData) in list(self.previewFrames.items()):
        previewName = ('previewFrame',ts)
        ts_x = self.secondsToXcoord(ts)
        if previewName not in self.canvasRegionCache:
          self.canvasRegionCache[previewName] = self.timeline_canvas.create_image(ts_x, 20, image=frameData, anchor='n',tags='previewFrame')
          self.timeline_canvas.lower(self.canvasRegionCache[previewName])
          self.timeline_canvas.lower(self.previewBG)
        elif self.uiDirty>0:
          self.timeline_canvas.coords(self.canvasRegionCache[previewName],ts_x, 20)

      if not self.framesRequested and self.controller.getcurrentFilename() is not None and self.controller.getTotalDuration() is not None:
        self.requestFrames(self.controller.getcurrentFilename(),0,self.controller.getTotalDuration(),timelineWidth,90)

      self.timeline_canvas.coords(self.rangeHeaderActiveRange,int(startpc*timelineWidth),0,(endpc*timelineWidth),20)

      seekpc = self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
      self.timeline_canvas.coords(self.canvasHeaderSeekPointer,seekpc*timelineWidth,0,seekpc*timelineWidth,20)
      
      seekMidpc  = (startpc+endpc)/2
      self.timeline_canvas.coords(self.rangeHeaderActiveMid,seekMidpc*timelineWidth,0,seekMidpc*timelineWidth,20)
    
      ticky=0
      if self.globalOptions.get('generateTimelineThumbnails',True):
        ticky=45

      if self.uiDirty>0:
        self.timeline_canvas.delete('ticks')
        ticky=0
        if self.globalOptions.get('generateTimelineThumbnails',True):
            ticky=45

        for ts,interesttype in self.controller.getInterestMarks():
          tx = int(self.secondsToXcoord(ts))
          if interesttype=='manual':
            tm = self.timeline_canvas.create_polygon(tx-5, 45+40,tx+5, 45+40, tx, 45+45,fill="#ead9a7",tags='ticks')
          if interesttype=='sceneChange':
            tm = self.timeline_canvas.create_polygon(tx-5, 45+40,tx+5, 45+40, tx, 45+45,fill="green",tags='ticks')

        self.tickmarks=[]


        initialzoom = self.timelineZoomFactor
        while 1:
            ticksdone = False
            tickStart = self.xCoordToSeconds(0)
            tickIncrement=  (self.xCoordToSeconds(timelineWidth)-self.xCoordToSeconds(0))/20
            tickStart = int((tickIncrement * round(tickStart/tickIncrement))-tickIncrement)
            while 1:
              
              if initialzoom != self.timelineZoomFactor:
                initialzoom = self.timelineZoomFactor
                break

              tickStart+=tickIncrement
              tx = int(self.secondsToXcoord(tickStart))
              if tx<0:
                pass
              elif tx>=self.winfo_width():
                ticksdone = True
                break
              else:          
                tm = self.timeline_canvas.create_line(tx, ticky+20, tx, ticky+25,fill="white",tags='ticks') 
                tm_txt = format_timedelta(  datetime.timedelta(seconds=round(self.xCoordToSeconds(tx))), '{hours_total}:{minutes2}:{seconds:02.2F}')
                tm = self.timeline_canvas.create_text(tx-1, ticky+30-1,text=tm_txt,fill="black",tags='ticks') 
                tm = self.timeline_canvas.create_text(tx+1, ticky+30+1,text=tm_txt,fill="black",tags='ticks')             
                tm = self.timeline_canvas.create_text(tx, ticky+30,text=tm_txt,fill="white",tags='ticks') 
            if ticksdone:
                break

      currentPlaybackX =  self.secondsToXcoord(self.roundToNearestFrame(self.controller.getCurrentPlaybackPosition()))
      self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,ticky+55,currentPlaybackX,timelineHeight )
      self.timeline_canvas.coords(self.canvasTimestampLabel,currentPlaybackX,ticky+45)
      self.timeline_canvas.itemconfig(self.canvasTimestampLabel,text=format_timedelta(datetime.timedelta(seconds=round(self.xCoordToSeconds(currentPlaybackX),2)), '{hours_total}:{minutes2}:{seconds:02.2F}'))
      activeRanges=set()

      checkRanges=True

      for rid,(s,e) in list(ranges):

        if checkRanges and (s)<self.controller.getCurrentPlaybackPosition()<(e):
          self.controller.setLoopPos(s,e)
          checkRanges=False

        activeRanges.add(rid)
        
        if rid in self.dirtySelectionRanges or self.uiDirty>0 or (rid,'main') not in self.canvasRegionCache:
          
          self.dirtySelectionRanges.add(rid)

          sx= self.secondsToXcoord(s)
          ex= self.secondsToXcoord(e)
          mx= int((sx+ex)/2)
          qw= int((ex-sx)/4)
          trimpreend    = self.secondsToXcoord(s+self.targetTrim)
          trimpostStart = self.secondsToXcoord(e-self.targetTrim)

          
          if (rid,'main') in self.canvasRegionCache:
            canvasUpdated = True
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'main')],sx+1, timelineHeight-self.midrangeHeight, ex-1, timelineHeight)

            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'startHandle')],sx, timelineHeight-self.handleHeight)
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'endHandle')],ex, timelineHeight-self.handleHeight)
            
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'label')],int((sx+ex)/2),timelineHeight-self.midrangeHeight-20)
              
            if self.clipped != rid:
              self.timeline_canvas.itemconfig(self.canvasRegionCache[(rid,'label')],text="{}s".format(format_timedelta(datetime.timedelta(seconds=round(e-s,2)), '{hours_total}:{minutes2}:{seconds:02.2F}') ) )
            
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'preTrim')],sx, timelineHeight-self.midrangeHeight, min(trimpreend,ex), timelineHeight)
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'postTrim')],max(trimpostStart,sx), timelineHeight-self.midrangeHeight, ex, timelineHeight)

            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'miniDrag')],sx, timelineHeight-self.miniMidrangeHeight, ex, timelineHeight)

            if self.clipped == rid:
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'main')],fill="#ffffff")
              self.timeline_canvas.itemconfig(self.canvasRegionCache[(rid,'label')],text="At Video Edge")
            else:
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'main')],fill="#69dbbe")

            if self.lastClickedRange == rid:
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'miniDrag')],fill="#e5f9f4")
            else:
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'miniDrag')],fill="#2bb390")


            if self.lastClickedEndpoint is None:
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],image=self.image_handle_left_base)
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],image=self.image_handle_right_base)
            elif self.lastClickedEndpoint[0] == rid and self.lastClickedEndpoint[1] == 's':
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],image=self.image_handle_left_light)
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],image=self.image_handle_right_base)
            elif self.lastClickedEndpoint[0] == rid and self.lastClickedEndpoint[1] == 'e':
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],image=self.image_handle_left_base)
              self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],image=self.image_handle_right_light)

            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'midline')], mx , timelineHeight-self.midrangeHeight-10, mx, timelineHeight-self.miniMidrangeHeight)

            hstx = (s/self.controller.getTotalDuration())*timelineWidth
            henx = (e/self.controller.getTotalDuration())*timelineWidth

            self.timeline_canvas.coords(self.canvasRegionCache[(rid,'headerR')],hstx,10, henx, 20)

            if self.clipped != rid:
              try:
                self.dirtySelectionRanges.remove(rid)
              except Exception as e:
                self.setUiDirtyFlag()
                print(e)
            else:
              self.clipped=None

          else:

            self.canvasRegionCache[(rid,'main')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#69dbbe",width=0, tags='fileSpecific')
            self.canvasRegionCache[(rid,'preTrim')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, trimpreend, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
            self.canvasRegionCache[(rid,'postTrim')] = self.timeline_canvas.create_rectangle(trimpostStart, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
            self.canvasRegionCache[(rid,'miniDrag')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.miniMidrangeHeight, ex, timelineHeight, fill="#2bb390",width=0, tags='fileSpecific')
            self.canvasRegionCache[(rid,'startHandle')] = self.timeline_canvas.create_image(sx, timelineHeight-self.handleHeight, anchor='ne', image=self.image_handle_left_base, tags='fileSpecific')
            self.canvasRegionCache[(rid,'endHandle')] = self.timeline_canvas.create_image(ex, timelineHeight-self.handleHeight, anchor='nw', image=self.image_handle_right_base, tags='fileSpecific')
            self.canvasRegionCache[(rid,'label')] = self.timeline_canvas.create_text( int((sx+ex)/2) , timelineHeight-self.midrangeHeight-20,text="{}s".format(format_timedelta(datetime.timedelta(seconds=round(e-s,2)), '{hours_total}:{minutes2}:{seconds:02.2F}')),fill="white", tags='fileSpecific') 
            self.canvasRegionCache[(rid,'midline')] = self.timeline_canvas.create_line( mx , timelineHeight-self.midrangeHeight-10, mx, timelineHeight-self.miniMidrangeHeight , fill="#ffffff",width=1, tags='fileSpecific')

            hstx = (s/self.controller.getTotalDuration())*timelineWidth
            henx = (e/self.controller.getTotalDuration())*timelineWidth
            self.canvasRegionCache[(rid,'headerR')] = self.timeline_canvas.create_rectangle(hstx,10, henx, 20, fill="#299b9b",width=0, tags='fileSpecific')
            
            self.dirtySelectionRanges.add(rid)
            canvasUpdated = True

      if self.uiDirty>0:
        self.decrementUiDirtyFlag()

      if canvasUpdated:
        self.timeline_canvas.update_idletasks()
        self.timeline_canvas.update()

      for (rid,name),i in list(self.canvasRegionCache.items()):
        if rid not in activeRanges and rid != 'previewFrame':
          self.timeline_canvas.delete(i)
          del self.canvasRegionCache[(rid,name)]

  def setUiDirtyFlag(self, specificRID=None, withLock=True):

    pos = 'm'
    if self.clickTarget is not None:
        _,pos,_,_ = self.clickTarget

    if specificRID is None:
      self.uiDirty = min(max(0,self.uiDirty+1),2)
      
      if pos in 'sm':
        self.timeline_canvas.delete('hoverFrameend')
      if pos in 'em':
        self.timeline_canvas.delete('hoverFramestart')

      self.hoverRID=None
      self.previewRIDRequested = False
    else:
      self.dirtySelectionRanges.add(specificRID)
      if self.hoverRID == specificRID:

        if pos in 'sm':
            self.timeline_canvas.delete('hoverFrameend')
        if pos in 'em':
            self.timeline_canvas.delete('hoverFramestart')

        self.hoverRID=None
        self.previewRIDRequested = False

  def decrementUiDirtyFlag(self):
    self.uiDirty = min(max(0,self.uiDirty-1),2)

  def canvasPopupAddNewSubClipToInterestMarksCallback(self,setDirtyAfter=True):
    a = 0
    b = 0
    if self.timeline_canvas_last_right_click_x is not None:
        cs = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
        a,b = self.controller.getSurroundingInterestMarks(cs)

    newRid = None
    if a != b:
        a,b = self.roundToNearestFrame(a),self.roundToNearestFrame(b)
        newRid = self.controller.addNewSubclip(a,b)

    self.timeline_canvas_last_right_click_x=None
    if setDirtyAfter and newRid is not None:
      self.setUiDirtyFlag(specificRID=newRid)


  def canvasPopupExpandSublcipToInterestMarksCallback(self,setDirtyAfter=True):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.expandSublcipToInterestMarks((e+s)/2)
          if setDirtyAfter:
            self.setUiDirtyFlag(specificRID=rid)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.expandSublcipToInterestMarks((e+s)/2)
          if setDirtyAfter:
            self.setUiDirtyFlag(specificRID=rid)
          break
    self.timeline_canvas_last_right_click_x=None

  def canvasPopupCloneSubClipCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.cloneSubclip((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.cloneSubclip((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None
    self.setUiDirtyFlag()


  def canvasPopupCopySubClipCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.copySubclip((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.copySubclip((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None
    

  def canvasPopupPasteSubClipCallback(self):
    newRid = self.controller.pasteSubclip()
    self.timeline_canvas_last_right_click_x=None
    self.setUiDirtyFlag(specificRID=newRid)

  def canvasPopupRemoveSubClipCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<=mid<=e:
          self.controller.removeSubclip((e+s)/2)
          break
        if lower<=e<=upper or lower<=s<=upper:
          self.controller.removeSubclip((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None

  def canvasPopupAddNewInterestMarkCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      self.controller.addNewInterestMark( self.xCoordToSeconds(self.timeline_canvas_last_right_click_x))
      self.setUiDirtyFlag()

  def canvasPopupAddNewSubClipCallback(self,setDirtyAfter=True,defaultSliceDurationOverride=None):
    if self.timeline_canvas_last_right_click_x is not None:
      if defaultSliceDurationOverride is not None:
          pre = defaultSliceDurationOverride*0.5
          post = defaultSliceDurationOverride*0.5
      else:
          pre = self.defaultSliceDuration*0.5
          post = self.defaultSliceDuration*0.5

      a = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)-pre
      b = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)+post
      a,b = self.roundToNearestFrame(a),self.roundToNearestFrame(b)
      newRid = self.controller.addNewSubclip(a,b)

    self.timeline_canvas_last_right_click_x=None
    if setDirtyAfter:
      self.setUiDirtyFlag(specificRID=newRid)

  def canvasPopupFindLowestError1s(self):
    self.findLowestErrorForBetterLoop( self.globalOptions.get('loopNudgeLimit1',1.0))

  def canvasPopupFindLowestError2s(self):
    self.findLowestErrorForBetterLoop( self.globalOptions.get('loopNudgeLimit2',2.0) )

  def canvasPopupFindContainingLoop3s(self):
    self.findLoopAroundFrame(self.globalOptions.get('loopSearchLower1',2), self.globalOptions.get('loopSearchUpper1',3))

  def canvasPopupFindContainingLoop6s(self):
    self.findLoopAroundFrame(self.globalOptions.get('loopSearchLower2',3), self.globalOptions.get('loopSearchUpper2',6))

  def canvasPopupReCenterOnInterFrameDistance(self,pos):
    if self.timeline_canvas_last_right_click_x is not None:
      selectedRange = None
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          selectedRange=rid
          break
        if lower<e<upper or lower<s<upper:
          selectedRange=rid
          break
      if selectedRange is not None:
        self.controller.moveToMaximumInterFrameDistance(rid,pos)
    self.timeline_canvas_last_right_click_x=None

  def findLoopAroundFrame(self,minSeconds,maxSeconds):
    if self.timeline_canvas_last_right_click_x is not None:
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      self.controller.findLoopAroundFrame(mid,minSeconds,maxSeconds)
    self.timeline_canvas_last_right_click_x=None


  def findLowestErrorForBetterLoop(self,secondsChange):
    
    if self.timeline_canvas_last_right_click_x is not None:
      selectedRange = None
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          selectedRange=rid
          break
        if lower<e<upper or lower<s<upper:
          selectedRange=rid
          break
      if selectedRange is not None:
        self.controller.findLowestErrorForBetterLoop(rid,secondsChange)
    self.timeline_canvas_last_right_click_x=None

  def setDefaultsliceDuration(self,value):
    self.defaultSliceDuration=value

  def setTargetTrim(self,value):
    self.targetTrim=value

  def canvasPopupRangeProperties(self):
    if self.timeline_canvas_last_right_click_x is not None:
      selectedRange = None
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          selectedRange=rid
          break
        if lower<e<upper or lower<s<upper:
          selectedRange=rid
          break
      if selectedRange is not None:
        self.controller.canvasPopupRangeProperties(rid)
    self.timeline_canvas_last_right_click_x=None

  def canvasPopupSimilarSounds(self):
    if self.timeline_canvas_last_right_click_x is not None:
      selectedRange = None
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          selectedRange=rid
          break
        if lower<e<upper or lower<s<upper:
          selectedRange=rid
          break
      if selectedRange is not None:
        self.controller.canvasPopupSimilarSounds(rid)
    self.timeline_canvas_last_right_click_x=None


if __name__ == '__main__':
  import webmGenerator
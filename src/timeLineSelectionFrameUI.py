
import tkinter as tk
import tkinter.ttk as ttk

import datetime
import threading
from math import floor
import time
import logging

import subprocess as sp
import numpy as np
import math

def format_timedelta(value, time_format="{days} days, {hours2}:{minutes2}:{seconds2}"):

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


def debounce(wait):
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                debounced._timer = None
                debounced._last_call = time.time()
                return fn(*args, **kwargs)

            time_since_last_call = time.time() - debounced._last_call
            if time_since_last_call >= wait:
                return call_it()

            if debounced._timer is None:
                debounced._timer = threading.Timer(wait - time_since_last_call, call_it)
                debounced._timer.start()
        debounced._timer = None
        debounced._last_call = 0
        return debounced
    return decorator

class TimeLineSelectionFrameUI(ttk.Frame):

  def __init__(self, master, controller, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.controller = controller

    self.timeline_canvas = tk.Canvas(self,width=200, height=150, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=1,column=0,sticky="nesw")
    self.grid_rowconfigure(1, weight=1)
    self.grid_columnconfigure(0, weight=1)

    self.timeline_canvas_popup_menu = tk.Menu(self, tearoff=0)

    self.timeline_canvas_popup_menu.add_command(label="Add new subclip",command=self.canvasPopupAddNewSubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Add new subclip to interest marks",command=self.canvasPopupAddNewSubClipToInterestMarksCallback)

    self.timeline_canvas_popup_menu.add_separator()

    self.timeline_canvas_popup_menu.add_command(label="Delete subclip",command=self.canvasPopupRemoveSubClipCallback)
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Clone subclip",command=self.canvasPopupCloneSubClipCallback)
    
    self.timeline_canvas_popup_menu.add_command(label="Expand subclip to interest marks",command=self.canvasPopupExpandSublcipToInterestMarksCallback)

    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Add new interest mark",command=self.canvasPopupAddNewInterestMarkCallback)
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Nudge to lowest error +- 1s",command=self.canvasPopupFindLowestError1s)
    self.timeline_canvas_popup_menu.add_command(label="Nudge to lowest error +- 2s",command=self.canvasPopupFindLowestError2s)
    
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Find loop of at most 2-3s here",command=self.canvasPopupFindContainingLoop3s)
    self.timeline_canvas_popup_menu.add_command(label="Find loop of at most 3-6s here",command=self.canvasPopupFindContainingLoop6s)

    
    self.timeline_canvas_last_right_click_x=None

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
    self.timeline_canvas.bind('<Left>', self.keyboardLeft)
    self.timeline_canvas.bind('<Right>', self.keyboardRight)


    self.timelineZoomFactor=1.0
    self.dragPreviewPos=0.1
    self.currentZoomRangeMidpoint=0.5
    self.canvasSeekPointer    = self.timeline_canvas.create_line(0, 0, 0, self.timeline_canvas.winfo_height(),fill="white")
    self.canvasTimestampLabel = self.timeline_canvas.create_text(0, 0, text='XXX',fill="white")

    self.targetTrim=0.25
    self.defaultSliceDuration=10.0
    
    self.handleWidth=10
    self.handleHeight=30
    self.midrangeHeight=20
    self.miniMidrangeHeight=7

    self.canvasRegionCache = {}
    self.timeline_mousedownstate={}
    self.tickmarks=[]
    self.uiDirty=True
    self.clickTarget=None

    self.rangeHeaderBG = self.timeline_canvas.create_rectangle(0,0,10,self.winfo_width(),fill="#4E4E4E")
    self.rangeHeaderActiveRange = self.timeline_canvas.create_rectangle(0,0,10,self.winfo_width(),fill="#9E9E9E")
    
    self.rangeHeaderActiveMid = self.timeline_canvas.create_line(0,self.winfo_width()/2,10,self.winfo_width()/2,fill="#4E4E4E")

    self.rangeHeaderClickStart=None

    self.previewBG = self.timeline_canvas.create_rectangle(10,0,10+45,self.winfo_width(),fill="#353535",width=1,outline="white")

    self.canvasHeaderSeekPointer = self.timeline_canvas.create_line(0, 0, 0,10,fill="white")
    self.lastSeek=None

    self.resumeplaybackTimer=None

    self.lastClickedEndpoint = None
    self.framesRequested = False
    self.previewFrames = {}
    self.dirtySelectionRanges = set()

    self.generateWaveImages = False

    self.lastFilenameForAudioToBytesRequest = None
    self.audioByteValuesReadLock = threading.Lock()
    self.audioByteValues        = []
    self.latestAudioByteDecoded = 0
    self.completedAudioByteDecoded = False
    self.audioToBytesThread     = None

    self.lastWavePicSectionsRequested = None
    self.waveAsPicSections            = []
    self.waveAsPicImage               = None
    self.wavePicSectionsThread        = None


  def processFileAudioToBytes(self,filename,totalDuration):
    import subprocess as sp
    sampleRate = 2000
    proc = sp.Popen(['ffmpeg', '-i', filename,  '-ac', '1', '-filter:a', 'compand,aresample={}:async=1'.format(sampleRate), '-map', '0:a', '-c:a', 'pcm_u8', '-f', 'data', '-'],stdout=sp.PIPE,stderr=sp.DEVNULL)
    n=0
    self.completedAudioByteDecoded = False
    while 1:
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
      self.audioByteValuesReadLock.release()
    proc.communicate()
    self.completedAudioByteDecoded = True
    self.audioToBytesThread = None

  def generateImageSections(self,filename,startpc,endpc,totalDuration,outputWidth):
    args = (filename,startpc,endpc,totalDuration,outputWidth)

    completeOnLastPass=False
    while 1:
      startTS = totalDuration*startpc
      endTS   = totalDuration*endpc

      self.audioByteValuesReadLock.acquire()
      if self.completedAudioByteDecoded:
        completeOnLastPass = True
      tempsamples = np.array(self.audioByteValues,np.uint8)
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

          background[sampleszMin:sampleszMax,x,0]=250

        except Exception as e:
          print(e)
        if args != self.lastWavePicSectionsRequested:
          return

      picdata = 'P6\n{w} {h}\n255\n'.format(w=outputWidth,h=40)
      for row in background:
        rowdata = []
        for dtum in row:
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

  def keyboardRight(self,e):
    if self.lastClickedEndpoint is not None:
      self.incrementEndpointPosition(1,*self.lastClickedEndpoint)


  def keyboardLeft(self,e):
    if self.lastClickedEndpoint is not None:
      self.incrementEndpointPosition(-1,*self.lastClickedEndpoint)


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
        self.resumeplaybackTimer = threading.Timer(0.8, self.controller.play)
        self.resumeplaybackTimer.start()

        if pos == 's':
          self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,sts+(increment*0.05))
          self.dirtySelectionRanges.add(rid)
          self.seekto(sts+(increment*0.05))
        elif pos == 'e':
          self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,ens+(increment*0.05))
          self.dirtySelectionRanges.add(rid)
          self.seekto(ens+(increment*0.05)-0.001)
        break

  def setDragPreviewPos(self,value):
    self.dragPreviewPos = value

  def reconfigure(self,e):
    self.uiDirty=True
    if self.controller.getTotalDuration() is not None:
      self.updateCanvas()

  def resetForNewFile(self):
    self.timelineZoomFactor=1.0
    self.currentZoomRangeMidpoint=0.5
    self.canvasRegionCache={}
    self.controller.requestTimelinePreviewFrames(None,None,None,None,None,self.frameResponseCallback)
    self.framesRequested = False;
    self.timeline_canvas.coords(self.canvasSeekPointer, -100,45+55,-100,0 )
    self.timeline_canvas.coords(self.canvasTimestampLabel,-100,45+45)
    self.previewFrames = {}
    self.timeline_canvas.delete('previewFrame')
    self.timeline_canvas.delete('fileSpecific')
    self.timeline_canvas.delete('ticks')
    self.uiDirty=True

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
      return rangeStart+( (xpos/self.winfo_width())*duration )
    except Exception as e:
      logging.error('x coord to seconds Exception',exc_info=e)
      return 0

  def timelineMousewheel(self,e):    
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      ctrl  = (e.state & 0x4) != 0
      for rid,(sts,ens) in ranges:          
        st=self.secondsToXcoord(sts)
        en=self.secondsToXcoord(ens)
        if st<=e.x<=en and e.y>self.winfo_height()-(self.midrangeHeight+10):
          targetSeconds = (sts+ens)/2
          if e.delta>0:
            targetSeconds+=0.01
          else:
            targetSeconds-=0.01
          self.controller.pause()
          try:
              self.resumeplaybackTimer.cancel()
          except(AttributeError):
              pass
          self.resumeplaybackTimer = threading.Timer(0.8, self.controller.play)
          self.resumeplaybackTimer.start()
          self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,'m',targetSeconds)
          self.dirtySelectionRanges.add(rid)
          if ctrl:
            self.controller.seekTo( ((targetSeconds-((ens-sts)/2))) + self.dragPreviewPos )
          else:
            self.controller.seekTo( ((targetSeconds+((ens-sts)/2))) - self.dragPreviewPos )
          break

      else:
        newZoomFactor = self.timelineZoomFactor
        if e.delta>0:
          newZoomFactor *= 1.01
          self.uiDirty=True
        else:
          newZoomFactor *= 0.99
          self.uiDirty=True
        newZoomFactor = min(max(1,newZoomFactor),50)
        if newZoomFactor == self.timelineZoomFactor:
          return
        self.timelineZoomFactor=newZoomFactor


  @debounce(0.1)
  def seekto(self,seconds):
    if self.lastSeek is not None and abs(self.lastSeek-seconds)<0.01:
      return
    else:
      self.lastSeek=seconds
    self.controller.seekTo(seconds)

  def timelineMousePress(self,e):
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

    if e.type in (tk.EventType.ButtonPress,tk.EventType.ButtonRelease):
      self.timeline_mousedownstate[e.num] = e.type == tk.EventType.ButtonPress

      if (e.num==1 and e.y<20) or e.num==2:
        self.rangeHeaderClickStart= self.currentZoomRangeMidpoint-(e.x/self.winfo_width())

      elif e.num==1 and e.y>self.winfo_height()-self.handleHeight:

        for rid,(sts,ens) in ranges:
          st=self.secondsToXcoord(sts)
          en=self.secondsToXcoord(ens)

          if (st<e.x<en and e.y>self.winfo_height()-self.midrangeHeight) or (st-self.handleWidth<e.x<en+self.handleWidth and e.y>self.winfo_height()-self.miniMidrangeHeight):
            self.clickTarget = (rid,'m',sts,ens)
            self.dirtySelectionRanges.add(rid)
            self.timelineMousePressOffset = ((st+en)/2)-e.x
            self.controller.pause()
            break
          elif st-self.handleWidth<e.x<st+2:
            self.clickTarget = (rid,'s',sts,ens)
            self.dirtySelectionRanges.add(rid)
            self.lastClickedEndpoint=(rid,'s')
            self.timelineMousePressOffset = st-e.x
            self.controller.pause()
            break
          elif en-2<e.x<en+self.handleWidth:
            self.clickTarget = (rid,'e',sts,ens)
            self.dirtySelectionRanges.add(rid)
            self.lastClickedEndpoint=(rid,'e')
            self.timelineMousePressOffset = en-e.x
            self.controller.pause()
            break


    if e.type in (tk.EventType.ButtonRelease,) and e.num in (1,2):
      self.clickTarget = None
      self.rangeHeaderClickStart=None
      self.controller.play()

    if self.timeline_mousedownstate.get(2,False):
      if self.rangeHeaderClickStart is not None:
        self.currentZoomRangeMidpoint = (e.x/self.winfo_width())+self.rangeHeaderClickStart
        self.uiDirty=True

    if self.timeline_mousedownstate.get(1,False):
      if self.clickTarget is None:
        if self.rangeHeaderClickStart is not None:
          self.currentZoomRangeMidpoint = ((e.x)/self.winfo_width())+self.rangeHeaderClickStart
          self.uiDirty=True
        else:          
          print(self.timelineMousePressOffset)
          seconds = self.xCoordToSeconds(e.x)
          self.controller.pause()
          self.seekto(seconds)
          self.controller.updateStatus('Seeking to {}s'.format(seconds))

          if e.x>self.winfo_width()-2:
            self.currentZoomRangeMidpoint+=0.001
          if e.x<2:
            self.currentZoomRangeMidpoint-=0.001
      else:
        rid,pos,os,oe = self.clickTarget

        targetSeconds = self.xCoordToSeconds(e.x+self.timelineMousePressOffset)
        self.dirtySelectionRanges.add(rid)
        self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,targetSeconds)
        self.dirtySelectionRanges.add(rid)
        if pos == 's':
          self.controller.seekTo( targetSeconds )
        elif pos == 'e':
          self.controller.seekTo( targetSeconds-0.1 )
        elif pos == 'm':
          if ctrl:
            targetSeconds = targetSeconds-((oe-os)/2)
          else:
            targetSeconds = targetSeconds+((oe-os)/2)
          self.controller.seekTo( targetSeconds-self.dragPreviewPos )

    if e.type == tk.EventType.ButtonPress:
      if e.num==3:      
        self.timeline_canvas_last_right_click_x=e.x
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

  def updateCanvas(self):
    canvasUpdated = False

    if self.controller.getcurrentFilename() is None or self.controller.getTotalDuration() is None:
      return

    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
    timelineWidth = self.winfo_width()
    timelineHeight = self.winfo_height()
    
    startpc = self.xCoordToSeconds(0)/self.controller.getTotalDuration()
    endpc   = self.xCoordToSeconds(timelineWidth)/self.controller.getTotalDuration()


    if self.uiDirty and self.generateWaveImages:

      if self.audioToBytesThread is None: 
        self.audioToBytesThread = threading.Timer(0.0, self.processFileAudioToBytes,args=(self.controller.controller.getcurrentFilename(),self.controller.getTotalDuration()))
        self.audioToBytesThread.daemon=True
        self.audioToBytesThread.start()

      newWaveAsPicRequest = (self.controller.controller.getcurrentFilename(),startpc,endpc,self.controller.getTotalDuration(),timelineWidth)

      if self.lastWavePicSectionsRequested != newWaveAsPicRequest:
        if self.wavePicSectionsThread is not None:
          self.wavePicSectionsThread.cancel()
          self.wavePicSectionsThread = None
        self.wavePicSectionsThread = threading.Timer(0.2, self.generateImageSections,args=newWaveAsPicRequest)
        self.wavePicSectionsThread.daemon=True
        self.wavePicSectionsThread.start()
        self.lastWavePicSectionsRequested = newWaveAsPicRequest

      self.timeline_canvas.coords(self.rangeHeaderBG,0,0,timelineWidth,20,)
      self.timeline_canvas.coords(self.previewBG,0,20,timelineWidth,20+45,)

    for ts,(frameWidth,frameData) in list(self.previewFrames.items()):
      previewName = ('previewFrame',ts)
      ts_x = self.secondsToXcoord(ts)
      if previewName not in self.canvasRegionCache:
        self.canvasRegionCache[previewName] = self.timeline_canvas.create_image(ts_x, 20, image=frameData, anchor='n',tags='previewFrame')
        self.timeline_canvas.lower(self.canvasRegionCache[previewName])
        self.timeline_canvas.lower(self.previewBG)
      elif self.uiDirty:
        self.timeline_canvas.coords(self.canvasRegionCache[previewName],ts_x, 20)

    if not self.framesRequested and self.controller.getcurrentFilename() is not None and self.controller.getTotalDuration() is not None:
      self.requestFrames(self.controller.getcurrentFilename(),0,self.controller.getTotalDuration(),timelineWidth,90)

    self.timeline_canvas.coords(self.rangeHeaderActiveRange,int(startpc*timelineWidth),0,(endpc*timelineWidth),20)

    seekpc = self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
    self.timeline_canvas.coords(self.canvasHeaderSeekPointer,seekpc*timelineWidth,0,seekpc*timelineWidth,20)
    
    seekMidpc  = (startpc+endpc)/2
    self.timeline_canvas.coords(self.rangeHeaderActiveMid,seekMidpc*timelineWidth,0,seekMidpc*timelineWidth,20)

    if self.uiDirty:
      self.timeline_canvas.delete('ticks')

      for ts,interesttype in self.controller.getInterestMarks():
        print(ts,interesttype)
        tx = int(self.secondsToXcoord(ts))
        if interesttype=='manual':
          tm = self.timeline_canvas.create_polygon(tx-5, 45+40,tx+5, 45+40, tx, 45+45,fill="#ead9a7",tags='ticks')
        if interesttype=='sceneChange':
          tm = self.timeline_canvas.create_polygon(tx-5, 45+40,tx+5, 45+40, tx, 45+45,fill="green",tags='ticks')

      self.tickmarks=[]
      tickStart = self.xCoordToSeconds(0)
      tickIncrement=  (self.xCoordToSeconds(timelineWidth)-self.xCoordToSeconds(0))/20

      tickStart = int((tickIncrement * round(tickStart/tickIncrement))-tickIncrement)

      while 1:
        tickStart+=tickIncrement
        tx = int(self.secondsToXcoord(tickStart))
        if tx<0:
          pass
        elif tx>=self.winfo_width():
          break
        else:          
          tm = self.timeline_canvas.create_line(tx, 45+20, tx, 45+22,fill="white",tags='ticks') 
          tm = self.timeline_canvas.create_text(tx, 45+30,text=format_timedelta(  datetime.timedelta(seconds=round(self.xCoordToSeconds(tx))), '{hours_total}:{minutes2}:{seconds2}'),fill="white",tags='ticks') 

    currentPlaybackX =  self.secondsToXcoord(self.controller.getCurrentPlaybackPosition())
    self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,45+55,currentPlaybackX,timelineHeight )
    self.timeline_canvas.coords(self.canvasTimestampLabel,currentPlaybackX,45+45)
    self.timeline_canvas.itemconfig(self.canvasTimestampLabel,text=format_timedelta(datetime.timedelta(seconds=round(self.xCoordToSeconds(currentPlaybackX))), '{hours_total}:{minutes2}:{seconds2}'))
    activeRanges=set()

    for rid,(s,e) in list(ranges):

      if s<self.controller.getCurrentPlaybackPosition()<e:
        self.controller.setLoopPos(s,e)

      activeRanges.add(rid)
      
      if rid in self.dirtySelectionRanges or self.uiDirty or (rid,'main') not in self.canvasRegionCache:
        
        self.dirtySelectionRanges.add(rid)

        sx= self.secondsToXcoord(s)
        ex= self.secondsToXcoord(e)
        trimpreend    = self.secondsToXcoord(s+self.targetTrim)
        trimpostStart = self.secondsToXcoord(e-self.targetTrim)

        
        if (rid,'main') in self.canvasRegionCache:
          print('update',rid)
          canvasUpdated = True
          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'main')],sx, timelineHeight-self.midrangeHeight, ex, timelineHeight)

          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'startHandle')],sx-self.handleWidth, timelineHeight-self.handleHeight, sx+0, timelineHeight)
          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'endHandle')],ex-0, timelineHeight-self.handleHeight, ex+self.handleWidth, timelineHeight)
          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'label')],int((sx+ex)/2),timelineHeight-self.midrangeHeight-20)
          self.timeline_canvas.itemconfig(self.canvasRegionCache[(rid,'label')],text="{}s".format(format_timedelta(datetime.timedelta(seconds=round(e-s,2)), '{hours_total}:{minutes2}:{seconds2}') ) )
          
          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'preTrim')],sx, timelineHeight-self.midrangeHeight, min(trimpreend,ex), timelineHeight)
          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'postTrim')],max(trimpostStart,sx), timelineHeight-self.midrangeHeight, ex, timelineHeight)

          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'miniDrag')],sx-self.handleWidth, timelineHeight-self.miniMidrangeHeight, ex+self.handleWidth, timelineHeight)


          if self.lastClickedEndpoint is None:
            self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],width=0)
            self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],width=0)
          elif self.lastClickedEndpoint[0] == rid and self.lastClickedEndpoint[1] == 's':
            self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],width=1,outline='white')
            self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],width=0)
          elif self.lastClickedEndpoint[0] == rid and self.lastClickedEndpoint[1] == 'e':
            self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],width=1,outline='white')
            self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],width=0)


          for dtx in (-1,1):
            for dty in (-1,0,1,2):
              dst_tn = 'startHandleDot'+str(dtx)+str(dty)
              self.timeline_canvas.coords(self.canvasRegionCache[(rid,dst_tn)], sx-(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , sx-(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1 ) 
              dst_tn = 'endHandleDot'+str(dtx)+str(dty)
              self.timeline_canvas.coords(self.canvasRegionCache[(rid,dst_tn)], ex+(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , ex+(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1 )


          hstx = (s/self.controller.getTotalDuration())*timelineWidth
          henx = (e/self.controller.getTotalDuration())*timelineWidth

          self.timeline_canvas.coords(self.canvasRegionCache[(rid,'headerR')],hstx,10, henx, 20)
          self.dirtySelectionRanges.remove(rid)
          
        else:
          print('add',rid)
              
          self.canvasRegionCache[(rid,'main')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#69dbbe",width=0, tags='fileSpecific')
          self.canvasRegionCache[(rid,'preTrim')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, trimpreend, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
          self.canvasRegionCache[(rid,'postTrim')] = self.timeline_canvas.create_rectangle(trimpostStart, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
       
          self.canvasRegionCache[(rid,'startHandle')] = self.timeline_canvas.create_rectangle(sx-self.handleWidth, timelineHeight-self.handleHeight, sx+0, timelineHeight, fill="#69bfdb",width=1, tags='fileSpecific')
          self.canvasRegionCache[(rid,'endHandle')] = self.timeline_canvas.create_rectangle(ex-0, timelineHeight-self.handleHeight, ex+self.handleWidth, timelineHeight, fill="#db6986",width=1, tags='fileSpecific')

          for dtx in (-1,1):
            for dty in (-1,0,1,2):
              dst_tn = 'startHandleDot'+str(dtx)+str(dty)
              self.canvasRegionCache[(rid,dst_tn)] = self.timeline_canvas.create_line( sx-(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , sx-(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1  , fill="#333",width=1, tags='fileSpecific')
              dst_tn = 'endHandleDot'+str(dtx)+str(dty)
              self.canvasRegionCache[(rid,dst_tn)] = self.timeline_canvas.create_line( ex+(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , ex+(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1  , fill="#333",width=1, tags='fileSpecific')


          self.canvasRegionCache[(rid,'label')] = self.timeline_canvas.create_text( int((sx+ex)/2) , timelineHeight-self.midrangeHeight-20,text="{}s".format(format_timedelta(datetime.timedelta(seconds=round(e-s,2)), '{hours_total}:{minutes2}:{seconds2}')),fill="white", tags='fileSpecific') 
      

          self.canvasRegionCache[(rid,'miniDrag')] = self.timeline_canvas.create_rectangle(sx-self.handleWidth, timelineHeight-self.miniMidrangeHeight, ex+self.handleWidth, timelineHeight, fill="#2bb390",width=0, tags='fileSpecific')


          hstx = (s/self.controller.getTotalDuration())*timelineWidth
          henx = (e/self.controller.getTotalDuration())*timelineWidth
          self.canvasRegionCache[(rid,'headerR')] = self.timeline_canvas.create_rectangle(hstx,10, henx, 20, fill="#299b9b",width=0, tags='fileSpecific')
          
          self.dirtySelectionRanges.add(rid)
          canvasUpdated = True

    if canvasUpdated:
      self.timeline_canvas.update_idletasks()
      self.timeline_canvas.update()

    for (rid,name),i in list(self.canvasRegionCache.items()):
      if rid not in activeRanges and rid != 'previewFrame':
        print('remove',rid)
        self.timeline_canvas.delete(i)
        del self.canvasRegionCache[(rid,name)]
    self.uiDirty=False

  def setUiDirtyFlag(self):
    self.uiDirty=True    


  def canvasPopupAddNewSubClipToInterestMarksCallback(self):
    self.canvasPopupAddNewSubClipCallback(setDirtyAfter=False)
    self.canvasPopupExpandSublcipToInterestMarksCallback(setDirtyAfter=False)
    self.uiDirty=True

  def canvasPopupExpandSublcipToInterestMarksCallback(self,setDirtyAfter=True):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.expandSublcipToInterestMarks((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.expandSublcipToInterestMarks((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None
    if setDirtyAfter:
      self.uiDirty=True


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
    self.uiDirty=True

  def canvasPopupRemoveSubClipCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.removeSubclip((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.removeSubclip((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None

  def canvasPopupAddNewInterestMarkCallback(self):
    print(self.timeline_canvas_last_right_click_x,)
    if self.timeline_canvas_last_right_click_x is not None:
      self.controller.addNewInterestMark( self.xCoordToSeconds(self.timeline_canvas_last_right_click_x))
      self.uiDirty=True

  def canvasPopupAddNewSubClipCallback(self,setDirtyAfter=True):
    print(self.timeline_canvas_last_right_click_x,)
    if self.timeline_canvas_last_right_click_x is not None:
      pre = self.defaultSliceDuration*0.5
      post = self.defaultSliceDuration*0.5
      self.controller.addNewSubclip( self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)-pre,self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)+post  )

    self.timeline_canvas_last_right_click_x=None
    if setDirtyAfter:
      self.uiDirty=True

  def canvasPopupFindLowestError1s(self):
    self.findLowestErrorForBetterLoop(1.0)

  def canvasPopupFindLowestError2s(self):
    self.findLowestErrorForBetterLoop(2.0)

  def canvasPopupFindContainingLoop3s(self):
    self.findLoopAroundFrame(2.0,3.0)

  def canvasPopupFindContainingLoop6s(self):
    self.findLoopAroundFrame(3.0,6.0)

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


if __name__ == '__main__':
  import webmGenerator
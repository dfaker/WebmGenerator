

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import subprocess as sp
import string
import os
import logging
import sys

import threading

try:
  from .encodingUtils import cleanFilenameForFfmpeg
except:
  from encodingUtils import cleanFilenameForFfmpeg

from datetime import datetime


scriptPath = os.path.dirname(os.path.abspath(__file__))
basescriptPath = os.path.split(scriptPath)[0]
scriptPath_frozen = os.path.dirname(os.path.abspath(sys.executable))
os.environ["PATH"] = scriptPath + os.pathsep + scriptPath_frozen + os.pathsep + os.environ["PATH"]
print(scriptPath)
print(scriptPath_frozen)

os.add_dll_directory(basescriptPath)
os.add_dll_directory(scriptPath)
os.add_dll_directory(scriptPath_frozen)

import mpv

class VideoAudioSync(tk.Toplevel):
  def __init__(self, master=None, controller=None, sequencedClips=[], dubFile=None, dubOffsetVar=None, fadeVar=None, mixVar=None, *args):

    tk.Toplevel.__init__(self, master)
    
    self.title('Sequence Preview and Audio Track Sync')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,100)
    self.controller=controller
    self.master=master

    self.isActive=True
    
    self.playerFrame = ttk.Frame(self,style='PlayerFrame.TFrame',height='200', width='200')
    self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0,columnspan=14)

    self.timeline_canvas = tk.Canvas(self,width=200, height=120, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=2,column=0,columnspan=14,sticky="nesw")
    
    self.timeline_canvas.bind("<Button-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<B1-Motion>", self.timelineMousePress)

    self.timeline_canvas.bind("<MouseWheel>", self.timelineMousewheel)
    self.timeline_canvas.bind("<Motion>", self.timelineMouseMotion)




    self.canvasZoomBG         = self.timeline_canvas.create_rectangle(-1, 0, -1, 20,fill="#3F3F7F")
    self.canvasZoomBGRange    = self.timeline_canvas.create_rectangle(-1, 0, -1, 20,fill="#9E9E9E")
    self.canvasZoomRangeMid   = self.timeline_canvas.create_line(-1, 0, -1, 20,fill="#3F3F7F")

    self.canvasSeekPointer      = self.timeline_canvas.create_line(-1, 0, -1, self.timeline_canvas.winfo_height(),fill="white")
    self.canvasUpperSeekPointer = self.timeline_canvas.create_rectangle(-1, 0, -1, self.timeline_canvas.winfo_height(),fill="#c5c5d8",outline='white')





    self.playerwid = self.playerFrame.winfo_id()

    self.dubFile   = dubFile
    self.dubOffsetVar = dubOffsetVar
    self.fadeVar      = fadeVar
    self.sequencedClips = sequencedClips
    self.volumeVar = tk.StringVar()
    self.seekOffsetVar = tk.StringVar()
    self.seekOffsetVar.set(-1)
    self.speedVar = tk.StringVar()
    self.speedVar.set(1)
    self.textInfo = tk.StringVar()
    self.textInfo.set('offset=0.00')

    self.mixVar = mixVar

    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=1)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=0)

    self.columnconfigure(0, weight=1)
    self.columnconfigure(1, weight=1)
    self.columnconfigure(2, weight=1)
    self.columnconfigure(3, weight=1)
    self.columnconfigure(4, weight=1)
    self.columnconfigure(5, weight=1)
    self.columnconfigure(6, weight=1)
    self.columnconfigure(7, weight=1)
    self.columnconfigure(8, weight=1)
    self.columnconfigure(9, weight=1)
    self.columnconfigure(10, weight=1)
    self.columnconfigure(11, weight=1)
    self.columnconfigure(12, weight=1)
    self.columnconfigure(13, weight=1)


    self.tickColours=["#a9f9b9","#7dc4ed","#f46350","#edc1a6","#dfff91","#0f21e0","#f73dc8","#8392db","#72dbb4","#cc8624","#88ed71","#d639be"]

    self.player = mpv.MPV(loop='inf',
                          mute=False,
                          volume=10,
                          autofit_larger='1280', wid=str(self.playerwid))

    self.currentTotalDuration=None
    self.currentTimePos=None
    self.ticktimestamps=[]
    self.tickXpos=[]
    self.colourMap={}
    self.ridListing=[]

    self.player.observe_property('time-pos', self.handleMpvTimePosChange)
    self.player.observe_property('duration', self.handleMpvDurationChange)
    self.player.observe_property('af-metadata',self.handleMpvafMetdata)


    if self.dubFile.get() is not None and os.path.exists(self.dubFile.get()):
      mp3name = os.path.basename(self.dubFile.get()) 

    self.labeldubFile = ttk.Label(self)
    self.labeldubFile.config(anchor='e',  text='Dubbing file:')
    self.labeldubFile.grid(row=3,column=0,sticky='ew')
    self.entrydubFile = ttk.Button(self,text='None',command=self.selectAudioOverride,width=40)
    Tooltip(self.entrydubFile,text='An mp3 audio file to use to replace the original video audio.')
    self.entrydubFile.grid(row=3,column=1,sticky='ew')
 

    self.labelpostSeekOffset = ttk.Label(self)
    self.labelpostSeekOffset.config(anchor='e',  text='Edit Seek Offset')
    self.labelpostSeekOffset.grid(row=3,column=2,sticky='ew')
    self.entrypostSeekOffset = ttk.Spinbox(self, textvariable=self.seekOffsetVar,from_=float('-inf'), 
                                          to=float('inf'), 
                                          increment=0.1)
    Tooltip(self.entrypostSeekOffset,text='Edit Seek Offset')
    self.entrypostSeekOffset.grid(row=3,column=3,sticky='ew')

    self.labelpostAudioVolume = ttk.Label(self)
    self.labelpostAudioVolume.config(anchor='e',  text='Volume')
    self.labelpostAudioVolume.grid(row=3,column=4,sticky='ew')
    self.entrypostAudioVolume = ttk.Spinbox(self, textvariable=self.volumeVar,from_=0, 
                                          to=100, 
                                          increment=5)
    Tooltip(self.entrypostAudioVolume,text='Audio Volume.')
    self.entrypostAudioVolume.grid(row=3,column=5,sticky='ew')
    self.volumeVar.set(0)
    self.volumeVar.trace('w',self.valueChangeVolume)


    self.labelpostAudioOverrideDelay = ttk.Label(self)
    self.labelpostAudioOverrideDelay.config(anchor='e',  text='Dub Delay (seconds)')
    self.labelpostAudioOverrideDelay.grid(row=3,column=6,sticky='ew')
    self.entrypostAudioOverrideDelay = ttk.Spinbox(self, textvariable=self.dubOffsetVar,from_=float('-inf'), 
                                          to=float('inf'), 
                                          increment=0.1)
    Tooltip(self.entrypostAudioOverrideDelay,text='Delay before the start of the mp3 dub audio.')
    self.entrypostAudioOverrideDelay.grid(row=3,column=7,sticky='ew')

    self.dubOffsetVar.trace('w',self.valueChangeCallback)      
    
    self.labelTransDuration = ttk.Label(self)
    self.labelTransDuration.config(anchor='e', padding='2', text='Transition Duration')
    self.labelTransDuration.grid(row=4,column=0,sticky='ew')
    self.entryTransDuration = ttk.Spinbox(self, 
                                          from_=0, 
                                          to=float('inf'), 
                                          increment=0.01,
                                          textvariable=self.fadeVar)

    self.entryTransDuration.grid(row=4,column=1,sticky='ew')
    self.fadeVar.trace('w',self.valueChangeCallback)

    self.labelPlaybackSpeed = ttk.Label(self)
    self.labelPlaybackSpeed.config(anchor='e', padding='2', text='Playback Speed')
    self.labelPlaybackSpeed.grid(row=4,column=2,sticky='ew')
    self.entrySpeed = ttk.Spinbox(self, 
                                          from_=0, 
                                          to=50, 
                                          increment=0.1,
                                          textvariable=self.speedVar)
    self.entrySpeed.grid(row=4,column=3,sticky='ew')
    self.speedVar.trace('w',self.speedChange)

    self.labelMixBias = ttk.Label(self)
    self.labelMixBias.config(anchor='e', padding='2', text='Audio Mix')
    self.labelMixBias.grid(row=4,column=4,sticky='ew')
    self.entryMixBias = ttk.Spinbox(self,
                                          from_=0, 
                                          to=1, 
                                          increment=0.1,
                                          textvariable=self.mixVar)
    self.entryMixBias.grid(row=4,column=5,sticky='ew')
    self.mixVar.trace('w',self.valueChangeCallback)

    self.labelMixInfo = ttk.Label(self,textvariable=self.textInfo)
    self.labelMixInfo.grid(row=4,column=6,sticky='ew',columnspan=2)

    self.attributes('-topmost', True)
    self.update()
    self.edlBytes=b''
    self.edlStreamFunc=None

    self.keepWidth=False
    self.blockSpectrumUpdates=False
    self.durationForScale=0
    self.redrawTimer=None
    self.lastseekPos=0

    self.timelineZoomFactor=1
    self.currentZoomRangeMidpoint=0.5
    self.rangeHeaderClickStart = None


    self.draggingTickIndex=None
    self.draggingTickOffset=0

    def quitFunc(key_state, key_name, key_char):
      self.isActive=False

      try:
        self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('duration', self.handleMpvDurationChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('af-metadata', self.handleMpvafMetdata)
      except Exception as e:
        print(e)

      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()
      self.isActive=False
      self.attributes('-topmost', False)
      self.update()

    self.player.register_key_binding("CLOSE_WIN", quitFunc)
    self.bind('<Configure>', self.reconfigureWindow)

    self.recalculateEDLTimings()


  @staticmethod
  def pureGetClampedCenterPosAndRange(totalDuration,zoomFactor,currentMidpoint):

    outputDuration = totalDuration*(1/zoomFactor)
    minPercent     = (1/zoomFactor)/2
    center         = min(max(minPercent,currentMidpoint),1-minPercent)
    lowerRange     = (totalDuration*center)-(outputDuration/2)
    return outputDuration,center,lowerRange

  def getClampedCenterPosAndRange(self,update=True,negative=False):

    duration = self.currentTotalDuration
    if duration is None:
      duration = self.durationForScale
    if duration is None:
      duration=0

    result  = self.pureGetClampedCenterPosAndRange(duration,
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
      ctrl  = (e.state & 0x4) != 0
      shift = (e.state & 0x1) != 0
      if e.y<20:

        factor = 0.10
        if shift:
          factor=0.25
        if ctrl:
          factor=1

        if e.delta>0:
          self.currentZoomRangeMidpoint += factor/self.timelineZoomFactor
          self.recalculateEDLTimings()
          return
        else:
          self.currentZoomRangeMidpoint -= factor/self.timelineZoomFactor
          self.recalculateEDLTimings()
          return
      else:
        dirty=False
        newZoomFactor = self.timelineZoomFactor
        if e.delta>0:
          newZoomFactor *= 1.5 if ctrl else 1.01
          dirty=True
        else:
          newZoomFactor *= 0.666 if ctrl  else 0.99
          dirty=True
        newZoomFactor = min(max(1,newZoomFactor),150)
        if newZoomFactor == self.timelineZoomFactor:
          return
        if dirty:
          self.timelineZoomFactor=newZoomFactor
          self.recalculateEDLTimings()

  def generateSpectrum(self):
    if (not self.blockSpectrumUpdates) and self.dubFile.get() is not None and os.path.exists(self.dubFile.get()) and self.currentTotalDuration is not None:
      t = threading.Thread(target=self.generateSpectrum_async,daemon=True)
      t.start()

  def generateSpectrum_async(self):
    if (not self.blockSpectrumUpdates) and self.dubFile.get() is not None and os.path.exists(self.dubFile.get()) and self.currentTotalDuration is not None:
      
      self.timeline_canvas.delete('waveAsPicImage')

      startoffset=self.xCoordToSeconds(0)
      try:
        startoffset = float(self.dubOffsetVar.get())+self.xCoordToSeconds(0)
      except:
        pass


      orig_height = self.timeline_canvas.winfo_height()
      orig_width = self.timeline_canvas.winfo_width()

      orig_startoffset = startoffset
      orig_currentTotalDuration = (self.xCoordToSeconds(orig_width)-self.xCoordToSeconds(0))
      

      proc = sp.Popen(['ffmpeg', '-y', '-i', self.dubFile.get(), '-filter_complex', "[0:a]atrim={}:{},bass=g=3,showwavespic=s={}x80:colors=5C5CAE".format(orig_startoffset,orig_currentTotalDuration+orig_startoffset,orig_width), '-c:v', 'ppm', '-f', 'rawvideo', '-'],stdout=sp.PIPE)
      outs,errs = proc.communicate()        

      startoffset=self.xCoordToSeconds(0)
      try:
        startoffset = float(self.dubOffsetVar.get())+self.xCoordToSeconds(0)
      except:
        pass
      newTotalDuration = (self.xCoordToSeconds(orig_width)-self.xCoordToSeconds(0))

      if orig_startoffset == startoffset and orig_currentTotalDuration == newTotalDuration and orig_width == self.timeline_canvas.winfo_width():
        self.waveAsPicImage = tk.PhotoImage(data=outs)
        self.timeline_canvas.delete('waveAsPicImage')
        canvasimg = self.timeline_canvas.create_image(0,orig_height-80,image=self.waveAsPicImage,anchor='nw',tags='waveAsPicImage')
        self.timeline_canvas.lower(canvasimg)


  def speedChange(self,*args):
    newspeed = min(max(0,float(self.speedVar.get())),50)
    self.player.speed = str(newspeed)


  def handleMpvafMetdata(self,name,value):
    print(name,value)


  def toggleBoringMode(self,boringMode):
    if boringMode:
      self.playerFrame.grid_forget()
      if self.dubFile.get() is None or self.dubFile.get() == 'None' or (not os.path.exists(self.dubFile.get())):
        self.player.volume=0
    else:
      self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0,columnspan=9)

  def selectAudioOverride(self):
    files = askopenfilename(multiple=False,filetypes=[('mp3','*.mp3',),('wav','*.wav')])
    if files is None or len(files)==0:
      self.dubFile.set('None')
      self.entrydubFile.config(text='None')
    else:
      self.entrydubFile.config(text=os.path.basename(str(files)))
      self.dubFile.set(str(files))

    self.generateSpectrum()

  def updateRegionsOnDrag(self,index,timestamp):
    movestart=moveend=ots=sv=otsn=svn = False

    if index>=0:
      movestart=True
      ots = self.ticktimestamps[index]
      sv  = self.sequencedClips[index]

    if index+2<=len(self.ticktimestamps):
      moveend=True
      otsn = self.ticktimestamps[index+1]
      svn  = self.sequencedClips[index+1]

    self.keepWidth=True
    if movestart:
      self.controller.updateSubclipBoundry(sv,ots,timestamp,'e')
    if moveend:
      self.controller.updateSubclipBoundry(svn,otsn,timestamp,'s')

  def timelineMouseMotion(self,e):  
    if e.y<20:
      self.timeline_canvas.config(cursor="sb_h_double_arrow")
      return
    elif 20+20<e.y<20+20+15:
      for tx,tidx in self.tickXpos:
        if tx-6-5-4<e.x<tx+6+5+4:
          self.timeline_canvas.config(cursor="sb_h_double_arrow")
          return
      else:
        tlw=self.timeline_canvas.winfo_width()
        if e.x>tlw-6-5-4:
          self.timeline_canvas.config(cursor="sb_h_double_arrow")
          return
    elif 20+5<e.y<20+20:
      for tx,tidx in self.tickXpos:
        if tx-6-5-4<e.x<tx:
          self.timeline_canvas.config(cursor="right_side")
          return
        elif tx<e.x<tx+6+5+4:
          self.timeline_canvas.config(cursor="left_side")
          return
    
    self.timeline_canvas.config(cursor="arrow")

  def timelineMousePress(self,e):  
    pressSeconds = self.xCoordToSeconds(e.x)

    print(e.type)

    if e.type == tk.EventType.ButtonPress:
      if 20+20<e.y<20+20+15:
        for tx,tidx in self.tickXpos:
          if tx-6-5-4<e.x<tx+6+5+4:
            self.draggingTickIndex=tidx
            self.draggingTickOffset=e.x-tx
        else:
          tlw=self.timeline_canvas.winfo_width()
          if e.x>tlw-6-5-4:
            self.draggingTickIndex=len(self.tickXpos)
            self.draggingTickOffset=e.x-tlw

      if e.y<20:
        self.rangeHeaderClickStart = self.currentZoomRangeMidpoint-(e.x/self.winfo_width())

    elif e.type == tk.EventType.Motion:
      if self.rangeHeaderClickStart is not None:
        self.currentZoomRangeMidpoint = (e.x/self.winfo_width())+self.rangeHeaderClickStart
        self.recalculateEDLTimings()

    elif e.type == tk.EventType.ButtonRelease:
      if self.rangeHeaderClickStart is not None:
        self.rangeHeaderClickStart=None

      if self.draggingTickIndex is not None:
        self.updateRegionsOnDrag(self.draggingTickIndex,pressSeconds)
        self.draggingTickIndex=None
        try:
          self.redrawTimer.cancel()
        except:
          pass
        self.restoreKeepWidthAndRecaulate()
      self.draggingTickIndex=None
      self.timeline_canvas.delete('dragTick')
      return

    if self.draggingTickIndex is not None:
      
      self.timeline_canvas.delete('dragTick')

      self.timeline_canvas.create_polygon(  e.x,    20+20+2, 
                                            e.x-7,  20+20+2+5, 
                                            e.x,    20+20+2+11,
                                            e.x+7,  20+20+2+5,
                                          fill='white',tags='dragTick')

      self.timeline_canvas.create_line(e.x, 20+0, 
                                       e.x, 200,fill='white',tags='dragTick')


    self.timeline_canvas.focus_set()

    if 20+5<e.y<20+20:
      for tx,tidx in self.tickXpos:
        if tx-6-5-4<e.x<tx:
          print(tidx,'+1')
          self.master.moveSequencedClipByIndex(tidx,+1)
          return
        elif tx<e.x<tx+6+5+4:
          print(tidx+1,'-1')
          self.master.moveSequencedClipByIndex(tidx+1,-1)
          return

    if self.rangeHeaderClickStart is None:
      if self.currentTotalDuration is None:
        self.player.command('seek','0','absolute-percent','exact')
      else:
        self.player.command('seek',self.xCoordToSeconds(e.x),'absolute','exact')

      if self.draggingTickIndex is None:
        for st,et,rid in self.ridListing:
          if st<pressSeconds<et:
            startoffset = pressSeconds-st
            self.master.synchroniseCutController(rid,startoffset)
            break


  def handleMpvTimePosChange(self,name,value):
    
    timelineWidth = self.timeline_canvas.winfo_width()
    timelineHeight = self.timeline_canvas.winfo_height()

    if value is not None:
      self.currentTimePos = value
      if self.currentTotalDuration is not None:
        currentPlaybackX = self.secondsToXcoord(self.currentTimePos) 

        if self.draggingTickIndex is None:
          self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,0,currentPlaybackX,timelineHeight )
          upperseekx = (self.currentTimePos/self.currentTotalDuration)*timelineWidth
          self.timeline_canvas.coords(self.canvasUpperSeekPointer, upperseekx-2,0,upperseekx+2,20 )
        else:
          self.timeline_canvas.coords(self.canvasSeekPointer,      -1,0,-1,timelineHeight )
          self.timeline_canvas.coords(self.canvasUpperSeekPointer, -1,0,-1,timelineHeight )


        for st,et,rid in self.ridListing:
          if st<self.currentTimePos<et:
            self.textInfo.set('offset={:0.4f}'.format(self.currentTimePos-st))
            break

  def handleMpvDurationChange(self,name,value):
    if value is not None:
      self.currentTotalDuration=value
      self.generateSpectrum()

  def valueChangeVolume(self,*args):
    self.player.volume = int(self.volumeVar.get())

  def valueChangeCallback(self,*args):
    if self.player:
      self.recalculateEDLTimings()

  def reconfigureWindow(self,e):
    self.recalculateEDLTimings(seekAfter=self.currentTimePos)

  def restoreKeepWidthAndRecaulate(self):
    if self.draggingTickIndex is not None:
      self.redrawTimer = threading.Timer(0.8, self.restoreKeepWidthAndRecaulate)
      self.redrawTimer.start()
      return

    self.keepWidth=False
    self.blockSpectrumUpdates=False
    self.recalculateEDLTimings()
    self.generateSpectrum()

  def recalculateEDLTimings(self,rid=None,pos=None,seekAfter=None):

    try:
      self.redrawTimer.cancel()
    except:
      pass

    if self.keepWidth:
      self.blockSpectrumUpdates=True
      self.redrawTimer = threading.Timer(0.8, self.restoreKeepWidthAndRecaulate)
      self.redrawTimer.start()

    if len(self.sequencedClips)==0:
      self.timeline_canvas.delete('ticks')
      self.timeline_canvas.delete('upperticks')
      self.player.stop()
      return

    edlstr = '# mpv EDL v0\n'
    endOffset=0
    startoffset=0
    audioFilename=self.dubFile.get()

    seekTarget=None
    seekOffset =  0
    try:
      seekOffset = float(self.seekOffsetVar.get())
    except:
      pass

    

    self.timeline_canvas.delete('ticks')
    self.timeline_canvas.delete('upperticks')

    self.ticktimestamps=[]
    self.tickXpos=[]
    self.ridListing=[]

    if audioFilename is not None and os.path.exists(audioFilename):
      endOffset    = float(self.dubOffsetVar.get())
      startoffset = float(self.dubOffsetVar.get())
      audioFilename = cleanFilenameForFfmpeg(audioFilename)
      audioFilename = audioFilename.replace('\\','/').replace(':','\\:').replace('\'','\\\\\'')
    else:
      audioFilename=None

    tickCounter=0
    for sv in self.sequencedClips:
      fn = sv.filename
      start = sv.s
      end = sv.e

      if rid is not None and rid==sv.rid:
        print(rid,sv.rid)
        if pos == 'e':
          seekTarget = tickCounter+(end-start)+seekOffset
        else:
          seekTarget = tickCounter+seekOffset

      if float(self.fadeVar.get()) < (end-start):
        start += (float(self.fadeVar.get())/2)
        end   -= (float(self.fadeVar.get())/2)
      tempTickCounter=tickCounter
      tickCounter += (end-start)
      self.ridListing.append( (tempTickCounter,tickCounter,sv.rid) )

      self.ticktimestamps.append(tickCounter)
      endOffset += end-start

      edlstr += '%{}%{},{},{}\n'.format(len(fn.encode('utf8')),fn,start,end-start)
    

    timelineWidth = self.timeline_canvas.winfo_width()

    startpc,endpc = 0,1

    if self.currentTotalDuration is not None:
      startpc = self.xCoordToSeconds(0)/self.currentTotalDuration
      endpc   = self.xCoordToSeconds(timelineWidth)/self.currentTotalDuration

    self.timeline_canvas.coords(self.canvasZoomBG,      0,0,  timelineWidth,20 )
    self.timeline_canvas.coords(self.canvasZoomBGRange, int(startpc*timelineWidth),0,(endpc*timelineWidth),20 )

    mid = (startpc+endpc)/2

    self.timeline_canvas.coords(self.canvasZoomRangeMid, int(mid*timelineWidth),0,int(mid*timelineWidth),20 )


    lastTick=0

    if not self.keepWidth:
      self.durationForScale=tickCounter

    idx=-1
    yo=20
    for idx,tick in enumerate(self.ticktimestamps[:-1]):

      tickrid = self.sequencedClips[idx].rid
      tickColour = self.colourMap.get(tickrid)
      if tickColour is None:
        tickColour = self.tickColours[0]
        self.colourMap[tickrid]=tickColour
        self.tickColours.append(self.tickColours.pop(0))

      utx = (tick/self.durationForScale)*timelineWidth
      self.timeline_canvas.create_line(utx,0,utx,20,fill='white',tags='upperticks')
      self.timeline_canvas.create_rectangle(utx-5, 0,
                                            utx+5, 4,
                                            fill='white',tags='upperticks')


      txl = self.secondsToXcoord(lastTick)
      tx  = self.secondsToXcoord(tick)

      self.tickXpos.append((tx,idx))

      self.timeline_canvas.create_rectangle(txl, yo+0,
                                            tx,  yo+5,
                                            fill=tickColour,tags='ticks')
      
      self.timeline_canvas.create_polygon(tx-6-5,    yo+9, 
                                          tx-6-5,    yo+9+10, 
                                          tx-4,      yo+9+5, 
                                          fill='grey',tags='ticks')
      
      self.timeline_canvas.create_polygon(tx+6+5,    yo+9, 
                                          tx+6+5,    yo+9+10, 
                                          tx+4,      yo+9+5, 
                                          fill='grey',tags='ticks')

      print(self.draggingTickIndex,idx)
      self.timeline_canvas.create_rectangle(tx-6-5-4, yo+20,
                                            tx+6+5+4, yo+20+15,
                                            outline='grey',tags='ticks')

      self.timeline_canvas.create_polygon(  tx,    yo+20+2, 
                                            tx-7,  yo+20+2+5, 
                                            tx,    yo+20+2+11,
                                            tx+7,  yo+20+2+5,

                                          fill='white',tags='ticks')

      self.timeline_canvas.create_line(tx, yo+0, 
                                       tx, yo+200,
                                       fill='white',tags='ticks')

      self.timeline_canvas.create_line(tx-6-5-4, yo+5, 
                                       tx-6-5-4, yo+20,
                                       fill='grey',tags='ticks')
      
      self.timeline_canvas.create_line(tx+6+5+4, yo+5, 
                                       tx+6+5+4, yo+20,
                                       fill='grey',tags='ticks')

      
      lastTick=tick

    tx = timelineWidth

    if endpc==1:
      self.timeline_canvas.create_rectangle(tx-6-5-4, yo+20,
                                            tx+6+5+4, yo+20+15,
                                            outline='grey',tags='ticks')

      self.timeline_canvas.create_polygon(  tx,    yo+20+2, 
                                            tx-7,  yo+20+2+5, 
                                            tx,    yo+20+2+11,
                                            tx+7,  yo+20+2+5,

                                          fill='white',tags='ticks')



    self.timeline_canvas.create_line(0,             yo+20, 
                                     timelineWidth, yo+20,
                                     fill='grey',tags='ticks')

    txl = self.secondsToXcoord(lastTick)

    tickrid = self.sequencedClips[idx+1].rid
    tickColour = self.colourMap.get(tickrid)
    if tickColour is None:
      tickColour = self.tickColours[0]
      self.colourMap[tickrid]=tickColour
      self.tickColours.append(self.tickColours.pop(0))

    self.timeline_canvas.create_rectangle(txl, yo+0,
                                          tx,  yo+5,
                                          fill=tickColour,tags='ticks')

    self.timeline_canvas.tag_lower('ticks', self.canvasSeekPointer)

    if seekAfter is not None:
      seekAfter = max(min(seekAfter,endOffset),0)
      self.player.start=str(seekAfter)

    if seekTarget is not None:
      seekTarget = max(min(seekTarget,endOffset),0)
      self.player.start=str(seekTarget) 

    self.player._python_streams = {}

    edlBytes = edlstr.encode('utf8')

    @self.player.python_stream('edlStream',len(edlBytes))
    def edlstream():
      yield edlBytes

    self.player.play('python://edlStream')

    del edlstream

    if audioFilename is not None:

      audioOverrideBias = float(self.mixVar.get())
      weightDub    = audioOverrideBias
      weightSource = 1-audioOverrideBias

      self.player.lavfi_complex="amovie=filename='{fn}',atrim=start={starts}:end={endts},asetpts=PTS-STARTPTS[ao]".format(fn=audioFilename,starts=startoffset,endts=endOffset,wd=weightDub,ws=weightSource)
    else:
      self.player.lavfi_complex=''


class CutSpecificationPlanner(tk.Toplevel):

  def __init__(self, master=None, controller=None, *args):
    tk.Toplevel.__init__(self, master)
    
    self.title('Audio Sync Specification Planner')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,400)


    self.loadbutton = ttk.Button(self,text='Load Audio',command=self.selectFile)
    self.loadbutton.grid(row=0,column=0,sticky='nesw',padx=0,pady=0,columnspan=9)


    self.playerFrame = ttk.Frame(self,style='PlayerFrame.TFrame',height='200', width='200')
    self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0,columnspan=9)

    self.timeline_canvas = tk.Canvas(self,width=200, height=130, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=2,column=0,columnspan=9,sticky="nesw")
    
    self.timeline_canvas.bind("<Button-1>", self.timelineMousePress)


    self.canvasSeekPointer = self.timeline_canvas.create_line(0, 0, 0, self.timeline_canvas.winfo_height(),fill="white")

    self.playerwid = self.playerFrame.winfo_id()

    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=1)
    self.rowconfigure(2, weight=0)

    self.columnconfigure(0, weight=1)

    self.currentTimePos=None
    self.currentTotalDuration=None

    self.player = mpv.MPV(loop='inf',
                          mute=False,
                          volume=50,
                          autofit_larger='1280', wid=str(self.playerwid))

    self.player.lavfi_complex="[aid1]asplit[as1][as2],[as1]showcqt=s=640x518[vo],[as2]anull[ao]"

    self.attributes('-topmost', True)
    self.update()

    self.player.observe_property('time-pos', self.handleMpvTimePosChange)
    self.player.observe_property('duration', self.handleMpvDurationChange)



    def quitFunc(key_state, key_name, key_char):
    
      try:
        self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('duration', self.handleMpvDurationChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('af-metadata', self.handleMpvafMetdata)
      except Exception as e:
        print(e)

      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()
      self.attributes('-topmost', False)
      self.update()




  def timelineMousePress(self,e):  
    self.player.command('seek',str((e.x/self.timeline_canvas.winfo_width())*100),'absolute-percent','exact')


  def handleMpvafMetdata(self,name,value):
    print(name,value)

  def handleMpvTimePosChange(self,name,value):
    
    timelineWidth = self.timeline_canvas.winfo_width()
    timelineHeight = self.timeline_canvas.winfo_height()

    if value is not None:
      self.currentTimePos = value
      if self.currentTotalDuration is not None:
        currentPlaybackX = int((self.currentTimePos/self.currentTotalDuration)*timelineWidth)
        self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,0,currentPlaybackX,timelineHeight )

  def handleMpvDurationChange(self,name,value):
    if value is not None:
      self.currentTotalDuration=value

  def selectFile(self):
    self.file = askopenfilename(multiple=False,filetypes=[('All files','*.*',)])
    if os.path.isfile(self.file):
      self.player.play(self.file)

class Tooltip:

  def __init__(self, widget,
               *,
               bg='#a7d9ea',
               fg='#282828',
               pad=(5, 3, 5, 3),
               text='widget info',
               waittime=400,
               wraplength=450):

    self.waittime = waittime  # in miliseconds, originally 500
    self.wraplength = wraplength  # in pixels, originally 180
    self.widget = widget
    self.text = text
    self.widget.bind("<Enter>", self.onEnter)
    self.widget.bind("<Leave>", self.onLeave)
    self.widget.bind("<ButtonPress>", self.onLeave)
    self.bg = bg
    self.fg=fg
    self.pad = pad
    self.id = None
    self.tw = None

  def onEnter(self, event=None):
    self.schedule()

  def onLeave(self, event=None):
    self.unschedule()
    self.hide()

  def schedule(self):
    self.unschedule()
    self.id = self.widget.after(self.waittime, self.show)

  def unschedule(self):
    id_ = self.id
    self.id = None
    if id_:
      self.widget.after_cancel(id_)

  def show(self):
    def tip_pos_calculator(widget, label,
                           *,
                           tip_delta=(10, 5), pad=(5, 3, 5, 3)):

        w = widget

        s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

        width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                         pad[1] + label.winfo_reqheight() + pad[3])

        mouse_x, mouse_y = w.winfo_pointerxy()

        x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
        x2, y2 = x1 + width, y1 + height

        x_delta = x2 - s_width
        if x_delta < 0:
          x_delta = 0
        y_delta = y2 - s_height
        if y_delta < 0:
          y_delta = 0

        offscreen = (x_delta, y_delta) != (0, 0)

        if offscreen:
          if x_delta:
            x1 = mouse_x - tip_delta[0] - width
          if y_delta:
            y1 = mouse_y - tip_delta[1] - height

        offscreen_again = y1 < 0  # out on the top

        if offscreen_again:
          y1 = 0

        return x1, y1

    bg = self.bg
    pad = self.pad
    widget = self.widget

    # creates a toplevel window
    self.tw = tk.Toplevel(widget)

    # Leaves only the label and removes the app window
    self.tw.wm_overrideredirect(True)

    win = tk.Frame(self.tw,
                   background=bg,
                   borderwidth=0)
    label = tk.Label(win,
                      text=self.text,
                      justify=tk.LEFT,
                      background=bg,
                      relief=tk.SOLID,
                      borderwidth=0,
                      wraplength=self.wraplength)

    label.grid(padx=(pad[0], pad[2]),
               pady=(pad[1], pad[3]),
               sticky=tk.NSEW)
    win.grid()

    x, y = tip_pos_calculator(widget, label)

    self.tw.wm_geometry("+%d+%d" % (x, y))

  def hide(self):
    tw = self.tw
    if tw:
      tw.destroy()
    self.tw = None

class V360HeadTrackingModal(tk.Toplevel):
  def __init__(self, master=None, controller=None, filterReference=None, *args):
    tk.Toplevel.__init__(self, master)
    self.title('Record VR head motions')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,600)    

    self.labelInstructions = ttk.Label(self)
    self.labelInstructions.config(text='Click in video to capture mouse, press Space to start recording motions.',anchor="center")
    self.labelInstructions.grid(row=0,column=0,sticky='new',padx=0,pady=0)

    self.playerFrame = ttk.Frame(self,style='PlayerFrame.TFrame',height='200', width='200')
    self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0)

    self.applyButton = ttk.Button(self, text='Apply')
    self.applyButton.grid(row=2,column=0,sticky='nesw',padx=5,pady=5)

    self.columnconfigure(0, weight=1)
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=1)
    self.rowconfigure(2, weight=0)

    self.playerwid = self.playerFrame.winfo_id()


class VoiceActivityDetectorModal(tk.Toplevel):


  def __init__(self, master=None,controller=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Detect voice activity')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,40)
    self.controller=controller
    self.columnconfigure(0, weight=0)
    self.columnconfigure(1, weight=1)

    self.labelSampleLength = ttk.Label(self)
    self.labelSampleLength.config(text='Sample length (ms) [10,20,30]')
    self.labelSampleLength.grid(row=0,column=0,sticky='new',padx=5,pady=5)
    self.varSampleLength   = tk.StringVar(self,'20')
    self.entrySampleLength = ttk.Entry(self,textvariable=self.varSampleLength)
    self.entrySampleLength.grid(row=0,column=1,sticky='new',padx=5,pady=5)


    self.labelAggresiveness = ttk.Label(self)
    self.labelAggresiveness.config(text='Recognition Aggressiveness [0.0-3.0]')
    self.labelAggresiveness.grid(row=2,column=0,sticky='new',padx=5,pady=5)

    self.varAggresiveness   = tk.StringVar(self,'3')
    self.entryAggresiveness  = ttk.Entry(self,textvariable=self.varAggresiveness)
    self.entryAggresiveness.grid(row=2,column=1,sticky='new',padx=5,pady=5)


    self.labelWindowLength = ttk.Label(self)
    self.labelWindowLength.config(text='Rolling confidence window length')
    self.labelWindowLength.grid(row=3,column=0,sticky='new',padx=5,pady=5)

    self.varWindowLength   = tk.StringVar(self,'1.5')
    self.entryWindowLength  = ttk.Entry(self,textvariable=self.varWindowLength)
    self.entryWindowLength.grid(row=3,column=1,sticky='new',padx=5,pady=5)


    self.labelMinimimDuration = ttk.Label(self)
    self.labelMinimimDuration.config(text='Minumum speech duration')
    self.labelMinimimDuration.grid(row=4,column=0,sticky='new',padx=5,pady=5)

    self.varMinimimDuration   = tk.StringVar(self,'2.0')
    self.entryMinimimDuration  = ttk.Entry(self,textvariable=self.varMinimimDuration)
    self.entryMinimimDuration.grid(row=4,column=1,sticky='new',padx=5,pady=5)


    self.labelBridgeDistance = ttk.Label(self)
    self.labelBridgeDistance.config(text='Bridge gaps of at most (s)')
    self.labelBridgeDistance.grid(row=5,column=0,sticky='new',padx=5,pady=5)

    self.varBridgeDistance  = tk.StringVar(self,'2.0')
    self.entryBridgeDistance = ttk.Entry(self,textvariable=self.varBridgeDistance)
    self.entryBridgeDistance.grid(row=5,column=1,sticky='new',padx=5,pady=5)


    self.labelCondidenceStart = ttk.Label(self)
    self.labelCondidenceStart.config(text='Confidence to trigger start speech')
    self.labelCondidenceStart.grid(row=6,column=0,sticky='new',padx=5,pady=5)

    self.varCondidenceStart    = tk.StringVar(self,'98.0')
    self.entryCondidenceStart   = ttk.Entry(self,textvariable=self.varCondidenceStart )
    self.entryCondidenceStart .grid(row=6,column=1,sticky='new',padx=5,pady=5)


    self.labelCondidenceEnd = ttk.Label(self)
    self.labelCondidenceEnd.config(text='Confidence to trigger end speech')
    self.labelCondidenceEnd.grid(row=7,column=0,sticky='new',padx=5,pady=5)

    self.varCondidenceEnd    = tk.StringVar(self,'80.0')
    self.entryCondidenceEnd   = ttk.Entry(self,textvariable=self.varCondidenceEnd )
    self.entryCondidenceEnd .grid(row=7,column=1,sticky='new',padx=5,pady=5)

    self.labelMinZcr= ttk.Label(self)
    self.labelMinZcr.config(text='Minimum zero crossing rate (-1 to skip)')
    self.labelMinZcr.grid(row=8,column=0,sticky='new',padx=5,pady=5)

    self.varMinZcr    = tk.StringVar(self,'-1')
    self.entryMinZcr   = ttk.Entry(self,textvariable=self.varMinZcr )
    self.entryMinZcr .grid(row=8,column=1,sticky='new',padx=5,pady=5)

    self.labelMaxZcr= ttk.Label(self)
    self.labelMaxZcr.config(text='Maximum zero crossing rate (-1 to skip)')
    self.labelMaxZcr.grid(row=9,column=0,sticky='new',padx=5,pady=5)

    self.varMaxZcr    = tk.StringVar(self,'-1')
    self.entryMaxZcr   = ttk.Entry(self,textvariable=self.varMaxZcr )
    self.entryMaxZcr .grid(row=9,column=1,sticky='new',padx=5,pady=5)

    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Scan and Add SubClips',command=self.addSublcips)
    self.downloadCmd.grid(row=10,column=0,columnspan=2,sticky='nesw')

    self.resizable(False, False) 

  def addSublcips(self):
    sampleLength    = float(self.varSampleLength.get())
   
    aggresiveness   = float(self.varAggresiveness.get())
    windowLength    = float(self.varWindowLength.get())
    minimimDuration = float(self.varMinimimDuration.get())
    bridgeDistance  = float(self.varBridgeDistance.get())
    condidenceStart = float(self.varCondidenceStart.get())
    condidenceEnd   = float(self.varCondidenceEnd.get())
    minZcr          = float(self.varMinZcr.get())
    maxZcr          = float(self.varMaxZcr.get())

    self.controller.runVoiceActivityDetection(sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,minZcr,maxZcr)
    self.destroy()

class TimestampModal(tk.Toplevel):
  
  def __init__(self, master=None,controller=None,initialValue='',videoDuration=0, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Cut the video at these timestamps')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,40)
    self.controller=controller
    self.videoDuration=videoDuration


    self.columnconfigure(0, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=2)


    self.labelInstruction = ttk.Label(self)
    self.labelInstruction.config(text='Add timestamp in "HH:MM:SS.ss - HH:MM:SS.ss" format')
    self.labelInstruction.grid(row=0,column=0,sticky='new',padx=5,pady=5)

    self.varTimestamps   = tk.StringVar(self,initialValue)
    self.entryTimestamps = ttk.Entry(self,textvariable=self.varTimestamps)
    self.entryTimestamps.grid(row=1,column=0,sticky='new',padx=5,pady=5)
    self.varTimestamps.trace('w',self.valueUpdated)

    self.varnegativeTS = tk.IntVar(0)
    self.checknegativeTS =  ttk.Checkbutton(self,text='Interpret as negative timestamps from end of clip.',var=self.varnegativeTS)
    self.checknegativeTS.grid(row=2,column=0,sticky='new',padx=5,pady=5)
    self.varnegativeTS.trace('w',self.valueUpdated)

    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Add SubClip',command=self.addSublcip,state='disabled')
    self.downloadCmd.grid(row=3,column=0,sticky='nesw')
    self.rowconfigure(5, weight=1)

    self.resizable(False, False) 

    self.entryTimestamps.focus()
    self.entryTimestamps.select_range(0, 'end')
    self.entryTimestamps.icursor('end')

    self.start = None
    self.end   = None

    self.valueUpdated()

  def valueUpdated(self,*args):
    self.start = None
    self.end   = None
    isIsNegative = bool(self.varnegativeTS.get())
    self.downloadCmd.config(state='disabled')
    rawRange = self.varTimestamps.get()

    multipliers = [1,60,60*60,60*60*60]

    startTS=0
    endTS=0

    if rawRange is not None:
      startText = ""
      endText   = ""

      isStart = True
      for char in rawRange.strip():
        if char in '1234567890.:':
          if isStart:
            startText += char
          else:
            endText += char
        else:
          isStart=False

      if len(startText)>0 and len(endText)>0:
        for mult,val in zip(multipliers,startText.split(':')[::-1]):
          startTS += mult*float(val)
        for mult,val in zip(multipliers,endText.split(':')[::-1]):
          endTS += mult*float(val)


    if (startTS != 0 or endTS != 0) and endTS != startTS:
      self.start = startTS
      self.end   = endTS     
      if isIsNegative:
        self.start = self.videoDuration-startTS
        self.end   = self.videoDuration-endTS
      self.start,self.end = sorted([self.start,self.end])
      self.downloadCmd.config(state='normal',text='Add SubClip from {}s to {}s ({}s)'.format(self.start,self.end,self.end-self.start))
    else:
      self.downloadCmd.config(state='disabled',text='Add SubClip')

  def addSublcip(self):
    if self.start != None and self.end != None:
      self.controller.addNewSubclip(max(self.start,0), min(self.end,self.videoDuration))


youtubeDLModalState = {
  'varPlayListLimit':'',
  'varUsername':'',
  'varPassword':'',
  'useCookies':0,
  'varBrowserCookies':''

}

class YoutubeDLModal(tk.Toplevel):
  
  def __init__(self, master=None,controller=None,initialUrl='', *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Download a video with youtube-dlp')
    self.style = ttk.Style()
    self.style.theme_use('clam')

    self.minsize(600,140)
    self.controller=controller

    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)

    self.labelUrl = ttk.Label(self)
    self.labelUrl.config(text='Url')
    self.labelUrl.grid(row=0,column=0,sticky='new',padx=5,pady=5)
    self.varUrl   = tk.StringVar(self,initialUrl)
    self.entryUrl = ttk.Entry(self,textvariable=self.varUrl)
    self.entryUrl.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.labelPlaylistLimit = ttk.Label(self)
    self.labelPlaylistLimit.config(text='Max download count')
    self.labelPlaylistLimit.grid(row=1,column=0,sticky='new',padx=5,pady=5)
    self.varPlayListLimit   = tk.StringVar(self,'')
    self.entryPlayListLimit = ttk.Entry(self,textvariable=self.varPlayListLimit)
    self.entryPlayListLimit.grid(row=1,column=1,sticky='new',padx=5,pady=5)

    self.labelUsername = ttk.Label(self)
    self.labelUsername.config(text='Username')
    self.labelUsername.grid(row=2,column=0,sticky='new',padx=5,pady=5)
    self.varUsername   = tk.StringVar(self,'')
    self.entryUsername = ttk.Entry(self,textvariable=self.varUsername)
    self.entryUsername.grid(row=2,column=1,sticky='new',padx=5,pady=5)

    self.labelPassword = ttk.Label(self)
    self.labelPassword.config(text='Password')
    self.labelPassword.grid(row=3,column=0,sticky='new',padx=5,pady=5)
    self.varPassword   = tk.StringVar(self,'')
    self.entryPassword = ttk.Entry(self,textvariable=self.varPassword)
    self.entryPassword.grid(row=3,column=1,sticky='new',padx=5,pady=5)

    self.labelCookies = ttk.Label(self)
    self.labelCookies.config(text='Use cookies.txt')
    self.labelCookies.grid(row=4,column=0,sticky='new',padx=5,pady=5)
    
    self.useCookies = tk.IntVar(self,0)
    self.entryCookies =  ttk.Checkbutton(self,text='Send credentials from cookies.txt',var=self.useCookies)
    if not os.path.exists('cookies.txt'):
      self.entryCookies['state']='disabled'
      self.entryCookies['text']='cookies.txt not found.'

    self.entryCookies.grid(row=4,column=1,sticky='new',padx=5,pady=5)

    self.labelBrowserCookies = ttk.Label(self)
    self.labelBrowserCookies.config(text='Get Cookies from Browser')
    self.labelBrowserCookies.grid(row=5,column=0,sticky='new',padx=5,pady=5)
    self.varBrowserCookies   = tk.StringVar(self,'')
    self.entryBrowserCookies =  ttk.Combobox(self,textvariable=self.varBrowserCookies)
    self.entryBrowserCookies.config(values=['brave', 'chrome', 'chromium', 'edge', 'firefox', 'opera', 'safari', 'vivaldi'])
    self.entryBrowserCookies.grid(row=5,column=1,sticky='new',padx=5,pady=5)


    self.labelQualitySort = ttk.Label(self)
    self.labelQualitySort.config(text='Video quality selection rule')
    self.labelQualitySort.grid(row=6,column=0,sticky='new',padx=5,pady=5)
    self.varQualitySort   = tk.StringVar(self,'default')
    self.entryQualitySort =  ttk.Combobox(self,textvariable=self.varQualitySort)
    self.entryQualitySort.config(values=['default', 'bestvideo+bestaudio/best', 'bestvideo*+bestaudio/best', 'best'])
    self.entryQualitySort.grid(row=6,column=1,sticky='new',padx=5,pady=5)


    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Download',command=self.download)
    self.downloadCmd.grid(row=7,column=0,columnspan=2,sticky='nesw')
    self.rowconfigure(5, weight=1)

    self.entryUrl.focus()
    self.entryUrl.select_range(0, 'end')
    self.entryUrl.icursor('end')

    self.resizable(False, False) 

  def download(self):
    url=self.varUrl.get()
    fileLimit=0
    username=self.varUsername.get()
    password=self.varPassword.get()
    useCookies = bool(self.useCookies.get())
    browserCookies=self.varBrowserCookies.get()
    qualitySort=self.varQualitySort.get()

    try:
      fileLimit = int(float(self.varPlayListLimit.get()))
    except Exception as e:
      print(e)
    self.controller.loadVideoYTdlCallback(url,fileLimit,username,password,useCookies,browserCookies,qualitySort)
    self.destroy()



class PerfectLoopScanModal(tk.Toplevel):
  
  def __init__(self, master=None,useRange=False,controller=None,starttime=0,endtime=0, *args):

    tk.Toplevel.__init__(self, master)

    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.style.configure ("warning.TLabel", font = ('Sans','10','bold'),textcolor='red')

    self.grab_set()
    self.title('Scan for perfect loops')


    self.controller=controller

    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=0)
    self.rowconfigure(5, weight=0)
    self.rowconfigure(6, weight=0)
    self.rowconfigure(7, weight=0)
    
    self.useRange = useRange

    initThreshold    = 10
    initMidThreshold = 18
    initMinLength    = 1.5
    initMaxLength    = 4.0
    initTimeSkip     = 1.0

    r=0

    self.labelWarning = ttk.Label(self)
    self.labelWarning.config(text='Experimental - can take a very long time and still return no loops.',style='warning.TLabel')
    self.labelWarning.grid(row=r,column=0,sticky='new',padx=5,pady=5,columnspan=2)


    r+=1

    if self.useRange:

      self.labelStartTime = ttk.Label(self)
      self.labelStartTime.config(text='Scan start timestamp')
      self.labelStartTime.grid(row=r,column=0,sticky='new',padx=5,pady=5)

      self.varStartTime   = tk.StringVar(self,starttime)
      self.entryStartTime = ttk.Entry(self,textvariable=self.varStartTime)
      self.entryStartTime.grid(row=r,column=1,sticky='new',padx=5,pady=5)

      r+=1

      self.labelEndTime = ttk.Label(self)
      self.labelEndTime.config(text='Scan end timestamp')
      self.labelEndTime.grid(row=r,column=0,sticky='new',padx=5,pady=5)

      self.varEndTime   = tk.StringVar(self,endtime)
      self.entryEndTime = ttk.Entry(self,textvariable=self.varEndTime)
      self.entryEndTime.grid(row=r,column=1,sticky='new',padx=5,pady=5)

      r += 1


    self.labelThreshold = ttk.Label(self)
    self.labelThreshold.config(text='Max loop difference threshold')
    self.labelThreshold.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varThreshold   = tk.StringVar(self,initThreshold)
    self.entryThreshold = ttk.Entry(self,textvariable=self.varThreshold)
    self.entryThreshold.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelMidThreshold = ttk.Label(self)
    self.labelMidThreshold.config(text='Min inbetween threshold')
    self.labelMidThreshold.grid(row=r,column=0,sticky='new',padx=5,pady=5)


    self.varMidThreshold   = tk.StringVar(self,initMidThreshold)
    self.entryMidThreshold = ttk.Entry(self,textvariable=self.varMidThreshold)
    self.entryMidThreshold.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelIfdMode = ttk.Label(self)
    self.labelIfdMode.config(text='IFD offset mode')
    self.labelIfdMode.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varIfdMode   = tk.IntVar(self,1)
    self.entryIfdMode = ttk.Checkbutton(self,text='Treat thresholds as offset from mean inter-frame-distance',var=self.varIfdMode)
    self.entryIfdMode.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelMinLength = ttk.Label(self)
    self.labelMinLength.config(text='Min loop length')
    self.labelMinLength.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varMinLength   = tk.StringVar(self,initMinLength)
    self.entryMinLength = ttk.Entry(self,textvariable=self.varMinLength)
    self.entryMinLength.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelMaxLength = ttk.Label(self)
    self.labelMaxLength.config(text='Max loop length')
    self.labelMaxLength.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varMaxLength   = tk.StringVar(self,initMaxLength)
    self.entryMaxLength = ttk.Entry(self,textvariable=self.varMaxLength)
    self.entryMaxLength.grid(row=r,column=1,sticky='new',padx=5,pady=5)


    r += 1

    self.labelTimeSkip = ttk.Label(self)
    self.labelTimeSkip.config(text='Time to skip between loops')
    self.labelTimeSkip.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varTimeSkip   = tk.StringVar(self,initTimeSkip)
    self.entryTimeSkip = ttk.Entry(self,textvariable=self.varTimeSkip)
    self.entryTimeSkip.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelfilterMode = ttk.Label(self)
    self.labelfilterMode.config(text='Final match selection mode')
    self.labelfilterMode.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varfilterMode   = tk.StringVar(self,'bestFirst')
    self.entryfilterMode = ttk.Combobox(self)
    self.entryfilterMode.config(textvariable=self.varfilterMode)
    self.entryfilterMode.config(values=['bestFirst','earliestFirst'])
    self.entryfilterMode.grid(row=r,column=1,sticky='new',padx=5,pady=5)


    r += 1

    self.scanCmd = ttk.Button(self)
    self.scanCmd.config(text='Scan for loops',command=self.scanForLoops)
    self.scanCmd.grid(row=r,column=0,columnspan=2,sticky='nesw')
    self.rowconfigure(r, weight=1)

    self.resizable(False, False) 

  def scanForLoops(self):
    threshold = float(self.varThreshold.get())
  
    midThreshold = float(self.varMidThreshold.get())
    minLength = float(self.varMinLength.get())
    maxLength = float(self.varMaxLength.get())
    timeSkip  = float(self.varTimeSkip.get())
    ifdmode   = bool(self.varIfdMode.get())
    selectionMode = self.varfilterMode.get()

    

    useRange=self.useRange
    if self.useRange:
      rangeStart=float(self.varStartTime.get())
      rangeEnd=float(self.varEndTime.get())
    else:
      rangeStart=None
      rangeEnd=None

    self.controller.submitFullLoopSearch(midThreshold=midThreshold,
                                         minLength=minLength,
                                         maxLength=maxLength,
                                         timeSkip=timeSkip,
                                         threshold=threshold,
                                         addCuts=True,
                                         useRange=useRange,
                                         rangeStart=rangeStart,
                                         ifdmode=ifdmode,
                                         rangeEnd=rangeEnd,
                                         selectionMode=selectionMode)
    self.destroy()


class SubtitleExtractionModal(tk.Toplevel):

  def __init__(self, master=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Extract Subtitles')
    self.minsize(600,150)
    


    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=1)
    self.rowconfigure(5, weight=0)
    

    self.labelFilename = ttk.Label(self)
    self.file=''
    self.labelFilename.config(text='Source file')
    self.labelFilename.grid(row=0,column=0,sticky='new',padx=5,pady=5)

    self.varFilename   = tk.StringVar()
    self.varFilename.set('None')
    self.entryFilename = ttk.Button(self)
    self.entryFilename.config(text='File: {}'.format(self.varFilename.get()[-20:]),command=self.selectFile)
    self.entryFilename.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.labelStream = ttk.Label(self)
    self.labelStream.config(text='Stream Index')
    self.labelStream.grid(row=1,column=0,sticky='new',padx=5,pady=5)

    self.varStream   = tk.StringVar()
    self.varStream.trace('w',self.streamChanged)
    self.entryStream = ttk.Combobox(self)
    self.entryStream.config(textvariable=self.varStream,state='disabled')
    self.entryStream.config(values=[])
    self.entryStream.grid(row=1,column=1,sticky='new',padx=5,pady=5)

    self.labelOutputName = ttk.Label(self)
    self.labelOutputName.config(text='Output Name:')
    self.labelOutputName.grid(row=2,column=0,sticky='new',padx=5,pady=5)

    self.labelOutputFileName = ttk.Label(self)
    self.labelOutputFileName.config(text='None')
    self.labelOutputFileName.grid(row=2,column=1,sticky='new',padx=5,pady=5)

    self.labelProgress = ttk.Label(self)
    self.labelProgress.config(text='Idle')
    self.labelProgress.grid(row=3,column=0,columnspan=2,sticky='new',padx=5,pady=5)


    self.extractCmd = ttk.Button(self)
    self.extractCmd.config(text='Extract',command=self.extract,state='disabled')
    self.extractCmd.grid(row=4,column=0,columnspan=2,sticky='nesw')


    self.statusProgress = ttk.Progressbar(self)
    self.statusProgress['value'] = 0
    self.statusProgress.grid(row=5,column=0,columnspan=2,sticky='nesw')
    self.statusProgress.config(style="Green.Horizontal.TProgressbar")


    self.resizable(False, False) 

    self.outputFilename=''
    self.streamInd=0
    self.subtitleThread=None
    self.close=False

    self.protocol("WM_DELETE_WINDOW", self.closeThreads)


  def selectFile(self):
    self.file = askopenfilename(multiple=False,filetypes=[('All files','*.*',)])
    subn=0
    self.statusProgress['value']=0
    if os.path.isfile(self.file):
      outs,errs = sp.Popen(['ffmpeg','-i',cleanFilenameForFfmpeg(self.file)],stderr=sp.PIPE).communicate()
      print(outs,errs)
      self.subs=[]
      for line in errs.split(b'\n'):
        if b'Stream #' in line and b'Subtitle' in line:
          self.subs.append( str(subn) +' - ' + line.strip().decode('utf8',errors='ignore'))
          subn+=1

      self.entryStream.config(values=self.subs)
      if len(self.subs)>0:
        self.varStream.set(self.subs[0])
        self.entryStream.config(state='normal')
        self.entryFilename.config(text='File: {}'.format(self.file[-100:]))
      else:
        self.varStream.set('')
        self.entryStream.config(state='disabled')
        self.entryFilename.config(text='File: None')
    else:
        self.varStream.set('')
        self.entryStream.config(state='disabled')      
        self.entryFilename.config(text='File: None')

  def streamChanged(self,*args):
    self.outputFilename=''
    self.statusProgress['value']=0
    if os.path.isfile(self.file) and self.varStream.get().split('-')[0].strip().isdigit():
      self.extractCmd.config(state='normal')
      filename = os.path.split(self.file)[-1]
      filename = os.path.splitext(filename)[0]
      streamName = self.varStream.get().split(':')
      self.streamInd = int(streamName[0].split(' ')[0])
      self.outputFilename = ''.join([x for x in filename+'.subs.'+str(self.streamInd)+'.'+streamName[1]+'.srt' if x in string.ascii_letters+string.digits+'. '])
      self.labelOutputFileName.config(text=self.outputFilename)
    else:
      self.extractCmd.config(state='disabled')
      if len(self.subs)==0:
        self.labelOutputFileName.config(text='No subtitle track found')
      else:
        self.labelOutputFileName.config(text='None')

  def watchsubtitleProgress(self):
    l=b''
    expectedLength=None
    self.statusProgress['value']=0
    while 1:
      c = self.proc.stderr.read(1)
      if self.close:
        break
      if len(c)==0:
        break
      if c in b'\n\r':
        print(l)
        if b'Duration: ' in l and expectedLength is None:
          expectedLength=l.split(b'Duration: ')[1].split(b',')[0]
          expectedLength = datetime.strptime(expectedLength.decode('utf8'),'%H:%M:%S.%f')
          expectedLength = expectedLength.microsecond/1000000 + expectedLength.second + expectedLength.minute*60 + expectedLength.hour*3600
        elif b'time=' in l and expectedLength is not None:
          currentReadPos=l.split(b'time=')[1].split(b' ')[0]
          currentReadPos = datetime.strptime(currentReadPos.decode('utf8'),'%H:%M:%S.%f')
          currentReadPos = currentReadPos.microsecond/1000000 + currentReadPos.second + currentReadPos.minute*60 + currentReadPos.hour*3600
          if not self.close:
            self.statusProgress['value']=(currentReadPos/expectedLength)*100
        self.labelProgress.config(text=l)
        l=b''
      else:
        l+=c
    if not self.close:
      self.statusProgress['value']=100
      self.entryStream.config(state='normal')     
      self.entryFilename.config(state='normal')
      self.extractCmd.config(state='normal')

  def closeThreads(self):
    self.close=True
    substhread = self.subtitleThread
    self.subtitleThread=None
    self.destroy()

  def extract(self):
    self.proc = sp.Popen(['ffmpeg','-y','-i', self.file, '-map', '0:s:{}'.format(self.streamInd), '-vsync', '0', '-an', '-vn' , '-f', 'srt' , self.outputFilename],stderr=sp.PIPE)
    self.subtitleThread = threading.Thread(target=self.watchsubtitleProgress)
    self.subtitleThread.daemon = True
    
    self.entryStream.config(state='disabled')     
    self.entryFilename.config(state='disabled')
    self.extractCmd.config(state='disabled')

    self.subtitleThread.start()


class OptionsDialog(tk.Toplevel):
  def __init__(self, master=None, optionsDict={}, changedProperties={}, changeCallback=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Options')
    self.minsize(600,140)
    self.optionsDict=optionsDict
    self.changedProperties=changedProperties
    self.changeCallback=changeCallback
    self.entryMap={}
    self.varMap={}
    self.validatorMap={}
    
    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)

    i=0

    columnHeight=25
    maxcol=1

    for i,(k,v) in enumerate(optionsDict.items()):
      print(i,k,v)
      labelValue = ttk.Label(self)
      labelValue.config(text=k)

      column = i//columnHeight
      column = column*2
      maxcol= max(maxcol,maxcol+1)
      row = i%columnHeight

      labelValue.grid(row=row,column=column,sticky='new',padx=5,pady=1)

      if type(v) == bool:

        valueVar   = tk.BooleanVar(self)
        self.varMap[k]=valueVar

        entryValue = ttk.Checkbutton(self,text="", variable=self.varMap[k])

        #okayCommand = self.register(lambda val,t=type(v):self.validateType(t,val))  
        #self.validatorMap[k]=okayCommand
        #entryValue.config(validate='key',validatecommand=(okayCommand ,'%P'))

        valueVar.set(v)

      else:
        valueVar   = tk.StringVar(self)
        self.varMap[k]=valueVar
        entryValue = ttk.Entry(self,textvariable=self.varMap[k])
      
        okayCommand = self.register(lambda val,t=type(v):self.validateType(t,val))  
        self.validatorMap[k]=okayCommand
        entryValue.config(validate='key',validatecommand=(okayCommand ,'%P'))

        valueVar.set(str(v))

      entryValue.grid(row=row,column=column+1,sticky='new',padx=5,pady=0)
      self.entryMap[k]=entryValue
      valueVar.set(str(v))
      valueVar.trace('w',lambda *args,k=k:self.valueChanged(k))

    self.saveChanges = ttk.Button(self,text='Save Changes',command=self.saveChanges)
    self.rowconfigure(i+1, weight=1)
    self.saveChanges.grid(row=i+1,column=0,columnspan=maxcol+2,sticky='nesw')


    self.resizable(False, False) 

  def validateType(self,fieldtype,nextVal):
    if nextVal=='':
      return 1
    try:
      fieldtype(nextVal)
      return 1
    except:
      return 0

  def saveChanges(self):
    print(self.changeCallback,self.changedProperties)
    if self.changeCallback is not None:
      print(self.changedProperties)
      self.changeCallback(self.changedProperties)
    self.destroy()

  def valueChanged(self,valueKey):
    originalValue = self.optionsDict[valueKey]
    try:
      if type(originalValue) == int:
        self.changedProperties[valueKey] = int(self.varMap.get(valueKey).get())
      elif type(originalValue) == float:
        self.changedProperties[valueKey] = float(self.varMap.get(valueKey).get())
      elif type(originalValue) == bool:
        self.changedProperties[valueKey] = bool(self.varMap.get(valueKey).get())
      else:
        self.changedProperties[valueKey] = self.varMap.get(valueKey).get()
    except Exception as e:
      try:
        del self.changedProperties[valueKey]
      except Exception as e:
        print(e)
    print(valueKey)

if __name__ == "__main__":
  app = CutSpecificationPlanner()
  app.mainloop()
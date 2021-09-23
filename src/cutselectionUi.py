
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilenames,askopenfilename
from tkinter import messagebox
from tkinter import simpledialog
from pygubu.widgets.scrolledframe import ScrolledFrame
import os
import threading
import signal
from math import floor
import logging
import time
import subprocess as sp

from .timeLineSelectionFrameUI import TimeLineSelectionFrameUI

def format_timedelta(value, time_format="{days} days, {hours2}:{minutes2}:{seconds2}"):

    if hasattr(value, 'seconds'):
        seconds = value.seconds + value.days * 24 * 3600
    else:
        seconds = value

    seconds_total = seconds

    minutes = int(floor(seconds / 60))
    minutes_total = minutes
    seconds -= minutes * 60

    seconds = int(seconds)

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

class VideoFilePreview(ttk.Frame):
    def __init__(self, master, parent, filename, *args, **kwargs):
        ttk.Frame.__init__(self, master)

        self.filename = filename
        self.basename = os.path.basename(filename)[:30]
        self.parent = parent
        self.cutsSelected = 0

        self.frameVideoFileWidget = self

        self.labelVideoFileTitle = ttk.Label(self.frameVideoFileWidget)
        self.labelVideoFileTitle.config(text=self.basename)
        self.labelVideoFileTitle.pack(anchor="n", side="top")

        self.labelVideoPreviewLabel = ttk.Label(self.frameVideoFileWidget)
        self.labelVideoPreviewLabel.config(text="No Preview Loaded")

        self.previewData = "P5\n200 117\n255\n" + ("0" * 200 * 117)
        self.labelVideoPreviewImage = tk.PhotoImage(data=self.previewData)
        try:
          self.labelVideoPreviewImage = tk.PhotoImage(file=".\\resources\\loadingPreview.png")
        except Exception as e:
          print(e)
        self.previewRequested = False

        self.labelVideoPreviewLabel.configure(image=self.labelVideoPreviewImage)

        self.labelVideoPreviewLabel.pack(side="top", expand="false", fill="y")

        self.labelVideoFilecountCutsSelected = ttk.Label(self.frameVideoFileWidget)
        self.labelVideoFilecountCutsSelected.config(
            text="{} Cuts selected".format(self.cutsSelected)
        )
        #self.labelVideoFilecountCutsSelected.pack(side="top")
        self.frameVideoFileButtonsFrame = ttk.Frame(self.frameVideoFileWidget)

        self.buttonVideoFileRemove = ttk.Button(self.frameVideoFileButtonsFrame)
        self.buttonVideoFileRemove.config(text="Remove")
        self.buttonVideoFileRemove.config(command=self.remove)
        self.buttonVideoFileRemove.config(style="small.TButton")
        self.buttonVideoFileRemove.pack(expand="true", fill="x", side="left")

        self.buttonVideoFilePlay = ttk.Button(self.frameVideoFileButtonsFrame)
        self.buttonVideoFilePlay.config(text="⯈ Play")
        self.buttonVideoFilePlay.config(command=self.play)
        self.buttonVideoFilePlay.config(style="small.TButton")
        self.buttonVideoFilePlay.pack(expand="true", fill="x", side="right")

        self.frameVideoFileButtonsFrame.config(height="200", width="200")
        self.frameVideoFileButtonsFrame.pack(fill="x", side="top")
        self.frameVideoFileWidget.config(
            height="200", padding="2", relief="groove", width="200"
        )
        self.frameVideoFileWidget.pack(expand="false", fill="x", pady="5", side="top")
        
    def requestPreviewFrameIfVisible(self):
      if not self.previewRequested:
        try:
          winy = self.winfo_rooty()
          winmaserHeight = self.master.winfo_vrootheight()

          if winy > 0 and winy < winmaserHeight:
            self.previewRequested = True
            self.parent.requestPreviewFrame(self.filename)
            logging.debug('Preview frame requested for cut selection ui file:{} winy:{} winMasterH:{}'.format(self.filename,winy,winmaserHeight))
            return True
          else:
            return False
        except Exception as e:
          logging.error('Exception requestPreviewFrameIfVisible',exc_info=e)
      return False

    def setVideoPreview(self, photoImage):
        self.labelVideoPreviewImage = photoImage
        self.labelVideoPreviewLabel.configure(image=self.labelVideoPreviewImage)

    def setTitle(self, title):
        self.labelVideoFileTitle.config(text=title)

    def setCutSelectionCount(self, selectionCount):
        self.labelVideoFilecountCutsSelected.config(
            text="{} Cuts selected".format(selectionCount)
        )

    def play(self):
        self.parent.playVideoFile(self.filename)

    def remove(self):
        self.parent.removeVideoFile(self.filename)


class CutselectionUi(ttk.Frame):
    def __init__(self, master=None, controller=None, *args, **kwargs):
        ttk.Frame.__init__(self, master)
        self.master=master
        self.controller = controller

        self.frameCutSelection = self
        self.frameUpperFrame = ttk.Frame(self.frameCutSelection)
        self.frameSliceSettings = ttk.Frame(self.frameUpperFrame)
        self.labelFrameSlice = ttk.Labelframe(self.frameSliceSettings)

        self.sliceLength = 30.0
        self.sliceLengthVar = tk.StringVar()
        self.sliceLengthVar.trace("w", self.sliceLengthChangeCallback)

        self.targetLength = 60.0
        self.targetLengthVar = tk.StringVar()
        self.targetLengthVar.trace("w", self.targetLengthChangeCallback)

        self.targetTrim = 0.5
        self.targetTrimVar = tk.StringVar()
        self.targetTrimVar.trace("w", self.targetTrimChangeCallback)

        self.dragPreviewPos = 0.1
        self.dragPreviewPosVar = tk.StringVar()
        self.dragPreviewPosVar.trace("w", self.dragPreviewPosCallback)

        self.frameSliceLength = ttk.Frame(self.labelFrameSlice)
        self.labelSiceLength = ttk.Label(self.frameSliceLength)
        self.labelSiceLength.config(text="Slice Length")
        self.labelSiceLength.pack(anchor="w", side="left")
        self.entrySiceLength = ttk.Spinbox(
            self.frameSliceLength,
            textvariable=self.sliceLengthVar,
            from_=0,
            to=float("inf"),
            increment=0.1,
        )
        self.entrySiceLength.pack(anchor="e", side="right")
        self.frameSliceLength.config(height="200", width="200")
        self.frameSliceLength.pack(fill="x", pady="2", side="top")

        self.frameTargetLength = ttk.Frame(self.labelFrameSlice)
        self.labelTargetLength = ttk.Label(self.frameTargetLength)
        self.labelTargetLength.config(text="Target Length")
        self.labelTargetLength.pack(side="left")
        self.entryTargetLength = ttk.Spinbox(
            self.frameTargetLength,
            textvariable=self.targetLengthVar,
            from_=0,
            to=float("inf"),
            increment=0.1,
        )

        self.entryTargetLength.pack(side="right")
        self.frameTargetLength.config(height="200", width="200")
        self.frameTargetLength.pack(fill="x", pady="2", side="top")

        self.frameTargetTrim = ttk.Frame(self.labelFrameSlice)
        self.labelTargetTrim = ttk.Label(self.frameTargetTrim)
        self.labelTargetTrim.config(text="Target Trim")
        self.labelTargetTrim.pack(side="left")
        self.entryTargetTrim = ttk.Spinbox(
            self.frameTargetTrim,
            textvariable=self.targetTrimVar,
            from_=0,
            to=float("inf"),
            increment=0.1,
        )

        self.entryTargetTrim.pack(side="right")
        self.frameTargetTrim.config(height="200", width="200")
        self.frameTargetTrim.pack(fill="x", pady="2", side="top")

        self.framePreviewPos = ttk.Frame(self.labelFrameSlice)
        self.labelPreviewPos = ttk.Label(self.framePreviewPos)
        self.labelPreviewPos.config(text="Drag offset")
        self.labelPreviewPos.pack(side="left")
        self.entryPreviewPos = ttk.Spinbox(
            self.framePreviewPos,
            textvariable=self.dragPreviewPosVar,
            from_=0.0,
            to=float("inf"),
            increment=0.01,
        )

        self.entryPreviewPos.pack(side="right")
        self.framePreviewPos.config(height="200", width="200")
        self.framePreviewPos.pack(fill="x", pady="2", side="top")

        self.loopModeVar = tk.StringVar()
        
        self.loopOptions = ['Loop current','Loop all']
        self.loopModeVar.set(self.loopOptions[0])
        self.frameLoopMode = ttk.Frame(self.labelFrameSlice)
        self.labelLoopMode = ttk.Label(self.frameLoopMode)
        self.labelLoopMode.config(text="Loop mode")
        self.labelLoopMode.pack(side="left")
        self.entryLoopMode = ttk.OptionMenu(
            self.frameLoopMode,
            self.loopModeVar,
            self.loopModeVar.get(),
            *self.loopOptions
        )

        self.entryLoopMode.pack(side="right")
        self.frameLoopMode.config(height="200", width="200")
        self.frameLoopMode.pack(fill="x", pady="2", side="top")
        self.loopModeVar.trace("w", self.updateLoopMode)

        self.frameVolume = ttk.Frame(self.labelFrameSlice)

        self.labelVolume = ttk.Label(self.frameVolume,text='Volume')
        self.labelVolume.pack(fill="x", pady="2", side="top")

        self.scaleVolume = ttk.Scale(self.frameVolume,from_=0, to=100)
        self.scaleVolume.config(command=self.setVolume)
        self.scaleVolume.pack(fill="x", padx="2", side="top")

        self.frameVolume.config(height="200", width="200")
        self.frameVolume.pack(fill="x", pady="2", side="top")

        self.frameCurrentSize = ttk.Frame(self.labelFrameSlice)

        self.labelCurrentSize = ttk.Label(self.frameCurrentSize)
        self.labelCurrentSize.config(text="0.00s 0.00% (-0.00s)")
        self.labelCurrentSize.pack(side="top")

        self.progressToSize = ttk.Progressbar(self.frameCurrentSize)
        self.progressToSize.config(mode="determinate", orient="horizontal")
        self.progressToSize.pack(expand="true", fill="x", side="left")
        self.progressToSize.config(value=0)
        self.progressToSize.pack(fill="x", side="top")

        self.frameCurrentSize.config(height="200", width="200")
        self.frameCurrentSize.pack(fill="x", side="top")

        self.labelFrameSlice.config(height="200", text="Slice Settings", width="200")
        self.labelFrameSlice.pack(fill="x", side="top")

        self.labelframeSourceVideos = ttk.Labelframe(self.frameSliceSettings)

        self.buttonLoadVideos = ttk.Button(self.labelframeSourceVideos)
        self.buttonLoadVideos.config(text="Load Videos")
        self.buttonLoadVideos.config(style="small.TButton")
        self.buttonLoadVideos.config(command=self.loadVideoFiles)
        self.buttonLoadVideos.pack(fill="x", side="top")

        self.buttonLoadYTdl = ttk.Button(self.labelframeSourceVideos)
        self.buttonLoadYTdl.config(text="Load youtube-dl supported url")
        self.buttonLoadYTdl.config(style="small.TButton")
        self.buttonLoadYTdl.config(command=self.loadVideoYTdl)
        self.buttonLoadYTdl.pack(fill="x", side="top")

        self.buttonClearSubclips = ttk.Button(self.labelframeSourceVideos)
        self.buttonClearSubclips.config(text="Clear all subclips")
        self.buttonClearSubclips.config(style="small.TButton")
        self.buttonClearSubclips.config(command=self.clearSubclips)
        self.buttonClearSubclips.pack(fill="x", side="top")

        self.scrolledframeVideoPreviewContainer = ScrolledFrame(
            self.labelframeSourceVideos, scrolltype="vertical"
        )
        self.videoPreviewContainer = self.scrolledframeVideoPreviewContainer.innerframe
        self.previews = []
        self.scrolledframeVideoPreviewContainer.configure(usemousewheel=True)
        self.scrolledframeVideoPreviewContainer.pack(
            expand="true", fill="both", side="top"
        )

        self.labelframeSourceVideos.config(
            height="200", text="Source Videos", width="200"
        )
        self.labelframeSourceVideos.pack(expand="true", fill="both", side="top")

        self.progresspreviewLabel = ttk.Label(self.frameSliceSettings)
        self.progresspreviewLabel.config(text="")
        self.progresspreviewData = "P5\n1 1\n255\n" + ("127" * 1 * 1)

        self.progressPreviewImage = tk.PhotoImage(data=self.progresspreviewData)
        self.progresspreviewLabel.configure(image=self.progressPreviewImage)
        self.progresspreviewLabel.pack(side="top", expand="false", fill="y")

        self.frameSliceSettings.config(height="200", width="200")
        self.frameSliceSettings.pack(
            expand="false", fill="y", padx="2", pady="2", side="left"
        )

        self.frameVideoPlayerAndControls = ttk.Frame(self.frameUpperFrame)

        self.labelVideoSummaryVar = tk.StringVar()
        self.labelVideoSummary = ttk.Entry(self.frameVideoPlayerAndControls,takefocus=False,style="subtle.TEntry",textvariable=self.labelVideoSummaryVar,justify=tk.CENTER)
        self.labelVideoSummary.pack(expand="false",fill="both", padx=0, pady=0, side="top")

        self.frameVideoPlayerFrame = ttk.Frame(self.frameVideoPlayerAndControls)
        self.frameVideoPlayerFrame.config(
            borderwidth="0", height="200", relief="flat", width="200",
            takefocus=True,style="PlayerFrame.TFrame"
        )

        try:
          self.frameVideoPlayerphoto = tk.PhotoImage(file=".\\resources\\playerbg.png")
          self.frameVideoPlayerlabel = ttk.Label(self.frameVideoPlayerFrame, image=self.frameVideoPlayerphoto)
          self.frameVideoPlayerlabel.image = self.frameVideoPlayerphoto
          self.frameVideoPlayerlabel.config(
              borderwidth="0", relief="flat", style="PlayerLabel.TLabel",takefocus=False
          )
          self.frameVideoPlayerlabel.pack(expand="true", fill="y",side='top')
        except Exception as e:
          print('Failed to load player bg image',e)

        self.frameVideoPlayerFrame.pack(expand="true", fill="both", side="top")

        self.frameVideoControls = ttk.Frame(self.frameVideoPlayerAndControls)

        self.buttonvideoPrevClip= ttk.Button(self.frameVideoControls,text='Prev Clip', style="small.TButton")
        self.buttonvideoPrevClip.config(command=self.prevClip)
        self.buttonvideoPrevClip.pack(expand="true", fill='x', side="left")

        self.buttonvideoJumpBack = ttk.Button(self.frameVideoControls,text='<< Jump', style="small.TButton")
        self.buttonvideoJumpBack.config(command=self.jumpBack)
        self.buttonvideoJumpBack.pack(expand="true", fill='x', side="left")

        self.buttonvideoPause = ttk.Button(self.frameVideoControls,text='Play', style="small.TButton")
        self.buttonvideoPause.config(command=self.playPauseToggle)
        self.buttonvideoPause.pack(expand="true", fill='x', side="left")        

        self.buttonvideoInterestMark = ttk.Button(self.frameVideoControls,text='Add Mark', style="small.TButton")
        self.buttonvideoInterestMark.config(command=self.addNewInterestMarkNow)
        self.buttonvideoInterestMark.pack(expand="true", fill='x', side="left")

        self.buttonvideoRandomClip= ttk.Button(self.frameVideoControls,text='Random Clip', style="small.TButton")
        self.buttonvideoRandomClip.config(command=self.randomClip)
        self.buttonvideoRandomClip.pack(expand="true", fill='x', side="left")

        self.buttonvideoJumpFwd = ttk.Button(self.frameVideoControls,text='Jump >>', style="small.TButton")
        self.buttonvideoJumpFwd.config(command=self.jumpFwd)
        self.buttonvideoJumpFwd.pack(expand="true", fill='x', side="left")

        self.buttonvideoAddFullClip = ttk.Button(self.frameVideoControls,text='Add Full Clip', style="small.TButton")
        self.buttonvideoAddFullClip.config(command=self.addFullClip)
        self.buttonvideoAddFullClip.pack(expand="true", fill='x', side="left")

        self.buttonvideoNextClip= ttk.Button(self.frameVideoControls,text='Next Clip', style="small.TButton")
        self.buttonvideoNextClip.config(command=self.nextClip)
        self.buttonvideoNextClip.pack(expand="true", fill='x', side="left")


        self.frameVideoControls.pack(expand="false", fill="x", side="top")

        self.frameVideoPlayerAndControls.pack(expand="true", fill="both", side="right")

        self.frameUpperFrame.config(height="200", width="200")
        self.frameUpperFrame.pack(expand="true", fill="both", side="top")

        self.frameTimeLineFrame = TimeLineSelectionFrameUI(self.frameCutSelection, self)

        self.frameTimeLineFrame.config(borderwidth="0", height="200", width="200",takefocus=True)
        self.frameTimeLineFrame.pack(fill="x", side="bottom")

        self.frameCutSelection.config(height="800", width="1500")
        self.frameCutSelection.pack(expand="true", fill="both", side="top")

        self.mainwindow = self.frameCutSelection

        self.targetLengthVar.set(str(self.targetLength))
        self.sliceLengthVar.set(str(self.sliceLength))
        self.targetTrimVar.set(str(self.targetTrim))
        self.dragPreviewPosVar.set(str(self.dragPreviewPos))

        self.frameUpperFrame.bind('<Key>',self.playerFrameKeypress)

        self.mouseRectDragging=False
        self.videoMouseRect=[None,None,None,None]
        self.screenMouseRect=[None,None,None,None]

        self.frameVideoPlayerFrame.bind("<Button-1>",          self.videomousePress)
        self.frameVideoPlayerFrame.bind("<ButtonRelease-1>",   self.videomousePress)
        self.frameVideoPlayerFrame.bind("<Motion>",            self.videomousePress)
        self.frameVideoPlayerFrame.bind("<MouseWheel>",        self.videoMousewheel)

       
        self._previewtimer = threading.Timer(0.5, self.updateVideoPreviews)
        self._previewtimer.daemon = True
        self._previewtimer.start()
        self.playingOnLastSwitchAway = True

    def updateProgressPreview(self,data):
      try:
        if data is None:
          self.progresspreviewData = "P5\n1 1\n255\n" + ("127" * 1 * 1)
        else:
          self.progresspreviewData  = data
        
        self.progressPreviewImage = tk.PhotoImage(data=self.progresspreviewData)
        self.progresspreviewLabel.configure(image=self.progressPreviewImage)
      except Exception as e:
        print(e)
        self.progresspreviewData = "P5\n1 1\n255\n" + ("127" * 1 * 1)
        self.progressPreviewImage = tk.PhotoImage(data=self.progresspreviewData)
        self.progresspreviewLabel.configure(image=self.progressPreviewImage)

    def updateSummary( self,filename,duration=0,videoparams={},containerfps=0,estimatedvffps=0):
      if filename is None:
        self.labelVideoSummaryVar.set("")
        return

      if estimatedvffps is None:
        estimatedvffps = 0
      if containerfps is None:
        containerfps = 0
      try:
        self.labelVideoSummaryVar.set("{} - {}s - {}x{} - {:2f} ({:2f})fps ".format(filename,
                                                                                    duration,
                                                                                    videoparams.get('w',0),
                                                                                    videoparams.get('h',0),
                                                                                    containerfps,
                                                                                    estimatedvffps))
      except:
        self.labelVideoSummaryVar.set("")

    def generateSoundWaveBackgrounds(self):
      self.frameTimeLineFrame.generateWaveImages = not self.frameTimeLineFrame.generateWaveImages
      self.frameTimeLineFrame.uiDirty = True

    def requestTimelinePreviewFrames(self,filename,startTime,Endtime,frameWidth,timelineWidth,callback):
      return self.controller.requestTimelinePreviewFrames(filename,startTime,Endtime,frameWidth,timelineWidth,callback)

    def updateVideoPreviews(self):
      for vidPReview in self.previews:
        if vidPReview.requestPreviewFrameIfVisible():
          break
      self._previewtimer = threading.Timer(0.5, self.updateVideoPreviews)
      self._previewtimer.daemon = True
      self._previewtimer.start()

    def setinitialFocus(self):
      self.master.deiconify()
      self.entrySiceLength.focus_set()

    def prevClip(self):
      self.controller.jumpClips(-1)

    def randomClip(self):
      self.controller.jumpClips(None)

    def nextClip(self):
      self.controller.jumpClips(1)

    def updateLoopMode(self,*args):
      self.controller.updateLoopMode(self.loopModeVar.get())

    def videoMousewheel(self,evt):
      self.controller.seekRelative(evt.delta/20)

    def videomousePress(self,e):
      if e.type == tk.EventType.ButtonPress:
        logging.debug('video mouse press start')
        self.mouseRectDragging=True
        self.screenMouseRect[0]=e.x
        self.screenMouseRect[1]=e.y
      elif e.type in (tk.EventType.Motion,tk.EventType.ButtonRelease) and self.mouseRectDragging:
        logging.debug('video mouse press drag')
        self.screenMouseRect[2]=e.x
        self.screenMouseRect[3]=e.y
        self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3])
      if e.type == tk.EventType.ButtonRelease:
        logging.debug('video mouse press release')
        self.mouseRectDragging=False
        if self.screenMouseRect[0] is not None and self.screenMouseRect[2] is not None:
          vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
          vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 

          self.videoMouseRect=[vx1,vy1,vx2,vy2]
          self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3])
        
      if self.screenMouseRect[0] is not None and not self.mouseRectDragging and self.screenMouseRect[0]==self.screenMouseRect[2] and self.screenMouseRect[1]==self.screenMouseRect[3]:
        logging.debug('video mouse rect clear')
        self.screenMouseRect=[None,None,None,None]
        self.mouseRectDragging=False
        self.controller.clearVideoRect()

    def confirmWithMessage(self,messageTitle,message,icon='warning'):
      return messagebox.askquestion(messageTitle,message,icon=icon)

    def jumpBack(self):
      self.controller.jumpBack()

    def playPauseToggle(self):
      self.controller.playPauseToggle()

    def jumpFwd(self):
      self.controller.jumpFwd()

    def playerFrameKeypress(self,e):
      pass

    def findLowestErrorForBetterLoop(self,rid,secondsChange):
      self.controller.findLowestErrorForBetterLoop(rid,secondsChange,self.videoMouseRect)

    def findLoopAroundFrame(self,mid,minSeconds,maxSeconds):
     self.controller.findRangeforLoop(mid,minSeconds,maxSeconds,self.videoMouseRect)



    def setVolume(self,value):
      self.controller.setVolume(value)

    def sliceLengthChangeCallback(self, *args):
        try:
            value = float(self.sliceLengthVar.get())
            self.frameTimeLineFrame.setDefaultsliceDuration(value)
        except Exception as e:
            logging.error('Exception sliceLengthChangeCallback',exc_info=e)

    def targetLengthChangeCallback(self, *args):
        try:
            value = float(self.targetLengthVar.get())
            self.targetLength = value
        except Exception as e:
            logging.error('Exception targetLengthChangeCallback',exc_info=e)

    def targetTrimChangeCallback(self, *args):
        try:
            value = float(self.targetTrimVar.get())
            self.frameTimeLineFrame.setTargetTrim(value)
        except Exception as e:
            logging.error('Exception targetTrimChangeCallback',exc_info=e)

    def dragPreviewPosCallback(self, *args):
      try:
        value = float(self.dragPreviewPosVar.get())
        self.frameTimeLineFrame.setDragPreviewPos(value)
      except Exception as e:
        logging.error('Exception dragPreviewPosCallback',exc_info=e)


    def updateProgressStatitics(self, totalExTrim, totalTrim):
        percent = totalExTrim / self.targetLength
        progressPercent = max(0, min(100, percent * 100))
        self.progressToSize.config(value=progressPercent)
        if percent > 1.0:
            self.progressToSize.config(style="Red.Horizontal.TProgressbar")
        else:
            self.progressToSize.config(style="Horizontal.TProgressbar")

        self.labelCurrentSize.config(
            text="{}s {:0.2%}% (-{}s)".format( format_timedelta(totalExTrim,'{hours_total}:{minutes2}:{seconds2}') , percent, format_timedelta(totalTrim,'{hours_total}:{minutes2}:{seconds2}'))
        )

    def setController(self, controller):
        self.controller = controller

    def getPlayerFrameWid(self):
        return self.frameVideoPlayerFrame.winfo_id()

    def tabSwitched(self, tabName):
        if str(self) == tabName:
            if self.playingOnLastSwitchAway:
              self.controller.play()
        else:
            self.playingOnLastSwitchAway = self.controller.isplaying()
            self.controller.pause()

    def updateFileListing(self, files):
        currentFiles = set([x.filename for x in self.previews])

        for filename in files:
            if filename not in currentFiles:
                self.previews.append(
                    VideoFilePreview(self.videoPreviewContainer, self, filename)
                )

        previewsToRemove = [x for x in self.previews if x.filename not in files]
        self.previews = [x for x in self.previews if x.filename in files]

        for preview in previewsToRemove:
            preview.destroy()

    def requestPreviewFrame(self, filename):
        self.controller.requestPreviewFrame(filename, None, (200, -1))

    def updateViewPreviewFrame(self, filename, imageData):
        for preview in self.previews:
            if preview.filename == filename:
                photo = tk.PhotoImage(data=imageData)
                preview.setVideoPreview(photo)
                self.scrolledframeVideoPreviewContainer.reposition()
                break

    def playVideoFile(self, filename):
        self.controller.playVideoFile(filename, 0)

    def clearSubclips(self):
        self.controller.clearallSubclips()

    def removeVideoFile(self, filename):
        self.controller.removeVideoFile(filename)
        previewsToRemove = [x for x in self.previews if x.filename == filename]
        self.previews = [x for x in self.previews if x.filename != filename]
        for preview in previewsToRemove:
            preview.destroy()

    def askInteger(self,title, prompt):
      return simpledialog.askinteger(title, prompt) 

    def askFloat(self,title, prompt):
      return simpledialog.askfloat(title, prompt) 

    def askString(self,title, prompt):
      return simpledialog.askstring(title, prompt) 

    def loadVideoYTdl(self):
      defaultUrl=''
      try:
        s = self.clipboard_get()
        if s is not None and len(s)>2 and '.' in s and ':' in s:
          defaultUrl=s
      except Exception as e:
        print(e)

      url = simpledialog.askstring(title="Download video from URL",initialvalue=defaultUrl,prompt="Download a video from a youtube-dl supported url")
      if url is not None and len(url)>0:
        self.controller.loadVideoYTdl(url)

    def startScreencap(self):
      windowRef=self
      windowRef.cliprunScreencap=True
      windowRef.completedScreenCapName=None

      def screenCapWorker(windowRef):

        capturefilename = 'DesktopCapture_'+str(time.time())+'.mkv'
        cmd = ['ffmpeg','-f','gdigrab','-framerate','30','-i','desktop','-c:v','h264_nvenc','-qp','0', capturefilename]

        if hasattr(os.sys, 'winver'):
          proc = sp.Popen(cmd,creationflags=sp.CREATE_NEW_PROCESS_GROUP,stderr=sp.DEVNULL,stdout=sp.DEVNULL,bufsize=10 ** 5)
        else:
          proc = sp.Popen(cmd,stderr=sp.DEVNULL,stdout=sp.DEVNULL,bufsize=10 ** 5)

        while windowRef.cliprunScreencap:
          print('Recording',proc.poll())
        
        if hasattr(os.sys, 'winver'):
          os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
        else:
          proc.send_signal(signal.SIGTERM)
        proc.communicate()

        windowRef.completedScreenCapName = capturefilename

      t = threading.Thread(target=screenCapWorker,args=(self,))
      t.start()

      tk.messagebox.showinfo(title="Recording screen", message="Recording Desktop, click 'OK' to stop Recording.")

      windowRef.cliprunScreencap=False
      t.join()
      if self.completedScreenCapName is not None:
        self.controller.loadFiles([windowRef.completedScreenCapName])
      else:
        tk.messagebox.showinfo(title="Recording screen Failed", message="Desktop recording failed.")


    def loadClipboardUrls(self):

      windowRef=self
      windowRef.cliprunWatch=True

      def clipWatchWorker(windowRef):
        foundUrls = []
        while windowRef.cliprunWatch:
          s=None
          try:
            s = windowRef.clipboard_get()
            if s is not None:
              s.replace('\n',' ')
              for substr in s.split(' '):
                substr = substr.strip()
                if substr not in foundUrls and len(substr)>2 and ':' in substr and '.' in substr:
                  windowRef.controller.loadVideoYTdl(substr)
                  foundUrls.append(substr)
                  print(substr)
          except Exception as e:
            pass
        print("END WATCH")

      t = threading.Thread(target=clipWatchWorker,args=(self,))
      t.start()
      tk.messagebox.showinfo(title="Watching clipboard", message="Monitoring clipboard for urls, any urls copied will be downloaded with youtube-dl.\nClick 'OK' to stop watching.")
      windowRef.cliprunWatch=False

    def loadVideoFiles(self):
      initialdir=self.controller.getGlobalOptions().get('defaultVideoFolder','.')
      filetypes=(('All files', '*.*'),)        
      fileList = askopenfilenames(initialdir=initialdir,filetypes=filetypes)
      self.controller.loadFiles(fileList)
      for fn in fileList:
        writeBackPath = os.path.abspath(os.path.dirname(fn))
        self.controller.getGlobalOptions()['defaultVideoFolder'] = writeBackPath
        break

    def loadImageFile(self):
      initialdir=self.controller.getGlobalOptions().get('defaultImageFolder','.')
      filetypes=(('All files', '*.*'),)
      fileList = askopenfilenames(initialdir=initialdir,filetypes=filetypes)
      duration=None
      if len(fileList)>0:
         duration = simpledialog.askfloat("Create video from still images", "What should the durtation of the new video clips be?",parent=self,minvalue=0.0, maxvalue=100000.0)
      for filename in fileList:
        if filename is not None and len(filename)>0:
          writeBackPath = os.path.abspath(os.path.dirname(filename))
          self.controller.getGlobalOptions()['defaultImageFolder'] = writeBackPath
          if duration is not None:
            self.controller.loadImageFile(filename,duration)

    def restartForNewFile(self, filename=None):
        self.frameTimeLineFrame.resetForNewFile()
        try:
          self.frameVideoPlayerlabel.pack_forget()
        except:
          pass

    def getIsPlaybackStarted(self):
        return self.controller.getIsPlaybackStarted()

    def update(self):
        self.frameTimeLineFrame.updateCanvas()

    def setUiDirtyFlag(self):
      self.frameTimeLineFrame.setUiDirtyFlag() 

    def play(self):
        self.controller.play()

    def pause(self):
        self.controller.pause()

    def seekTo(self, seconds):
        self.controller.seekTo(seconds)

    def updateStatus(self, status):
        pass

    def getTotalDuration(self):
        return self.controller.getTotalDuration()

    def addFullClip(self):
      self.controller.addFullClip()

    def addNewInterestMarkNow(self):
      self.controller.addNewInterestMark(self.controller.getCurrentPlaybackPosition())

    def addNewInterestMark(self,point):
      self.controller.addNewInterestMark(point)

    def getInterestMarks(self):
      return self.controller.getInterestMarks()

    def addNewSubclip(self, start, end):
        return self.controller.addNewSubclip(start, end)

    def expandSublcipToInterestMarks(self, point):
      self.controller.expandSublcipToInterestMarks(point)

    def cloneSubclip(self, point):
        self.controller.cloneSubclip(point)

    def copySubclip(self, point):
        self.controller.copySubclip(point)

    def pasteSubclip(self):
        self.controller.pasteSubclip()

    def removeSubclip(self, point):
        self.controller.removeSubclip(point)

    def getRangesForClip(self, currentFilename):
        return self.controller.getRangesForClip(currentFilename)

    def getcurrentFilename(self):
        return self.controller.getcurrentFilename()

    def getCurrentPlaybackPosition(self):
        return self.controller.getCurrentPlaybackPosition()

    def setLoopPos(self, start, end):
        self.controller.setLoopPos(start, end)

    def updatePointForClip(self, filename, rid, pos, seconds):
        if self.controller.updatePointForClip(filename, rid, pos, seconds):
          return rid
        else:
          return False

    def runSceneChangeDetection(self):
      self.controller.runSceneChangeDetection()


if __name__ == "__main__":
    import webmGenerator


import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilenames,askopenfilename
from tkinter import messagebox
from tkinter import simpledialog

import os
import threading
import signal
from math import floor
import random
import logging
import time
import subprocess as sp

from .modalWindows import PerfectLoopScanModal, YoutubeDLModal, TimestampModal, VoiceActivityDetectorModal, Tooltip, CutSpecificationPlanner, EditSubclipModal

from .timeLineSelectionFrameUI import TimeLineSelectionFrameUI

from pygubu.widgets.scrolledframe import ScrolledFrame

fastSeekLock = threading.RLock()

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

placeholderPreviewGrey = None
placeholderPreviewImage = None

class VideoFilePreview(ttk.Frame):
    def __init__(self, master, parent, filename, *args, **kwargs):
        global placeholderPreviewGrey, placeholderPreviewImage

        ttk.Frame.__init__(self, master)

        self.filename = filename
        self.basename = os.path.basename(filename)[:30]
        self.parent = parent
        self.cutsSelected = 0

        self.frameVideoFileWidget = self
        self.configure(style="previewImg.TFrame")

        self.labelVideoFileTitle = ttk.Label(self.frameVideoFileWidget, style="previewImg.TLabel", justify='center')
        self.labelVideoFileTitle.config(text=self.basename,width=30)
        self.labelVideoFileTitle.pack(anchor="n", side="top", expand='false')

        self.labelVideoPreviewLabel = ttk.Label(self.frameVideoFileWidget, justify='center', style="previewImg.TLabel")
        self.labelVideoPreviewLabel.config(text="No Preview Loaded")

        self.previewData = ""
        if placeholderPreviewGrey is None:
            self.previewData = "P5\n200 117\n255\n" + ("0" * 200 * 117)
            placeholderPreviewGrey = tk.PhotoImage(data=self.previewData)
        self.labelVideoPreviewImage = placeholderPreviewGrey
        try:
          if placeholderPreviewImage is None:
            placeholderPreviewImage = tk.PhotoImage(file=".\\resources\\loadingPreview.png")
          self.labelVideoPreviewImage = placeholderPreviewImage
        except Exception as e:
          print(e)
        self.previewRequested = False

        self.labelVideoPreviewLabel.configure(image=self.labelVideoPreviewImage)

        self.labelVideoPreviewLabel.pack(side="top", expand="true", fill="y")

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


def binseq(upper,lower):
    mid = (upper+lower)/2
    yield mid
    g1,g2 = binseq(lower,mid), binseq(mid,upper)
    while 1:
        for gen in [g1,g2]:
            yield next(gen)

class CutselectionUi(ttk.Frame):
    def __init__(self, master=None, controller=None,globalOptions={},*args, **kwargs):
        ttk.Frame.__init__(self, master)
        self.master=master
        self.controller = controller
        self.globalOptions=globalOptions


        self.frameCutSelection = self
        self.frameUpperFrame = ttk.Frame(self.frameCutSelection)
        self.frameSliceSettings = ttk.Frame(self.frameUpperFrame)
        self.labelFrameSlice = ttk.Frame(self.frameSliceSettings)

        self.sliceLength = globalOptions.get('defaultSliceLength',30.0)
        self.sliceLengthVar = tk.StringVar()
        self.sliceLengthVar.trace("w", self.sliceLengthChangeCallback)

        self.targetLength = globalOptions.get('defaultTargetLength',60.0)
        self.targetLengthVar = tk.StringVar()
        self.targetLengthVar.trace("w", self.targetLengthChangeCallback)

        self.targetTrim = globalOptions.get('defaultTrimLength',0.0)
        self.targetTrimVar = tk.StringVar()
        self.targetTrimVar.trace("w", self.targetTrimChangeCallback)

        self.dragPreviewPos = globalOptions.get('defaultDragOffset',0.1)
        self.dragPreviewPosVar = tk.StringVar()
        self.dragPreviewPosVar.trace("w", self.dragPreviewPosCallback)

        self.playbackSpeed = globalOptions.get('defaultPlaybackSpeed',0.1)
        self.playbackSpeedVar = tk.StringVar(self,'1')
        self.playbackSpeedVar.trace("w", self.playbackSpeedCallback)

        self.frameSliceLength = ttk.Frame(self.labelFrameSlice)
        self.labelSiceLength = ttk.Label(self.frameSliceLength)
        self.labelSiceLength.config(text="Slice Length")
        self.labelSiceLength.pack(anchor="w",pady="0", side="left")
        self.entrySiceLength = ttk.Spinbox(
            self.frameSliceLength,
            textvariable=self.sliceLengthVar,
            from_=0,
            to=float("inf"),
            increment=0.1
        )
        Tooltip(self.entrySiceLength,text='The default initial length of newly added subclips.')

        self.entrySiceLength.pack(anchor="e",pady="0", side="right")
        self.frameSliceLength.config(height="200", width="200")
        self.frameSliceLength.pack(fill="x", pady="0", side="top")

        self.frameTargetLength = ttk.Frame(self.labelFrameSlice)
        self.labelTargetLength = ttk.Label(self.frameTargetLength)
        self.labelTargetLength.config(text="Target Length")
        self.labelTargetLength.pack(side="left",pady=0)
        self.entryTargetLength = ttk.Spinbox(
            self.frameTargetLength,
            textvariable=self.targetLengthVar,
            from_=0,
            to=float("inf"),
            increment=0.1
        )

        Tooltip(self.entryTargetLength,text='The target length of the final clip, useful if you want to hit a certain duration.')

        self.entryTargetLength.pack(side="right",pady="0")
        self.frameTargetLength.config(height="200", width="200")
        self.frameTargetLength.pack(fill="x", pady="0", side="top")

        self.frameTargetTrim = ttk.Frame(self.labelFrameSlice)
        self.labelTargetTrim = ttk.Label(self.frameTargetTrim)
        self.labelTargetTrim.config(text="Target Trim")
        self.labelTargetTrim.pack(side="left",pady="0")
        self.entryTargetTrim = ttk.Spinbox(
            self.frameTargetTrim,
            textvariable=self.targetTrimVar,
            from_=0,
            to=float("inf"),
            increment=0.1,
        )

        Tooltip(self.entryTargetTrim,text='The expected overlap between clips, only useful if you plan to use join clips into a sequence and add fade effects between scenes.')

        self.entryTargetTrim.pack(side="right")
        self.frameTargetTrim.config(height="200", width="200")
        self.frameTargetTrim.pack(fill="x", pady="0", side="top")

        self.framePreviewPos = ttk.Frame(self.labelFrameSlice)
        self.labelPreviewPos = ttk.Label(self.framePreviewPos)
        self.labelPreviewPos.config(text="Drag offset")
        self.labelPreviewPos.pack(side="left",pady="0")
        self.entryPreviewPos = ttk.Spinbox(
            self.framePreviewPos,
            textvariable=self.dragPreviewPosVar,
            from_=0.0,
            to=float("inf"),
            increment=0.01,
        )

        Tooltip(self.entryPreviewPos,text='The number of seconds the preview is offset from the start or end of the clip when dragging, useful fo aligning events, hold ctrl to switch between offsetting from start or end.')


        self.entryPreviewPos.pack(side="right")
        self.framePreviewPos.config(height="200", width="200")
        self.framePreviewPos.pack(fill="x", pady="0", side="top")







        self.framePlaybackSpeed = ttk.Frame(self.labelFrameSlice)
        self.labelPlaybackSpeed = ttk.Label(self.framePlaybackSpeed)
        self.labelPlaybackSpeed.config(text="Play Speed")
        self.labelPlaybackSpeed.pack(side="left",pady="0")
        self.entryPlaybackSpeed = ttk.Spinbox(
            self.framePlaybackSpeed,
            textvariable=self.playbackSpeedVar,
            from_=0.0,
            to=20.0,
            increment=0.01,
        )

        Tooltip(self.entryPlaybackSpeed,text='Playback speed multiplier.')


        self.entryPlaybackSpeed.pack(side="right")
        self.framePlaybackSpeed.config(height="200", width="200")
        self.framePlaybackSpeed.pack(fill="x", pady="0", side="top")













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

        Tooltip(self.entryLoopMode,text='How to loop between subclips, either just loop the current clip, or jump between clips for a full preview of all subclips.')

        self.entryLoopMode.config(style="small.TMenubutton")
        self.entryLoopMode.pack(side="right")
        self.frameLoopMode.config(height="200", width="200")
        self.frameLoopMode.pack(fill="x", pady="0", side="top")
        self.loopModeVar.trace("w", self.updateLoopMode)

        self.frameVolume = ttk.Frame(self.labelFrameSlice)

        self.labelVolume = ttk.Label(self.frameVolume,text='Volume')
        self.labelVolume.pack(fill="x", pady="0", side="top")

        self.scaleVolume = ttk.Scale(self.frameVolume,from_=0, to=100)
        self.scaleVolume.config(command=self.setVolume)
        self.scaleVolume.pack(fill="x", padx="0", side="top")

        self.frameVolume.config(height="200", width="200")
        self.frameVolume.pack(fill="x", pady="0", side="top")

        self.frameCurrentSize = ttk.Frame(self.labelFrameSlice)

        self.labelCurrentSize = ttk.Label(self.frameCurrentSize)
        self.labelCurrentSize.config(text="0.00s 0.00% (-0.00s)")
        self.labelCurrentSize.pack(side="top")

        Tooltip(self.labelCurrentSize,text='Current size counter displaying: Total Length, Percentage of Target size, (Seconds deducted by target trim overlap)')


        self.progressToSize = ttk.Progressbar(self.frameCurrentSize)
        self.progressToSize.config(mode="determinate", orient="horizontal")
        self.progressToSize.pack(expand="true", fill="x", side="left")
        self.progressToSize.config(value=0)
        self.progressToSize.pack(fill="x", side="top")

        self.frameCurrentSize.config(height="200", width="200")
        self.frameCurrentSize.pack(fill="x", side="top")

        self.labelFrameSlice.config(height="200", width="200")
        self.labelFrameSlice.pack(fill="x",pady=0,side="top")

        self.labelframeSourceVideos = ttk.Frame(self.frameSliceSettings)

        self.labelframeButtons = ttk.Frame(self.labelframeSourceVideos,style="frameButtons.TFrame")



        self.buttonLoadVideos = ttk.Button(self.labelframeButtons)
        self.buttonLoadVideos.config(text="Load File")
        self.buttonLoadVideos.config(style="small.TButton")
        self.buttonLoadVideos.config(command=self.loadVideoFiles)
        self.buttonLoadVideos.pack(expand='true', fill="x", side="left")

        Tooltip(self.buttonLoadVideos,text='Load a video file from your system')

        self.buttonLoadYTdl = ttk.Button(self.labelframeButtons)
        self.buttonLoadYTdl.config(text="Load URL")
        self.buttonLoadYTdl.config(style="small.TButton")
        self.buttonLoadYTdl.config(command=self.loadVideoYTdl)
        self.buttonLoadYTdl.pack(expand='true', fill="x", side="left")

        Tooltip(self.buttonLoadYTdl,text='Download a video from a URL using yt-dlp, many popualr video and streaming sites automatically supported.')

        self.buttonClearSubclips = ttk.Button(self.labelframeButtons)
        self.buttonClearSubclips.config(text="Clear SubClips")
        self.buttonClearSubclips.config(style="small.TButton")
        self.buttonClearSubclips.config(command=self.clearSubclips)
        self.buttonClearSubclips.pack(expand='true', fill="x", side="left")

        Tooltip(self.buttonClearSubclips,text='Remove all subclips to start a fresh with the same videos loaded.')

        self.labelframeButtons.pack(expand='false', fill="x", side="top")

        self.searchframeButtons = ttk.Frame(self.labelframeSourceVideos,style="frameButtons.TFrame")
        self.searchStringVar = tk.StringVar(self,'')
        self.entrySearch = ttk.Entry(self.searchframeButtons,textvariable=self.searchStringVar)
        self.entrySearch.pack(expand='true', fill="x", side="left")
        self.entrySearch.bind('<Return>',self.search)

        self.buttonSearch = ttk.Button(self.searchframeButtons)
        self.buttonSearch.config(text="🔎")
        self.buttonSearch.config(style="smallIcon.TButton")
        self.buttonSearch.config(command=lambda:self.search(0))
        self.buttonSearch.pack(expand='false', side="right")

        self.searchframeButtons.pack(expand='false', fill="x", side="top")

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
            height="200", width="200"
        )
        self.labelframeSourceVideos.pack(expand="true", fill="both", side="top")

        self.previewsListview = tk.Listbox(self.videoPreviewContainer)
        self.previewsscrollbar = tk.Scrollbar(self.videoPreviewContainer)
        self.previewsscrollbarx = tk.Scrollbar(self.videoPreviewContainer,orient='horizontal')
         

        self.previewsListview.config(yscrollcommand = self.previewsscrollbar.set,
                                     xscrollcommand = self.previewsscrollbarx.set)
        
        self.previewsscrollbar.config(command = self.previewsListview.yview)
        self.previewsscrollbarx.config(command = self.previewsListview.xview)

    

        self.previewsListview.bind('<Double-1>', self.switchvideoFromListview)

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

        self.frameVideoPlannerFrame = ttk.Frame(self.frameVideoPlayerAndControls)
        self.frameVideoPlannerFrame.pack(expand="false", fill="both", side="bottom")

        self.frameVideoPlayerFrame = ttk.Frame(self.frameVideoPlayerAndControls)
        self.frameVideoPlayerFrame.config(
            borderwidth="0", height="200", relief="flat", width="200",
            takefocus=True,style="PlayerFrame.TFrame"
        )

        self.video_canvas_popup_menu = tk.Menu(self, tearoff=0)


        self.video_canvas_popup_menu.add_command(label="Toggle scaling" ,command=lambda :self.fitoScreen())
        self.video_canvas_popup_menu.add_command(label="Scale to 720:-1"   ,command=lambda :self.fitoDimension(720))
        self.video_canvas_popup_menu.add_command(label="Scale to 1080:-1"   ,command=lambda :self.fitoDimension(1080))




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

        self.buttonvideoPrevClip= ttk.Button(self.frameVideoControls,text='Prev Clip', style="smallVideoSub.TButton")
        self.buttonvideoPrevClip.config(command=self.prevClip)
        self.buttonvideoPrevClip.pack(expand="true", fill='x', side="left")

        self.buttonvideoJumpBack = ttk.Button(self.frameVideoControls,text='<< Jump', style="smallVideoSub.TButton")
        self.buttonvideoJumpBack.config(command=self.jumpBack)
        self.buttonvideoJumpBack.pack(expand="true", fill='x', side="left")

        self.buttonvideoPause = ttk.Button(self.frameVideoControls,text='Play', style="smallVideoSub.TButton")
        self.buttonvideoPause.config(command=self.playPauseToggle)
        self.buttonvideoPause.pack(expand="true", fill='x', side="left")        

        self.buttonvideoInterestMark = ttk.Button(self.frameVideoControls,text='Add Mark', style="smallVideoSub.TButton")
        self.buttonvideoInterestMark.config(command=self.addNewInterestMarkNow)
        self.buttonvideoInterestMark.pack(expand="true", fill='x', side="left")

        self.buttonvideoRandomClip= ttk.Button(self.frameVideoControls,text='Random Clip', style="smallVideoSub.TButton")
        self.buttonvideoRandomClip.config(command=self.randomClip)
        self.buttonvideoRandomClip.pack(expand="true", fill='x', side="left")

        self.buttonvideoJumpFwd = ttk.Button(self.frameVideoControls,text='Jump >>', style="smallVideoSub.TButton")
        self.buttonvideoJumpFwd.config(command=self.jumpFwd)
        self.buttonvideoJumpFwd.pack(expand="true", fill='x', side="left")

        self.buttonvideoAddFullClip = ttk.Button(self.frameVideoControls,text='Add Full Clip', style="smallVideoSub.TButton")
        self.buttonvideoAddFullClip.config(command=self.addFullClip)
        self.buttonvideoAddFullClip.pack(expand="true", fill='x', side="left")

        self.buttonvideoNextClip= ttk.Button(self.frameVideoControls,text='Next Clip', style="smallVideoSub.TButton")
        self.buttonvideoNextClip.config(command=self.nextClip)
        self.buttonvideoNextClip.pack(expand="true", fill='x', side="left")


        self.frameVideoControls.pack(expand="false", fill="x", side="top")




        self.frameVideoPlayerAndControls.pack(expand="true", fill="both", side="right")




        self.frameUpperFrame.config(height="200", width="200")
        self.frameUpperFrame.pack(expand="true", fill="both", side="top")



        self.frameTimeLineFrame = TimeLineSelectionFrameUI(self.frameCutSelection, self, globalOptions=self.globalOptions)


        self.frameCutSelection.config(height="800", width="1500")
        self.frameCutSelection.pack(expand="true", fill="both", side="top")


        self.frameTimeLineFrame.config(borderwidth="0", height="200", width="200",takefocus=True)
        self.frameTimeLineFrame.pack(fill="x", side="bottom")


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



        self.frameVideoPlayerFrame.bind("<Button-3>",          self.showvideoContextMenu)


        self.frameVideoPlayerFrame.bind("q",        lambda s=self: s.jumpClips(-1))
        self.frameVideoPlayerFrame.bind("e",        lambda s=self: s.jumpClips(1))
        self.frameVideoPlayerFrame.bind("Q",        lambda s=self: s.jumpClips(-1))
        self.frameVideoPlayerFrame.bind("E",        lambda s=self: s.jumpClips(1))
        
        self.frameVideoPlayerFrame.bind("r",        lambda s=self: s.randomClip())
        self.frameVideoPlayerFrame.bind("R",        lambda s=self: s.randomClip())

        self.frameVideoPlayerFrame.bind("f",        lambda s=self: s.fastSeek())
        self.frameVideoPlayerFrame.bind("Ctrl-f",   lambda s=self: s.search())

        self._previewtimer = threading.Timer(0.5, self.updateVideoPreviews)
        self._previewtimer.daemon = True
        self._previewtimer.start()
        self.playingOnLastSwitchAway = True

        self.frameRate = None
        self.disableFileWidgets=False

        g = binseq(0,1000)
        self.seekpoints = [next(g)/1000 for i in range(1000)]

    def switchvideoFromListview(self,e):
        cs = self.previewsListview.curselection()
        sel = self.previewsListview.get(cs[0])
        self.playVideoFile(sel)
        
    def requestAutoconvert(self):
        self.controller.requestAutoconvert()

    def searchrandom(self,e):
        searchStr = self.searchStringVar.get()
        self.controller.jumpToSearch(searchStr,randomjump=True)

    def search(self,e):
        searchStr = self.searchStringVar.get()
        self.controller.jumpToSearch(searchStr)

    def setDragDur(self,dur):
      self.sliceLengthVar.set(str(round(dur,4)))

    def forgetPlannerFrame(self):
      self.frameVideoPlannerFrame.pack_forget()

    def getPlannerFrame(self):
      self.frameVideoPlannerFrame.pack(expand="false", fill="both", side="bottom")
      return self.frameVideoPlannerFrame

    def showSlicePlanner(self):
      pass

    def fitoDimension(self,dim):
      self.controller.fitoDim(dim)

    def fitoScreen(self):
      self.controller.fitoScreen()

    def showvideoContextMenu(self,e):
      self.video_canvas_popup_menu.tk_popup(e.x_root,e.y_root)

    def setPausedStatus(self,paused):
      if paused:
        self.buttonvideoPause.config(text="⯈ Play")
      else:
        self.buttonvideoPause.config(text="⏸ Pause")

    def jumpClips(self,dir):
      self.controller.jumpClips(dir)

    def canvasPopupRangeProperties(self, rid):
        scm = EditSubclipModal(master=self,controller=self.controller, rid=rid)
        scm.mainloop()

    def addSubclipByTextRange(self,controller,totalDuration):
      initial=''
      try:
        initial = self.clipboard_get().split('\n')[0]
      except Exception as e:
        print(e)

      tsModal = TimestampModal(master=self,controller=controller,initialValue=initial,videoDuration=totalDuration)
      tsModal.mainloop()

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
        self.labelVideoSummaryVar.set("{} - {}s - {}x{} - {:3.3f} ({:3.3f})fps {} {} [SAR {:2.2f} DAR {:2.2f}]".format(filename,
                                                                                    duration,
                                                                                    videoparams.get('w',0),
                                                                                    videoparams.get('h',0),
                                                                                    containerfps,
                                                                                    estimatedvffps,
                                                                                    videoparams.get('pixelformat',''),
                                                                                    videoparams.get('hw-pixelformat',''),
                                                                                    videoparams.get('par',1),
                                                                                    videoparams.get('aspect',1)
                                                                                     ))
      except:
        self.labelVideoSummaryVar.set("")

    def generateSoundWaveBackgrounds(self,style='GENERAL'):
      self.frameTimeLineFrame.generateWaveStyle=style
      self.frameTimeLineFrame.generateWaveImages = not self.frameTimeLineFrame.generateWaveImages
      self.frameTimeLineFrame.uiDirty = True

    def requestRIDHoverPreviews(self,rid,size,callback,start=None,end=None):
        self.controller.requestRIDHoverPreviews(rid,size,callback,start=start,end=end)

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

    def stepBackwards(self):
      self.controller.stepBackwards()

    def stepForwards(self):
      self.controller.stepForwards()

    def fastSeek(self,centerAfter=False):
      with fastSeekLock:

          if len(self.seekpoints) == 0:
            g = binseq(0,1000)
            self.seekpoints = [next(g)/1000 for i in range(1000)]
            print('RESET SEEKPOINTS')
          
          fn = self.getcurrentFilename()
          ranges = self.getRangesForClip(fn)
          while 1:
            point = self.seekpoints.pop(0)
            clear = True
            print(point,self.getTotalDuration())
            for i,(s,e) in ranges:
                print(s,e)
                if s<=point*self.getTotalDuration()<=e:
                    clear = False
                    break
            if clear:
                break

          self.seekTo(point*self.getTotalDuration(),centerAfter=centerAfter)
          
          return point*self.getTotalDuration()

    def videoMousewheel(self,evt):
      ctrl  = evt and ((evt.state & 0x4) != 0)

      if ctrl:
        self.controller.seekRelative(evt.delta/200)
      else:
        self.controller.seekRelative(evt.delta/20)

    def clearVideoMousePress(self):
        self.screenMouseRect=[None,None,None,None]
        self.mouseRectDragging=False
        self.controller.clearVideoRect()

    def videomousePress(self,e):
      try:
          if e.type == tk.EventType.ButtonPress:
            logging.debug('video mouse press start')
            self.mouseRectDragging=True
            self.screenMouseRect[0]=e.x
            self.screenMouseRect[1]=e.y
          elif e.type in (tk.EventType.Motion,tk.EventType.ButtonRelease) and self.mouseRectDragging:
            logging.debug('video mouse press drag')
            self.screenMouseRect[2]=e.x
            self.screenMouseRect[3]=e.y
            
            vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
            vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 

            self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3],desc='{}x{}'.format(int(abs(vx1-vx2)),int(abs(vy1-vy2))))
          if e.type == tk.EventType.ButtonRelease:
            logging.debug('video mouse press release')
            self.mouseRectDragging=False
            if self.screenMouseRect[0] is not None and self.screenMouseRect[2] is not None:
              vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
              vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 

              self.videoMouseRect=[vx1,vy1,vx2,vy2]
              self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3],desc='{}x{}'.format(int(abs(vx1-vx2)),int(abs(vy1-vy2))))
            
          if self.screenMouseRect[0] is not None and not self.mouseRectDragging and self.screenMouseRect[0]==self.screenMouseRect[2] and self.screenMouseRect[1]==self.screenMouseRect[3]:
            logging.debug('video mouse rect clear')
            self.screenMouseRect=[None,None,None,None]
            self.mouseRectDragging=False
            self.controller.clearVideoRect()
      except Exception as e:
        print('Video not loaded',e)

    def getCurrentlySelectedRegion(self):
      return self.frameTimeLineFrame.getCurrentlySelectedRegion()


    def clearCurrentlySelectedRegion(self):
      return self.frameTimeLineFrame.clearCurrentlySelectedRegion()

    def confirmWithMessage(self,messageTitle,message,icon='warning',allowCancel=False):
      if allowCancel:
        return messagebox.askyesnocancel(messageTitle,message,icon=icon)
      return messagebox.askquestion(messageTitle,message,icon=icon)

    def jumpBack(self):
      self.controller.jumpBack()

    def playPauseToggle(self):
      self.controller.playPauseToggle()

    def jumpFwd(self):
      self.controller.jumpFwd()

    def playerFrameKeypress(self,e):
      pass

    def moveToMaximumInterFrameDistance(self,rid,pos):
      self.controller.moveToMaximumInterFrameDistance(rid,pos)

    def findLowestErrorForBetterLoop(self,rid,secondsChange):
      self.controller.findLowestErrorForBetterLoop(rid,secondsChange,self.videoMouseRect)

    def findLoopAroundFrame(self,mid,minSeconds,maxSeconds):
     self.controller.findRangeforLoop(mid,minSeconds,maxSeconds,self.videoMouseRect)


    def seekRelative(self,offset):
      self.controller.seekRelative(offset)

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
        if self.controller is not None:
          self.controller.updateProgressStatistics()


    def playbackSpeedCallback(self, *args):
      try:
        value = float(self.playbackSpeedVar.get())
        self.controller.setPlaybackSpeed(value)
      except Exception as e:
        logging.error('Exception playbackSpeedCallback',exc_info=e)

    def dragPreviewPosCallback(self, *args):
      try:
        value = self.dragPreviewPosVar.get()
        mode = 'abs'
        if '%' in value:
            value = value.strip().replace('%','')
            mode  = 'percent'
        value = float(value)

        self.frameTimeLineFrame.setDragPreviewPos(value,mode)
      except Exception as e:
        logging.error('Exception dragPreviewPosCallback',exc_info=e)


    def updateProgressStatitics(self, totalExTrim, totalTrim, totalFiles, unplayedFiles):
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

        self.buttonvideoRandomClip.config(text='Random ({}/{})'.format(unplayedFiles,totalFiles))

    def setController(self, controller):
        self.controller = controller

    def getPlayerFrameWid(self):
        return self.frameVideoPlayerFrame.winfo_id()

    def tabSwitched(self, tabName):
        if str(self) == tabName:
            if self.playingOnLastSwitchAway:
              self.controller.play()
              self.controller.isActiveTab=True
        else:
            self.playingOnLastSwitchAway = self.controller.isplaying()
            self.controller.pause()
            self.controller.isActiveTab=False

    def updateFileListing(self, files):
        if self.disableFileWidgets:
          for preview in self.previews:
              preview.destroy()
          
          try:
            self.previewsListview.delete(0,'end')
          except Exception as e:
            print(e)

          for filename in files:
            self.previewsListview.insert('end', filename)
          self.previewsscrollbar.pack(side = 'right', fill = 'both')
          self.previewsscrollbarx.pack(side = 'bottom', fill = 'both')
          self.previewsListview.pack(expand=True, side='left', fill='both')

        else:
          self.previewsListview.pack_forget()
          self.previewsscrollbar.pack_forget()
          self.previewsscrollbarx.pack_forget()
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
        self.controller.requestPreviewFrame(filename, None, (200, 200))

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

    def askInteger(self,title, prompt, initialvalue=None):
      return simpledialog.askinteger(title, prompt, initialvalue=initialvalue) 

    def askFloat(self,title, prompt, initialvalue=None):
      return simpledialog.askfloat(title, prompt, initialvalue=initialvalue) 

    def askString(self,title, prompt, initialvalue=None):
      return simpledialog.askstring(title, prompt, initialvalue=initialvalue) 

    def centerTimelineOnCurrentPosition(self):
      self.frameTimeLineFrame.centerTimelineOnCurrentPosition()

    def loadVideoYTdl(self):
      defaultUrl=''
      try:
        s = self.clipboard_get()
        if s is not None and len(s)>2 and '.' in s and ':' in s:
          defaultUrl=s
      except Exception as e:
        print(e)
      modal = YoutubeDLModal(master=self,controller=self,initialUrl=defaultUrl)
      modal.mainloop()
      
    def loadVideoYTdlCallback(self,url,fileLimit,username,password,useCookies,browserCookies,qualitySort):
      if url is not None and len(url)>0:
        self.controller.loadVideoYTdl(url,fileLimit,username,password,useCookies,browserCookies,qualitySort)


    def displayrunVoiceActivityDetectionmodal(self,useRange=False,rangeStart=None,rangeEnd=None):
      voiceModal = VoiceActivityDetectorModal(master=self,controller=self)
      voiceModal.mainloop()

    def runVoiceActivityDetection(self,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,minZcr,maxZcr):
      self.controller.runVoiceActivityDetection(sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,minZcr,maxZcr)

    def startScreencap(self,captureType='gdigrab'):
      windowRef=self
      windowRef.cliprunScreencap=True
      windowRef.completedScreenCapName=None

      def screenCapWorker(windowRef):

        capturefilename = 'DesktopCapture_'+str(time.time())+'.mkv'
        if captureType == 'ddagrab':
            cmd = ['ffmpeg','-f', 'lavfi', '-i', 'ddagrab', '-c:v', 'h264_nvenc', '-cq', '18', capturefilename]
        elif captureType=='gdigrab_nvenc':
            cmd = ['ffmpeg','-f','gdigrab','-framerate','30','-i','desktop','-c:v','h264_nvenc','-qp','0', capturefilename]
        else:
            cmd = ['ffmpeg','-f','gdigrab','-framerate','30','-i','desktop', capturefilename]

        if hasattr(os.sys, 'winver'):
          proc = sp.Popen(cmd,creationflags=sp.CREATE_NEW_PROCESS_GROUP,stderr=sp.DEVNULL,stdout=sp.DEVNULL,bufsize=10 ** 5)
        else:
          proc = sp.Popen(cmd,stderr=sp.DEVNULL,stdout=sp.DEVNULL,bufsize=10 ** 5)

        while windowRef.cliprunScreencap:
          pollresult = proc.poll()
          print('Recording',pollresult)
          if pollresult == 1:
            break
        
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
                  windowRef.controller.loadVideoYTdlFromClipboard(substr)
                  foundUrls.append(substr)
                  print(substr)
          except Exception as e:
            print('loadClipboardUrls Exception',e)
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
         duration = simpledialog.askfloat("Create video from still images", "What should the durtation of the new video clips be in seconds?",parent=self, minvalue=0.0, maxvalue=100000.0)
      for filename in fileList:
        if filename is not None and len(filename)>0:
          writeBackPath = os.path.abspath(os.path.dirname(filename))
          self.controller.getGlobalOptions()['defaultImageFolder'] = writeBackPath
          if duration is not None:
            self.controller.loadImageFile(filename,duration)

    def displayLoopSearchModal(self,useRange=False,rangeStart=None,rangeEnd=None):
      loopSearchModal = PerfectLoopScanModal(master=self,controller=self.controller,useRange=useRange,starttime=rangeStart,endtime=rangeEnd)
      loopSearchModal.mainloop()

    def restartForNewFile(self, filename=None):
        self.frameRate = None
        self.frameTimeLineFrame.resetForNewFile()
        g = binseq(0,1000)
        self.seekpoints = [next(g)/1000 for i in range(1000)]
        try:
          self.frameVideoPlayerlabel.pack_forget()
        except:
          pass

    def getIsPlaybackStarted(self):
        return self.controller.getIsPlaybackStarted()

    def update(self,withLock=True):
        self.frameTimeLineFrame.updateCanvas(withLock=False)

    def setUiDirtyFlag(self,withLock=False,specificRID=None):
      self.frameTimeLineFrame.setUiDirtyFlag(specificRID=specificRID)
      try:
        self.frameTimeLineFrame.updateCanvas(withLock=withLock) 
      except Exception as e:
        print(e)

    def play(self):
        self.controller.play()

    def pause(self):
        self.controller.pause()

    def seekTo(self, seconds, centerAfter=False):
        self.controller.seekTo(seconds,centerAfter=centerAfter)

    def updateStatus(self, status):
        pass

    def handleMpvFPSChange(self,fps):
        self.frameRate = fps
        self.frameTimeLineFrame.updateFrameRate(fps)

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

    def setAB(self, start, end,seekAfter=True):
        return self.controller.setAB(start, end, seekAfter=seekAfter)

    def addNewSubclip(self, start, end,seekAfter=True):
        return self.controller.addNewSubclip(start, end, seekAfter=seekAfter)

    def getSurroundingInterestMarks(self,point):
       return self.controller.getSurroundingInterestMarks(point)

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

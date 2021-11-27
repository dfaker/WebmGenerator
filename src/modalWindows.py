

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import subprocess as sp
import string
import os
import threading
try:
  from .encodingUtils import cleanFilenameForFfmpeg
except:
  from encodingUtils import cleanFilenameForFfmpeg
from datetime import datetime



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


    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Download',command=self.download)
    self.downloadCmd.grid(row=6,column=0,columnspan=2,sticky='nesw')
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

    try:
      fileLimit = int(float(self.varPlayListLimit.get()))
    except Exception as e:
      print(e)
    self.controller.loadVideoYTdlCallback(url,fileLimit,username,password,useCookies,browserCookies)
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
  app = V360HeadTrackingModal()
  app.mainloop()
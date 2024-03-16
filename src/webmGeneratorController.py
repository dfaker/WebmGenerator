
import os
import sys
import logging
import time

try:
  scriptPath = os.path.dirname(os.path.abspath(__file__))
  basescriptPath = os.path.split(scriptPath)[0]
  scriptPath_frozen = os.path.dirname(os.path.abspath(sys.executable))
  os.environ["PATH"] = scriptPath + os.pathsep + scriptPath_frozen + os.pathsep + os.environ["PATH"]
  print(scriptPath)
  print(scriptPath_frozen)

  
  os.add_dll_directory(basescriptPath)
  os.add_dll_directory(scriptPath)
  os.add_dll_directory(scriptPath_frozen)
except AttributeError as e:
  print(e)
except Exception as e:
  logging.error("scriptPath Exception",exc_info=e)

os.environ["FREI0R_PATH"] = os.path.abspath(os.path.join('src','frei0r-1'))


from tkinter import Tk

try:
  from tkinterdnd2 import Tk as TkinterDnDTk
  from tkinterdnd2 import DND_FILES,DND_TEXT,CF_UNICODETEXT,CF_TEXT
except Exception as e:
  print(e)

import json
import mimetypes
import random

from .cutselectionUi import CutselectionUi
from .filterSelectionUi import FilterSelectionUi
from .mergeSelectionUi import MergeSelectionUi
from .composeUi import ComposeUi
from .webmGeneratorUi import WebmGeneratorUi


from .cutselectionController import CutselectionController
from .filterSelectionController import FilterSelectionController
from .mergeSelectionController import MergeSelectionController
from .composeController import ComposeController


from .videoManager   import VideoManager
from .ffmpegService import FFmpegService  
from .youtubeDLService import YTDLService
from .faceDetectionService import FaceDetectionService
from .voiceActivityService import VoiceActivityService

class WebmGeneratorController:
  
  def __init__(self,initialFiles):

    self.configFileName = 'configuration.json'
    self.globalOptions = {
      "statsWorkers":1,
      "encodeWorkers":1,
      "imageWorkers":2,
      "encoderStageThreads":4,
      "maxSizeOptimizationRetries":6,
      "generateRIDHoverPreviews":False,
      "passCudaFlags":False,
      "tempFolder":'tempVideoFiles',
      "tempDownloadFolder":'tempDownloadedVideoFiles',
      "defaultAutosaveFilename":'autosave.webgproj',
      "titleMetadataSuffix":' WmG',
      "startFullscreen":False,
      "darkMode":False,
      "disableSubtitlesInPlayers":True,
      "quickFilters":"",

      "useNewCrossfade":True,
      "allowableTargetSizeUnderrun":0.15,
      "allowEarlyExitIfUndersized":True,

      "nvEncIntermediateFiles":True,
      "alwaysForcenvEncIntermediateFiles":False,

      "generateTimelineThumbnails":True,
      "perClipSpeedAdjustment":False,
      "defaultPSNRWidthReductionFactor":0.05,

      "loadRelativeCopyOnFileNotExists":False,
      "clampSeeksToFPS":False,

      "initialBr":16777216,
      "maxEncodeAttemptsGif":10,
      "maxEncodeAttempts":6,
      'vp8lagInFrames':25,
      'mp4NvencTuneParam':'hq',
      'mp4NvencPresetParam':'hq',
      'mp4Libx264TuneParam':'slower',

      "cutsTabPlayerBackgroundColour":"#282828",
      "filtersTabPlayerBackgroundColour":"#282828",
      "autoLoadLastAutosave":False,
      "deleteDownloadsAtExit":False,
      "embedSequencePlanner":True,

      'askToShuffleLoadedFiles':False,

      'autoResumeAfterSeek':True,

      "downloadNameFormat":'%(title)s-%(id)s.%(uploader,creator,channel)s.{passNumber}.%(ext)s',
      "defaultMinterpolateFlags":"mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1:scd=fdiff:fps=30",
      "defaultProfile":"None",
      "defaultPostProcessingFilter":"None",
      
      "defaultSliceLength":30.0,
      "defaultTargetLength":60.0,
      "defaultTrimLength":0.0,
      "defaultDragOffset":0.1,

      "defaultVideoFolder":".",
      "defaultImageFolder":".",
      "defaultAudioFolder":".",
      "defaultFontFolder":".",
      "defaultSubtitleFolder":".",

      "loopNudgeLimit1":10,
      "loopNudgeLimit2":25,
      
      "loopSearchLower1":2,
      "loopSearchUpper1":3,
      
      "loopSearchLower2":3,
      "loopSearchUpper2":6,

      "seekSpeedNormal":1.0,
      "seekSpeedFast":5.0,
      "seekSpeedSlow":0.1,

      "initialseekpc":0,
    }

    if os.path.exists(self.configFileName) and os.path.isfile(self.configFileName):
      try:
        tempConfig = json.loads(open(self.configFileName,'r').read())
      except Exception as e:
        tempConfig = {}


      for key in self.globalOptions.keys():
        try:
          if type(self.globalOptions.get(key)) == bool:
            self.globalOptions[key] = bool(tempConfig.get(key,self.globalOptions[key]))
          elif type(self.globalOptions.get(key)) == float:
            self.globalOptions[key] = float(tempConfig.get(key,self.globalOptions[key]))
          elif type(self.globalOptions.get(key)) == int:
            self.globalOptions[key] = int(tempConfig.get(key,self.globalOptions[key]))
          else:
            self.globalOptions[key] = str(tempConfig.get(key,self.globalOptions[key]))
        except Exception as e:
          logging.error("WebmGeneratorController __init__ Exception",exc_info=e)

    open(self.configFileName,'w').write(json.dumps(self.globalOptions,indent=1))

    self.parallelVideoJobs    = self.globalOptions.get("parallelVideoJobs",3)
    self.statsWorkers         = self.globalOptions.get("statsWorkers",1)
    self.encodeWorkers        = self.globalOptions.get("encodeWorkers",1)
    self.imageWorkers         = self.globalOptions.get("imageWorkers",2)
    self.defaultProfile       = self.globalOptions.get("defaultProfile","None")
    self.passCudaFlags        = self.globalOptions.get('passCudaFlags', False) == True
    self.tempFolder           = self.globalOptions.get('tempFolder', 'tempVideoFiles')
    self.tempDownloadFolder   = self.globalOptions.get('tempDownloadFolder', 'tempDownloadedVideoFiles') 
    self.autosaveFilename     = self.globalOptions.get('defaultAutosaveFilename', 'autosave.webgproj') 
    self.lastSaveFile=None
    self.shutdown = False
    self.abortLoad = False

    projectToLoad = None

    self.webmMegeneratorUi = None

    if len(initialFiles)==1 and initialFiles[0].upper().strip().endswith('.WEBGPROJ'):
      projectToLoad = initialFiles[0]
      initialFiles=[]

    self.startPoint=0
    if len(initialFiles) == 2:
        try:
            self.startPoint = float(initialFiles[-1].strip())
        except:
            pass

    self.initialFiles = self.cleanInitialFiles(initialFiles)
    
    try:
      self.root = TkinterDnDTk()
      self.root.drop_target_register(DND_FILES)
      self.root.drop_target_register(DND_TEXT)

      self.root.dnd_bind('<<Drop>>',self.loadDrop)

      self.root.dnd_bind('<<DropEnter>>',self.enterDrop)
      self.root.dnd_bind('<<DropLeave>>',self.leaveDrop)


    except Exception as e:
      self.root = Tk()
      print(e)

    
    self.keyQueue=[]
    self.root.bind_all("<Key>", self.globalKeyCallback)

    self.root.protocol("WM_DELETE_WINDOW", self.close_ui)

    self.webmMegeneratorUi = WebmGeneratorUi(self,self.root)

    self.faceDetectionService = FaceDetectionService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus,
                                                     globalOptions=self.globalOptions)

    self.cutselectionUi     = CutselectionUi(self.root,globalOptions=self.globalOptions)
    self.filterSselectionUi = FilterSelectionUi(self.root,globalOptions=self.globalOptions,enableFaceDetection=self.faceDetectionService.faceDetectEnabled())
    self.composeUi   = ComposeUi(self.root,defaultProfile=self.defaultProfile,globalOptions=self.globalOptions)
    self.mergeSelectionUi   = MergeSelectionUi(self.root,defaultProfile=self.defaultProfile,globalOptions=self.globalOptions)

    self.webmMegeneratorUi.addPane(self.cutselectionUi,'Cuts')
    self.webmMegeneratorUi.addPane(self.filterSselectionUi,'Filters')
    #self.webmMegeneratorUi.addPane(self.composeUi,'Compose')
    self.webmMegeneratorUi.addPane(self.mergeSelectionUi,'Merge')

    self.videoManager  = VideoManager(globalOptions=self.globalOptions)
    
    self.ffmpegService = FFmpegService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus,
                                       imageWorkerCount=self.imageWorkers,
                                       encodeWorkerCount=self.encodeWorkers,
                                       statsWorkerCount=self.statsWorkers,
                                       globalOptions=self.globalOptions)

    self.ytdlService   = YTDLService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus,
                                     globalOptions=self.globalOptions)
    self.voiceActivityService = VoiceActivityService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus,
                                     globalOptions=self.globalOptions)



    self.cutselectionController = CutselectionController(self.cutselectionUi,
                                                         self.initialFiles,
                                                         self.videoManager,
                                                         self.ffmpegService,
                                                         self.ytdlService,
                                                         self.voiceActivityService,
                                                         self,
                                                         self.globalOptions,
                                                         self.startPoint)
    print('cutselectionController loaded')

    self.filterSelectionController = FilterSelectionController(self,
                                                               self.filterSselectionUi,
                                                               self.videoManager,
                                                               self.ffmpegService,
                                                               self.faceDetectionService,
                                                               self.globalOptions)
    print('filterSelectionController loaded')

    self.composeController = ComposeController(self.composeUi,
                                                             self.videoManager,
                                                             self.ffmpegService,
                                                             self.filterSelectionController,                                                             
                                                             self.globalOptions
                                                             )
    print('composeController loaded')


    self.mergeSelectionController = MergeSelectionController(self.mergeSelectionUi,
                                                             self.videoManager,
                                                             self.ffmpegService,
                                                             self.filterSelectionController,
                                                             self.cutselectionController,
                                                             self,
                                                             self.globalOptions
                                                             )
    print('mergeSelectionController loaded')

    self.recentlyPlayed = []
    self.recentProjects = []
    self.autoConvert = False

    try:
        for line in open('recentlyPlayed.pl','r').readlines():
            self.recentlyPlayed.append(line.strip())
    except Exception as e:
        print(e)

    try:
        for line in open('recentProjects.pl','r').readlines():
            self.recentProjects.append(line.strip())
    except Exception as e:
        print(e)
    

    self.webmMegeneratorUi.updateRecentlyPlayed()

    self.webmMegeneratorUi.updateRecentProjects()

    if os.path.exists(self.autosaveFilename) and len(self.initialFiles)==0:
      lastSaveData = newSaveData = None
      try:
        lastSaveData = json.loads(open(self.autosaveFilename,'r').read())
        newSaveData  = self.getSaveData()
        if self.globalOptions['autoLoadLastAutosave']:
          self.loadAutoSave()
      except Exception as e:
        logging.error("Load last save Exception",exc_info=e)

    if projectToLoad is not None:
      self.openProject(projectToLoad)

    self.plannerFrameEmebeded=False
    self.dropsToIgnore = set()

  def jumpToTab(self,tabInd):
    self.webmMegeneratorUi.switchTab(1)

  def showSlicePlanner(self):
    self.cutselectionUi.showSlicePlanner()


  def logProject(self,fn):
    if not os.path.exists(fn):
        return

    try:
        self.recentProjects.remove(fn)
    except Exception as e:
        pass
    self.recentProjects.insert(0,fn)
    self.recentProjects = self.recentProjects[:20]

    self.webmMegeneratorUi.updateRecentProjects()

  def logPlayback(self, fn):
    if not os.path.exists(fn):
        return
    try:
        self.recentlyPlayed.remove(fn)
    except Exception as e:
        pass
    self.recentlyPlayed.insert(0,fn)
    self.recentlyPlayed = self.recentlyPlayed[:20]

    self.webmMegeneratorUi.updateRecentlyPlayed()

    self.requestAutoconvert()

  def requestAutoconvert(self):
    if self.autoConvert:
        self.mergeSelectionController.autoConvert()

  def getRecentProjects(self):
    return self.recentProjects

  def getRecentlyPlayed(self):
    return self.recentlyPlayed

  def showSequencePreview(self):
    
    self.cutselectionUi.forgetPlannerFrame()

    if self.globalOptions.get('embedSequencePlanner',False):
      self.plannerFrameEmebeded = not self.plannerFrameEmebeded
      if self.plannerFrameEmebeded:
        self.mergeSelectionUi.previewSequencetimings(uiParent=self.cutselectionUi.getPlannerFrame())
      else:
        self.mergeSelectionUi.destroyPlannerModal()
    else:
      self.mergeSelectionUi.previewSequencetimings(uiParent=None)

  def setIgnoreDrop(self,path):
    self.dropsToIgnore.add(path)



  def listdropFiles(self,strdropfiles):
    dropfiles = []
    bopen = 0
    lastchar = ' '
    for c in strdropfiles:
      
      if c == '{' and lastchar != '\\' and bopen == 0:
        bopen=1
        dropfiles.append('')
      elif c == '}' and bopen==1 and lastchar != '\\':
        bopen=0
        dropfiles.append('')
      elif c == ' ' and not bopen and lastchar != '\\':
        dropfiles.append('')
      else:

        if c == '{':
          bopen+=1
        elif c == '}':
          bopen-=1

        if len(dropfiles)==0:
          dropfiles.append('')
        if lastchar == '\\':
          dropfiles[-1] = dropfiles[-1][:-1]+c
        else:
          dropfiles[-1] = dropfiles[-1]+c
      lastchar=c

    return [x for x in dropfiles if x.strip() != '']

  def enterDrop(self,drop):
    try:
        dropfiles = self.listdropFiles(drop.data)
        if len(dropfiles) > 1 or (len(dropfiles) ==1 and os.path.isdir(dropfiles[0]) ):
            self.webmMegeneratorUi.showDrop(len(dropfiles))
    except Exception as e:
        print(e)
        self.webmMegeneratorUi.hideDrop()

  def registerComplete(self,filename,clip=None):

    label = os.path.basename(filename)
    filename = os.path.abspath(filename)
    img=None
    if clip is not None:
        img = clip.getpreviewImg()

    self.webmMegeneratorUi.registerComplete(label,filename,img=img)

  def leaveDrop(self,drop):
    self.webmMegeneratorUi.hideDrop()

  def toggleCompletedFrame(self):
    self.cutselectionUi.toggleCompletedFrame()

  def setAutoConvert(self,state):
    self.autoConvert = state

  def loadDrop(self,drop):
    print(drop.type)
    if drop.type in (CF_UNICODETEXT,CF_TEXT):
      self.cutselectionController.loadVideoYTdlFromClipboard(drop.data)
      return

    if drop.data in self.dropsToIgnore:
        return

    print(drop.data)
    dropfiles = self.listdropFiles(drop.data)
    
    print(dropfiles)

    if len(dropfiles)>0:

      if self.globalOptions.get('askToShuffleLoadedFiles',False):
        if len(dropfiles)>1:
          response = self.cutselectionUi.confirmWithMessage('Shuffle files?','Do you want to shuffle the order of the dropped files?',icon='warning')
          if response=='yes':
            random.shuffle(dropfiles)

      loadOptions={}
      if 'ctrl' in drop.modifiers:
        print('getFileLoadOptions enter')
        loadOptions = self.webmMegeneratorUi.getFileLoadOptions()
        print('getFileLoadOptions exit')

      self.webmMegeneratorUi.setLoadLabel('Loading files...')

      def doAsyncLoad(dropfiles,loadOptions):
        print('doAsyncLoad',dropfiles,loadOptions )

        self.cutselectionController.loadFiles(self.cleanInitialFiles(dropfiles,loadOptions=loadOptions))
        self.cutselectionUi.clearVideoMousePress()
        self.webmMegeneratorUi.hideDrop()

      self.root.after(0,doAsyncLoad,dropfiles,loadOptions)
    else:
      self.cutselectionUi.clearVideoMousePress()
      self.webmMegeneratorUi.hideDrop()


  def updateGlobalOptions(self,changedOptions):
    print(changedOptions)
    for k,v in changedOptions.items():
      self.globalOptions[k]=v
    open(self.configFileName,'w').write(json.dumps(self.globalOptions,indent=1))


  def takeScreenshotToFile(self,selectedTab):
    if selectedTab == '.!cutselectionui':
      print('Cut Selection screenshot')
      self.cutselectionController.takeScreenshotToFile(self.tempFolder,includes='video')
    elif selectedTab == '.!filterselectionui':
      print('Filter screenshot')
      self.filterSelectionController.takeScreenshotToFile(self.tempFolder,includes='video')

  def globalKeyCallback(self,evt):
    ctrl  = (evt.state & 0x4) != 0
    shift = (evt.state & 0x1) != 0
    
    if ctrl:
      if evt.keysym=='q':
        self.root.destroy()
      elif evt.keysym=='n':
        self.webmMegeneratorUi.newProject()
      elif evt.keysym=='b':
        self.webmMegeneratorUi.toggleBoringMode()
        self.mergeSelectionUi.toggleBoringMode(self.webmMegeneratorUi.boringMode)

    if ctrl and shift and evt.keysym == 'question':
        tabName = self.webmMegeneratorUi.getTabName()
        self.webmMegeneratorUi.toggleHelpFor(tabName)

    self.cutselectionController.handleGlobalKeyEvent(evt)

  def autoSaveExists(self):
    return os.path.exists(self.autosaveFilename)
    
  def loadAutoSave(self):
    try:
      self.openProject(self.autosaveFilename)
    except Exception as e:
      logging.error("Audoload save failed",exc_info=e)

  def getDownloadFilesCountAndsize(self):
    sz = 0
    count = 0
    if os.path.exists(self.tempDownloadFolder):
      for f in os.listdir(self.tempDownloadFolder):
        sz+=os.stat(os.path.join(self.tempDownloadFolder,f)).st_size
        count+=1
    return count,sz

  def clearDownloadedfiles(self):
    if os.path.exists(self.tempDownloadFolder):
      for f in os.listdir(self.tempDownloadFolder):
        try: 
          os.remove(os.path.join(self.tempDownloadFolder,f))
          self.cutselectionController.removefileIfLoaded(os.path.join(self.tempDownloadFolder,f))
        except Exception as e:
          print(e)

  def runFullLoopSearch(self):
    self.cutselectionController.runFullLoopSearch()

  def runSceneChangeDetection(self):
    self.cutselectionController.runSceneChangeDetection()

  def runVoiceActivityDetection(self):
    self.cutselectionController.showVoiceActivityDetectionModal()

  def runSceneChangeDetectionCuts(self):
    self.cutselectionController.runSceneChangeDetection(addCuts=True)    


  def runSceneCentreDetectionCuts(self):
    self.cutselectionController.runSceneCentreDetectionCuts(addCuts=True)    


  def scanAndAddLoudSections(self):
    self.cutselectionController.scanAndAddLoudSections()

  def cleanInitialFiles(self,files,loadOptions={}):
    finalFiles = []

    self.abortLoad=False

    sortKey    = loadOptions.get('sort','None')
    substrings = loadOptions.get('filter','')

    substrings = [x.strip().upper() for x in substrings.split() if len(x.strip())>0]

    print('cleanInitialFiles',loadOptions,substrings)

    getStats = False
    if sortKey in ['File Size ascending','File Size descending','Created date ascending','Created date descending',
                   'Modified date ascending','Modified date descending','Access date ascending','Access date descending']:
      getStats = True

    start = time.time()

    try:
      if self.webmMegeneratorUi is not None:
        self.webmMegeneratorUi.setLoadLabel('Loading files {}\n(Scanning root folder)'.format(len(finalFiles)))
    except Exception as e:
      logging.error("webmMegeneratorUi.setLoadLabel",exc_info=e)

    for f in map(os.path.normpath,files):

      if os.path.isfile(f):
        if self.shutdown or self.abortLoad:
          break
        g = mimetypes.guess_type(f)
        if g is not None and g[0] is not None and 'video' in g[0] and all([x in f.upper() for x in substrings]):
          key = None
          if getStats:
            key = os.stat(f)
          finalFiles.append((key,f))
          try:
            if abs(start - time.time()) > 0.2:
              self.webmMegeneratorUi.setLoadLabel('Loading files {}\n{}'.format(len(finalFiles),f))
              start = time.time()
          except Exception as e:
            logging.error("cleanInitialFiles filesort",exc_info=e)
      elif os.path.isdir(f):
        for r,dl,fl in os.walk(f):
          if self.shutdown or self.abortLoad:
            break
          for nf in fl:
            p = os.path.join(r,nf)
            if os.path.isfile(p):

              g = mimetypes.guess_type(p)
              if g is not None and g[0] is not None and 'video' in g[0] and all([x in p.upper() for x in substrings]):
                key = None
                if getStats:
                  key = os.stat(p)
                finalFiles.append((key,p))
                try:
                  if abs(start - time.time()) > 0.2:
                    self.webmMegeneratorUi.setLoadLabel('Loading files {}\n{}\n(Processing {})'.format(len(finalFiles),p,r))
                    start = time.time()
                except Exception as e:
                  logging.error("cleanInitialFiles dirsort",exc_info=e)

    self.abortLoad=False

    if self.shutdown:
      return []

    keyfunc = None

    sortFuncMap = {
      'Filename ascending':         (lambda x:os.path.basename(x[1]),False),
      'Filename descending':        (lambda x:os.path.basename(x[1]),True),
      'Path ascending':             (lambda x:x[1],False),
      'Path descending':            (lambda x:x[1],True),
      'File Size ascending':        (lambda x:x[0].st_size,False),
      'File Size descending':       (lambda x:x[0].st_size,True),
      'Created date ascending':     (lambda x:x[0].st_ctime,False),
      'Created date descending':    (lambda x:x[0].st_ctime,True),
      'Modified date ascending':    (lambda x:x[0].st_mtime,False),
      'Modified date descending':   (lambda x:x[0].st_mtime,True),
      'Access date ascending':      (lambda x:x[0].st_atime,False),
      'Access date descending':     (lambda x:x[0].st_atime,True)
    }

    sortFunc,reverseSort = sortFuncMap.get(sortKey,(None,None))

    if sortFunc is not None:
      finalFiles = sorted(finalFiles,key=sortFunc,reverse=reverseSort)

    if self.shutdown:
      return []

    return [x[1] for x in finalFiles]

  def abortCurrentLoad(self):
    self.abortLoad=True

  def newProject(self):

    self.cutselectionController.reset()
    self.videoManager.reset()
    self.lastSaveFile = None

  def openProject(self,filename):
    print('openProject',filename)
    if filename is not None:
      with open(filename,'r') as loadFile:
        saveData = json.loads(loadFile.read())

        print(saveData)

        self.newProject()
        self.lastSaveFile = filename
        for loadMethod in [self.cutselectionController.loadStateFromSave,
                           self.videoManager.loadStateFromSave,
                           self.filterSelectionController.loadStateFromSave]:
          try:
            loadMethod(saveData)
          except Exception as e:
            print(e)

  def fillGapsBetweenSublcips(self):
    self.cutselectionController.fillGapsBetweenSublcips()

  def splitClipIntoNEqualSections(self):
    self.cutselectionController.splitClipIntoNEqualSections()

  def splitClipIntoSectionsOfLengthN(self):
    self.cutselectionController.splitClipIntoSectionsOfLengthN()

  def generateSoundWaveBackgrounds(self,style='GENERAL'):
    self.cutselectionController.generateSoundWaveBackgrounds(style=style)

  def clearAllSubclipsOnCurrentClip(self):
    self.cutselectionController.clearAllSubclipsOnCurrentClip()

  def clearAllInterestMarksOnCurrentClip(self):
    self.cutselectionController.clearAllInterestMarksOnCurrentClip()

  def addSubclipByTextRange(self):
    self.cutselectionController.addSubclipByTextRange()

  def getSaveData(self):
    saveData = {}
    for saveMethod in [self.cutselectionController.getStateForSave,
                       self.videoManager.getStateForSave,
                       self.filterSelectionController.getStateForSave]:
      try:
        saveData.update(saveMethod())
      except Exception as e:
        print(e)
    return saveData

  def saveProject(self,filename):
    if filename is not None:
      try:
        saveData = self.getSaveData()
        with open(filename,'w') as saveFile:
          saveFile.write(json.dumps(saveData))
          self.lastSaveFile = filename
      except Exception as e:
        logging.error("saveProject save failed",exc_info=e)

  def toggleYTPreview(self,toggleValue):
    self.ytdlService.togglePreview(toggleValue)

  def splitStream(self):
    self.ytdlService.splitStream()

  def updateYoutubeDl(self):
    self.ytdlService.update()

  def cancelCurrentYoutubeDl(self):
    self.ytdlService.cancelCurrentYoutubeDl()
    self.ffmpegService.cancelCurrentScans()

  def close_ui(self):
    if self.lastSaveFile is not None and self.lastSaveFile != self.autosaveFilename:
      lastSaveData = json.loads(open(self.lastSaveFile,'r').read())
      newSaveData  = self.getSaveData()
      if newSaveData != lastSaveData:
        response = self.cutselectionUi.confirmWithMessage('Changes since last save','You have made changes since your last save, do you want to save current project to \'{}\'?'.format(self.lastSaveFile),icon='warning',allowCancel=True)
        print(response)
        if response == 'yes':
          self.saveProject(self.lastSaveFile)
          self.saveProject(self.autosaveFilename)
        if response is None:
            return
    else:
      self.saveProject(self.autosaveFilename)

    try:
        if len(self.recentlyPlayed) >0:
            with open('recentlyPlayed.pl','w') as rp:
                for line in self.recentlyPlayed:
                    rp.write(line+'\n')
    except Exception as e:
        logging.error("RecentlyPlayed.pl Played load Exception",exc_info=e)

    try:
        if len(self.recentProjects) >0:
            with open('recentProjects.pl','w') as rp:
                for line in self.recentProjects:
                    rp.write(line+'\n')
    except Exception as e:
        logging.error("recentProjects.pl Played load Exception",exc_info=e)



    self.shutdown = True
    self.cutselectionController.close_ui()
    logging.debug('self.cutselectionController.close_ui()')
    logging.debug('self.ffmpegService.cancelAllEncodeRequests()')
    self.ffmpegService.cancelAllEncodeRequests()
    logging.debug('self.cutselectionController.close_ui()')
    self.filterSelectionController.close_ui()
    logging.debug('self.filterSelectionController.close_ui()')
    self.mergeSelectionController.close_ui()
    logging.debug('self.mergeSelectionController.close_ui()')
    self.webmMegeneratorUi.close_ui()

    try:
      self.root.destroy()
    except Exception as e:
      logging.error("root.destroy() Exception",exc_info=e)

    print('temp clean up start')
    if os.path.exists(self.tempFolder):
      for f in os.listdir(self.tempFolder):
        try:
          os.remove(os.path.join(self.tempFolder,f))
        except Exception as e:
          logging.error("Temp clean up Exception",exc_info=e)
    print('temp clean up end')

    print('download clean up start')
    if os.path.exists(self.tempDownloadFolder):
      for f in os.listdir(self.tempDownloadFolder):
        if f.endswith('.part') or self.globalOptions.get('deleteDownloadsAtExit',False):
          try: 
            os.remove(os.path.join(self.tempDownloadFolder,f))
          except Exception as e:
            logging.error("Download clean up Exception",exc_info=e)
    print('download clean up end')

    
  def __call__(self):
    self.webmMegeneratorUi.run()
    logging.debug('EXIT')

if __name__ == '__main__':
  import webmGenerator
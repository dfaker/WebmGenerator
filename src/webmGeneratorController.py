
import os
import sys
import logging

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

from tkinter import Tk
import json
import mimetypes

from .cutselectionUi import CutselectionUi
from .filterSelectionUi import FilterSelectionUi
from .mergeSelectionUi import MergeSelectionUi
from .webmGeneratorUi import WebmGeneratorUi
    
from .cutselectionController import CutselectionController
from .filterSelectionController import FilterSelectionController
from .mergeSelectionController import MergeSelectionController

from .videoManager   import VideoManager
from .ffmpegService import FFmpegService  
from .youtubeDLService import YTDLService

class WebmGeneratorController:
  
  def __init__(self,initialFiles):

    self.configFileName = 'configuration.json'
    self.globalOptions = {
      "statsWorkers":1,
      "encodeWorkers":1,
      "imageWorkers":2,
      "encoderStageThreads":4,
      "maxSizeOptimizationRetries":6,
      "passCudaFlags":False,
      "tempFolder":'tempVideoFiles',
      "tempDownloadFolder":'tempDownloadedVideoFiles',
      "defaultAutosaveFilename":'autosave.webgproj',
      "defaultProfile":"None"
    }

    if os.path.exists(self.configFileName) and os.path.isfile(self.configFileName):
      tempConfig = json.loads(open(self.configFileName,'r').read())

      for key in self.globalOptions.keys():
        try:
          if type(self.globalOptions.get(key)) == int:
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


    self.initialFiles = self.cleanInitialFiles(initialFiles)
    self.root = Tk()
    
    self.root.protocol("WM_DELETE_WINDOW", self.close_ui)

    self.webmMegeneratorUi = WebmGeneratorUi(self,self.root)

    self.cutselectionUi     = CutselectionUi(self.root)
    self.filterSselectionUi = FilterSelectionUi(self.root)
    self.mergeSelectionUi   = MergeSelectionUi(self.root,defaultProfile=self.defaultProfile)

    self.webmMegeneratorUi.addPane(self.cutselectionUi,'Cuts')
    self.webmMegeneratorUi.addPane(self.filterSselectionUi,'Filters')
    self.webmMegeneratorUi.addPane(self.mergeSelectionUi,'Merge')

    self.videoManager  = VideoManager()
    self.ffmpegService = FFmpegService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus,imageWorkerCount=self.imageWorkers,encodeWorkerCount=self.encodeWorkers,statsWorkerCount=self.statsWorkers)
    self.ytdlService   = YTDLService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus)

    self.cutselectionController = CutselectionController(self.cutselectionUi,
                                                         self.initialFiles,
                                                         self.videoManager,
                                                         self.ffmpegService,
                                                         self.ytdlService)

    self.filterSelectionController = FilterSelectionController(self.filterSselectionUi,
                                                         self.videoManager,
                                                         self.ffmpegService)

    self.mergeSelectionController = MergeSelectionController(self.mergeSelectionUi,
                                                             self.videoManager,
                                                             self.ffmpegService,
                                                             self.filterSelectionController
                                                             )

    if os.path.exists(self.autosaveFilename) and len(self.initialFiles)==0:
      lastSaveData = newSaveData = None
      try:
        lastSaveData = json.loads(open(self.autosaveFilename,'r').read())
        newSaveData  = self.getSaveData()
      except Exception as e:
        logging.error("Load last save Exception",exc_info=e)

  def autoSaveExists(self):
    return os.path.exists(self.autosaveFilename)
    
  def loadAutoSave(self):
    try:
      self.openProject(self.autosaveFilename)
    except Exception as e:
      logging.error("Audoload save failed",exc_info=e)

  def runSceneChangeDetection(self):
    self.cutselectionController.runSceneChangeDetection()

  def cleanInitialFiles(self,files):
    finalFiles = []
    for f in files:
      print('Initial file',f)
      if os.path.isfile(f):
        g = mimetypes.guess_type(f)
        if g is not None and g[0] is not None and 'video' in g[0]:
          finalFiles.append(f)
      elif os.path.isdir(f):
        for r,dl,fl in os.walk(f):
          for nf in fl:
            p = os.path.join(r,nf)
            if os.path.isfile(p):
              g = mimetypes.guess_type(p)
              if g is not None and g[0] is not None and 'video' in g[0]:
                finalFiles.append(p)
    return finalFiles


  def newProject(self):

    self.cutselectionController.reset()
    self.videoManager.reset()
    self.lastSaveFile = None

  def openProject(self,filename):
    if filename is not None:
      with open(filename,'r') as loadFile:
        saveData = json.loads(loadFile.read())
        self.newProject()
        self.lastSaveFile = filename
        self.cutselectionController.loadStateFromSave(saveData)
        self.videoManager.loadStateFromSave(saveData)


  def splitClipIntoNEqualSections(self):
    self.cutselectionController.splitClipIntoNEqualSections()

  def splitClipIntoSectionsOfLengthN(self):
    self.cutselectionController.splitClipIntoSectionsOfLengthN()

  def generateSoundWaveBackgrounds(self):
    self.cutselectionController.generateSoundWaveBackgrounds()

  def clearAllSubclipsOnCurrentClip(self):
    self.cutselectionController.clearAllSubclipsOnCurrentClip()

  def addSubclipByTextRange(self):
    self.cutselectionController.addSubclipByTextRange()

  def getSaveData(self):
    saveData = {}
    saveData.update(self.cutselectionController.getStateForSave())
    saveData.update(self.videoManager.getStateForSave())
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

  def close_ui(self):
    if self.lastSaveFile is not None and self.lastSaveFile != self.autosaveFilename:
      lastSaveData = json.loads(open(self.lastSaveFile,'r').read())
      newSaveData  = self.getSaveData()
      if newSaveData != lastSaveData:
        response = self.cutselectionUi.confirmWithMessage('Changes since last save','You have made changes since your last save, do you want to save current project to \'{}\'?'.format(self.lastSaveFile),icon='warning')
        if response == 'yes':
          self.saveProject(self.lastSaveFile)
          self.saveProject(self.autosaveFilename)
    else:
      self.saveProject(self.autosaveFilename)

    logging.debug('self.cutselectionController.close_ui()')
    self.cutselectionController.close_ui()
    logging.debug('self.cutselectionController.close_ui()')
    self.filterSelectionController.close_ui()
    logging.debug('self.filterSelectionController.close_ui()')
    self.webmMegeneratorUi.close_ui()


    try:
      self.root.destroy()
    except Exception as e:
      logging.error("root.destroy() Exception",exc_info=e)

    if os.path.exists(self.tempFolder):
      for f in os.listdir(self.tempFolder):
        try:
          os.remove(os.path.join(self.tempFolder,f))
        except Exception as e:
          print(e)

    if os.path.exists(self.tempDownloadFolder):
      for f in os.listdir(self.tempDownloadFolder):
        if f.endswith('.part'):
          try: 
            os.remove(os.path.join(self.tempDownloadFolder,f))
          except Exception as e:
            print(e)

  def __call__(self):
    self.webmMegeneratorUi.run()
    logging.debug('EXIT')

if __name__ == '__main__':
  import webmGenerator
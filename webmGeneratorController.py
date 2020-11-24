
import os
import sys

try:
  scriptPath = os.path.dirname(os.path.abspath(__file__))
  scriptPath_frozen = os.path.dirname(os.path.abspath(sys.executable))
  os.environ["PATH"] = scriptPath + os.pathsep + scriptPath_frozen + os.pathsep + os.environ["PATH"]
  os.add_dll_directory(scriptPath)
  os.add_dll_directory(scriptPath_frozen)
except AttributeError:
  pass
except Exception as e:
  print(e,scriptPath)

from tkinter import Tk
import json
import mimetypes

from cutselectionUi import CutselectionUi
from filterSelectionUi import FilterSelectionUi
from mergeSelectionUi import MergeSelectionUi
from webmGeneratorUi import WebmGeneratorUi
    
from cutselectionController import CutselectionController
from filterSelectionController import FilterSelectionController
from mergeSelectionController import MergeSelectionController

from videoManager   import VideoManager
from ffmpegService import FFmpegService  
from youtubeDLService import YTDLService

class WebmGeneratorController:
  
  def __init__(self,initialFiles):

    self.tempFolder='tempVideoFiles'
    self.tempDownloadFolder='tempDownloadedVideoFiles'
    self.lastSaveFile=None
    self.autosaveFilename = 'autosave.webgproj'

    self.globalOptions = {
      "parallelVideoJobs":3,
      "statsWorkers":1,
      "encodeWorkers":1,
      "tempFolder":'tempVideoFiles',
      "tempDownloadFolder":'tempDownloadedVideoFiles',
      "autosaveFilename":'autosave.webgproj',
      "defaultProfile":"None"
    }

    self.initialFiles = self.cleanInitialFiles(initialFiles+[self.tempDownloadFolder])
    self.root = Tk()
    
    self.root.protocol("WM_DELETE_WINDOW", self.close_ui)

    self.webmMegeneratorUi = WebmGeneratorUi(self,self.root)

    self.cutselectionUi     = CutselectionUi(self.root)
    self.filterSselectionUi = FilterSelectionUi(self.root)
    self.mergeSelectionUi   = MergeSelectionUi(self.root)

    self.webmMegeneratorUi.addPane(self.cutselectionUi,'Cuts')
    self.webmMegeneratorUi.addPane(self.filterSselectionUi,'Filters')
    self.webmMegeneratorUi.addPane(self.mergeSelectionUi,'Merge')

    self.videoManager  = VideoManager()
    self.ffmpegService = FFmpegService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus)
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
        print(e)

      if lastSaveData != newSaveData:
        response = self.cutselectionUi.confirmWithMessage('Load autosave from last session?','Load autosave from last session?',icon='warning')
        if response=='yes':
          try:
            self.openProject(self.autosaveFilename)
          except Exception as e:
            print('audoload save failed',e)

  def cleanInitialFiles(self,files):
    finalFiles = []
    for f in files:
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

  def getSaveData(self):
    saveData = {}
    saveData.update(self.cutselectionController.getStateForSave())
    saveData.update(self.videoManager.getStateForSave())
    return saveData  

  def saveProject(self,filename):
    if filename is not None:
      saveData = self.getSaveData()
      with open(filename,'w') as saveFile:
        saveFile.write(json.dumps(saveData))
        self.lastSaveFile = filename

  def updateYoutubeDl(self):
    self.ytdlService.update()

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

    print('self.cutselectionController.close_ui()')
    self.cutselectionController.close_ui()
    print('self.cutselectionController.close_ui()')
    self.filterSelectionController.close_ui()
    print('self.filterSelectionController.close_ui()')
    self.webmMegeneratorUi.close_ui()
    try:
      self.root.destroy()
    except Exception as e:
      print(e)

    if os.path.exists(self.tempFolder):
      for f in os.listdir(self.tempFolder):
        os.remove(os.path.join(self.tempFolder,f))

    if os.path.exists(self.tempDownloadFolder):
      for f in os.listdir(self.tempDownloadFolder):
        if f.endswith('.part'):
          os.remove(os.path.join(self.tempDownloadFolder,f))


  def __call__(self):
    self.webmMegeneratorUi.run()
    print('EXIT')

if __name__ == '__main__':
  import webmGenerator
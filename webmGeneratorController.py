
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

    self.initialFiles = self.cleanInitialFiles(initialFiles+['tempDownloadedVideoFiles'])
    self.root = Tk()
    
    self.root.protocol("WM_DELETE_WINDOW", self.close_ui)

    self.webmMegeneratorUi = WebmGeneratorUi(self,self.root)

    self.cutselectionUi = CutselectionUi(self.root)
    self.filterSselectionUi = FilterSelectionUi(self.root)
    self.mergeSelectionUi = MergeSelectionUi(self.root)

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

  def openProject(self,filename):
    if filename is not None:
      with open(filename,'r') as loadFile:
        saveData = json.loads(loadFile.read())

        self.newProject()
        
        self.cutselectionController.loadStateFromSave(saveData)
        self.videoManager.loadStateFromSave(saveData)

  def saveProject(self,filename):
    if filename is not None:
      saveData = {}
      saveData.update(self.cutselectionController.getStateForSave())
      saveData.update(self.videoManager.getStateForSave())
      with open(filename,'w') as saveFile:
        saveFile.write(json.dumps(saveData))

  def updateYoutubeDl(self):
    self.ytdlService.update()

  def close_ui(self):
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

    for f in os.listdir(self.tempFolder):
      os.remove(os.path.join(self.tempFolder,f))

  def __call__(self):
    self.webmMegeneratorUi.run()
    print('EXIT')

if __name__ == '__main__':
  import webmGenerator

from tkinter import Tk
import os

try:
  scriptPath = os.path.dirname(os.path.abspath(__file__))
  os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
  os.add_dll_directory(scriptPath)
except Exception as e:
  print(e,scriptPath)

from cutselectionUi import CutselectionUi
from filterSelectionUi import FilterSelectionUi
from mergeSelectionUi import MergeSelectionUi
from webmGeneratorUi import WebmGeneratorUi
    
from cutselectionController import CutselectionController
from filterSelectionController import FilterSelectionController
from mergeSelectionController import MergeSelectionController



from videoManager   import VideoManager
from ffmpegService import FFmpegService  

class WebmGeneratorController:
  
  def __init__(self,initialFiles):

    self.tempFolder='tempVideoFiles'

    self.initialFiles = initialFiles
    self.root = Tk()
    
    self.root.protocol("WM_DELETE_WINDOW", self.close_ui)

    self.webmMegeneratorUi = WebmGeneratorUi(self.root)

    self.cutselectionUi = CutselectionUi(self.root)
    self.filterSselectionUi = FilterSelectionUi(self.root)
    self.mergeSelectionUi = MergeSelectionUi(self.root)

    self.webmMegeneratorUi.addPane(self.cutselectionUi,'Cuts')
    self.webmMegeneratorUi.addPane(self.filterSselectionUi,'Filters')
    self.webmMegeneratorUi.addPane(self.mergeSelectionUi,'Merge')

    self.videoManager = VideoManager()
    self.ffmpegService = FFmpegService(globalStatusCallback=self.webmMegeneratorUi.updateGlobalStatus)

    self.cutselectionController = CutselectionController(self.cutselectionUi,
                                                         initialFiles,
                                                         self.videoManager,
                                                         self.ffmpegService)

    self.filterSelectionController = FilterSelectionController(self.filterSselectionUi,
                                                         self.videoManager,
                                                         self.ffmpegService)

    self.mergeSelectionController = MergeSelectionController(self.mergeSelectionUi,
                                                             self.videoManager,
                                                             self.ffmpegService,
                                                             self.filterSelectionController
                                                             )

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
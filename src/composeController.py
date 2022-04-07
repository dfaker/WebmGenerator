
import os
import json

class ComposeController:

  def __init__(self,ui,videoManager,ffmpegService,filterController,globalOptions={}):
    self.ui=ui
    self.globalOptions=globalOptions
    self.videoManager=videoManager
    self.ffmpegService=ffmpegService
    self.filterController=filterController

    self.ui.setController(self)

if __name__ == '__main__':
  import webmGenerator

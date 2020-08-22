
class MergeSelectionController:

  def __init__(self,ui,videoManager,ffmpegService,filterController):
    self.ui=ui
    self.ui.setController(self)
    self.videoManager=videoManager
    self.ffmpegService=ffmpegService
    self.filterController=filterController

  def getFilteredClips(self):
    return self.filterController.getClipsWithFilters()

  def requestPreviewFrame(self,rid,filename,timestamp,filterexp,size,callback):
    self.ffmpegService.requestPreviewFrame(rid,filename,timestamp,filterexp,size,callback)

  def encode(self,requestId,mode,seq,options,filenamePrefix,statusCallback):
    print('encode',requestId,mode,seq,options,filenamePrefix)
    self.ffmpegService.encode(requestId,mode,seq,options,filenamePrefix,statusCallback)

if __name__ == '__main__':
  import webmGenerator


import os
import json

class MergeSelectionController:

  def __init__(self,ui,videoManager,ffmpegService,filterController,cutController,controller,globalOptions={}):
    self.ui=ui
    self.globalOptions=globalOptions
    self.videoManager=videoManager
    self.ffmpegService=ffmpegService
    self.filterController=filterController
    self.cutController=cutController
    self.profileSpecPath = 'customEncodeProfiles'
    self.controller = controller
    self.maxAutoconvert = -1

    self.stdProfileSpecs = [ 
      {'name':'None','editable':False},
      {'name':'Default max quality mp4','editable':False,'outputFormat':'mp4:x264','maximumSize':'0.0'},
      {'name':'Sub 4M max quality vp8 webm','editable':False,'outputFormat':'webm:VP8','maximumSize':'4.0'},
      {'name':'Sub 100M max quality mp4','editable':False,'outputFormat':'mp4:x264','maximumSize':'100.0'}
    ]

    self.customProfileSpecs = [
      {'name':'Sub 8M max quality mp4','editable':False,'outputFormat':'mp4:x264','maximumSize':'8.0'}
    ]

    if os.path.exists(self.profileSpecPath):
      for profileFile in os.listdir(self.profileSpecPath):
        profileFilename = os.path.join(self.profileSpecPath,profileFile)
        if os.path.exists(profileFilename) and os.path.isfile(profileFilename):
          try:
            profile = json.loads( open(profileFilename,'r').read() )
            profile['filename'] = profileFile
            profile['editable'] = True
            profileName = profile['name']
            profile['name'] = profileName 
            self.customProfileSpecs.append( profile )
          except Exception as e:
            print('Custom profile load error',profileFilename,e)

    self.ui.setController(self)
    self.videoManager.addSubclipChangeCallback(self.ui.videoSubclipDurationChangeCallback)

  def autoConvert(self):
    self.ui.updateSelectableVideos()
    self.ui.clearSequence(includeProgress=False)
    self.maxAutoconvert = self.ui.addAllClipsInTimelineOrder(minrid=self.maxAutoconvert,clearProgress=False)
    self.ui.encodeCurrent()
    self.ui.clearSequence(includeProgress=False)

  def setIgnoreDrop(self,path):
    self.controller.setIgnoreDrop(path)

  def setDragDur(self,dur):
    self.cutController.setDragDur(dur)

  def broadcastModalFocus(self):
    self.cutController.playingModalGotFocus()

  def broadcastModalLoseFocus(self):
    self.cutController.playingModalLostFocus()    

  def jumpToFilterByRid(self,rid):
    self.filterController.jumpToFilterByRid(rid)

  def updateSubclipBoundry(self,subclip,originalts,ts,pos,towardsMiddle=True):

    filename,s,e = self.videoManager.getDetailsForRangeId(subclip.rid)

    if pos == 's':
      newPosSeconds = s-(originalts-ts)
    else:
      newPosSeconds = e-(originalts-ts)

    newPosSeconds = max(0,newPosSeconds)

    if towardsMiddle:
      halfDiff = (originalts-ts)/2
      if pos == 's':
        self.videoManager.updatePointForClip(filename,subclip.rid,'s',s-halfDiff)
        self.videoManager.updatePointForClip(filename,subclip.rid,'e',e+halfDiff)
      elif pos == 'e':
        self.videoManager.updatePointForClip(filename,subclip.rid,'s',s+halfDiff)
        self.videoManager.updatePointForClip(filename,subclip.rid,'e',e-halfDiff)
    else:  
      self.videoManager.updatePointForClip(filename,subclip.rid,pos,newPosSeconds)

  def synchroniseCutController(self,rid,startoffset,forceTabJump=False):
    self.cutController.jumpToRidAndOffset(rid,startoffset,forceTabJump)

  def getDefaultPostFilter(self):
    return self.globalOptions.get('defaultPostProcessingFilter','')

  def getFilteredClips(self):
    return self.filterController.getClipsWithFilters()

  def requestPreviewFrame(self,rid,filename,timestamp,filterexp,size,callback):
    self.ffmpegService.requestPreviewFrame(rid,filename,timestamp,filterexp,size,callback)

  def encode(self,requestId,mode,seq,options,filenamePrefix,statusCallback):
    print('encode',requestId,mode,seq,options,filenamePrefix)
    self.ffmpegService.encode(requestId,mode,seq,options,filenamePrefix,statusCallback)

  def cancelEncodeRequest(self,requestId):
    self.ffmpegService.cancelEncodeRequest(requestId)

  def deleteCustomProfile(self,profileName):
    return ''

  def saveCustomProfile(self,profile):
    os.path.exists(self.profileSpecPath) or os.mkdir(self.profileSpecPath)
    return ''

  def getProfiles(self):
    return self.stdProfileSpecs + self.customProfileSpecs

  def close_ui(self):
    try:
      self.ui.close_ui()
    except Exception as e:
      print(e)

if __name__ == '__main__':
  import webmGenerator

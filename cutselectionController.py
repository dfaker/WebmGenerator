
import mpv
import math
import os
import random

import logging


class CutselectionController:

  def __init__(self,ui,initialFiles,videoManager,ffmpegService,ytdlService):
    self.ui = ui
    self.ui.setController(self)
    self.videoManager = videoManager
    self.ffmpegService = ffmpegService
    self.ytdlService   = ytdlService

    self.loopMode='Loop current'

    self.initialisePlayer()
    self.files=[]
    self.currentLoopCycleStart = None
    self.currentLoopCycleEnd   = None
    self.removeAllDownloads    = False
    self.removeDownloadRun     = 0

    self.currentlyPlayingFileName=None
    self.currentTimePos=None
    self.currentTotalDuration=None
    self.currentLoop_a=None
    self.currentLoop_b=None

    """
    if len(initialFiles)>1:
      response = self.ui.confirmWithMessage('Shuffle files?','Do you want to shuffle the intially loaded files?',icon='warning')
      if response=='yes':
        random.shuffle(initialFiles)
    """
    
    self.ui.setinitialFocus()

    self.loadFiles(initialFiles)
    

  def updateLoopMode(self,loopMode):
    self.loopMode=loopMode
    self.currentLoop_a=None
    self.currentLoop_b=None
    if self.loopMode == 'Loop all':
      self.player.ab_loop_a=-1
      self.player.ab_loop_b=-1


  def checkLoopCycleJump(self):
    if self.loopMode == 'Loop all':
      if (self.currentLoopCycleStart is None or
          self.currentLoopCycleEnd is None or 
          self.currentTimePos < self.currentLoopCycleStart or
          self.currentTimePos > self.currentLoopCycleEnd):
        subclipranges = self.videoManager.getRangesForClip(self.currentlyPlayingFileName)
        if len(subclipranges)>0:
          subclipranges = sorted(subclipranges,key=lambda x:x[1][1])
          jumpRangeFound=False
          for i,(s,e) in subclipranges:
            if e>self.currentTimePos:
              self.currentLoopCycleStart=s
              self.currentLoopCycleEnd=e
              jumpRangeFound=True
              break
          else:
              self.currentLoopCycleStart  = subclipranges[0][1][0]
              self.currentLoopCycleEnd    = subclipranges[0][1][1]
              jumpRangeFound=True
          if jumpRangeFound:
            self.seekTo(self.currentLoopCycleStart)

  def reset(self):
    for file in self.files:
      self.removeVideoFile(file)
    self.currentlyPlayingFileName=None
    self.currentTimePos=None
    self.currentTotalDuration=None
    self.currentLoop_a=None
    self.currentLoop_b=None
    self.currentLoopCycleStart = None
    self.currentLoopCycleEnd   = None
    self.ui.updateFileListing(self.files)

  def getStateForSave(self):
    return {'loadedFiles':self.files[:]}

  def loadStateFromSave(self,data):
    for file in self.files:
      self.removeVideoFile(file)
    self.loadFiles(data['loadedFiles'])

  def initialisePlayer(self):
    playerFrameWid = self.ui.getPlayerFrameWid()
    self.player = mpv.MPV(wid=str(int(playerFrameWid)),
                          osc=True,
                          loop='inf',
                          mute=True,
                          volume=0,
                          autofit_larger='1280')

    self.player.observe_property('time-pos', self.handleMpvTimePosChange)
    self.player.observe_property('duration', self.handleMpvDurationChange)

  def close_ui(self):
    self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
    self.player.unobserve_property('duration', self.handleMpvDurationChange)
    for file in self.files:
      self.removeVideoFile(file)
    try:
      self.ui.destroy()
      del self.ui.master
      logging.info('CutselectionController destroyed')
    except:
      pass

  def handleMpvTimePosChange(self,name,value):
    if value is not None:
      self.currentTimePos = value
      self.checkLoopCycleJump()
      if self.currentTotalDuration is not None:
        self.ui.update()

  def handleMpvDurationChange(self,name,value):
    if value is not None:
      logging.debug('Duration updated {}'.format(value))
      self.currentTotalDuration=value

  def getIsPlaybackStarted(self):
    return self.currentTotalDuration is not None and self.currentTimePos is not None

  def jumpClips(self,offset):
    try:
      nextClipInd = self.files.index(self.currentlyPlayingFileName)+offset      
      self.playVideoFile(self.files[nextClipInd%len(self.files)],0)      
    except ValueError as e:
      logging.error('Exception jumpClips',exc_info=e)

  def playVideoFile(self,filename,startTimestamp):
    self.currentTotalDuration=None
    self.currentTimePos=None
    self.player.start=startTimestamp
    self.player.play(filename)
    self.player.command('load-script','screenspacetools.lua')
    self.currentlyPlayingFileName=filename
    self.ui.restartForNewFile(self.currentlyPlayingFileName)

  def setVideoRect(self,x,y,w,h):
    self.player.command('script-message','screenspacetools_rect',x,y,w,h,'2f344bdd','69dbdbff',1,'inner')

  def clearVideoRect(self):
    self.player.command('script-message','screenspacetools_clear')

  def screenSpaceToVideoSpace(self,x,y):
    vid_w = self.player.width
    vid_h = self.player.height
    osd_w = self.player.osd_width
    osd_h = self.player.osd_height

    scale = min(osd_w/vid_w, osd_h/vid_h)
    vid_sw, vid_sh = scale*vid_w, scale*vid_h

    off_x = math.floor((osd_w - vid_sw)/2)
    off_y = math.floor((osd_h - vid_sh)/2)

    vx1 = min(max(x, off_x), off_x + vid_sw)
    vy1 = min(max(y, off_y), off_y + vid_sh)
    vx1 = math.floor((vx1 - off_x) / scale)
    vy1 = math.floor((vy1 - off_y) / scale)
    return vx1,vy1

  def seekRelative(self,amount):
    if self.currentTotalDuration is not None:
      self.player.command('seek',str(amount),'relative')

  def jumpBack(self):
    self.player.command('seek','-10','relative')

  def playPauseToggle(self):
    self.player.pause = not(self.player.pause)

  def jumpFwd(self):
    self.player.command('seek','10','relative')

  def play(self):
    self.player.pause=False

  def pause(self):
    self.player.pause=True

  def seekTo(self,seconds):
    self.player.command('seek',str(seconds),'absolute','exact')

  def getTotalDuration(self):
    return self.currentTotalDuration

  def removeVideoFile(self,filename):
    deleteFile = self.removeAllDownloads
    _,justFilename = os.path.split(filename)
    localNameifDownloaded = os.path.join('tempDownloadedVideoFiles',justFilename)
    fileIsInTempFolder = os.path.isfile(localNameifDownloaded) and os.path.samefile( filename,localNameifDownloaded )
    
    if not deleteFile:
      if fileIsInTempFolder:
        response = self.ui.confirmWithMessage('Also remove downloaded video?' ,'Video "{}" was downloaded with youtube-dl, do you also want to delete the downloaded temporary file?'.format(justFilename),icon='warning')
        if response=='yes':
          deleteFile=True
          self.removeDownloadRun += 1
        else:
          self.removeDownloadRun = 0

      if self.removeDownloadRun>5:
        response = self.ui.confirmWithMessage('Delete doownloaded videos for all all future clip removals?' ,'Do you want to delete the downloaded temporary files for all future clip removals?',icon='warning')
        if response=='yes':
          self.removeAllDownloads=True

    self.files = [x for x in self.files if x != filename]
    self.videoManager.removeVideo(filename)
    if self.currentlyPlayingFileName == filename:
      if len(self.files)>0:
        self.playVideoFile(self.files[0],0)
      else:
        self.player.command('stop')
        self.currentlyPlayingFileName=None
    self.updateProgressStatistics()

    if fileIsInTempFolder and deleteFile:
      os.remove(filename)

  def returnYTDLDownlaodedVideo(self,filename):
    logging.debug('YTDL file returned {}'.format(filename))
    self.loadFiles([filename])

  def loadVideoYTdl(self,url):
    self.ytdlService.loadUrl(url,self.returnYTDLDownlaodedVideo)

  def returnImageLoadAsVideo(self,filename):
    self.loadFiles([filename])

  def loadImageFile(self,filename,duration):
    self.ffmpegService.loadImageFile(filename,duration,self.returnImageLoadAsVideo)

  def loadFiles(self,fileList):
    for file in fileList:
      if file not in self.files:
        self.files.append(file)
        if self.currentlyPlayingFileName is None:
          self.playVideoFile(file,0)
    self.ui.updateFileListing(self.files[:])
    self.updateProgressStatistics()

  def returnPreviewFrame(self,requestId,timestamp,size,responseImage):
    self.ui.updateViewPreviewFrame(requestId,responseImage)

  def requestPreviewFrame(self,filename,timestamp,size):
    self.ffmpegService.requestPreviewFrame(filename,filename,'10%','',size,self.returnPreviewFrame)

  def getcurrentFilename(self):
    return self.currentlyPlayingFileName

  def getRangesForClip(self,filename):
    return self.videoManager.getRangesForClip(filename)

  def getCurrentPlaybackPosition(self):
    return self.currentTimePos

  def updatePointForClip(self,filename,rid,pos,seconds):
    if seconds<0:
      seconds=0
    if seconds>self.currentTotalDuration:
      seconds=self.currentTotalDuration

    self.videoManager.updatePointForClip(filename,rid,pos,seconds)
    self.updateProgressStatistics()
    self.currentLoopCycleStart  = None
    self.currentLoopCycleEnd    = None


  def clearallSubclips(self):
    self.videoManager.clearallSubclips()
    self.updateProgressStatistics()
    
  def addNewInterestMark(self,point):
    if point<0:
      point=0
    if point>self.currentTotalDuration:
      point=currentTotalDuration

    self.videoManager.addNewInterestMark(self.currentlyPlayingFileName,point)
    self.ui.setUiDirtyFlag()

  def setVolume(self,value):
    self.player.volume=int(float(value))
    self.player.mute = float(value)<=0

  def getInterestMarks(self):
    return self.videoManager.getInterestMarks(self.currentlyPlayingFileName)

  def addNewSubclip(self,start,end):
    if start<0:
      start=0
    if start>self.currentTotalDuration:
      start=self.currentTotalDuration

    if end<0:
      end=0
    if end>self.currentTotalDuration:
      end=self.currentTotalDuration

    self.videoManager.registerNewSubclip(self.currentlyPlayingFileName,start,end)
    self.updateProgressStatistics()
    self.seekTo(start+((end-start)*0.8))


  def cloneSubclip(self,point):
    self.videoManager.cloneSubclip(self.currentlyPlayingFileName,point)
    self.updateProgressStatistics()
    self.currentLoopCycleStart  = None
    self.currentLoopCycleEnd    = None


  def removeSubclip(self,point):
    self.videoManager.removeSubclip(self.currentlyPlayingFileName,point)
    self.updateProgressStatistics()
    self.currentLoopCycleStart  = None
    self.currentLoopCycleEnd    = None

  def updateProgressStatistics(self):
    totalExTrim=0.0
    totalTrim=0.0
    for filename,rid,s,e in self.videoManager.getAllClips():
      totalExTrim += (e-s)-(self.ui.targetTrim*2)
      totalTrim   += (self.ui.targetTrim*2)
    self.ui.updateProgressStatitics(totalExTrim,totalTrim)


  def lowestErrorLoopCallback(self,filename,rid,mse,finals,finale):
    self.videoManager.updateDetailsForRangeId(filename,rid,finals,finale)
    self.setLoopPos(finals,finale)
    self.seekTo(finals)

  def findLowestErrorForBetterLoop(self,rid,secondsChange,rect):
    filename,start,end = self.videoManager.getDetailsForRangeId(rid)

    cropCoords=None
    x1,y1,x2,y2 = rect
    if x1 is not None:
      x1,x2 = sorted([x1,x2])
      y1,y2 = sorted([y1,y2])
      cropCoords = (x1,y1,x2-x1,y2-y1)
    self.ffmpegService.findLowerErrorRangeforLoop( filename,start,end,rid,secondsChange,cropCoords,self.lowestErrorLoopCallback )

  def sceneChangeCallback(self,filename,timestamp):
    self.videoManager.addNewInterestMark(filename,timestamp,kind='sceneChange')
    self.ui.setUiDirtyFlag()

  def runSceneChangeDetection(self):
    self.ffmpegService.runSceneChangeDetection(self.currentlyPlayingFileName,self.currentTotalDuration,self.sceneChangeCallback)

  def setLoopPos(self,start,end):
    if self.loopMode == 'Loop current':
      if (self.currentLoop_a is None or 
          self.currentLoop_a != start or
          self.currentLoop_b is None or 
          self.currentLoop_b != end):
        self.currentLoop_a = start
        self.currentLoop_b = end
        self.player.ab_loop_a=self.currentLoop_a
        self.player.ab_loop_b=self.currentLoop_b

if __name__ == '__main__':
  import webmGenerator
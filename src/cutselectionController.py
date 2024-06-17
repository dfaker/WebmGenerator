
import mpv
import math
import os
import random
import os
import logging
import time

from .modalWindows import youtubeDLModalState


class CutselectionController:

  def __init__(self,ui,initialFiles,videoManager,ffmpegService,ytdlService,voiceActivityService,controller,globalOptions={},initialSeek=0):
    self.globalOptions=globalOptions
    self.randomlyPlayedFiles = set()
    self.ui = ui
    self.ui.setController(self)
    self.videoManager = videoManager
    self.ffmpegService = ffmpegService
    self.ytdlService   = ytdlService
    self.voiceActivityService = voiceActivityService
    self.loopMode='Loop current'
    self.controller = controller
    self.initialSeek = initialSeek

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
    self.copiedTimeRange = None
    self.fit=True
    self.isActiveTab=True
    self.frameRate = None


    if self.globalOptions.get('askToShuffleLoadedFiles',False):
      if len(initialFiles)>1:
        response = self.ui.confirmWithMessage('Shuffle files?','Do you want to shuffle the intially loaded files?',icon='warning')
        if response=='yes':
          random.shuffle(initialFiles)
    
    self.ui.setinitialFocus()
    self.initialFiles = initialFiles

    self.ui.after(50, self.loadInitialFiles)

  def getRangeDetails(self,rid):
    fn = self.getcurrentFilename()
    rangeDetails = self.videoManager.getRangeDetailsForClip(fn,rid)
    return rangeDetails 

  def setDragDur(self,dur):
    self.ui.setDragDur(dur)

  def loadInitialFiles(self):
    if self.initialFiles is not None and len(self.initialFiles)>0:
      self.loadFiles(self.initialFiles)

  def fitoDim(self,dim):
    self.fit = False
    self.player.video_unscaled = not self.fit
    self.player.vf='lavfi=[scale={}:-1:sws_dither=none:sws_flags=neighbor]'.format(dim)

  def fitoScreen(self):
    self.player.autofit_larger='1280'
    self.fit = not self.fit
    self.player.video_unscaled = not self.fit
    self.player.vf=''

  def playingModalGotFocus(self):
    if self.isActiveTab:
      self.player.pause = True

  def playingModalLostFocus(self):
    if self.isActiveTab:
      self.player.pause = False


  def takeScreenshotToFile(self,screenshotPath,includes='video'):
    screenshotPath =  os.path.abspath(os.path.join(screenshotPath,'{}.png'.format(time.time())))
    print(screenshotPath)
    self.player.screenshot_to_file( screenshotPath ,includes='video')

  def getGlobalOptions(self):
    return self.globalOptions


  def splitClipIntoNEqualSections(self):
    n = self.ui.askInteger('How Many sections would you like to split into?','How Many sections would you like to split into?',initialvalue=10)

    if n is not None and n >= 1:
      useRange,a,b = self.askToUseRangeIfSet()
      
      print(useRange,a,b)

      if not useRange:
        self.clearAllSubclipsOnCurrentClip()
      
      endPoint = self.getTotalDuration()
      sectionLength = self.getTotalDuration()/n
      start = 0
      if useRange:
        start = a
        endPoint = b
        sectionLength = (b-a)/n 
      for _ in range(n):
        if start != min(start+sectionLength,endPoint):
          print(start,min(start+sectionLength,endPoint))
          self.addNewSubclip(start, min(start+sectionLength,endPoint),seekAfter=False)
        start = start+sectionLength
      self.updateProgressStatistics()
      self.ui.setUiDirtyFlag()
      self.seekTo(endPoint)

  def addSubclipByTextRange(self):
    self.ui.addSubclipByTextRange(self,self.getTotalDuration())

  def jumpToSearch(self,searchStr,randomjump=False):
    searchParts = [x.upper() for x in searchStr.split(' ') if len(x)>0]
    nextClipInd = self.files.index(self.currentlyPlayingFileName)+1
    foundfile = None
    possibles = []
    if randomjump:
        nextClipInd = 0

    for e in self.files[nextClipInd:]:
        if all([x in e.upper() for x in searchParts]):
            if randomjump:
                possibles.append(e)
                foundfile = e
            else:
                foundfile = e
                break

    if len(possibles) > 0  and randomjump:
        foundfile = random.choice(possibles)

    if foundfile is None:
        for e in self.files[:nextClipInd-1]:
            if all([x in e.upper() for x in searchParts]):
                foundfile = e
                break

    if foundfile is not None:
        nextFile = foundfile
        self.playVideoFile(nextFile,0)
        self.randomlyPlayedFiles.add(self.currentlyPlayingFileName)
        self.randomlyPlayedFiles.add(nextFile)

  def jumpToRidAndOffset(self,rid,startoffset,forceTabJump=False):
    if self.isActiveTab:
      try:
        filename,s,e = self.videoManager.getDetailsForRangeId(rid)

        if self.frameRate is None:
          pass

        if self.currentlyPlayingFileName != filename:
          for file in self.files:
            if file == filename:
              self.playVideoFile(file,s+startoffset)
        elif self.currentlyPlayingFileName == filename:
          self.seekTo(s+startoffset,centerAfter=True)
          self.ui.setUiDirtyFlag(specificRID=rid)
      except Exception as e:
        print(e)

  def fillGapsBetweenSublcips(self):
    subclipranges = self.videoManager.getRangesForClip(self.currentlyPlayingFileName)

    if len(subclipranges)>0:
      subclipranges = sorted(subclipranges,key=lambda x:x[1][1])

      lastEnd = None
      for i,(s,e) in subclipranges:
        if lastEnd is not None:
          if lastEnd != s:
            self.addNewSubclip(lastEnd,s,seekAfter=False)
        lastEnd = e

  def requestAutoconvert(self):
    self.controller.requestAutoconvert()

  def splitClipIntoSectionsOfLengthN(self):
    sectionLength = self.ui.askFloat('How long should the secions be?','How long should the secions be? (Seconds)', initialvalue=30)
    if sectionLength is not None and sectionLength >= 0:
      useRange,a,b = self.askToUseRangeIfSet()


      if not useRange:
        self.clearAllSubclipsOnCurrentClip()
      
      start = 0
      endPoint = self.getTotalDuration()
      if useRange:
        start = a
        endPoint = b 

      while start < endPoint:
        self.addNewSubclip(start, min(start+sectionLength,endPoint),seekAfter=False)
        start = start+sectionLength
      self.updateProgressStatistics()
      self.ui.setUiDirtyFlag()
      self.seekTo(endPoint)

  def generateSoundWaveBackgrounds(self,style='GENERAL'):
    self.ui.generateSoundWaveBackgrounds(style=style)

  def clearAllSubclipsOnCurrentClip(self):
    if self.currentlyPlayingFileName is not None:
      self.videoManager.clearallSubclipsOnFile(self.currentlyPlayingFileName)
      self.updateProgressStatistics()

  def clearAllInterestMarksOnCurrentClip(self):
    if self.currentlyPlayingFileName is not None:
      self.videoManager.clearallInterestMarksOnFile(self.currentlyPlayingFileName)
      self.updateProgressStatistics()
      self.ui.setUiDirtyFlag()

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

  def removefileIfLoaded(self,filename):
    fileRemoved=False
    for file in self.files:
      print(file,filename)
      print(file==filename)
      if file==filename:
        self.removeVideoFile(file)
        fileRemoved=True
    if fileRemoved:
      self.ui.updateSummary(None)
      self.ui.updateFileListing(self.files)
      self.ui.setUiDirtyFlag()

  def handleGlobalKeyEvent(self,evt):
    pass

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
    self.frameRate = None
    self.ui.updateSummary(None)
    self.ui.updateFileListing(self.files)
    self.ui.restartForNewFile()

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
                          autofit_larger='1280',
                          autoload_files='no',
                          cover_art_auto='no',
                          audio_file_auto='no',
                          start='{}%'.format(self.globalOptions.get('initialseekpc',0)),
                          sub_auto='no')

    if self.globalOptions.get('disableSubtitlesInPlayers',True):
      self.player.subtitles=False

    try:
        self.player.background=self.globalOptions.get('cutsTabPlayerBackgroundColour','#282828')
    except:
        pass

    try:
        self.player.background_color=self.globalOptions.get('cutsTabPlayerBackgroundColour','#282828')
    except:
        pass

    self.player.observe_property('time-pos',          self.handleMpvTimePosChange)
    self.player.observe_property('duration',          self.handleMpvDurationChange)
    self.player.observe_property('pause',             self.playbackStatusChanged)
    self.player.observe_property('fps',               self.handleMpvFPSChange)
    self.player.observe_property('container-fps',  self.handleMpvFPSChange)

    self.overlay = None
  
  def setPlaybackSpeed(self,speed):
    self.player.speed = speed

  def close_ui(self):

    try:
      self.player.stop()
    except Exception as e:
      print(e)

    try:
      self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
    except Exception as e:
      print(e)

    try:
      self.player.unobserve_property('duration', self.handleMpvDurationChange)
    except Exception as e:
      print(e)

    try:
      self.player.unobserve_property('fps', self.handleMpvFPSChange)
    except Exception as e:
      print(e)

    try:
      self.player.unobserve_property('container-fps',  self.handleMpvFPSChange)
    except Exception as e:
      print(e)

    try:
      self.player.unobserve_property('pause', self.playbackStatusChanged)
    except Exception as e:
      print(e)
    
    """
    for file in self.files:
      try:
        self.removeVideoFile(file)
      except Exception as e:
        print(e)
    """
    
    try:
      self.ui.destroy()
      del self.ui.master
      logging.info('CutselectionController destroyed')
    except:
      pass

  def playbackStatusChanged(self,name,value):
    self.ui.setPausedStatus(value)

  def handleMpvTimePosChange(self,name,value):
    if value is not None:
      self.currentTimePos = value
      self.checkLoopCycleJump()
      if self.currentTotalDuration is not None:
        self.ui.update(withLock=False)

  def handleMpvFPSChange(self,name,value):
    clampToFPS = self.globalOptions.get('clampSeeksToFPS',False)
    if clampToFPS and value is not None and value>0:
      self.frameRate = value
      self.ui.handleMpvFPSChange(value)

  def handleMpvDurationChange(self,name,value):
    if value is not None:
      logging.debug('Duration updated {}'.format(value))
      self.currentTotalDuration=value

      self.ui.updateSummary( self.player.filename,self.player.duration,self.player.video_params,self.player.container_fps,self.player.estimated_vf_fps)

  def getIsPlaybackStarted(self):
    return self.currentTotalDuration is not None and self.currentTimePos is not None

  def jumpClips(self,offset):
    if offset is None:
      unplayed =  set(self.files).difference(self.randomlyPlayedFiles)
      if len(unplayed)==0:
        self.randomlyPlayedFiles=set()
        unplayed = set(files)
      for _ in range(10):
          nextRandomFile = random.choice(list(unplayed))
          exists = os.path.isfile(nextRandomFile)
          if exists:
            self.playVideoFile(nextRandomFile,0)
          self.randomlyPlayedFiles.add(self.currentlyPlayingFileName)
          self.randomlyPlayedFiles.add(nextRandomFile)
          if exists:
            break
    else:
      try:
        for imult in range(1,10):
            nextClipInd = self.files.index(self.currentlyPlayingFileName)+(offset*imult)      
            nextFile = self.files[nextClipInd%len(self.files)]
            exists = os.path.isfile(nextFile)
            if exists:
                self.playVideoFile(nextFile,0)
            self.randomlyPlayedFiles.add(self.currentlyPlayingFileName)
            self.randomlyPlayedFiles.add(nextFile)
            if exists:
                break
      except ValueError as e:
        logging.error('Exception jumpClips',exc_info=e)

    self.updateProgressStatistics()

  def playVideoFile(self,filename,startTimestamp=0):
    self.currentTotalDuration=None
    self.currentTimePos=None
    if startTimestamp == 0:
        self.player.start = '{}%'.format(self.globalOptions.get('initialseekpc',0))
    else:
        self.player.start = startTimestamp
    
    self.player.play(filename)
    self.player.command('load-script',os.path.join('src','screenspacetools.lua'))
    self.currentlyPlayingFileName=filename
    self.controller.logPlayback(filename)
    self.ui.restartForNewFile(self.currentlyPlayingFileName)

  def setVideoRect(self,x,y,w,h,desc=''):
    self.player.command('script-message','screenspacetools_rect',x,y,w,h,desc,'2f344bdd','69dbdbff',1,'inner')

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

  def stepBackwards(self):
    self.player.command('frame-back-step')

  def stepForwards(self):
    self.player.command('frame-step')

  def seekRelative(self,amount):
    print(amount)
    if self.currentTotalDuration is not None:
      self.player.command('seek',str(amount),'relative','exact')

  def jumpBack(self):
    self.player.command('seek','-10','relative')

  def playPauseToggle(self):
    self.player.pause = not(self.player.pause)

  def jumpFwd(self):
    self.player.command('seek','10','relative')

  def isplaying(self):
    return not self.player.pause
  
  def play(self):
    self.player.pause=False

  def pause(self):
    self.player.pause=True

  def seekTo(self,seconds,centerAfter=False):
    if self.currentTotalDuration is not None:
      self.ui.updateSummary( self.player.filename,self.player.duration,self.player.video_params,self.player.container_fps,self.player.estimated_vf_fps)
    
    self.player.command('async', 'seek',str(seconds),'absolute','exact')
    if centerAfter:
      self.ui.centerTimelineOnCurrentPosition()


  def getTotalDuration(self):
    if self.currentTotalDuration is None:
      tempdur = self.player.duration
      if tempdur is not None and tempdur > 0:
        self.currentTotalDuration = tempdur

    return self.currentTotalDuration

  def removeVideoFile(self,filename):
    self.files = [x for x in self.files if x != filename]
    self.videoManager.removeVideo(filename)
    if self.currentlyPlayingFileName == filename:
      if len(self.files)>0:
        self.playVideoFile(self.files[0],0)
      else:
        self.player.command('stop')
        self.ui.updateSummary(None)
        self.currentlyPlayingFileName=None
        self.ui.frameTimeLineFrame.resetForNewFile()
    self.updateProgressStatistics()

  def returnYTDLDownlaodedVideo(self,filename):
    logging.debug('YTDL file returned {}'.format(filename))
    self.loadFiles([filename])

  def loadVideoYTdlFromClipboard(self,url):
    username = youtubeDLModalState['varUsername']
    password = youtubeDLModalState['varPassword']
    browserCookies = youtubeDLModalState['varBrowserCookies']
    code2factor = youtubeDLModalState['var2factor']



    self.ytdlService.loadUrl(url,0,username,password,False,browserCookies,'default',code2factor,self.returnYTDLDownlaodedVideo)

  def loadVideoYTdl(self,url,fileLimit,username,password,useCookies,browserCookies,qualitySort,code2Factor,retrycount=0):
    self.ytdlService.loadUrl(url,fileLimit,username,password,useCookies,browserCookies,qualitySort,code2Factor,self.returnYTDLDownlaodedVideo,retrycount=0)

  def returnImageLoadAsVideo(self,filename):
    self.loadFiles([os.path.abspath(filename)])

  def loadImageFile(self,filename,duration):
    self.ffmpegService.loadImageFile(filename,duration,self.returnImageLoadAsVideo)

  def loadFiles(self,fileList,asktoSort=False):

    if asktoSort:
      pass

    self.ui.disableFileWidgets = False or self.ui.disableFileWidgets
    if len(fileList) > 1000:    
        self.ui.disableFileWidgets=True
    elif len(fileList) > 100:
      response = self.ui.confirmWithMessage('Disable previews in listing?','You\'re loading {} files at once, showing these as widgets will affect performance, do you want to disable the image previews and just show a list of filenames?'.format(len(fileList)),icon='warning')
      if response=='yes':
        self.ui.disableFileWidgets=True

    for file in fileList:
      if file not in self.files:
        file_for_load = file

        if self.globalOptions.get('loadRelativeCopyOnFileNotExists',False) and not os.path.exists(file_for_load):
            relative_file = os.path.basename(file_for_load)
            if os.path.exists(relative_file):
                file_for_load = relative_file

        self.files.append(file_for_load)
        if self.currentlyPlayingFileName is None:
          self.playVideoFile(file_for_load,self.initialSeek)
          self.initialSeek=0

    self.ui.updateFileListing(self.files[:])
    self.updateProgressStatistics()

  def returnPreviewFrame(self,requestId,timestamp,size,responseImage):
    self.ui.updateViewPreviewFrame(requestId,responseImage)

  def requestPreviewFrame(self,filename,timestamp,size):
    print('requestPreviewFrame',filename,timestamp,size)
    self.ffmpegService.requestPreviewFrame(filename,filename,'10%','',size,self.returnPreviewFrame)

  def getcurrentFilename(self):
    return self.currentlyPlayingFileName

  def requestRIDHoverPreviews(self,rid,size,callback, start=None, end=None):
    if rid == 'V':
        filename = self.getcurrentFilename()
        startTime = start
        Endtime = end
        self.ffmpegService.requestHoverPreviewFrames(filename,startTime,Endtime,size,0,callback)
    elif rid is not None:
        filename,startTime,Endtime = self.videoManager.getDetailsForRangeId(rid)
        self.ffmpegService.requestHoverPreviewFrames(filename,startTime,Endtime,size,0,callback)

  def requestTimelinePreviewFrames(self,filename,startTime,Endtime,frameWidth,timelineWidth,callback):
    if self.globalOptions.get('generateTimelineThumbnails',True):
      self.ffmpegService.requestTimelinePreviewFrames(filename,startTime,Endtime,frameWidth,timelineWidth,callback)
    return True

  def getRangesForClip(self,filename):
    return self.videoManager.getRangesForClip(filename)

  def getCurrentPlaybackPosition(self):
    return self.currentTimePos

  def updateLabelForRid(self,rid,label):
    filename = self.getcurrentFilename()
    self.videoManager.updateLabelForClip(filename,rid,label)

  def updateSeqGroupForRid(self,rid,groupId):
    filename = self.getcurrentFilename()
    self.videoManager.updateSeqGroupForClip(filename,rid,groupId)

  def getSeqGroupForRid(self,rid):
    filename = self.getcurrentFilename()
    return self.videoManager.getSeqGroupForClip(filename,rid)

  def getLabelForRid(self,rid):
    filename = self.getcurrentFilename()
    return self.videoManager.getLabelForClip(filename,rid)

  def updatePointForRid(self,rid,pos,seconds):
    filename = self.getcurrentFilename()
    self.updatePointForClip(filename,rid,pos,seconds)
    self.ui.setUiDirtyFlag(specificRID=rid)

  def updatePointForClip(self,filename,rid,pos,seconds):
    clipped = False

    print(self,filename,rid,pos,seconds)
    if seconds<0:
      seconds=0
      clipped=True
    if seconds>self.currentTotalDuration:
      seconds=self.currentTotalDuration
      clipped=True

    if pos == 'm':
      _,rs,re = self.videoManager.getDetailsForRangeId(rid)
      print('move',rid,rs,re,(re-rs)/2)
      rhlen = (re-rs)/2
      if (seconds-rhlen)<0:
        seconds=rhlen
        clipped=True
      elif (seconds+rhlen)>self.currentTotalDuration:
        seconds=self.currentTotalDuration-rhlen
        clipped=True

    self.videoManager.updatePointForClip(filename,rid,pos,seconds)
    self.updateProgressStatistics()
    self.currentLoopCycleStart  = None
    self.currentLoopCycleEnd    = None
    return clipped

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

  def addFullClip(self):
    self.videoManager.clearallSubclipsOnFile(self.currentlyPlayingFileName)
    self.videoManager.registerNewSubclip(self.currentlyPlayingFileName,0.0,self.currentTotalDuration)
    self.updateProgressStatistics()

  def setAB(self,start,end,seekAfter=True):
    if start<0:
      start=0
    if start>self.currentTotalDuration:
      start=self.currentTotalDuration

    if end<0:
      end=0
    if end>self.currentTotalDuration:
      end=self.currentTotalDuration

    self.currentLoop_a = start
    self.currentLoop_b = end
    self.player.ab_loop_a=start
    self.player.ab_loop_b=end

  def addNewSubclip(self,start,end,seekAfter=True):
    if start<0:
      start=0
    if start>self.currentTotalDuration:
      start=self.currentTotalDuration

    if end<0:
      end=0
    if end>self.currentTotalDuration:
      end=self.currentTotalDuration

    newRID = self.videoManager.registerNewSubclip(self.currentlyPlayingFileName,start,end)
    self.updateProgressStatistics()
    if seekAfter:
      self.seekTo(start+((end-start)*0.8))
    self.ui.setUiDirtyFlag(specificRID=newRID)
    return newRID

  def getSurroundingInterestMarks(self,point):
    return self.videoManager.getSurroundingInterestMarks(self.currentlyPlayingFileName,point)

  def expandSublcipToInterestMarks(self,point):
    self.videoManager.expandSublcipToInterestMarks(self.currentlyPlayingFileName,point)
    self.updateProgressStatistics()

  def cloneSubclip(self,point):
    self.videoManager.cloneSubclip(self.currentlyPlayingFileName,point)
    self.updateProgressStatistics()

  def copySubclip(self,point):
    for i,(s,e) in self.videoManager.getRangesForClip(self.currentlyPlayingFileName):
      print(s,e,point)
      if float(s) <= float(point) <= float(e):

        self.copiedTimeRange = (float(s),float(e))

  def pasteSubclip(self):
    if self.copiedTimeRange is not None:
      s,e = self.copiedTimeRange
      return self.addNewSubclip(s,e)


  def removeSubclip(self,point):
    self.videoManager.removeSubclip(self.currentlyPlayingFileName,point)
    self.updateProgressStatistics()
    self.currentLoopCycleStart  = None
    self.currentLoopCycleEnd    = None
    self.currentLoop_a=None
    self.currentLoop_b=None
    self.player.ab_loop_a=-1
    self.player.ab_loop_b=-1
    self.ui.setUiDirtyFlag()

  def updateProgressStatistics(self):
    totalExTrim=0.0
    totalTrim=0.0

    targetTrim=0
    try:
      targetTrim=float(self.ui.targetTrimVar.get())
    except Exception as e:
      print('updateProgressStatistics',e)

    for filename,rid,s,e in self.videoManager.getAllClips():
      totalExTrim += (e-s)-(targetTrim*2)
      totalTrim   += (targetTrim*2)


    clipsleft = len(set(self.files).difference(self.randomlyPlayedFiles))

    self.ui.updateProgressStatitics(totalExTrim,totalTrim,len(self.files),clipsleft)

  def lowestErrorLoopCallback(self,filename,rid,mse,finals,finale):
    self.videoManager.updateDetailsForRangeId(filename,rid,finals,finale)
    self.setLoopPos(finals,finale)
    self.ui.setUiDirtyFlag()
    self.seekTo(finals)

  def moveToMaximumInterFrameDistance(self,rid,pos):
    filename,start,end = self.videoManager.getDetailsForRangeId(rid)
    self.ffmpegService.moveToMaximumInterFrameDistance( filename,start,end,pos,rid,self.lowestErrorLoopCallback )

  def findLowestErrorForBetterLoop(self,rid,secondsChange,rect):
    filename,start,end = self.videoManager.getDetailsForRangeId(rid)

    cropCoords=None
    x1,y1,x2,y2 = rect
    if x1 is not None:
      x1,x2 = sorted([x1,x2])
      y1,y2 = sorted([y1,y2])
      cropCoords = (x1,y1,x2-x1,y2-y1)
    self.ffmpegService.findLowerErrorRangeforLoop( filename,start,end,rid,secondsChange,cropCoords,self.lowestErrorLoopCallback )

  def foundLoopCallback(self,filename,mse,finals,finale):
    self.videoManager.registerNewSubclip(filename,finals,finale)
    self.setLoopPos(finals,finale)
    self.ui.setUiDirtyFlag()
    self.seekTo(finals)

  def findRangeforLoop(self,secondsCenter,minSeconds,maxSeconds,rect):
    if self.currentlyPlayingFileName is not None:
      cropCoords=None
      x1,y1,x2,y2 = rect
      if x1 is not None:
        x1,x2 = sorted([x1,x2])
        y1,y2 = sorted([y1,y2])
        cropCoords = (x1,y1,x2-x1,y2-y1)
      self.ffmpegService.findRangeforLoop( self.currentlyPlayingFileName,secondsCenter,minSeconds,maxSeconds,cropCoords,self.foundLoopCallback )

  def similarSoundCallback(self,filename,mse,tslist):
    for s,e in tslist:
        self.videoManager.registerNewSubclip(filename,s,e)
    self.ui.setUiDirtyFlag()

  def findSimilarSounds(self,startTime,endTime,limit,distance):
    if self.currentlyPlayingFileName is not None:
        self.ffmpegService.findSimilarSounds( self.currentlyPlayingFileName,startTime,endTime,limit,distance,self.similarSoundCallback )


  def sceneChangeCallback(self,filename,timestamp,timestampEnd=None,kind='Mark'):
    if kind == 'Mark':
      self.videoManager.addNewInterestMark(filename,timestamp,kind='sceneChange')
    elif kind == 'Cut':
      self.videoManager.registerNewSubclip(filename,timestamp,max(timestamp+0.01,timestampEnd-0.01))
    self.updateProgressStatistics()
    self.ui.setUiDirtyFlag(withLock=True)

  def askToUseRangeIfSet(self):
    useRange=False
    a,b = self.ui.getCurrentlySelectedRegion()
    if a is not None and b is not None:
      useRange = self.ui.confirmWithMessage("Use selected temporary range?","Do you want to limit the search in the selected range {:0.3f} to {:0.3f} ?".format(a,b),icon='question')
      if not useRange:
        useRange,a,b = False,None,None
      else:
        self.ui.clearCurrentlySelectedRegion()
    return useRange,a,b

  def runSceneCentreDetectionCuts(self,addCuts=False):
    sceneLength = self.ui.askFloat('What should the length of the representative scenes be?','Scene Length (seconds)', initialvalue=30)
    if sceneLength is not None:
      sceneLength = abs(sceneLength)
      useRange,a,b = self.askToUseRangeIfSet()


      self.ffmpegService.runRepresentativeCentresDetection(self.currentlyPlayingFileName,self.currentTotalDuration,self.sceneChangeCallback,clipLength=sceneLength,addCuts=addCuts,useRange=useRange,rangeStart=a,rangeEnd=b)

  def runFullLoopSearch(self):
    threshold=0
    addCuts=True
    useRange,a,b = self.askToUseRangeIfSet()
    if not useRange:
      a=0
      b=self.currentTotalDuration
    self.ui.displayLoopSearchModal(useRange=useRange,rangeStart=a,rangeEnd=b)


  def showVoiceActivityDetectionModal(self):
    self.ui.displayrunVoiceActivityDetectionmodal()

  def runVoiceActivityDetection(self,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,minZcr,maxZcr):
    self.voiceActivityService.scanForVoiceActivity(self.currentlyPlayingFileName,self.currentTotalDuration,self.sceneChangeCallback,sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,minZcr,maxZcr)

  def submitFullLoopSearch(self,midThreshold=30,minLength=1,maxLength=5,timeSkip=1,threshold=30,addCuts=True,useRange=False,rangeStart=None,rangeEnd=None,ifdmode=False,selectionMode='bestFirst'):
    self.ffmpegService.fullLoopSearch(self.currentlyPlayingFileName,self.currentTotalDuration,self.sceneChangeCallback,midThreshold=midThreshold,
                                                                                                                       minLength=minLength,
                                                                                                                       maxLength=maxLength,
                                                                                                                       timeSkip=timeSkip,
                                                                                                                       threshold=threshold,
                                                                                                                       addCuts=addCuts,
                                                                                                                       useRange=useRange,
                                                                                                                       rangeStart=rangeStart,
                                                                                                                       ifdmode=ifdmode,
                                                                                                                       rangeEnd=rangeEnd,
                                                                                                                       selectionMode=selectionMode)


  def runSceneChangeDetection(self,addCuts=False):
    threshold = self.ui.askFloat('What should the threshold of scene detection be?','Scene change proportion', initialvalue=0.3)
    if threshold is not None:
      threshold = abs(threshold)
      useRange,a,b = self.askToUseRangeIfSet()

      self.ffmpegService.runSceneChangeDetection(self.currentlyPlayingFileName,self.currentTotalDuration,self.sceneChangeCallback,threshold=threshold,addCuts=addCuts,useRange=useRange,rangeStart=a,rangeEnd=b)

  def scanAndAddLoudSectionsCallback(self,filename,start,end):
    self.videoManager.registerNewSubclip(filename,start,end)
    self.ui.setUiDirtyFlag()

  def scanAndAddLoudSections(self):
    threshold = self.ui.askFloat('How loud does the section have to be to add it?','Loudness Threshold (-dB)', initialvalue=20)
    if threshold is not None:
      threshold=abs(threshold)
      useRange,a,b = self.askToUseRangeIfSet()

      self.ffmpegService.scanAndAddLoudSections(self.currentlyPlayingFileName,self.currentTotalDuration,threshold,self.scanAndAddLoudSectionsCallback,useRange=useRange,rangeStart=a,rangeEnd=b)

  

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
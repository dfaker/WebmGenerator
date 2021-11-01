import mpv
import math
import os
import json
import time

class FilterSelectionController:

  def __init__(self,ui,videoManager,ffmpegService,faceDetectService,globalOptions={}):
    self.globalOptions=globalOptions
    self.ui = ui
    self.templates = {}
    self.faceDetectService = faceDetectService

    os.path.exists('filterTemplates') or os.mkdir('filterTemplates')
    for fn in os.listdir('filterTemplates'):
      if fn.endswith('.json'):
        try:
          name = fn.rpartition('.')[0]
          value = json.loads(open(os.path.join('filterTemplates',fn),'r').read())
          self.templates[name]=value
          print(name,value)
        except Exception as e:
          print(e)

    print(self.templates)

    self.ui.setController(self)
    self.videoManager = videoManager
    self.ffmpegService = ffmpegService

    playerFrameWid = self.ui.getPlayerFrameWid()
    self.player = mpv.MPV(wid=str(int(playerFrameWid)),
                          osc=False,
                          log_handler=self.errorHandler,
                          loglevel='debug',
                          loop='inf',
                          mute=True,
                          background=globalOptions.get('filtersTabPlayerBackgroundColour','#282828'),
                          cursor_autohide="always",
                          autofit_larger='1280',
                          audio_file_auto='no',
                          sub_auto='no')

    self.player.command('load-script',os.path.join('src','screenspacetools.lua'))
    self.player.observe_property('time-pos', self.handleMpvTimePosChange)

    self.playerStart=0
    self.playerEnd=0
    self.player.speed=2
    self.currentlyPlayingFileName=None
    self.installedFonts = None
    self.filterApplicationMode = 'lavfi_complex'

  def faceDetectEnabled(self):
    return self.faceDetectService.faceDetectEnabled()

  def getFaceBoundingRect(self,callback):
    self.faceDetectService.getFaceBoundingRect(self.currentlyPlayingFileName,'',self.player.time_pos,callback)

  def takeScreenshotToFile(self,screenshotPath,includes='video'):
    screenshotPath =  os.path.abspath(os.path.join(screenshotPath,'{}.png'.format(time.time())))
    print(screenshotPath)
    self.player.screenshot_to_file( screenshotPath ,includes='video')


  def errorHandler(self,kind,module,err):
    print(kind,'|',module,'|',err)
    if kind=='error' and 'Disabling filter filterStack' in err:
      self.clearFilter()
      self.ui.filterFailure()
    if kind=='fatal' and 'failed to configure the filter' in err:
      self.clearFilter()
      self.ui.filterFailure()

  def stepRelative(self,amount):
    if amount>0:
      self.player.command('frame-step')
    else:
      self.player.command('frame-back-step')
    
  def seekRelative(self,amount):
    self.player.command('seek',str(amount),'relative','exact')

  def togglePause(self):
    self.player.pause = not(self.player.pause)

  def getClipDuration(self):
    s,e = float(self.playerStart),float(self.playerEnd)
    d = e-s
    return d

  def getTemplateListing(self):
    return self.templates.items()

  def getGlobalOptions(self):
    return self.globalOptions

  def handleMpvTimePosChange(self,name,value):
    if value is not None and self.ui is not None:
      s,e = float(self.playerStart),float(self.playerEnd)
      if s<=value<=e:
        self.ui.updateSeekPositionThousands( ((value-s)/(e-s))*1000,value-s )
        self.ui.updateSeekLabel((value-s))

    self.screenSpaceToVideoSpace(-1,-1)

  def gettempVideoFilePath(self):
    return self.globalOptions.get('tempFolder','tempVideoFiles')

  def requestAutocrop(self,rid,mid,filename,callback):
    self.ffmpegService.requestAutocrop(rid,mid,filename,callback)

  def seekToPercent(self,pc):
    s,e = float(self.playerStart),float(self.playerEnd)
    d = e-s
    self.player.command('seek',str(s+(d*pc)),'absolute','exact')

  def getCurrentPlaybackPosition(self):
    try:
      s = float(self.playerStart)
      return self.player.time_pos-s
    except Exception as e:
      return 0

  def normaliseTimestamp(self,ts):
    fts = float(ts)
    s,e = float(self.playerStart),float(self.playerEnd)

    fts = max(min(e,fts),s)
    return float(self.playerStart) + float(ts)

  def seekToTimelinePoint(self,ts):
    self.player.command('seek',str(self.normaliseTimestamp(ts)),'absolute','exact')

  def setSpeed(self,speed):
    self.player.speed=speed

  def fitoScreen(self,fit):
    self.player.video_unscaled = not fit

  def close_ui(self):
    try:
      self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
    except Exception as e:
      print(e)

  def getAllSubclips(self):
    return self.videoManager.getAllClips()

  def clearFilter(self):
    if self.filterApplicationMode == 'lavfi_complex':
      self.player.lavfi_complex='[vid1]null[vo]'
    else:
      self.player.command('async','vf', 'del',    "@filterStack")

  def setFilter(self,filterExpStr):
    if self.filterApplicationMode == 'lavfi_complex':
      self.player.lavfi_complex='[vid1] '+filterExpStr+' [vo]'
    else:
      self.player.command('async','vf', 'add',    '@filterStack:lavfi="{}"'.format(filterExpStr))

  def play(self):
    self.player.pause=False
  
  def pause(self):
    self.player.pause=True

  def stop(self):
    self.player.command('stop')

  def drawVideoCrosshair(self,x1,y1):
    self.player.command('script-message','screenspacetools_mouse_cross',x1,y1)

  def setVideoVector(self,x1,y1,x2,y2):
    self.player.command('script-message','screenspacetools_drawVector',x1,y1,x2,y2)

  def addVideoRegMark(self,x,y,style='cross'):
    self.player.command('script-message','screenspacetools_regMark',x,y,style)

  def setVideoRect(self,x,y,w,h):
    self.player.command('script-message','screenspacetools_rect',x,y,w,h,'2f344bdd','69dbdbff',1,'inner')

  def clearVideoRect(self):
    self.player.command('script-message','screenspacetools_clear')

  def getVideoDimensions(self):
    osd_w = self.player.width
    osd_h = self.player.height
    return osd_w,osd_h

  def screenSpaceToVideoSpace(self,x,y):
    try:
      #soruce video    

      par = self.player.video_out_params.get('par',1)
      
      vid_w = self.player.video_out_params['dw']
      vid_h = self.player.video_out_params['dh']


      #displayframe
      osd_w = self.player.osd_width
      osd_h = self.player.osd_height

      #paddingAroundFrame
      osd_dim = self.player.osd_dimensions
      osd_top = osd_dim['mt']
      osd_bottom = osd_dim['mb']
      osd_left = osd_dim['ml']
      osd_right = osd_dim['mr']

      boxw = (osd_w-osd_right-osd_left)*par
      boxh = osd_h-osd_top-osd_bottom

      ox = ((x-osd_right)*(vid_w/boxw))
      oy = ((y-osd_top)*(vid_h/boxh))
    
      return ox,oy
    except Exception as e:
      print(e)
      return 0,0


  def videoSpaceToScreenSpace(self,x,y):
    try:
      #soruce video    

      par = self.player.video_out_params.get('par',1)
      
      vid_w = self.player.video_out_params['dw']
      vid_h = self.player.video_out_params['dh']


      #displayframe
      osd_w = self.player.osd_width
      osd_h = self.player.osd_height

      #paddingAroundFrame
      osd_dim = self.player.osd_dimensions
      osd_top = osd_dim['mt']
      osd_bottom = osd_dim['mb']
      osd_left = osd_dim['ml']
      osd_right = osd_dim['mr']

      boxw = (osd_w-osd_right-osd_left)*par
      boxh = osd_h-osd_top-osd_bottom

      ox = ((x)*(boxw/vid_w))+osd_right   
      oy = ((y)*(boxh/vid_h))+osd_top
    
      return ox,oy
    except Exception as e:
      print(e)
      return 0,0


  def getClipsWithFilters(self):
    response=[]
    for filename,rid,s,e in self.videoManager.getAllClips():
      result = [filename,rid,s,e,'null','null']
      filteredVersion = self.ui.subclips.get(rid)
      if filteredVersion is not None:
        result[4]=filteredVersion.get('filterexp','null')
        result[5]=filteredVersion.get('filterexpEncStage','null')
      if result[4] == '':
        result[4]='null'

      if result[5] == '':
        result[5]='null'
      response.append( tuple(result) )
    return response

  def setVolume(self,value):
    self.player.volume=int(float(value))
    self.player.mute = float(value)<=0

  def getInstalledFonts(self):
    if self.installedFonts is None:
      pass
    return self.installedFonts

  def playVideoFile(self,filename,s,e):
    self.player.start=s
    self.playerStart=s
    self.playerEnd=e
    self.player.ab_loop_a=s
    self.player.ab_loop_b=e
    if self.currentlyPlayingFileName != filename:
      self.player.play(filename)
    else:
      try:
        self.player.command('seek',s,'absolute','exact')
      except:
        self.player.play(filename)

    self.currentlyPlayingFileName=filename
    self.ui.setActiveTimeLineValue(None)
    

if __name__ == '__main__':
  import webmGenerator
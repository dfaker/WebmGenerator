import mpv
import math
import os
import json

class FilterSelectionController:

  def __init__(self,ui,videoManager,ffmpegService,globalOptions={}):
    self.globalOptions=globalOptions
    self.ui = ui
    self.templates = {}

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
                          osc=True,
                          #log_handler=print,
                          #loglevel='debug',
                          loop='inf',
                          mute=True,
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

  def gettempVideoFilePath(self):
    return self.globalOptions.get('tempFolder','tempVideoFiles')

  def requestAutocrop(self,rid,mid,filename,callback):
    self.ffmpegService.requestAutocrop(rid,mid,filename,callback)

  def seekToPercent(self,pc):
    s,e = float(self.playerStart),float(self.playerEnd)
    d = e-s
    self.player.command('seek',str(s+(d*pc)),'absolute','exact')

  def getCurrentPlaybackPosition(self):
    s = float(self.playerStart)
    return self.player.time_pos-s

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
    self.player.command('async','vf', 'del',    "@filterStack")

  def setFilter(self,filterExpStr):
    print(filterExpStr)
    self.player.command('async','vf', 'add',    "@filterStack:lavfi=\"{}\"".format(filterExpStr))

  def play(self):
    self.player.pause=False
  
  def pause(self):
    self.player.pause=True

  def stop(self):
    self.player.command('stop')

  def setVideoRect(self,x,y,w,h):
    print('script-message','screenspacetools_rect',x,y,w,h,'2f344bdd','69dbdbff',1,'inner')
    self.player.command('script-message','screenspacetools_rect',x,y,w,h,'2f344bdd','69dbdbff',1,'inner')

  def clearVideoRect(self):
    self.player.command('script-message','screenspacetools_clear')

  def getVideoDimensions(self):
    osd_w = self.player.width
    osd_h = self.player.height
    return osd_w,osd_h

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
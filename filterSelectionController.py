import mpv
import math

class FilterSelectionController:

  def __init__(self,ui,videoManager,ffmpegService):
    self.ui = ui
    self.ui.setController(self)
    self.videoManager = videoManager
    self.ffmpegService = ffmpegService

    playerFrameWid = self.ui.getPlayerFrameWid()
    self.player = mpv.MPV(wid=str(int(playerFrameWid)),
                          osc=True,
                          loop='inf',
                          mute=True,
                          autofit_larger='1280')
    self.player.command('load-script','screenspacetools.lua')
    self.player.speed=2
    self.currentlyPlayingFileName=None

  def setSpeed(self,speed):
    self.player.speed=speed

  def fitoScreen(self,fit):
    self.player.video_unscaled = not fit

  def close_ui(self):
    self.player.terminate()
    del self.player

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

  def getClipsWithFilters(self):
    response=[]
    for filename,rid,s,e in self.videoManager.getAllClips():
      result = [filename,rid,s,e,'null']
      filteredVersion = self.ui.subclips.get(rid)
      if filteredVersion is not None:
        result[4]=filteredVersion.get('filterexp','null')
      if result[4] == '':
        result[4]='null'
      response.append( tuple(result) )
    return response

  def playVideoFile(self,filename,s,e):
    self.player.start=s
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

if __name__ == '__main__':
  import webmGenerator
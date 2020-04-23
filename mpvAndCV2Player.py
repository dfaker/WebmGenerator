
import mpv
import cv2
import numpy as np
from win32api import GetSystemMetrics
from cv2GUI import Cv2GUI

class MpvAndCV2Player():

  def __init__(self,cat,filename):
    self.player = mpv.MPV(input_default_bindings=True, osc=True)
    self.player.loop_playlist = 'inf'
    self.player.mute = 'yes'
    self.player.speed = 2
    self.player.autofit_larger=1280
    self.player.geometry='50%:50%'
    self.player.command('load-script','easycrop.lua')

    self.category = cat
    self.filename=filename

    self.player.register_message_handler('easycrop', self._handleMpvCropChange)

    self.player.observe_property('time-pos', self._handleMpvTimePosChange)

    self.seeker = Cv2GUI(self)

    for button in self.seeker.buttons:
      self.player.register_key_binding(button['key'],         self._handleMpvKeypress)

    self.player.register_key_binding("CLOSE_WIN", self._handleMpvKeypress)

    

    self.posA=None
    self.posB=None

    self.cropRect = (0,0,0,0)
    self.active=False
    self.totalDuration=None
    self.currentTime=0
    self.showLogo=False
    self.showFooter=False
    self.selected=False
    self.endSelection=False
    self.toggleLogo()

  def toggleLogo(self):
    print(self.showLogo)
    self.showLogo = not self.showLogo
    if self.showLogo:
      self.player.command('vf', 'add',    "@logo:lavfi=\"movie='logo.png'[pwm],[vid1][pwm]overlay=5:5[vo]\"")
    else:
      self.player.command('vf', 'del', "@logo:lavfi=\"movie='logo.png'[pwm],[vid1][pwm]overlay=5:5[vo]\"")

  def togglefooter(self):
    print(self.showLogo)
    self.showFooter = not self.showFooter
    if self.showFooter:
      self.player.command('vf', 'add',    "@footer:lavfi=\"movie='footer.png'[pwm],[vid1][pwm]overlay=(W-w)/2:(H-h)[vo]\"")
    else:
      self.player.command('vf', 'del', "@footer:lavfi=\"movie='footer.png'[pwm],[vid1][pwm]overlay=(W-w)/2:(H-h)/2[vo]\"")


  def setABLoopRange(self,start,end):
      self.posA=start
      self.posB=end
      self.player.ab_loop_a=start
      self.player.ab_loop_b=end
      self.player.command('seek', end-1, 'absolute', 'exact')

  def _handleMpvCropChange(self,w,h,x,y):
    self.cropRect = w,h,x,y
    if self.showLogo:
      self.toggleLogo()
      self.toggleLogo()

    if self.showFooter:
      self.togglefooter()
      self.togglefooter()

  def _handleMpvKeypress(self,state,key,bubble=True):
    if state=='d-':
      if key == 't':
        self.toggleLogo()
      if key == 'y':
        self.togglefooter()
      if key == 'c':
        self.player.command('script-binding','easycrop/easy_crop')
      if key in ('q','e','r'):
        if bubble:
          self.seeker._handleCV2Keypress(ord(key))
        if key == 'q':
          self.posA is not None and self.posB is not None:
            self.selected=True
        if key == 'r':
          self.endSelection=True
        self.active=False

  def _handleMpvTimePosChange(self,name, value):
    self.currentTime=value
    if self.totalDuration is None:
      self.totalDuration = self.player.duration

  def playVideo(self):
    self.active=True
    self.player.play(self.filename)
    while self.active:
      self.seeker.update()
    self.player.terminate()
    self.seeker.destroy()

    result = []
    if self.selected and self.posA is not None and self.posB is not None:
      result.append( ((self.category, self.filename , self.posA, self.posB),(self.showLogo , self.showFooter), self.cropRect) )
    if self.endSelection:
      return None
    return result
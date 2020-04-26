
import mpv
import cv2
import numpy as np
from win32api import GetSystemMetrics
from cv2GUI import Cv2GUI

class MpvAndCV2Player():

  def __init__(self,cat,filename,sessionProperties):


    self.posA=None
    self.posB=None

    self.cropRect = (0,0,0,0)
    self.active=False
    self.totalDuration=None
    self.currentTime=0
    
    self.selected=False
    self.endSelection=False
    

    self.player = mpv.MPV(input_default_bindings=True, osc=True)
    self.player.loop_playlist = 'inf'
    self.player.mute = 'yes'
    self.player.speed = 2
    self.player.no_keepaspect_window=True

    self.player.autofit_larger=1280
    self.player.geometry='50%:50%'
    self.player.command('load-script','easycrop.lua')

    self.category = cat
    self.filename=filename
    self.sessionProperties = sessionProperties

    self.player.register_message_handler('easycrop', self._handleMpvCropChange)

    self.player.observe_property('time-pos', self._handleMpvTimePosChange)

    self.seeker = Cv2GUI(self)

    for button in self.seeker.buttons:
      self.player.register_key_binding(button['key'],         self._handleMpvKeypress)

    self.player.register_key_binding("CLOSE_WIN", self._handleMpvKeypress)

  


    self.toggleLogo()
    self.toggleLogo()


  def toggleLogo(self):
    self.sessionProperties.showLogo = not self.sessionProperties.showLogo
    if self.sessionProperties.showLogo:
      self.player.command('vf', 'add',    "@logo:lavfi=\"movie='logo.png'[pwm],[vid1][pwm]overlay=5:5[vo]\"")
    else:
      self.player.command('vf', 'del', "@logo:lavfi=\"movie='logo.png'[pwm],[vid1][pwm]overlay=5:5[vo]\"")

  def getFilterExpression(self,filterStack):
    filterExp = ','.join([x.getFilterExpression() for x in filterStack])
    if len(filterStack)==0:
      return None
    return filterExp

  def recaulcateFilters(self,filterStack):

    filterExp = ','.join([x.getFilterExpression() for x in filterStack])
    print(filterExp)
    if len(filterStack)==0:
      self.player.command('vf', 'del',    "@filterStack:lavfi=\"{}\"".format(filterExp))
    if len(filterStack)>0:
      self.player.command('vf', 'add',    "@filterStack:lavfi=\"{}\"".format(filterExp))
    self._handleMpvCropChange(*self.cropRect)

  def seek(self,pos):
    self.player.command('seek', pos, 'absolute', 'exact')

  def setABLoopRange(self,start,end,jumpAfterSet='End'):
      self.posA=start
      self.posB=end
      self.player.ab_loop_a=start
      self.player.ab_loop_b=end
      if jumpAfterSet=='End':
        self.player.command('seek', end-1.0, 'absolute', 'exact')
      elif jumpAfterSet=='Start':
        self.player.command('seek', start, 'absolute', 'exact')


  def _handleMpvCropChange(self,w,h,x,y):
    self.cropRect = w,h,x,y
    if self.sessionProperties.showLogo:
      self.toggleLogo()
      self.toggleLogo()

  def _handleMpvKeypress(self,state,key,bubble=True):
    if state=='d-':
      if key == 't':
        self.toggleLogo()
      if key == 'c':
        self.player.command('script-binding','easycrop/easy_crop')
      if key in ('q','e','r'):
        if bubble:
          self.seeker._handleCV2Keypress(ord(key))
        if key == 'q':
          if self.posA is not None and self.posB is not None:
            self.selected=True
        if key == 'r':
          self.endSelection=True
        self.active=False

  def _handleMpvTimePosChange(self,name, value):
    if value is not None:
      self.currentTime=value
    if self.totalDuration is None and self.player.duration is not None:
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
      result.append(
                    (
                      (self.category, self.filename , self.posA, self.posB)
                      ,(self.sessionProperties.showLogo , self.getFilterExpression(self.seeker.filterStack) )
                      ,self.cropRect
                      ,(
                         self.sessionProperties.fpsLimit
                        ,self.sessionProperties.sizeLimit
                        ,self.sessionProperties.audioBR
                        ,self.sessionProperties.videoBrMax
                        ,self.sessionProperties.maxVWidth
                        ,self.sessionProperties.minVWidth
                      )
                    )
                   )
    if self.endSelection:
      return None
    return result
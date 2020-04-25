
import mpv
import cv2
import numpy as np
import colortheme
from tkinter import Tk

def get_curr_screen_width():
    root = Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    return int(geometry.split('x')[0])

class Cv2GUI():

  def __init__(self,player):
    self.imshape = (126,get_curr_screen_width()-100,3)
    self.seeker = np.zeros(self.imshape,np.uint8)
    self.player = player
    self.font = cv2.FONT_HERSHEY_SIMPLEX
    self.seekResolution=1.5
    self.seekInc=1/self.seekResolution
    self.clipDuration=30.0
    self.scrubPercent=0.5
    self.tickIncrement=30

    self.colors = colortheme.ColorProvider()
    self.pixelsNeededForIncrement=None

    self.draggingSeek=False
    self.draggingScrub=False
    self.scrubOffset=0.0
    self.timeCentre=None

    self.draggingStart = False
    self.draggingEnd   = False

    cv2.namedWindow("seeker")
    cv2.setMouseCallback("seeker", self._handleCV2Click)

    self.buttons = [
      {'key':'q','text':'Queue Current Clip [Q]',  'color':self.colors.color_button  },
      {'key':'e','text':'Next File [E]',           'color':self.colors.color_button  },
      {'key':'r','text':'Exit and Process [R]',    'color':self.colors.color_button  },
      {'key':'t','text':'Toggle Logo [T]',         'color':self.colors.color_button  },
      {'key':'y','text':'Toggle Footer [Y]',       'color':self.colors.color_button  },
      {'key':'c','text':'Crop [C]',                'color':self.colors.color_button  },
    ]

    xorigin=5
    for button in self.buttons:
      (bw,bh),baseline = cv2.getTextSize(button['text'],self.font, 0.4, 1)
      button['position'] = (xorigin,15,bw,bh)
      xorigin = xorigin+bw+15
    self.infoXorigin = xorigin
    self.infoFormat = "Start:{:01.2f}s End:{:01.2f}s Dur:{:01.2f}s"

    self.recauclateButtons()

  def recauclateButtons(self):
    xorigin=5
    self.colors = colortheme.ColorProvider()
    for cycle in self.player.sessionProperties.cycles:
      if not hasattr(self.player.sessionProperties, cycle['prop']):
        setattr(self.player.sessionProperties, cycle['prop'], cycle['default'])
      (bw,bh),baseline = cv2.getTextSize( cycle['text'].format( getattr(self.player.sessionProperties, cycle['prop'] ) ) ,self.font, 0.4, 1)
      cycle['position'] = (xorigin,115,bw,bh)
      xorigin = xorigin+bw+15


  def destroy(self):  
    cv2.destroyAllWindows()

  def timeTox(self,time):
    if self.pixelScrubRatio>=1.0:
      return (time/self.player.totalDuration)*self.imshape[1]
    ScrubSecconds = ((self.pixelScrubWidth)*self.pixelScrubRatio)
    scrubStart = (self.scrubPercent* (self.player.totalDuration - (ScrubSecconds) ))
    xpos = ((time-scrubStart)/(ScrubSecconds))*self.imshape[1]
    return xpos

  def xToTime(self,x):
    if self.pixelScrubRatio>=1.0:
      return (x/self.imshape[1])*self.player.totalDuration
    xPercent = x/self.imshape[1]
    ScrubSecconds = (self.pixelScrubWidth*self.pixelScrubRatio)
    scrubStart = (self.scrubPercent* (self.player.totalDuration - (ScrubSecconds) ))
    return xPercent*(ScrubSecconds)+scrubStart

  def _handleCV2Click(self,event, x, y, flags, param):

    if self.draggingSeek:
      percentInc=0.0
      if x > self.imshape[1] - 10:
        percentInc = 0.01
      elif x<10:
        percentInc = -0.01
      if percentInc!=0.0:
        self.scrubPercent = min(1,max(0,percentInc+self.scrubPercent))


    if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_LBUTTONDBLCLK:
      if y<26:
        for button in self.buttons:
          bx,_,bw,_ = button['position']
          if bx-5 < x < bx+bw+5:
            self._handleCV2Keypress(ord(button['key']))
            break
      elif 26<y<46:
        self.draggingScrub=True
      elif 46<y<100:
      
        if self.timeCentre is not None and y<60:
          seekstart  = int(self.timeTox(self.timeCentre-(self.clipDuration/2)))
          seekend    = int(self.timeTox(self.timeCentre+(self.clipDuration/2)))

          if seekstart-10<x<seekstart+10:
            self.draggingStart=True
          elif seekend-10<x<seekend+10:
            self.draggingEnd=True
          else:
            self.draggingSeek=True

        else:
          self.draggingSeek=True
      elif 100<y<125:
        for cycle in self.player.sessionProperties.cycles:
          bx,_,bw,_ = cycle['position']
          if bx-5 < x < bx+bw+5:
            current = getattr(self.player.sessionProperties,cycle['prop'])
            ind = (cycle['cycle'].index(current)+1)%len(cycle['cycle'])
            setattr(self.player.sessionProperties,cycle['prop'],cycle['cycle'][ind])
            self.recauclateButtons()

    elif event == cv2.EVENT_LBUTTONUP:
      self.draggingSeek=False
      self.draggingScrub=False

      self.draggingStart=False
      self.draggingEnd=False

    elif event==cv2.EVENT_MOUSEWHEEL:
      increment = 0
      if flags>0:
        increment = 0.2
      else:
        increment = -0.2

      if y>46:
        self.clipDuration+=increment
        if self.timeCentre is not None:
          self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2))
      else:
        if self.pixelScrubRatio<1:
          pass
          """self.pixelScrubWidth = min(self.imshape[1],int(self.pixelScrubWidth+(increment*10)))""" 


    if self.draggingScrub:
      if self.pixelScrubRatio<1:
        self.scrubPercent = min(1.0,max(0.0,( x-(self.pixelScrubWidth//2) )/(self.imshape[1]-(self.pixelScrubWidth))))
      else:
        self.scrubPercent=0.5
    elif self.draggingSeek:
      tempTime = self.xToTime(x)
      if tempTime != self.timeCentre:
        self.timeCentre = tempTime
        self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2))
    elif self.draggingEnd or self.draggingStart:
      tempTime = self.xToTime(x)

      otherTime = self.timeCentre+(self.clipDuration/2)
      jumpLocation='Start'
      if self.draggingEnd:
        otherTime = self.timeCentre-(self.clipDuration/2)
        jumpLocation='End'
      self.clipDuration = abs(tempTime-otherTime)
      self.timeCentre   = (tempTime+otherTime)/2
      self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2),jumpLocation)


  def _handleCV2Keypress(self,key):
    if key in [ord(x['key']) for x in self.buttons]:
      self.player._handleMpvKeypress('d-',chr(key),bubble=False)


  def drawButtons(self):
    self.seeker[0:26,:,:]=self.colors.color_buttonBarBg
    for button in self.buttons:
      x,y,w,h = button['position']
      cv2.putText(self.seeker, button['text'], (x,y), self.font, 0.4, self.colors.color_button_text, 1, cv2.LINE_AA) 
      cv2.rectangle(self.seeker, (x-5,0),(x+w+5,y+h), self.colors.color_button, 1)

    if self.timeCentre is not None:
      cv2.putText(self.seeker, self.infoFormat.format(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2),self.clipDuration) , 
                  (self.infoXorigin,y), 
                  self.font, 0.4, self.colors.color_button_text, 1, cv2.LINE_AA) 
    else:
      cv2.putText(self.seeker, self.infoFormat.format(0,0,0) , (self.infoXorigin,y), self.font, 0.4, self.colors.color_button_text, 1, cv2.LINE_AA) 

  def drawScrubBar(self):
    self.seeker[26:46,:,:]=self.colors.color_scrbBg

    if self.pixelsNeededForIncrement is None: 
      self.pixelsNeededForIncrement = int(self.player.totalDuration*(1/self.seekResolution))
      self.pixelScrubRatio = self.imshape[1]/self.pixelsNeededForIncrement

      if self.pixelScrubRatio>1:
        self.pixelScrubRatio=1.0
        self.pixelScrubWidth = self.imshape[1]
      else:
        self.pixelScrubWidth = int(self.imshape[1]*self.pixelScrubRatio)

    scrubCentre = (self.imshape[1]-self.pixelScrubWidth) *self.scrubPercent
    scrubStart = self.pixelScrubWidth//2 + int(  scrubCentre-(self.pixelScrubWidth//2) )
    scrubEnd   = self.pixelScrubWidth//2 + int(  scrubCentre+(self.pixelScrubWidth//2) )

    self.seeker[26:46,scrubStart:scrubEnd,:]=self.colors.color_scrubcurentRange

    if self.pixelsNeededForIncrement is not None: 
      x = int((self.player.currentTime/self.player.totalDuration)* (self.imshape[1]-self.pixelScrubWidth) )+(self.pixelScrubWidth//2)
      x = int(max(min(x,self.imshape[1]-1),0))
      self.seeker[26:46,x:x,:]=self.colors.color_scrubcurrentTime

      if self.timeCentre is not None:
        x = int((self.timeCentre/self.player.totalDuration)* (self.imshape[1]-self.pixelScrubWidth) )+(self.pixelScrubWidth//2)
        x = int(max(min(x,self.imshape[1]-1),0))
        w = max(4,int(self.clipDuration*self.pixelScrubRatio/4))
        self.seeker[26:46,x-w:x+w,:]=self.colors.color_scrubSelectedRange


  def drawSeeKBar(self):

    tickStart = self.xToTime(0)
    tickStart = int((self.tickIncrement * round(tickStart/self.tickIncrement))-5)

    while 1:
      tickStart+=self.tickIncrement
      tx = int(self.timeTox(tickStart))
      if tx<0:
        pass
      elif tx>=self.imshape[1]:
        break
      else:
        self.seeker[80:85,tx,:] = self.colors.color_timelineTick
        (bw,bh),baseline = cv2.getTextSize(str(tickStart),self.font, 0.3, 1)
        cv2.putText(self.seeker, str(tickStart), (tx-(bw//2),96), self.font, 0.3, self.colors.color_timelineText, 1, cv2.LINE_AA)

    if self.pixelsNeededForIncrement is not None: 
      x = self.timeTox(self.player.currentTime)
      x = max(min(x,self.imshape[1]-1),0)
      self.seeker[46:,int(x),:]= self.colors.color_seekercurrentTime
    
    if self.timeCentre is not None:
      seekstart  = int(self.timeTox(self.timeCentre-(self.clipDuration/2)))
      seekcentre = int(self.timeTox(self.timeCentre))
      seekend    = int(self.timeTox(self.timeCentre+(self.clipDuration/2)))

      seekstart  = max(min(seekstart,self.imshape[1]-1),0)
      seekcentre = max(min(seekcentre,self.imshape[1]-1),0)
      seekend    = max(min(seekend,self.imshape[1]-1),0)

      self.seeker[46:56,seekstart:seekend,:] = self.colors.color_seekerHeader

      self.seeker[46:100,seekstart,:]  = self.colors.color_seekEdge
      self.seeker[46:60,seekstart-10:seekstart+10,:]=self.colors.color_seekStartTab

      self.seeker[46:100,seekcentre,:] = self.colors.color_seekCentre
      
      self.seeker[46:100,seekend,:]    = self.colors.color_seekEdge
      self.seeker[46:60,seekend-10:seekend+10,:]= self.colors.color_seekEndTab
  

  def drawCycleBar(self):
    self.seeker[100:126,:,:]=self.colors.color_cycleBarBg
    for cycle in self.player.sessionProperties.cycles:
      x,y,w,h = cycle['position']
      cv2.putText(self.seeker, cycle['text'].format( getattr(self.player.sessionProperties, cycle['prop'] ) ), 
                  (x,y), self.font, 0.4, self.colors.color_button_text , 1, cv2.LINE_AA) 
      cv2.rectangle(self.seeker, (x-5,100),(x+w+5,y+h), self.colors.color_button, 1)

  def update(self):
    self.seeker = np.zeros(self.imshape,np.uint8)
    self.seeker[:,:,:] = self.colors.color_bg
    if self.player.totalDuration is not None and self.player.totalDuration > 0:
      if self.clipDuration > self.player.totalDuration:
        self.clipDuration=self.player.totalDuration
      self.drawButtons()
      self.drawScrubBar()
      self.drawSeeKBar()
      self.drawCycleBar()

    cv2.imshow("seeker",self.seeker)
    self._handleCV2Keypress(cv2.waitKey(1))

import mpv
import cv2
import numpy as np
from win32api import GetSystemMetrics

class Cv2GUI():

  def __init__(self,player):
    self.imshape = (100,GetSystemMetrics(0)-10,3)
    self.seeker = np.zeros(self.imshape,np.uint8)
    self.player = player
    self.font = cv2.FONT_HERSHEY_SIMPLEX
    self.seekResolution=1.5
    self.seekInc=1/self.seekResolution
    self.clipDuration=30.0
    self.scrubPercent=0.5
    self.tickIncrement=10

    self.pixelsNeededForIncrement=None

    self.draggingSeek=False
    self.draggingScrub=False
    self.scrubOffset=0.0
    self.timeCentre=None


    cv2.namedWindow("seeker")
    cv2.setMouseCallback("seeker", self._handleCV2Click)

    self.buttons = [
      {'key':'q','text':'Queue Current Selection [Q]' },
      {'key':'e','text':'Next File [E]'},
      {'key':'r','text':'End File Selection [R]'},
      {'key':'t','text':'Toggle Logo [T]'},
      {'key':'y','text':'Toggle Footer [Y]'},
      {'key':'c','text':'Crop [C]'}
    ]

    xorigin=5
    for button in self.buttons:
      (bw,bh),baseline = cv2.getTextSize(button['text'],self.font, 0.4, 1)
      button['position'] = (xorigin,15,bw,bh)
      xorigin = xorigin+bw+15
    self.infoXorigin = xorigin

    self.infoFormat = "Start:{:01.2f}s End:{:01.2f}s Dur:{:01.2f}s"

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
    if event == cv2.EVENT_LBUTTONDOWN:
      if y<26:
        for button in self.buttons:
          bx,_,bw,_ = button['position']
          if bx-5 < x < bx+bw+5:
            self._handleCV2Keypress(ord(button['key']))
            break
      elif 26<y<46:
        self.draggingScrub=True
        print(self.scrubOffset)
      elif 46<y:
        self.draggingSeek=True
    elif event == cv2.EVENT_LBUTTONUP:
      self.draggingSeek=False
      self.draggingScrub=False
    elif event==cv2.EVENT_MOUSEWHEEL:
      if flags>0:
        self.clipDuration+=0.2
      else:
        self.clipDuration-=0.2
      if self.timeCentre is not None:
        self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2))

    if self.draggingScrub:
      if self.pixelScrubRatio<1:
        self.scrubPercent = min(1.0,max(0.0,( x-(self.pixelScrubWidth//2) )/(self.imshape[1]-(self.pixelScrubWidth))))
      else:
        self.scrubPercent=0.5
    elif self.draggingSeek:
      self.timeCentre = self.xToTime(x)
      self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2))

  def _handleCV2Keypress(self,key):
    if key in [ord(x['key']) for x in self.buttons]:
      self.player._handleMpvKeypress('d-',chr(key),bubble=False)


  def drawButtons(self):
    self.seeker[0:26,:,:]=(10,90,10)
    for button in self.buttons:
      x,y,w,h = button['position']
      cv2.putText(self.seeker, button['text'], (x,y), self.font, 0.4, (50,255,50), 1, cv2.LINE_AA) 
      cv2.rectangle(self.seeker, (x-5,0),(x+w+5,y+h), (50,255,50), 1)

    if self.timeCentre is not None:
      cv2.putText(self.seeker, self.infoFormat.format(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2),self.clipDuration) , (self.infoXorigin,y), self.font, 0.4, (50,255,50), 1, cv2.LINE_AA) 
    else:
      cv2.putText(self.seeker, self.infoFormat.format(0,0,0) , (self.infoXorigin,y), self.font, 0.4, (50,255,50), 1, cv2.LINE_AA) 

  def drawScrubBar(self):
    self.seeker[26:46,:,:]=(90,10,10)

    if self.pixelsNeededForIncrement is None: 
      self.pixelsNeededForIncrement = int(self.player.totalDuration*(1/self.seekResolution))
      
      print(self.pixelsNeededForIncrement)

      self.pixelScrubRatio = self.imshape[1]/self.pixelsNeededForIncrement

      if self.pixelScrubRatio>1:
        self.pixelScrubRatio=1.0
        self.pixelScrubWidth = self.imshape[1]
      else:
        self.pixelScrubWidth = int(self.imshape[1]*self.pixelScrubRatio)

    scrubCentre = (self.imshape[1]-self.pixelScrubWidth) *self.scrubPercent
    scrubStart = self.pixelScrubWidth//2 + int(  scrubCentre-(self.pixelScrubWidth//2) )
    scrubEnd   = self.pixelScrubWidth//2 + int(  scrubCentre+(self.pixelScrubWidth//2) )

    self.seeker[26:46,scrubStart:scrubEnd,:]=(250,10,10)

    if self.pixelsNeededForIncrement is not None: 
      x = int((self.player.currentTime/self.player.totalDuration)*self.imshape[1])
      x = max(min(x,self.imshape[1]-1),0)
      self.seeker[26:46,int(x),:]=(255,255,255)
    
  def drawSeeKBar(self):

    if self.pixelsNeededForIncrement is not None: 
      x = self.timeTox(self.player.currentTime)
      x = max(min(x,self.imshape[1]-1),0)
      self.seeker[46:,int(x),:]=(250,250,250)
    
    if self.timeCentre is not None:
      seekstart  = int(self.timeTox(self.timeCentre-(self.clipDuration/2)))
      seekcentre = int(self.timeTox(self.timeCentre))
      seekend    = int(self.timeTox(self.timeCentre+(self.clipDuration/2)))

      seekstart = max(min(seekstart,self.imshape[1]-1),0)
      seekcentre = max(min(seekcentre,self.imshape[1]-1),0)
      seekend = max(min(seekend,self.imshape[1]-1),0)

      self.seeker[46:56,seekstart:seekend,:]=(90,90,90)
      self.seeker[46:,seekstart,:]  =(120,120,120)
      self.seeker[46:,seekcentre,:] =(220,220,220)
      self.seeker[46:,seekend,:]    =(120,120,120)
      


  def update(self):
    self.seeker = np.zeros(self.imshape,np.uint8)
    if self.player.totalDuration is not None:
      self.drawButtons()
      self.drawScrubBar()
      self.drawSeeKBar()

    cv2.imshow("seeker",self.seeker)
    self._handleCV2Keypress(cv2.waitKey(1))
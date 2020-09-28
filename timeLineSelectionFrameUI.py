
import tkinter as tk
import tkinter.ttk as ttk

import datetime
import threading

import time
def debounce(wait):
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                debounced._timer = None
                debounced._last_call = time.time()
                return fn(*args, **kwargs)

            time_since_last_call = time.time() - debounced._last_call
            if time_since_last_call >= wait:
                return call_it()

            if debounced._timer is None:
                debounced._timer = threading.Timer(wait - time_since_last_call, call_it)
                debounced._timer.start()
        debounced._timer = None
        debounced._last_call = 0
        return debounced
    return decorator

class TimeLineSelectionFrameUI(ttk.Frame):

  def __init__(self, master, controller, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.controller = controller

    self.timeline_canvas = tk.Canvas(self,width=200, height=100, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=1,column=0,sticky="nesw")
    self.grid_rowconfigure(1, weight=1)
    self.grid_columnconfigure(0, weight=1)

    self.timeline_canvas_popup_menu = tk.Menu(self, tearoff=0)
    self.timeline_canvas_popup_menu.add_command(label="Add new subclip",
                                                command=self.canvasPopupAddNewSubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Delete subclip",
                                                command=self.canvasPopupRemoveSubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Add new interest mark",
                                                command=self.canvasPopupAddNewInterestMarkCallback)

    self.timeline_canvas_popup_menu.add_command(label="Nudge to lowest error +- 1s",
                                                command=self.canvasPopupFindLowestError1s)

    self.timeline_canvas_popup_menu.add_command(label="Nudge to lowest error +- 2s",
                                                command=self.canvasPopupFindLowestError2s)

    self.timeline_canvas_popup_menu.add_command(label="Run scene scene change detection",
                                                command=self.canvasPopupRunSceneChangeDetection)

    self.timeline_canvas_last_right_click_x=None

    self.timeline_canvas.bind("<Button-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<Button-3>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-3>", self.timelineMousePress)
    self.timeline_canvas.bind("<Button-2>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-2>", self.timelineMousePress)
    self.timeline_canvas.bind("<Enter>", self.timelineMousePress)
    self.timeline_canvas.bind("<Leave>", self.timelineMousePress)
    self.timeline_canvas.bind("<Motion>", self.timelineMousePress)

    self.timeline_canvas.bind("<MouseWheel>", self.timelineMousewheel)

    self.timeline_canvas.bind('<Configure>',self.reconfigure)

    self.timelineZoomFactor=1.0
    self.currentZoomRangeMidpoint=0.5
    self.canvasSeekPointer    = self.timeline_canvas.create_line(0, 0, 0, self.timeline_canvas.winfo_height(),fill="white")
    self.canvasTimestampLabel = self.timeline_canvas.create_text(0, 0, text='XXX',fill="white")

    self.targetTrim=0.25
    self.defaultSliceDuration=10.0
    
    self.handleWidth=10
    self.handleHeight=30
    self.midrangeHeight=20

    self.canvasRegionCache = {}
    self.timeline_mousedownstate={}
    self.tickmarks=[]
    self.uiDirty=True
    self.clickTarget=None

    self.rangeHeaderBG = self.timeline_canvas.create_rectangle(0,0,10,self.winfo_width(),fill="#4E4E4E")
    self.rangeHeaderActiveRange = self.timeline_canvas.create_rectangle(0,0,10,self.winfo_width(),fill="#9E9E9E")
    
    self.rangeHeaderActiveMid = self.timeline_canvas.create_line(0,self.winfo_width()/2,10,self.winfo_width()/2,fill="#4E4E4E")

    self.rangeHeaderClickStart=None

    self.canvasHeaderSeekPointer = self.timeline_canvas.create_line(0, 0, 0,10,fill="white")
    self.lastSeek=None

  def reconfigure(self,e):
    self.uiDirty=True
    if self.controller.getTotalDuration() is not None:
      self.updateCanvas()

  def resetForNewFile(self):
    self.timelineZoomFactor=1.0
    self.currentZoomRangeMidpoint=0.5
    self.uiDirty=True
    self.timeline_canvas.delete('fileSpecific')
    self.canvasRegionCache={}


  @staticmethod
  def pureGetClampedCenterPosAndRange(totalDuration,zoomFactor,currentMidpoint):

    outputDuration = totalDuration*(1/zoomFactor)
    minPercent     = (1/zoomFactor)/2
    center         = min(max(minPercent,currentMidpoint),1-minPercent)
    lowerRange     = (totalDuration*center)-(outputDuration/2)
    return outputDuration,center,lowerRange

  def getClampedCenterPosAndRange(self,update=True,negative=False):

    result  = self.pureGetClampedCenterPosAndRange(self.controller.getTotalDuration(),
                                                   self.timelineZoomFactor,
                                                   self.currentZoomRangeMidpoint)
    
    outputDuration,center,lowerRange = result
    if update:
      self.currentZoomRangeMidpoint=center

    return center,lowerRange,outputDuration

  def secondsToXcoord(self,seconds,update=True,negative=False):
    center,rangeStart,duration = self.getClampedCenterPosAndRange(update=update,negative=negative)
    return (((seconds-rangeStart))/duration)*self.winfo_width()

  def xCoordToSeconds(self,xpos,update=True,negative=False):
    center,rangeStart,duration = self.getClampedCenterPosAndRange(update=update,negative=negative)
    return rangeStart+( (xpos/self.winfo_width())*duration )

  def timelineMousewheel(self,e):      
      newZoomFactor = self.timelineZoomFactor
      if e.delta>0:
        newZoomFactor *= 1.01
        self.uiDirty=True
      else:
        newZoomFactor *= 0.99
        self.uiDirty=True
      newZoomFactor = min(max(1,newZoomFactor),50)
      if newZoomFactor == self.timelineZoomFactor:
        return
      self.timelineZoomFactor=newZoomFactor


  @debounce(0.1)
  def seekto(self,seconds):
    if self.lastSeek is not None and abs(self.lastSeek-seconds)<0.01:
      return
    else:
      self.lastSeek=seconds
    self.controller.seekTo(seconds)

  def timelineMousePress(self,e):
    if not self.controller.getIsPlaybackStarted():
      return

    self.focus_set() 

    if str(e.type) in ('ButtonPress','ButtonRelease'):
      self.timeline_mousedownstate[e.num] = str(e.type)=='ButtonPress'

      if (e.num==1 and e.y<20) or e.num==2:
        self.rangeHeaderClickStart= self.currentZoomRangeMidpoint-(e.x/self.winfo_width())

      elif e.num==1 and e.y>self.winfo_height()-self.handleHeight:

        ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
        for rid,(sts,ens) in ranges:
          st=self.secondsToXcoord(sts)
          en=self.secondsToXcoord(ens)
          if st-self.handleWidth<e.x<st+2:
            self.clickTarget = (rid,'s',sts,ens)
            self.controller.pause()
            break
          elif en-2<e.x<en+self.handleWidth:
            self.clickTarget = (rid,'e',sts,ens)

            self.controller.pause()
            break
          elif st<e.x<en and e.y>self.winfo_height()-self.midrangeHeight:
            self.clickTarget = (rid,'m',sts,ens)
            self.controller.pause()
            break

    if str(e.type) in ('ButtonRelease') and e.num in (1,2):
      self.clickTarget = None
      self.rangeHeaderClickStart=None
      self.controller.play()

    if self.timeline_mousedownstate.get(2,False):
      if self.rangeHeaderClickStart is not None:
        self.currentZoomRangeMidpoint = (e.x/self.winfo_width())+self.rangeHeaderClickStart
        self.uiDirty=True

    if self.timeline_mousedownstate.get(1,False):
      if self.clickTarget is None:
        if self.rangeHeaderClickStart is not None:

          self.currentZoomRangeMidpoint = (e.x/self.winfo_width())+self.rangeHeaderClickStart
          self.uiDirty=True
        else:          
          seconds = self.xCoordToSeconds(e.x)
          self.controller.pause()
          self.seekto(seconds)
          self.controller.updateStatus('Seeking to {}s'.format(seconds))

          if e.x>self.winfo_width()-2:
            self.currentZoomRangeMidpoint+=0.001
          if e.x<2:
            self.currentZoomRangeMidpoint-=0.001
      else:
        rid,pos,os,oe = self.clickTarget

        targetSeconds = self.xCoordToSeconds(e.x)

        ctrl  = (e.state & 0x4) != 0
        if ctrl:

          targetSeconds = round(targetSeconds)

        self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,targetSeconds)
        

        if pos == 's':
          self.controller.seekTo( targetSeconds )

        elif pos == 'e':
          self.controller.seekTo( targetSeconds-0.1 )
        elif pos == 'm':
          targetSeconds = targetSeconds+((oe-os)/2)
          self.controller.seekTo( targetSeconds-0.1 )

    if str(e.type) == 'ButtonPress':
      if e.num==3:      
        self.timeline_canvas_last_right_click_x=e.x
        self.timeline_canvas_popup_menu.tk_popup(e.x_root,e.y_root)

  def updateCanvas(self):
    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
    timelineWidth = self.winfo_width()
    timelineHeight = self.winfo_height()

    self.timeline_canvas.coords(self.rangeHeaderBG,0,0,timelineWidth,20,)

    startpc = self.xCoordToSeconds(0)/self.controller.getTotalDuration()
    endpc   = self.xCoordToSeconds(timelineWidth)/self.controller.getTotalDuration()

    self.timeline_canvas.coords(self.rangeHeaderActiveRange,int(startpc*timelineWidth),0,(endpc*timelineWidth),20)

    seekpc = self.controller.getCurrentPlaybackPosition()/self.controller.getTotalDuration()
    self.timeline_canvas.coords(self.canvasHeaderSeekPointer,seekpc*timelineWidth,0,seekpc*timelineWidth,20)
    
    seekMidpc  = (startpc+endpc)/2
    self.timeline_canvas.coords(self.rangeHeaderActiveMid,seekMidpc*timelineWidth,0,seekMidpc*timelineWidth,20)

    if self.uiDirty:
      self.timeline_canvas.delete('ticks')

      for ts,interesttype in self.controller.getInterestMarks():
        print(ts,interesttype)
        tx = int(self.secondsToXcoord(ts))
        if interesttype=='manual':
          tm = self.timeline_canvas.create_polygon(tx-5, 40,tx+5, 40, tx, 45,fill="#ead9a7",tags='ticks')
        if interesttype=='sceneChange':
          tm = self.timeline_canvas.create_polygon(tx-5, 40,tx+5, 40, tx, 45,fill="green",tags='ticks')

      self.tickmarks=[]
      tickStart = self.xCoordToSeconds(0)
      tickIncrement=  (self.xCoordToSeconds(timelineWidth)-self.xCoordToSeconds(0))/10

      tickStart = int((tickIncrement * round(tickStart/tickIncrement))-tickIncrement)

      while 1:
        tickStart+=tickIncrement
        tx = int(self.secondsToXcoord(tickStart))
        if tx<0:
          pass
        elif tx>=self.winfo_width():
          break
        else:          
          tm = self.timeline_canvas.create_line(tx, 20, tx, 22,fill="white",tags='ticks') 
          tm = self.timeline_canvas.create_text(tx, 30,text=str(datetime.timedelta(seconds=round(self.xCoordToSeconds(tx)))),fill="white",tags='ticks') 



    currentPlaybackX =  self.secondsToXcoord(self.controller.getCurrentPlaybackPosition())
    self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,55,currentPlaybackX,timelineHeight )
    self.timeline_canvas.coords(self.canvasTimestampLabel,currentPlaybackX,45)
    self.timeline_canvas.itemconfig(self.canvasTimestampLabel,text=str(datetime.timedelta(seconds=round(self.xCoordToSeconds(currentPlaybackX)))))
    activeRanges=set()
    for rid,(s,e) in list(ranges):

      if s<self.controller.getCurrentPlaybackPosition()<e:
        self.controller.setLoopPos(s,e)

      
      sx= self.secondsToXcoord(s)
      ex= self.secondsToXcoord(e)
      trimpreend    = self.secondsToXcoord(s+self.targetTrim)
      trimpostStart = self.secondsToXcoord(e-self.targetTrim)

      activeRanges.add(rid)
      if (rid,'main') in self.canvasRegionCache:

        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'startHandle')],sx-self.handleWidth, timelineHeight-self.handleHeight, sx+0, timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'main')],sx, timelineHeight-self.midrangeHeight, ex, timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'endHandle')],ex-0, timelineHeight-self.handleHeight, ex+self.handleWidth, timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'label')],int((sx+ex)/2),timelineHeight-self.midrangeHeight-20)
        self.timeline_canvas.itemconfig(self.canvasRegionCache[(rid,'label')],text="{}s".format(str(datetime.timedelta(seconds=round(e-s,2))) ) )
        
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'preTrim')],sx, timelineHeight-self.midrangeHeight, trimpreend, timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'postTrim')],trimpostStart, timelineHeight-self.midrangeHeight, ex, timelineHeight)



        hstx = (s/self.controller.getTotalDuration())*timelineWidth
        henx = (e/self.controller.getTotalDuration())*timelineWidth

        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'headerR')],hstx,10, henx, 20)
        

      else:
        print('add',rid)

        self.canvasRegionCache[(rid,'main')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#69dbbe",width=0, tags='fileSpecific')
        self.canvasRegionCache[(rid,'startHandle')] = self.timeline_canvas.create_rectangle(sx-self.handleWidth, timelineHeight-self.handleHeight, sx+0, timelineHeight, fill="#69bfdb",width=0, tags='fileSpecific')
        self.canvasRegionCache[(rid,'endHandle')] = self.timeline_canvas.create_rectangle(ex-0, timelineHeight-self.handleHeight, ex+self.handleWidth, timelineHeight, fill="#db6986",width=0, tags='fileSpecific')
        self.canvasRegionCache[(rid,'label')] = self.timeline_canvas.create_text( int((sx+ex)/2) , timelineHeight-self.midrangeHeight-20,text="{}s".format(str(datetime.timedelta(seconds=round(e-s,2))).strip('0').strip(':')),fill="white", tags='fileSpecific') 
    
        self.canvasRegionCache[(rid,'preTrim')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, trimpreend, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
        self.canvasRegionCache[(rid,'postTrim')] = self.timeline_canvas.create_rectangle(trimpostStart, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')

        hstx = (s/self.controller.getTotalDuration())*timelineWidth
        henx = (e/self.controller.getTotalDuration())*timelineWidth
        self.canvasRegionCache[(rid,'headerR')] = self.timeline_canvas.create_rectangle(hstx,10, henx, 20, fill="#299b9b",width=0, tags='fileSpecific')
        
    for (rid,name),i in list(self.canvasRegionCache.items()):
      if rid not in activeRanges:
        print('remove',rid)
        self.timeline_canvas.delete(i)
        del self.canvasRegionCache[(rid,name)]
    self.uiDirty=False

  def setUiDirtyFlag(self):
    self.uiDirty=True    

  def canvasPopupRemoveSubClipCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.removeSubclip((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.removeSubclip((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None

  def canvasPopupAddNewInterestMarkCallback(self):
    print(self.timeline_canvas_last_right_click_x,)
    if self.timeline_canvas_last_right_click_x is not None:
      self.controller.addNewInterestMark( self.xCoordToSeconds(self.timeline_canvas_last_right_click_x))
      self.uiDirty=True

  def canvasPopupAddNewSubClipCallback(self):
    print(self.timeline_canvas_last_right_click_x,)
    if self.timeline_canvas_last_right_click_x is not None:
      pre = self.defaultSliceDuration*0.5
      post = self.defaultSliceDuration*0.5
      self.controller.addNewSubclip( self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)-pre,self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)+post  )

    self.timeline_canvas_last_right_click_x=None

  def canvasPopupRunSceneChangeDetection(self):
    self.controller.runSceneChangeDetection()

  def canvasPopupFindLowestError1s(self):
    self.findLowestErrorForBetterLoop(1.0)

  def canvasPopupFindLowestError2s(self):
    self.findLowestErrorForBetterLoop(2.0)

  def findLowestErrorForBetterLoop(self,secondsChange):
    
    if self.timeline_canvas_last_right_click_x is not None:
      selectedRange = None
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          selectedRange=rid
          break
        if lower<e<upper or lower<s<upper:
          selectedRange=rid
          break
      if selectedRange is not None:
        self.controller.findLowestErrorForBetterLoop(rid,secondsChange)
    self.timeline_canvas_last_right_click_x=None

  def setDefaultsliceDuration(self,value):
    self.defaultSliceDuration=value

  def setTargetTrim(self,value):
    self.targetTrim=value


if __name__ == '__main__':
  import webmGenerator
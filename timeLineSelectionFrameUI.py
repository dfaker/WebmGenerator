
import tkinter as tk
import tkinter.ttk as ttk

import datetime
import threading
from math import floor
import time
import logging

def format_timedelta(value, time_format="{days} days, {hours2}:{minutes2}:{seconds2}"):

    if hasattr(value, 'seconds'):
        seconds = value.seconds + value.days * 24 * 3600
    else:
        seconds = value

    seconds_total = seconds

    minutes = int(floor(seconds / 60))
    minutes_total = minutes
    seconds -= minutes * 60

    if hasattr(value, 'microseconds'):
      seconds += (value.microseconds/1000000)
      seconds = round(seconds,2)

    hours = int(floor(minutes / 60))
    hours_total = hours
    minutes -= hours * 60

    days = int(floor(hours / 24))
    days_total = days
    hours -= days * 24

    years = int(floor(days / 365))
    years_total = years
    days -= years * 365

    return time_format.format(**{
        'seconds': seconds,
        'seconds2': str(seconds).zfill(2),
        'minutes': minutes,
        'minutes2': str(minutes).zfill(2),
        'hours': hours,
        'hours2': str(hours).zfill(2),
        'days': days,
        'years': years,
        'seconds_total': seconds_total,
        'minutes_total': minutes_total,
        'hours_total': hours_total,
        'days_total': days_total,
        'years_total': years_total,
    })


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

    self.timeline_canvas = tk.Canvas(self,width=200, height=150, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=1,column=0,sticky="nesw")
    self.grid_rowconfigure(1, weight=1)
    self.grid_columnconfigure(0, weight=1)

    self.timeline_canvas_popup_menu = tk.Menu(self, tearoff=0)

    self.timeline_canvas_popup_menu.add_command(label="Add new subclip",command=self.canvasPopupAddNewSubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Delete subclip",command=self.canvasPopupRemoveSubClipCallback)
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Clone subclip",command=self.canvasPopupCloneSubClipCallback)
    self.timeline_canvas_popup_menu.add_command(label="Expand subclip to interest marks",command=self.canvasPopupExpandSublcipToInterestMarksCallback)
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Add new interest mark",command=self.canvasPopupAddNewInterestMarkCallback)
    self.timeline_canvas_popup_menu.add_separator()
    self.timeline_canvas_popup_menu.add_command(label="Nudge to lowest error +- 1s",command=self.canvasPopupFindLowestError1s)
    self.timeline_canvas_popup_menu.add_command(label="Nudge to lowest error +- 2s",command=self.canvasPopupFindLowestError2s)
    
    
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

    self.timeline_canvas.focus_set()
    self.timeline_canvas.bind('<Left>', self.keyboardLeft)
    self.timeline_canvas.bind('<Right>', self.keyboardRight)


    self.timelineZoomFactor=1.0
    self.dragPreviewPos=0.1
    self.currentZoomRangeMidpoint=0.5
    self.canvasSeekPointer    = self.timeline_canvas.create_line(0, 0, 0, self.timeline_canvas.winfo_height(),fill="white")
    self.canvasTimestampLabel = self.timeline_canvas.create_text(0, 0, text='XXX',fill="white")

    self.targetTrim=0.25
    self.defaultSliceDuration=10.0
    
    self.handleWidth=10
    self.handleHeight=30
    self.midrangeHeight=20
    self.miniMidrangeHeight=7

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

    self.resumeplaybackTimer=None

    self.lastClickedEndpoint = None
    self.framesRequested = False
    self.previewFrames = {}

  def keyboardRight(self,e):
    if self.lastClickedEndpoint is not None:
      self.incrementEndpointPosition(1,*self.lastClickedEndpoint)


  def keyboardLeft(self,e):
    if self.lastClickedEndpoint is not None:
      self.incrementEndpointPosition(-1,*self.lastClickedEndpoint)


  def incrementEndpointPosition(self,increment,markerrid,pos):
    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
    for rid,(sts,ens) in ranges:
      if rid == markerrid:
        newTs = 0

        self.controller.pause()
        try:
            self.resumeplaybackTimer.cancel()
        except(AttributeError):
            pass
        self.resumeplaybackTimer = threading.Timer(0.8, self.controller.play)
        self.resumeplaybackTimer.start()

        if pos == 's':
          self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,sts+(increment*0.05))
          self.seekto(sts+(increment*0.05))
        elif pos == 'e':
          self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,ens+(increment*0.05))
          self.seekto(ens+(increment*0.05)-0.001)
        break

  def setDragPreviewPos(self,value):
    self.dragPreviewPos = value

  def reconfigure(self,e):
    self.uiDirty=True
    if self.controller.getTotalDuration() is not None:
      self.updateCanvas()

  def resetForNewFile(self):
    self.timelineZoomFactor=1.0
    self.currentZoomRangeMidpoint=0.5
    self.uiDirty=True
    self.timeline_canvas.delete('fileSpecific')
    self.timeline_canvas.delete('ticks')
    self.canvasRegionCache={}
    self.controller.requestTimelinePreviewFrames(None,None,None,None,None,self.frameResponseCallback)
    self.framesRequested = False;
    self.timeline_canvas.delete('previewFrame')
    self.timeline_canvas.coords(self.canvasSeekPointer, -100,45+55,-100,0 )
    self.timeline_canvas.coords(self.canvasTimestampLabel,-100,45+45)
    self.previewFrames = {}


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
    try:
      center,rangeStart,duration = self.getClampedCenterPosAndRange(update=update,negative=negative)
      return (((seconds-rangeStart))/duration)*self.winfo_width()
    except Exception as e:
      logging.error('Seconds to x coord Exception',exc_info=e)
      return 0

  def xCoordToSeconds(self,xpos,update=True,negative=False):
    try:
      center,rangeStart,duration = self.getClampedCenterPosAndRange(update=update,negative=negative)
      return rangeStart+( (xpos/self.winfo_width())*duration )
    except Exception as e:
      logging.error('x coord to seconds Exception',exc_info=e)
      return 0

  def timelineMousewheel(self,e):    
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      ctrl  = (e.state & 0x4) != 0
      for rid,(sts,ens) in ranges:          
        st=self.secondsToXcoord(sts)
        en=self.secondsToXcoord(ens)
        if st<=e.x<=en and e.y>self.winfo_height()-(self.midrangeHeight+10):
          targetSeconds = (sts+ens)/2
          if e.delta>0:
            targetSeconds+=0.01
          else:
            targetSeconds-=0.01
          self.controller.pause()
          try:
              self.resumeplaybackTimer.cancel()
          except(AttributeError):
              pass
          self.resumeplaybackTimer = threading.Timer(0.8, self.controller.play)
          self.resumeplaybackTimer.start()
          self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,'m',targetSeconds)
          if ctrl:
            self.controller.seekTo( ((targetSeconds-((ens-sts)/2))) + self.dragPreviewPos )
          else:
            self.controller.seekTo( ((targetSeconds+((ens-sts)/2))) - self.dragPreviewPos )
          break

      else:
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
      self.timeline_canvas.config(cursor="no")
      return    

    enableDraggableHint=False
    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())

    if e.y<20:
      enableDraggableHint=True
    elif self.clickTarget is not None:
      enableDraggableHint=True
    else:
      for rid,(sts,ens) in ranges:
        st=self.secondsToXcoord(sts)
        en=self.secondsToXcoord(ens)

        if (st<e.x<en and e.y>self.winfo_height()-self.midrangeHeight) or (st-self.handleWidth<e.x<en+self.handleWidth and e.y>self.winfo_height()-self.miniMidrangeHeight):
          enableDraggableHint=True
        elif st-self.handleWidth<e.x<st+2:
          enableDraggableHint=True
        elif en-2<e.x<en+self.handleWidth:
          enableDraggableHint=True

    if enableDraggableHint:
        self.timeline_canvas.config(cursor="sb_h_double_arrow")
    else:
        self.timeline_canvas.config(cursor="crosshair")



    ctrl  = (e.state & 0x4) != 0
    

    self.timeline_canvas.focus_set()

    if str(e.type) in ('ButtonPress'):
      self.lastClickedEndpoint=None
      self.timelineMousePressOffset=0

    if str(e.type) in ('ButtonPress','ButtonRelease'):
      self.timeline_mousedownstate[e.num] = str(e.type)=='ButtonPress'

      if (e.num==1 and e.y<20) or e.num==2:
        self.rangeHeaderClickStart= self.currentZoomRangeMidpoint-(e.x/self.winfo_width())

      elif e.num==1 and e.y>self.winfo_height()-self.handleHeight:

        for rid,(sts,ens) in ranges:
          st=self.secondsToXcoord(sts)
          en=self.secondsToXcoord(ens)

          if (st<e.x<en and e.y>self.winfo_height()-self.midrangeHeight) or (st-self.handleWidth<e.x<en+self.handleWidth and e.y>self.winfo_height()-self.miniMidrangeHeight):
            self.clickTarget = (rid,'m',sts,ens)
            self.timelineMousePressOffset = ((st+en)/2)-e.x
            self.controller.pause()
            break
          elif st-self.handleWidth<e.x<st+2:
            self.clickTarget = (rid,'s',sts,ens)
            self.lastClickedEndpoint=(rid,'s')
            self.timelineMousePressOffset = st-e.x
            self.controller.pause()
            break
          elif en-2<e.x<en+self.handleWidth:
            self.clickTarget = (rid,'e',sts,ens)
            self.lastClickedEndpoint=(rid,'e')
            self.timelineMousePressOffset = en-e.x
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
          self.currentZoomRangeMidpoint = ((e.x)/self.winfo_width())+self.rangeHeaderClickStart
          self.uiDirty=True
        else:          
          print(self.timelineMousePressOffset)
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

        targetSeconds = self.xCoordToSeconds(e.x+self.timelineMousePressOffset)

        self.controller.updatePointForClip(self.controller.getcurrentFilename(),rid,pos,targetSeconds)
  
        if pos == 's':
          self.controller.seekTo( targetSeconds )
        elif pos == 'e':
          self.controller.seekTo( targetSeconds-0.1 )
        elif pos == 'm':
          if ctrl:
            targetSeconds = targetSeconds-((oe-os)/2)
          else:
            targetSeconds = targetSeconds+((oe-os)/2)
          self.controller.seekTo( targetSeconds-self.dragPreviewPos )



    if str(e.type) == 'ButtonPress':
      if e.num==3:      
        self.timeline_canvas_last_right_click_x=e.x
        self.timeline_canvas_popup_menu.tk_popup(e.x_root,e.y_root)



  def frameResponseCallback(self,filename,timestamp,frameWidth,frameData):
    previewData = tk.PhotoImage(data=frameData)
    if filename == self.controller.getcurrentFilename():
      previewName = ('previewFrame',timestamp)

      if previewName in self.canvasRegionCache:
        self.timeline_canvas.itemconfig(self.canvasRegionCache[previewName],image=previewData, anchor='n',tags='previewFrame')
      self.previewFrames[timestamp] = (frameWidth,previewData)

  def requestFrames(self,filename,startTime,Endtime,timelineWidth,frameWidth):
    self.framesRequested=self.controller.requestTimelinePreviewFrames(filename,startTime,Endtime,frameWidth,timelineWidth,self.frameResponseCallback)

  def updateCanvas(self):

    if self.controller.getcurrentFilename() is None or self.controller.getTotalDuration() is None:
      return

    for ts,(frameWidth,frameData) in list(self.previewFrames.items()):
      previewName = ('previewFrame',ts)
      ts_x = self.secondsToXcoord(ts)
      if previewName not in self.canvasRegionCache:
        self.canvasRegionCache[previewName] = self.timeline_canvas.create_image(ts_x, 20, image=frameData, anchor='n',tags='previewFrame')
        self.timeline_canvas.lower(self.canvasRegionCache[previewName])
      elif self.uiDirty:
        self.timeline_canvas.coords(self.canvasRegionCache[previewName],ts_x, 20)



    ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
    timelineWidth = self.winfo_width()
    timelineHeight = self.winfo_height()

    self.timeline_canvas.coords(self.rangeHeaderBG,0,0,timelineWidth,20,)

    startpc = self.xCoordToSeconds(0)/self.controller.getTotalDuration()
    endpc   = self.xCoordToSeconds(timelineWidth)/self.controller.getTotalDuration()

    if not self.framesRequested and self.controller.getcurrentFilename() is not None and self.controller.getTotalDuration() is not None:
      self.requestFrames(self.controller.getcurrentFilename(),0,self.controller.getTotalDuration(),timelineWidth,90)

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
          tm = self.timeline_canvas.create_polygon(tx-5, 45+40,tx+5, 45+40, tx, 45+45,fill="#ead9a7",tags='ticks')
        if interesttype=='sceneChange':
          tm = self.timeline_canvas.create_polygon(tx-5, 45+40,tx+5, 45+40, tx, 45+45,fill="green",tags='ticks')

      self.tickmarks=[]
      tickStart = self.xCoordToSeconds(0)
      tickIncrement=  (self.xCoordToSeconds(timelineWidth)-self.xCoordToSeconds(0))/20

      tickStart = int((tickIncrement * round(tickStart/tickIncrement))-tickIncrement)

      while 1:
        tickStart+=tickIncrement
        tx = int(self.secondsToXcoord(tickStart))
        if tx<0:
          pass
        elif tx>=self.winfo_width():
          break
        else:          
          tm = self.timeline_canvas.create_line(tx, 45+20, tx, 45+22,fill="white",tags='ticks') 
          tm = self.timeline_canvas.create_text(tx, 45+30,text=format_timedelta(  datetime.timedelta(seconds=round(self.xCoordToSeconds(tx))), '{hours_total}:{minutes2}:{seconds2}'),fill="white",tags='ticks') 

    currentPlaybackX =  self.secondsToXcoord(self.controller.getCurrentPlaybackPosition())
    self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,45+55,currentPlaybackX,timelineHeight )
    self.timeline_canvas.coords(self.canvasTimestampLabel,currentPlaybackX,45+45)
    self.timeline_canvas.itemconfig(self.canvasTimestampLabel,text=format_timedelta(datetime.timedelta(seconds=round(self.xCoordToSeconds(currentPlaybackX))), '{hours_total}:{minutes2}:{seconds2}'))
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



        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'main')],sx, timelineHeight-self.midrangeHeight, ex, timelineHeight)

        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'startHandle')],sx-self.handleWidth, timelineHeight-self.handleHeight, sx+0, timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'endHandle')],ex-0, timelineHeight-self.handleHeight, ex+self.handleWidth, timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'label')],int((sx+ex)/2),timelineHeight-self.midrangeHeight-20)
        self.timeline_canvas.itemconfig(self.canvasRegionCache[(rid,'label')],text="{}s".format(format_timedelta(datetime.timedelta(seconds=round(e-s,2)), '{hours_total}:{minutes2}:{seconds2}') ) )
        
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'preTrim')],sx, timelineHeight-self.midrangeHeight, min(trimpreend,ex), timelineHeight)
        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'postTrim')],max(trimpostStart,sx), timelineHeight-self.midrangeHeight, ex, timelineHeight)

        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'miniDrag')],sx-self.handleWidth, timelineHeight-self.miniMidrangeHeight, ex+self.handleWidth, timelineHeight)


        if self.lastClickedEndpoint is None:
          self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],width=0)
          self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],width=0)
        elif self.lastClickedEndpoint[0] == rid and self.lastClickedEndpoint[1] == 's':
          self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],width=1,outline='white')
          self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],width=0)
        elif self.lastClickedEndpoint[0] == rid and self.lastClickedEndpoint[1] == 'e':
          self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'endHandle')],width=1,outline='white')
          self.timeline_canvas.itemconfigure(self.canvasRegionCache[(rid,'startHandle')],width=0)


        for dtx in (-1,1):
          for dty in (-1,0,1,2):
            dst_tn = 'startHandleDot'+str(dtx)+str(dty)
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,dst_tn)], sx-(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , sx-(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1 ) 
            dst_tn = 'endHandleDot'+str(dtx)+str(dty)
            self.timeline_canvas.coords(self.canvasRegionCache[(rid,dst_tn)], ex+(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , ex+(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1 )


        hstx = (s/self.controller.getTotalDuration())*timelineWidth
        henx = (e/self.controller.getTotalDuration())*timelineWidth

        self.timeline_canvas.coords(self.canvasRegionCache[(rid,'headerR')],hstx,10, henx, 20)
        
      else:
        print('add',rid)
        

            
        self.canvasRegionCache[(rid,'main')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#69dbbe",width=0, tags='fileSpecific')
        self.canvasRegionCache[(rid,'preTrim')] = self.timeline_canvas.create_rectangle(sx, timelineHeight-self.midrangeHeight, trimpreend, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
        self.canvasRegionCache[(rid,'postTrim')] = self.timeline_canvas.create_rectangle(trimpostStart, timelineHeight-self.midrangeHeight, ex, timelineHeight, fill="#218a6f",width=0, tags='fileSpecific')
     
        self.canvasRegionCache[(rid,'startHandle')] = self.timeline_canvas.create_rectangle(sx-self.handleWidth, timelineHeight-self.handleHeight, sx+0, timelineHeight, fill="#69bfdb",width=1, tags='fileSpecific')
        self.canvasRegionCache[(rid,'endHandle')] = self.timeline_canvas.create_rectangle(ex-0, timelineHeight-self.handleHeight, ex+self.handleWidth, timelineHeight, fill="#db6986",width=1, tags='fileSpecific')


   
        for dtx in (-1,1):
          for dty in (-1,0,1,2):
            dst_tn = 'startHandleDot'+str(dtx)+str(dty)
            self.canvasRegionCache[(rid,dst_tn)] = self.timeline_canvas.create_line( sx-(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , sx-(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1  , fill="#333",width=1, tags='fileSpecific')
            dst_tn = 'endHandleDot'+str(dtx)+str(dty)
            self.canvasRegionCache[(rid,dst_tn)] = self.timeline_canvas.create_line( ex+(self.handleWidth/2)+(2*dtx) , timelineHeight-self.handleHeight+8+(5*dty) , ex+(self.handleWidth/2)+(2*dtx), timelineHeight-self.handleHeight+8+(5*dty)+1  , fill="#333",width=1, tags='fileSpecific')


        self.canvasRegionCache[(rid,'label')] = self.timeline_canvas.create_text( int((sx+ex)/2) , timelineHeight-self.midrangeHeight-20,text="{}s".format(format_timedelta(datetime.timedelta(seconds=round(e-s,2)), '{hours_total}:{minutes2}:{seconds2}')),fill="white", tags='fileSpecific') 
    

        self.canvasRegionCache[(rid,'miniDrag')] = self.timeline_canvas.create_rectangle(sx-self.handleWidth, timelineHeight-self.miniMidrangeHeight, ex+self.handleWidth, timelineHeight, fill="#2bb390",width=0, tags='fileSpecific')


        hstx = (s/self.controller.getTotalDuration())*timelineWidth
        henx = (e/self.controller.getTotalDuration())*timelineWidth
        self.canvasRegionCache[(rid,'headerR')] = self.timeline_canvas.create_rectangle(hstx,10, henx, 20, fill="#299b9b",width=0, tags='fileSpecific')
        


    for (rid,name),i in list(self.canvasRegionCache.items()):
      if rid not in activeRanges and rid != 'previewFrame':
        print('remove',rid)
        self.timeline_canvas.delete(i)
        del self.canvasRegionCache[(rid,name)]
    self.uiDirty=False

  def setUiDirtyFlag(self):
    self.uiDirty=True    

  def canvasPopupExpandSublcipToInterestMarksCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.expandSublcipToInterestMarks((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.expandSublcipToInterestMarks((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None


  def canvasPopupCloneSubClipCallback(self):
    if self.timeline_canvas_last_right_click_x is not None:
      ranges = self.controller.getRangesForClip(self.controller.getcurrentFilename())
      mid   = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x)
      lower = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x-self.handleWidth)
      upper = self.xCoordToSeconds(self.timeline_canvas_last_right_click_x+self.handleWidth)
      for rid,(s,e) in list(ranges):
        if s<mid<e:
          self.controller.cloneSubclip((e+s)/2)
          break
        if lower<e<upper or lower<s<upper:
          self.controller.cloneSubclip((e+s)/2)
          break
    self.timeline_canvas_last_right_click_x=None

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
import tkinter as tk
import tkinter.ttk as ttk
from filterSpec import selectableFilters
from pygubu.widgets.scrolledframe import ScrolledFrame
import os
import copy
import math

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

class FilterValuePair(ttk.Frame):
  def __init__(self, master,controller,param, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.param = param
    self.controller=controller
    self.frameFilterValuePair = self
    self.labelfilterValueLabel = ttk.Label(self.frameFilterValuePair)
    self.labelfilterValueLabel.config(text=param['n'])
    self.labelfilterValueLabel.pack(expand='true', fill='x', side='left')
    self.valueVar = tk.StringVar()

    if 'rectProp' in param is not None:
      self.controller.registerRectProp(param.get('rectProp'),self.valueVar)

    if param['type'] == 'cycle':
      self.selectableValues = param['cycle']
      self.valueVar.set(param['d'])
      self.entryFilterValueValue = ttk.Combobox(self.frameFilterValuePair)
      self.entryFilterValueValue.config(textvariable=self.valueVar)
      self.entryFilterValueValue.config(values=self.selectableValues)
      self.entryFilterValueValue.config(state='readonly')
    elif param['type'] == 'float':
      self.valueVar.set(param['d'])
      if param.get('range') is None:
        vmin,vmax = float('-inf'),float('inf')
      else:
        vmin,vmax = param['range']
        if vmin is None:
          vmin = float('-inf')
        if vmax is None:
          vmax = float('inf')
      self.entryFilterValueValue = ttk.Spinbox(self.frameFilterValuePair)
      self.entryFilterValueValue.config(textvariable=self.valueVar)
      self.entryFilterValueValue.config(from_=vmin)
      self.entryFilterValueValue.config(to=vmax)
      self.entryFilterValueValue.config(increment=param['inc'])
    elif param['type'] == 'string':
      self.valueVar.set(param['d'])
      self.entryFilterValueValue = ttk.Entry(self.frameFilterValuePair)
      self.entryFilterValueValue.config(textvariable=self.valueVar)
    elif param['type'] == 'int':
      self.entryFilterValueValue = ttk.Spinbox(self.frameFilterValuePair)
      self.entryFilterValueValue.config(textvariable=self.valueVar)
      self.valueVar.set(param['d'])
      if param.get('range') is None:
        vmin,vmax = float('-inf'),float('inf')
      else:
        vmin,vmax = param['range']
        if vmin is None:
          vmin = float('-inf')
        if vmax is None:
          vmax = float('inf')
      self.entryFilterValueValue.config(from_=vmin)
      self.entryFilterValueValue.config(to=vmax)
      self.entryFilterValueValue.config(increment=param['inc'])
    else:
      print(param)

    self.entryFilterValueValue.pack(side='right')
    self.frameFilterValuePair.config(height='200', width='200')
    self.frameFilterValuePair.pack(expand='true', fill='x', side='top')
    self.valueVar.trace("w", self.valueUpdated)

  def getValuePair(self):
    if self.param['type'] == 'string':
      val = self.valueVar.get()
      if not val.endswith("'"):
        val=val+"'"
      if not val.startswith("'"):
        val="'"+val
      return (self.param['n'],"{}".format(val))
    else:
      return (self.param['n'],self.valueVar.get())

  @debounce(0.1)
  def valueUpdated(self,*args):
    self.controller.recaculateFilters()

class FilterSpecification(ttk.Frame):
  def __init__(self, master,controller,spec, filterId, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.filterId=filterId
    self.enabled=True
    self.spec=spec
    self.controller=controller
    self.frameFilterDetailsWidget = self
    self.labelFilterName = ttk.Label(self.frameFilterDetailsWidget)
    self.labelFilterName.config(text=spec['name'])
    self.labelFilterName.pack(side='top')
    self.frameFilterConfigFrame = ttk.Frame(self.frameFilterDetailsWidget)
    self.frameFilterActions = ttk.Frame(self.frameFilterConfigFrame)
    self.buttonfilterActionRemove = ttk.Button(self.frameFilterActions)
    self.buttonfilterActionRemove.config(text='Remove')
    self.buttonfilterActionRemove.config(command=self.remove)    
    self.buttonfilterActionRemove.pack(expand='true', fill='x', side='left')
    self.buttonfilterActionToggleEnabled = ttk.Button(self.frameFilterActions)
    self.buttonfilterActionToggleEnabled.config(text='Enabled', width='7')
    self.buttonfilterActionToggleEnabled.config(command=self.toggleEnabled)
    self.buttonfilterActionToggleEnabled.pack(expand='true', fill='x', side='left')
    self.buttonFilterActionDownStack = ttk.Button(self.frameFilterActions)
    self.buttonFilterActionDownStack.config(text='▼', width='2')
    self.buttonFilterActionDownStack.pack(side='left')
    self.buttonFilterActionUpStack = ttk.Button(self.frameFilterActions)
    self.buttonFilterActionUpStack.config(text='▲', width='2')
    self.buttonFilterActionUpStack.pack(side='left')
    self.frameFilterActions.config(height='200', width='200')
    self.frameFilterActions.pack(expand='true', fill='x', side='top')
    self.rectProps={}
    self.filterValuePairs= []
    for param in spec.get('params',[]):      
      self.filterValuePairs.append(FilterValuePair(self.frameFilterConfigFrame,self,param))
    
    if len(self.rectProps)>0:
      self.buttonFilterValuesFromSelection = ttk.Button(self.frameFilterConfigFrame)
      self.buttonFilterValuesFromSelection.config(text='Populate from selection')
      self.buttonFilterValuesFromSelection.config(command=self.populateRectPropValues)
      self.buttonFilterValuesFromSelection.pack(expand='true', fill='x', side='top')
    self.frameFilterConfigFrame.config(height='200', width='200')
    self.frameFilterConfigFrame.pack(expand='true', fill='x', side='top')
    self.frameFilterDetailsWidget.config(height='200', padding='2', relief='groove', width='200')
    self.frameFilterDetailsWidget.pack(expand='false', fill='x', side='top')



  def populateRectPropValues(self):
    x1,y1,x2,y2 = self.controller.getRectProperties()

    x1,x2 = sorted([x1,x2])
    y1,y2 = sorted([y1,y2])

    rectDerivedProps = dict(
      x=x1,y=y1,x1=x1,y1=y1,x2=x2,y2=y2,
      w=x2-x1,h=y2-y1,cx=(x1+x2)/2,cy=(y1+y2)/2
    )

    for k,v in rectDerivedProps.items():
      if k in self.rectProps:
        self.rectProps.get(k).set(v)

  def registerRectProp(self,prop,var):
    self.rectProps[prop]=var

  def toggleEnabled(self):
    self.enabled = not self.enabled
    if self.enabled:
      self.buttonfilterActionToggleEnabled.config(text='Enabled')
    else:
      self.buttonfilterActionToggleEnabled.config(text='Disabled')
    self.controller.recaculateFilters()

  def getFilterExpression(self,preview=False):
    if not self.enabled:
      return 'null'

    if preview:
      filterExp= self.spec.get("filterPreview",self.spec.get("filter",'null'))
    else:
      filterExp= self.spec.get("filter",'null')
      

    filerExprams=[]
    i=id(self)
    values = dict( x.getValuePair() for x in self.filterValuePairs )
    formatDict={}

    for param in self.spec.get('params',[]):

      if '{'+param['n']+'}' in filterExp:
        formatDict.update({'fn':i,param['n']:values[param['n']] },)
      else:
        if param['type'] == 'float':
          try:
            filerExprams.append(':{}={:01.6f}'.format(param['n'],float(values[param['n']]) ) )
          except:
            filerExprams.append(':{}={:01.6f}'.format(param['n'],0) )
        elif param['type'] == 'int':
          try:
            filerExprams.append(':{}={}'.format(param['n'],int(values[param['n']])))
          except:
            filerExprams.append(':{}={:01.2f}'.format(param['n'],0) )
        else:
          filerExprams.append(':{}={}'.format(param['n'],values[param['n']]) )

    if len(formatDict)>0:
      filterExp = filterExp.format( **formatDict )

    for i,e in enumerate(filerExprams):
      if i==0:
        filterExp+= '='+e[1:]
      else:
        filterExp+= e

    return filterExp

  def recaculateFilters(self):
    self.controller.recaculateFilters()

  def remove(self):
    self.controller.removeFilter(self.filterId)


class FilterSelectionUi(ttk.Frame):
  def __init__(self, master=None, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    # build ui
    self.frameFilterFrame = self
    self.controller=None
    self.frameFilterSelectionFrame = ttk.Frame(self.frameFilterFrame)
    self.labelframeFilterBrowserFrame = ttk.Labelframe(self.frameFilterSelectionFrame)
    self.frameVideoPickerFrame = ttk.Frame(self.labelframeFilterBrowserFrame)
    self.buttonVideoPickerPrevious = ttk.Button(self.frameVideoPickerFrame)
    self.buttonVideoPickerPrevious.config(text='<', width='1')
    self.buttonVideoPickerPrevious.config(command=self.goToPreviousSubclip)
    self.buttonVideoPickerPrevious.pack(anchor='w', side='left')
    self.labelVideoPickerLabel = ttk.Label(self.frameVideoPickerFrame)
    self.labelVideoPickerLabel.config(text='No Subclips Selected 0/0')
    self.labelVideoPickerLabel.pack(expand='true', fill='x', side='left')
    self.VideoPickerNext = ttk.Button(self.frameVideoPickerFrame)
    self.VideoPickerNext.config(text='>', width='1')
    self.VideoPickerNext.config(command=self.goToNextSubclip)    
    self.VideoPickerNext.pack(anchor='nw', expand='false', side='right')
    self.frameVideoPickerFrame.config(height='200', width='200')
    self.frameVideoPickerFrame.pack(fill='x', padx='2', side='top')


    self.frameFilterActionsGlobal = ttk.Frame(self.labelframeFilterBrowserFrame)
    
    self.buttonFilterActionClear = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonFilterActionClear.config(text='Clear filters')
    self.buttonFilterActionClear.config(command=self.clearFilters)
    self.buttonFilterActionClear.pack(expand='true', fill='x', side='left')

    self.buttonPasteFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonPasteFilters.config(text='Paste filters')
    self.buttonPasteFilters.config(command=self.pasteFilters)
    self.buttonPasteFilters.pack(expand='true', fill='x', side='right')
    
    self.buttonCopyFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonCopyFilters.config(text='Copy filters')
    self.buttonCopyFilters.config(command=self.copyfilters)
    self.buttonCopyFilters.pack(expand='true', fill='x', side='right')

    self.frameFilterActionsGlobal.config(height='200', width='200')
    self.frameFilterActionsGlobal.pack(fill='x', side='top')


    self.framefilterAdditionFrame = ttk.Frame(self.labelframeFilterBrowserFrame)
    self.buttonAddFilter = ttk.Button(self.framefilterAdditionFrame)
    self.buttonAddFilter.config(text='Add Filter')
    self.buttonAddFilter.config(command=self.addSelectedfilter)
    self.buttonAddFilter.pack(side='right')
    self.selectedFilter=tk.StringVar()
    self.selectableFilters = [x['name'] for x in selectableFilters]
    self.selectedFilter.set(self.selectableFilters[0])   
    self.comboboxFilterSelection = ttk.OptionMenu(self.framefilterAdditionFrame,self.selectedFilter,self.selectedFilter.get(),*self.selectableFilters)
    self.comboboxFilterSelection.pack(expand='true', fill='both', side='left')
    self.framefilterAdditionFrame.config(height='200', width='200')
    self.framefilterAdditionFrame.pack(expand='false', fill='x', padx='2',pady='3', side='top')
    self.scrolledframeFilterContainer = ScrolledFrame(self.labelframeFilterBrowserFrame, scrolltype='vertical')
    self.filterContainer = self.scrolledframeFilterContainer.innerframe
    self.filterSpecifications = []
    self.filterSpecificationCount=0
    self.scrolledframeFilterContainer.configure(usemousewheel=True)
    self.scrolledframeFilterContainer.pack(expand='true', fill='both', side='top')

  

    self.labelframeFilterBrowserFrame.config(height='200', text='Filtering', width='200')
    self.labelframeFilterBrowserFrame.pack(anchor='w', expand='false', fill='y', side='left')

    self.playerContainerFrame = ttk.Frame(self.frameFilterSelectionFrame)
    self.playerContainerFrame.pack(expand='true', fill='both', side='right')


    self.selectionOptionsFrame = ttk.Frame(self.playerContainerFrame)

    self.fixSeectionArEnabledVar = tk.BooleanVar()
    self.fixSeectionArEnabledVar.set(False)
    self.arFixCheckbox = ttk.Checkbutton(self.selectionOptionsFrame,text="Restrict selection aspect ratio", variable=self.fixSeectionArEnabledVar)
    self.arFixCheckbox.pack(expand='false', side='left')
    
    self.fixSeectionArVar = tk.StringVar()
    self.fixSeectionArVar.set('1.7')
    self.spinBoxArRatio = ttk.Spinbox(self.selectionOptionsFrame,textvariable=self.fixSeectionArVar,from_=float('-inf'), to=float('inf'), increment=0.01)
    self.spinBoxArRatio.pack(expand='false', side='left')

    self.fitToScreenVar = tk.BooleanVar()
    self.fitToScreenVar.trace('w',self.changeFitToScreen)
    self.fitToScreenVar.set(True)
    self.fitToScreenCheckbox = ttk.Checkbutton(self.selectionOptionsFrame,text="Fit to screen", variable=self.fitToScreenVar)
    self.fitToScreenCheckbox.pack(expand='false', side='left')



    self.speedVar = tk.StringVar()
    self.speedVar.trace('w',self.speedChange)
    self.speedVar.set('2.0')
    self.spinboxSpeed = ttk.Spinbox(self.selectionOptionsFrame,textvariable=self.speedVar,from_=float('0'), to=float('inf'), increment=0.1)
    self.spinboxSpeed.pack(expand='false', side='right')

    self.speedLabel = ttk.Label(self.selectionOptionsFrame)
    self.speedLabel.config(text='Preview speed')
    self.speedLabel.pack(expand='false', side='right')


    self.selectionOptionsFrame.pack(expand='false', fill='x', side='top')

    self.framePlayerFrame = ttk.Frame(self.playerContainerFrame, style='PlayerFrame.TFrame')
    self.framePlayerFrame.config(height='200', width='200')
    self.framePlayerFrame.pack(expand='true', fill='both', side='right')

    self.mouseRectDragging=False
    self.videoMouseRect=[None,None,None,None]
    self.screenMouseRect=[None,None,None,None]

    self.framePlayerFrame.bind("<Button-1>",          self.videomousePress)
    self.framePlayerFrame.bind("<ButtonRelease-1>",   self.videomousePress)
    self.framePlayerFrame.bind("<Motion>",            self.videomousePress)

    self.frameFilterSelectionFrame.config(height='200', width='200')
    self.frameFilterSelectionFrame.pack(expand='true', fill='both', side='top')
    """
    self.frameValueTimelineFrame = ttk.Frame(self.frameFilterFrame)
    
    self.canvasValueTimeline = tk.Canvas(self.frameValueTimelineFrame)
    self.canvasValueTimeline.config(background='#373737', height='200', highlightthickness='0')
    self.canvasValueTimeline.pack(expand='true', fill='both', side='top')
    
    self.frameValueTimelineFrame.config(height='10', width='200')
    self.frameValueTimelineFrame.pack(expand='false', fill='x', side='bottom')
    """
    self.frameFilterFrame.config(height='200', width='200')
    self.frameFilterFrame.pack(expand='true', fill='both', side='top')
    

    self.mainwindow = self.frameFilterFrame
    self.subclips={}
    self.subClipOrder=[]
    self.currentSubclipIndex=None
    self.filterClipboard=[]
    

  def speedChange(self,*args):
    speed = self.speedVar.get()
    try:
      speed = float(speed)
      if self.controller is not None:  
        self.controller.setSpeed(speed)
    except:
      pass


  def changeFitToScreen(self,*args):
    fitToScreen = self.fitToScreenVar.get()
    if self.controller is not None:
      self.controller.fitoScreen(fitToScreen)

  def getRectProperties(self):
    return self.videoMouseRect

  def applyScreenSpaceAR(self):
    forceAR = None
    print(self.fixSeectionArEnabledVar.get())
    if self.fixSeectionArEnabledVar.get():
      try:
        forceAR = float(self.fixSeectionArVar.get())
      except Exception as e:
        print(e)
    print(forceAR)
    if forceAR is not None:
      if self.screenMouseRect[3] > self.screenMouseRect[1]:
        self.screenMouseRect[3] = self.screenMouseRect[1] + abs(self.screenMouseRect[0]-self.screenMouseRect[2])/forceAR
      else:
        self.screenMouseRect[3] = self.screenMouseRect[1] - abs(self.screenMouseRect[0]-self.screenMouseRect[2])/forceAR
    else:
      try:
        self.fixSeectionArVar.set( str( round( abs(self.screenMouseRect[0]-self.screenMouseRect[2])/abs(self.screenMouseRect[1]-self.screenMouseRect[3]),4  ))  )
      except:
        pass

  def videomousePress(self,e):
      if str(e.type) == 'ButtonPress':
        print('start')
        self.mouseRectDragging=True
        self.screenMouseRect[0]=e.x
        self.screenMouseRect[1]=e.y
      elif str(e.type) in ('Motion','ButtonRelease') and self.mouseRectDragging:
        print('show')
        self.screenMouseRect[2]=e.x
        self.screenMouseRect[3]=e.y
        self.applyScreenSpaceAR()
        self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3])
      if str(e.type) == 'ButtonRelease':
        print('release')
        self.mouseRectDragging=False

        vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
        vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 


        self.videoMouseRect=[vx1,vy1,vx2,vy2]
        self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3])
      
      if self.screenMouseRect[0] is not None and not self.mouseRectDragging and self.screenMouseRect[0]==self.screenMouseRect[2] and self.screenMouseRect[1]==self.screenMouseRect[3]:
        print('clear')
        self.screenMouseRect=[None,None,None,None]
        self.mouseRectDragging=False
        self.controller.clearVideoRect()

  def addSelectedfilter(self):
    self.filterSpecificationCount+=1
    newFilter = None
    for spec in selectableFilters:
      if spec['name'] == self.selectedFilter.get():
        newFilter = FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        self.filterSpecifications.append( newFilter)
        break
    if newFilter is not None and self.videoMouseRect[2] is not None:
      newFilter.populateRectPropValues()
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters()

  def removeFilter(self,filterId):
    for filter in self.filterSpecifications:
      if filter.filterId == filterId:
        filter.destroy()
    self.filterSpecifications = [x for x in self.filterSpecifications if x.filterId != filterId]
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters()

  def clearFilters(self):
    for filter in self.filterSpecifications:
      filter.destroy()
    self.filterSpecifications=[]
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters()

  def recaculateFilters(self):
    filterexpPreview=[]
    filterExpReal=[]
    for filter in self.filterSpecifications:
      filterexpPreview.append(filter.getFilterExpression(preview=True)) 
      filterExpReal.append(filter.getFilterExpression(preview=False))
    filterExpStrPreview = ','.join(filterexpPreview)
    filterExpStrReal = ','.join(filterExpReal)

    if len(filterexpPreview)==0:
      self.controller.clearFilter()
    if len(filterexpPreview)>0:
      self.controller.setFilter(filterExpStrPreview)

    if self.currentSubclipIndex is not None:
      currentClip = self.getCurrentClip()
      if currentClip is not None:
        currentClip['filters'] = self.convertFilterstoSpecDefaults()
        currentClip['filterexp'] =filterExpStrReal


  def convertFilterstoSpecDefaults(self):
    filterstack=[]
    for ifilter in self.filterSpecifications:
      baseSpec = None     
      for spec in selectableFilters:
        if spec['name'] == ifilter.spec['name']:
          baseSpec=copy.deepcopy(spec)
          break
      for n,v in [x.getValuePair() for x in ifilter.filterValuePairs]:
        for param in baseSpec['params']:
          if param['n']==n:
            param['d']=v
            break
      filterstack.append(baseSpec)
    return filterstack


  def setController(self,controller):
    self.controller=controller

  def tabSwitched(self,tabName):
    if str(self) == tabName:
      self.recauclateSubclips()
      self.controller.play()
    else:
      self.controller.pause()

  def recauclateSubclips(self):
    unusedRids = set(self.subclips.keys())
    clipsChanged=set()

    for filename,rid,s,e in self.controller.getAllSubclips():
      if rid in self.subclips:
        unusedRids.remove(rid)
        if self.subclips[rid]['start'] != s or self.subclips[rid]['end'] != e:
          self.subclips[rid]['start']=s
          self.subclips[rid]['end']=e
          clipsChanged.add(rid)        
      else:
        self.subclips[rid] = dict(start=s,end=e,filename=filename,filters=[])
        clipsChanged.add(rid)
    
    for k in unusedRids:
      del self.subclips[k]

    tempSeclectedRid=None
    if self.currentSubclipIndex is not None:
      tempSeclectedRid = self.subClipOrder[self.currentSubclipIndex]

    self.subClipOrder = [k for k,v in sorted( self.subclips.items(), key=lambda x:(x[1]['filename'],x[1]['start']) ) ]

    if tempSeclectedRid in self.subClipOrder:
      self.setSubclipIndex(self.subClipOrder.index(tempSeclectedRid))
      if tempSeclectedRid in clipsChanged:
        self.updateFilterDisplay()
    elif len(self.subClipOrder)>0:      
      self.setSubclipIndex(0)
      self.updateFilterDisplay()
    else:
      self.setSubclipIndex(None)
      self.controller.stop()
      self.labelVideoPickerLabel.config(text='No Subclips Selected 0/0')
    self.updateFilterDisplay()

  def getCurrentClip(self):
    try:
      return self.subclips[self.subClipOrder[self.currentSubclipIndex]]
    except Exception as e:
      print(e)
    return None

  def goToNextSubclip(self):
    if self.currentSubclipIndex is not None:
      self.setSubclipIndex( (self.currentSubclipIndex+1)%len(self.subClipOrder) )
      self.updateFilterDisplay()

  def goToPreviousSubclip(self):
    if self.currentSubclipIndex is not None:
      self.setSubclipIndex( (self.currentSubclipIndex-1)%len(self.subClipOrder) )
      self.updateFilterDisplay()


  def copyfilters(self):
    if self.currentSubclipIndex is not None:
      self.filterClipboard = self.convertFilterstoSpecDefaults()

  def pasteFilters(self):
    if self.currentSubclipIndex is not None:
      rid = self.subClipOrder[self.currentSubclipIndex]
      self.subclips[rid]['filters'] = copy.deepcopy(self.filterClipboard)
      for f in self.filterSpecifications:
        f.destroy()
      self.filterSpecifications=[]
      rid = self.subClipOrder[self.currentSubclipIndex]
      print(rid,self.subclips[rid])
      for spec in self.subclips[rid].setdefault('filters',[]):
        self.filterSpecificationCount+=1
        self.filterSpecifications.append( 
          FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        )
      self.recaculateFilters()


  def setSubclipIndex(self,newIndex):
    self.recaculateFilters()
    if self.currentSubclipIndex is not None and len(self.subClipOrder)>0:
      rid = self.subClipOrder[self.currentSubclipIndex]
      print('rid---',rid,self.subclips[rid])
      #print('rid[fil]---',self.subclips[rid]['filters'])
      self.subclips[rid]['filters'] = self.convertFilterstoSpecDefaults()

    self.currentSubclipIndex = newIndex
    for f in self.filterSpecifications:
      f.destroy()
    self.filterSpecifications=[]

    if newIndex is not None and len(self.subClipOrder)>0:
      rid = self.subClipOrder[self.currentSubclipIndex]
      print(rid,self.subclips[rid])
      for spec in self.subclips[rid].setdefault('filters',[]):
        self.filterSpecificationCount+=1
        self.filterSpecifications.append( 
          FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        )
      self.recaculateFilters()

  def updateFilterDisplay(self):
    currentClip = self.getCurrentClip()
    if currentClip is None:
      pass
    else:
      basename = os.path.basename(currentClip['filename'])[:18]
      s=currentClip['start']
      e=currentClip['end']
      newLabel = '{n} {s:0.2f}-{e:0.2f} {i}/{len}'.format(n=basename,
                                                s=s,
                                                e=e,
                                                i=self.currentSubclipIndex+1,
                                                len=len(self.subClipOrder))
      self.labelVideoPickerLabel.config(text=newLabel)
      print(currentClip['filename'],s,e)
      self.controller.playVideoFile(currentClip['filename'],s,e)

  def getPlayerFrameWid(self):
    return self.framePlayerFrame.winfo_id()

if __name__ == '__main__':
  import webmGenerator

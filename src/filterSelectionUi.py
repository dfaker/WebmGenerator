import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrolledframe import ScrolledFrame
import os
import copy
import math
import logging
import threading
import time
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import json
from .filterSpec import selectableFilters
from .encodingUtils import cleanFilenameForFfmpeg

import numpy as np
from math import sqrt


def cubic_interp1d(x0, x, y):
    """
    Interpolate a 1-D function using cubic splines.
      x0 : a float or an 1d-array
      x : (N,) array_like
          A 1-D array of real/complex values.
      y : (N,) array_like
          A 1-D array of real values. The length of y along the
          interpolation axis must be equal to the length of x.

    Implement a trick to generate at first step the cholesky matrice L of
    the tridiagonal matrice A (thus L is a bidiagonal matrice that
    can be solved in two distinct loops).

    additional ref: www.math.uh.edu/~jingqiu/math4364/spline.pdf 
    """
    x = np.asfarray(x)
    y = np.asfarray(y)

    # remove non finite values
    # indexes = np.isfinite(x)
    # x = x[indexes]
    # y = y[indexes]

    # check if sorted
    if np.any(np.diff(x) < 0):
        indexes = np.argsort(x)
        x = x[indexes]
        y = y[indexes]

    size = len(x)

    xdiff = np.diff(x)
    ydiff = np.diff(y)

    # allocate buffer matrices
    Li = np.empty(size)
    Li_1 = np.empty(size-1)
    z = np.empty(size)

    # fill diagonals Li and Li-1 and solve [L][y] = [B]
    Li[0] = sqrt(2*xdiff[0])
    Li_1[0] = 0.0
    B0 = 0.0 # natural boundary
    z[0] = B0 / Li[0]

    for i in range(1, size-1, 1):
        Li_1[i] = xdiff[i-1] / Li[i-1]
        Li[i] = sqrt(2*(xdiff[i-1]+xdiff[i]) - Li_1[i-1] * Li_1[i-1])
        Bi = 6*(ydiff[i]/xdiff[i] - ydiff[i-1]/xdiff[i-1])
        z[i] = (Bi - Li_1[i-1]*z[i-1])/Li[i]

    i = size - 1
    Li_1[i-1] = xdiff[-1] / Li[i-1]
    Li[i] = sqrt(2*xdiff[-1] - Li_1[i-1] * Li_1[i-1])
    Bi = 0.0 # natural boundary
    z[i] = (Bi - Li_1[i-1]*z[i-1])/Li[i]

    # solve [L.T][x] = [y]
    i = size-1
    z[i] = z[i] / Li[i]
    for i in range(size-2, -1, -1):
        z[i] = (z[i] - Li_1[i-1]*z[i+1])/Li[i]

    # find index
    index = x.searchsorted(x0)
    np.clip(index, 1, size-1, index)

    xi1, xi0 = x[index], x[index-1]
    yi1, yi0 = y[index], y[index-1]
    zi1, zi0 = z[index], z[index-1]
    hi1 = xi1 - xi0

    # calculate cubic
    f0 = zi0/(6*hi1)*(xi1-x0)**3 + \
         zi1/(6*hi1)*(x0-xi0)**3 + \
         (yi1/hi1 - zi1*hi1/6)*(x0-xi0) + \
         (yi0/hi1 - zi0*hi1/6)*(xi1-x0)
    return f0



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
    self.fileCategory = param.get('fileCategory',None)
    self.keyValues= self.param.get('keyValues',{})
    self.valueVar = tk.StringVar()

    self.n = self.param['n']
    self.vmin,self.vmax = float('-inf'),float('inf')
    if param.get('rectProp') is not None:
      self.controller.registerRectProp(param.get('rectProp'),self.valueVar)

    self.commandVarSelected  = False
    self.commandVarAvaliable = False 
    self.commandVarEnabled   = False
    self.commandvarName      = None
    self.commandInterpolationMode = param.get('interpMode','lerp')
    self.interpolationModes = ['lerp','lerp-smooth','lerp-smooth-2nd','lerp-sigmoid','lerp-smooth-inv','neighbour','neighbour-relative']
    self.interpVar = tk.StringVar()
    self.interpVar.set(self.commandInterpolationMode)

    self.interpVar.trace('w',self.interpolationChanged)

    self.commandVarTarget = []
    self.commandVarProperty = []


    print(len(param.get('commandVar',[])))

    if len(param.get('commandVar',[]))==2:
      self.commandVarAvaliable  = True 
      self.commandVarEnabled    = False
      self.commandVarSelected   = False
      self.commandvarName, targetPairs = param['commandVar']

      for cmdTarget,cmdProp in targetPairs:
        self.commandVarTarget.append(cmdTarget)
        self.commandVarProperty.append(cmdProp)


      self.commandButton = ttk.Button(self.frameFilterValuePair)
      self.commandButton.config(text='T', style='smallOnechar.TButton',command=self.toggleTimelineCmdMode) 
      self.commandButton.pack(expand='false', side='left')

      self.commandSelectButton = ttk.Button(self.frameFilterValuePair)
      self.commandSelectButton.config(text='S',state='disabled', style='smallOnechar.TButton',command=self.toggleTimelineSelection) 
      self.commandSelectButton.pack(expand='false', side='left')

    self.entryInterpValue = ttk.Combobox(self.frameFilterValuePair)
    self.entryInterpValue.config(textvariable=self.interpVar)
    self.entryInterpValue.config(values=self.interpolationModes)


    if param.get('desc','') != '':
      self.labelfilterValueLabel.config(text=param['n']+' ('+param['desc']+')')
    else:
      self.labelfilterValueLabel.config(text=param['n'])

    self.labelfilterValueLabel.pack(expand='true', fill='x', side='left')

    if param['type'] == 'cycle':
      self.selectableValues = param['cycle']
      self.valueVar.set(param['d'])
      self.entryFilterValueValue = ttk.Combobox(self.frameFilterValuePair)
      self.entryFilterValueValue.config(textvariable=self.valueVar)
      self.entryFilterValueValue.config(values=self.selectableValues)
      #self.entryFilterValueValue.config(state='readonly')
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
      self.vmin,self.vmax = vmin,vmax
      self.entryFilterValueValue = ttk.Spinbox(self.frameFilterValuePair)
      self.entryFilterValueValue.config(textvariable=self.valueVar)
      self.entryFilterValueValue.config(from_=vmin)
      self.entryFilterValueValue.config(to=vmax)
      self.entryFilterValueValue.config(increment=param['inc'])
    elif param['type'] == 'string' or param['type'] == 'bareString':
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
      self.vmin,self.vmax = vmin,vmax
      self.entryFilterValueValue.config(from_=vmin)
      self.entryFilterValueValue.config(to=vmax)
      self.entryFilterValueValue.config(increment=param['inc'])
    elif param['type'] == 'file':
      self.valueVar.set(param['d'])
      self.entryFilterValueValue = ttk.Button(self.frameFilterValuePair)
      self.entryFilterValueValue.config(text='File: {}'.format(self.valueVar.get()[-20:]),command=self.selectFile)
    else:
      logging.error("Unhandled param {}".format(str(param)))


    self.entryFilterValueValue.pack(side='right')

    self.frameFilterValuePair.config(height='200', width='200')
    self.frameFilterValuePair.pack(expand='true', fill='x', side='top')
    self.valueVar.trace("w", self.valueUpdated)

    if self.commandVarAvaliable:
      
      self.commandVarSelected = self.param.get('commandVarSelected',False)
      if self.commandVarSelected:
        self.commandSelectButton.config(style='smallOnecharenabled.TButton')
        #self.entryFilterValueValue['state']='disabled'
        self.entryFilterValueValue.pack_forget()
        self.entryInterpValue.pack(side='right')
      else:
        self.commandSelectButton.config(style='smallOnechar.TButton') 
        #self.entryFilterValueValue['state']='normal'
        self.entryInterpValue.pack_forget()
        self.entryFilterValueValue.pack(side='right')

      self.commandVarEnabled  = self.param.get('commandVarEnabled',False)
      if self.commandVarEnabled:
        self.commandButton.config(style='smallOnecharenabled.TButton') 
        self.commandSelectButton['state']='normal'
      else:
        self.commandButton.config(style='smallOnechar.TButton')
        self.commandSelectButton['state']='disabled' 

  def interpolationChanged(self,*args):
    newmode = self.interpVar.get()
    if newmode in self.interpolationModes:
      self.commandInterpolationMode = newmode
      self.controller.recaculateFilters()
    else:
      self.interpVar.set(self.commandInterpolationMode)

  def addKeyValue(self,seconds):
    try:      
      lower = [(k,v) for k,v in sorted(self.keyValues.items()) if k<seconds][-1:]
      upper = [(k,v) for k,v in sorted(self.keyValues.items(),reverse=True) if k>seconds][-1:]

      if len(lower)==1 and len(upper)==1:
        neighbourRange    = upper[0][1]-lower[0][1]
        neighbourDuration = upper[0][0]-lower[0][0]
        percent = (seconds-lower[0][0])/neighbourDuration

        self.keyValues[seconds]= self.convertKeyValueToType(  lower[0][1]+(neighbourRange*percent) )
      
      elif len(lower)==1:
        self.keyValues[seconds]= self.convertKeyValueToType( lower[0][1] )
      elif len(upper)==1:
        self.keyValues[seconds]= self.convertKeyValueToType( upper[0][1] )
      else:
        self.keyValues[seconds]= self.convertKeyValueToType(self.valueVar.get())

    except Exception as e:
      self.keyValues[seconds]= self.convertKeyValueToType(self.param['d'])
      print(e)
    #self.valueVar.set(self.keyValues[seconds])
    print(self.keyValues)

  def removeKeyValue(self,seconds):
    del self.keyValues[seconds]
    print(self.keyValues)

  def incrementKeyValue(self,seconds,valueOffset):
    if seconds in self.keyValues:
      
      newval = self.keyValues[seconds]+(valueOffset*self.param['inc'])
      newval = max(min(newval,self.vmax),self.vmin)

      self.keyValues[seconds] = self.convertKeyValueToType(newval)
      lower = [v for k,v in sorted(self.keyValues.items()) if k<seconds][-1:]
      upper = [v for k,v in sorted(self.keyValues.items(),reverse=True) if k>seconds][-1:]
      #self.valueVar.set(self.keyValues[seconds])
      self.controller.recaculateFilters()
    print(self.keyValues)

  def convertKeyValueToType(self,value):
    if self.param['type'] == 'int':
      return int(value)
    elif self.param['type'] == 'float':
      return float(value)
    return value

  def getKeyValues(self,interpolation=0):
    
    sortedKVs = sorted(list(self.keyValues.items()).copy())
    if interpolation>0 and len(sortedKVs)>1:

      x = np.array([x[0] for x in sortedKVs])
      y = np.array([x[1] for x in sortedKVs])

      x_new = np.linspace(x[0], x[-1] , int((x[-1]-x[0])*int(interpolation)) )
      y_new  = cubic_interp1d(x_new, x, y)

      return sorted(  [(a,b,False) for a,b, in zip(x_new,y_new)]  + [(a,b,True) for a,b, in sortedKVs])
    else:
      return [(a,b,True) for a,b, in sortedKVs]

  def deactivateTimeLineSection(self):
    if self.commandVarAvaliable:
      self.commandVarSelected   = False
      self.commandSelectButton.config(style='smallOnechar.TButton') 

  def toggleTimelineSelection(self,toggle=True):
    if self.commandVarAvaliable:
      if self.commandVarSelected:
        if toggle:
          self.commandVarSelected   = False
        self.commandSelectButton.config(style='smallOnechar.TButton') 
        self.controller.setActiveTimeLineValue(None)
      else:
        if toggle:
          self.commandVarSelected   = True
        self.commandSelectButton.config(style='smallOnecharenabled.TButton')
        self.controller.setActiveTimeLineValue(self)

  def toggleTimelineCmdMode(self,toggle=True):
    if self.commandVarAvaliable:
      if self.commandVarEnabled:
        if toggle:
          self.commandVarEnabled   = False
          self.commandVarSelected=False
        #self.entryFilterValueValue['state']='normal'
        
        self.entryInterpValue.pack_forget()
        self.entryFilterValueValue.pack(side='right')

        self.commandButton.config(style='smallOnechar.TButton') 
        self.commandSelectButton.config(style='smallOnechar.TButton') 
        self.commandSelectButton['state']='disabled'
      else:
        if toggle:
          self.commandVarEnabled   = True
        self.commandButton.config(style='smallOnecharenabled.TButton')
        #self.entryFilterValueValue['state']='disabled'

        self.entryFilterValueValue.pack_forget()
        self.entryInterpValue.pack(side='right')

        self.commandSelectButton['state']='normal'
        self.toggleTimelineSelection()

  def selectFile(self):
    initialdir='.'
    filetypes=(('All files', '*.*'),)

    if self.fileCategory=='font':
      initialdir=self.controller.getGlobalOptions().get('defaultFontFolder','.')
    elif self.fileCategory=='subtitle':
      initialdir=self.controller.getGlobalOptions().get('defaultSubtitleFolder','.')
      filetypes=(('Subtitle', '*.srt'),)
    elif self.fileCategory=='image':
      initialdir=self.controller.getGlobalOptions().get('defaultImageFolder','.')
    elif self.fileCategory=='video':
      initialdir=self.controller.getGlobalOptions().get('defaultVideoFolder','.')
    print(initialdir,filetypes)
    fn = askopenfilename(initialdir=initialdir,filetypes=filetypes)
    if fn is None or len(fn)==0:
      self.entryFilterValueValue.config(text='Select file')
    else:
      cleanPath = os.path.abspath(fn).replace('\\','/').replace(':','\\:')
      writeBackPath = os.path.abspath(os.path.dirname(fn))

      if self.fileCategory=='font':
        self.controller.getGlobalOptions()['defaultFontFolder'] = writeBackPath
      elif self.fileCategory=='subtitle':
        self.controller.getGlobalOptions()['defaultSubtitleFolder'] = writeBackPath
      elif self.fileCategory=='image':
        self.controller.getGlobalOptions()['defaultImageFolder'] = writeBackPath
      elif self.fileCategory=='video':
        self.controller.getGlobalOptions()['defaultVideoFolder'] = writeBackPath

      self.valueVar.set(cleanPath)
      print(self.valueVar.get())
      self.entryFilterValueValue.config(text='File: {}'.format(self.valueVar.get()[-20:]))

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



    self.timelineReinit = self.spec.get('timelineReinit',False)
    
    self.labelFilterName = ttk.Label(self.frameFilterDetailsWidget)
    self.labelFilterName.config(text=spec['name'],style="Bold.TLabel")
    self.labelFilterName.pack(side='top')

    if spec.get('desc','') != '':
      self.labelFilterDesc = ttk.Label(self.frameFilterDetailsWidget)
      self.labelFilterDesc.config(text=spec.get('desc',''),wraplength=290,justify=tk.CENTER)
      self.labelFilterDesc.pack(side='top',fill="x",expand="true")



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
    self.timelineSupport = spec.get('timelineSupport',False)
    self.encodingStageFilter = spec.get('encodingStageFilter',False)
    self.timelineStart = tk.StringVar()
    self.timelineEnd   = tk.StringVar()



    if self.timelineSupport:

      def timelineStartChanged(*args):
        self.recaculateFilters()
        try:
          ts = float(self.timelineStart.get())
          self.controller.seekToTimelinePoint(ts)
        except:
          pass  

      def timelineEndChanged(*args):
        self.recaculateFilters()
        try:
          ts = float(self.timelineEnd.get())
          self.controller.seekToTimelinePoint(ts)
        except:
          pass  


      self.frameTimeline = ttk.Frame(self.frameFilterDetailsWidget)

      self.timelineStart.trace('w',timelineStartChanged)
      self.timelineEnd.trace('w',timelineEndChanged)

      self.frameTimelineStart = ttk.Frame(self.frameTimeline)
      self.labelTimelineStart = ttk.Label(self.frameTimelineStart)
      self.labelTimelineStart.config(text='Start at:')
      self.labelTimelineStart.pack(expand='false', fill='x', side='left')
      self.entryTimelineStart = ttk.Spinbox(self.frameTimelineStart)
      self.entryTimelineStart.config(textvariable=self.timelineStart)
      self.entryTimelineStart.config(from_=0)
      self.entryTimelineStart.config(to=100)
      self.entryTimelineStart.config(increment=0.1)
      self.entryTimelineStart.pack(expand='false', fill='x', side='right')

      self.entryTimelineStartGetNow = ttk.Button(self.frameTimelineStart,text='Current Time',style="small.TButton",command=self.getCurrenttimeForStart)
      self.entryTimelineStartGetNow.pack(expand='false', fill='x', side='right')

      self.frameTimelineStart.pack(expand='true', fill='x', side='top')


      self.frameTimelineEnd = ttk.Frame(self.frameTimeline)
      self.labelTimelineEnd = ttk.Label(self.frameTimelineEnd)
      self.labelTimelineEnd.config(text='End at:')
      self.labelTimelineEnd.pack(expand='false', fill='x', side='left')
      self.entryTimelineEnd = ttk.Spinbox(self.frameTimelineEnd)
      self.entryTimelineEnd.config(textvariable=self.timelineEnd)
      self.entryTimelineEnd.config(from_=0)
      self.entryTimelineEnd.config(to=100)
      self.entryTimelineEnd.config(increment=0.1)
      self.entryTimelineEnd.pack(expand='false', fill='x', side='right')

      self.entryTimelineEndGetNow = ttk.Button(self.frameTimelineEnd,text='Current Time',style="small.TButton",command=self.getCurrenttimeForEnd)
      self.entryTimelineEndGetNow.pack(expand='false', fill='x', side='right')

      self.frameTimelineEnd.pack(expand='true', fill='x', side='top')

      self.frameTimeline.pack(expand='true', fill='x', side='top')

    for param in spec.get('params',[]):    
      if param.get('type') == 'timelineStart':
        self.timelineStart.set(param.get('value',''))
      elif param.get('type') == 'timelineEnd':
        self.timelineEnd.set(param.get('value',''))
      else:
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

  def setActiveTimeLineValue(self,activeValuePair):
    self.controller.setActiveTimeLineValue(activeValuePair)
  
  def hasKeyValueCommandsSet(self):
    for fvp in self.filterValuePairs:
      if len(fvp.getKeyValues())>0:
        return True
    return False

  def deselectNonMatchingFilterValuePairs(self,activeValuePair):
    for fvp in self.filterValuePairs:
      if fvp != activeValuePair:
        fvp.deactivateTimeLineSection()

  def getGlobalOptions(self):
    return self.controller.getGlobalOptions()

  def getClipDuration(self):
    return self.controller.getClipDuration()

  def getCurrenttimeForStart(self):
    self.timelineStart.set(self.controller.getCurrentPlaybackPosition())

  def getCurrenttimeForEnd(self):
    self.timelineEnd.set(self.controller.getCurrentPlaybackPosition())

  def getTimelineValuesAsSpecifications(self):
    specs = []
    try:
      ts = float(self.timelineStart.get())
      specs.append({'type':'timelineStart','value':ts})
    except:
      pass  
    try:
      ts = float(self.timelineEnd.get())
      specs.append({'type':'timelineEnd', 'value':ts})
    except:
      pass  
    return specs


  def populateRectPropValues(self):
    x1,y1,x2,y2 = self.controller.getRectProperties()
    iw,ih       = self.controller.getVideoDimensions()

    x1,x2 = sorted([x1,x2])
    y1,y2 = sorted([y1,y2])


    rectDerivedProps = dict(
      x=x1,y=y1,x1=x1,y1=y1,x2=x2,y2=y2,
      w=x2-x1,h=y2-y1,cx=(x1+x2)/2,cy=(y1+y2)/2,
      xf=round(x1/iw,4),yf=round(y1/ih,4),wf=round((x2-x1)/iw,4),hf=round((y2-y1)/ih,4),
      px0=x1,py0=y1,
      px1=x2,py1=y1,
      px2=x1,py2=y2,
      px3=x2,py3=y2,
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

  def getFilterExpression(self,preview=False,encodingStage=False):
    if not self.enabled:
      return 'null'

    if preview:
      filterExp= self.spec.get("filterPreview",self.spec.get("filter",'null'))
    elif self.encodingStageFilter and encodingStage==False:
      return 'null'
    else:
      filterExp= self.spec.get("filter",'null')
    

    filerExprams=[]
    i=id(self)
    values = dict( x.getValuePair() for x in self.filterValuePairs )
    print('values',values)
    formatDict={}

    for param in self.spec.get('params',[]):
      if param.get('n') is not None:
        if '{'+param['n']+'}' in filterExp:
          formatDict.update({'fn':i,param['n']:values[param['n']] },)
        else:
          try:
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
          except:
            filerExprams.append(':{}={}'.format(param['n'],values[param['n']]) )

    if '{fn}' in filterExp:
      formatDict.update({'fn':i,})

    if len(formatDict)>0:
      filterExp = filterExp.format( **formatDict )

    for i,e in enumerate(filerExprams):
      if i==0:
        filterExp+= '='+e[1:]
      else:
        filterExp+= e

    if self.timelineSupport and filterExp != 'null' and not self.encodingStageFilter:
      tsStart = None
      tsEnd   = None

      try:
        tsStart = float(self.timelineStart.get())
        if preview:
          tsStart = self.controller.normaliseTimestamp(tsStart)
      except Exception as e:
        print(e)

      try:
        tsEnd = float(self.timelineEnd.get())
        if preview:
          tsEnd = self.controller.normaliseTimestamp(tsEnd)
      except Exception as e:
        print(e)

      timelineExpression = ''
      if tsStart is not None and tsEnd is not None:
        timelineExpression = ":enable='between(t,{},{})'".format(tsStart,tsEnd)
      elif tsStart is not None:
        timelineExpression = ":enable='gte(t,{})'".format(tsStart)
      elif tsEnd is not None:
        timelineExpression = ":enable='lte(t,{})'".format(tsEnd)

      print('timelineExpression',timelineExpression)

      if '{timelineExpression}' in filterExp:
        filterExp = filterExp.format(timelineExpression=timelineExpression)
      else:
        filterExp += timelineExpression

    return filterExp

  def getTimeLimeCommandValues(self):
    commands = {}
    for fvp in self.filterValuePairs:
      if fvp.commandVarEnabled:
        for varTarget in fvp.commandVarTarget:  
          varTarget = varTarget.format(fn=id(self))
          for varProperty  in  fvp.commandVarProperty:
            for timeStamp,commandValue,_ in fvp.getKeyValues(interpolation=self.controller.interpolationFactor):
              commands.setdefault(timeStamp,[]).append((varTarget,varProperty,commandValue,fvp.commandInterpolationMode))

    return commands

  def recaculateFilters(self):
    print('recaculateFilters')
    self.controller.recaculateFilters()

  def remove(self):
    for fvp in self.filterValuePairs:
      if fvp.commandVarSelected:
        self.controller.setActiveTimeLineValue(None)
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
    self.buttonFilterActionClear.config(command=self.clearFilters,style="smallTall.TButton")
    self.buttonFilterActionClear.pack(expand='true', fill='x', side='left')

    self.buttonOverrideFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonOverrideFilters.config(text='Apply to all')
    self.buttonOverrideFilters.config(command=self.overrideFilters,style="smallTall.TButton")
    self.buttonOverrideFilters.pack(expand='true', fill='x', side='right')

    self.buttonPasteFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonPasteFilters.config(text='Paste filters')
    self.buttonPasteFilters.config(command=self.pasteFilters,style="smallTall.TButton")
    self.buttonPasteFilters.pack(expand='true', fill='x', side='right')
    
    self.buttonCopyFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonCopyFilters.config(text='Copy filters')
    self.buttonCopyFilters.config(command=self.copyfilters,style="smallTall.TButton")
    self.buttonCopyFilters.pack(expand='true', fill='x', side='right')

    self.frameFilterActionsGlobal.config(height='200', width='200')
    self.frameFilterActionsGlobal.pack(fill='x', side='top')


    self.framefilterAdditionFrame = ttk.Frame(self.labelframeFilterBrowserFrame)
    self.buttonAddFilter = ttk.Button(self.framefilterAdditionFrame)
    self.buttonAddFilter.config(text='Add Filter')
    self.buttonAddFilter.config(command=self.addSelectedfilter)
    self.buttonAddFilter.pack(side='right')
    self.selectedFilter=tk.StringVar()
    self.selectableFilters = sorted([x['name'] for x in selectableFilters],key=lambda x:x.upper())
    self.selectedFilter.set('crop')   

    self.comboboxFilterSelection = ttk.OptionMenu(self.framefilterAdditionFrame,self.selectedFilter,self.selectedFilter.get(),*self.selectableFilters)
    self.comboboxFilterSelection.pack(expand='true', fill='both', side='left')
    self.framefilterAdditionFrame.config(height='200', width='200')
    self.framefilterAdditionFrame.pack(expand='false', fill='x', padx='2',pady='3', side='top')
    self.scrolledframeFilterContainer = ScrolledFrame(self.labelframeFilterBrowserFrame, scrolltype='vertical')
    self.filterContainer = self.scrolledframeFilterContainer.innerframe
    self.filterSpecifications = []
    self.filterSpecificationCount=0
    self.scrolledframeFilterContainer.configure(usemousewheel=False)
    self.scrolledframeFilterContainer.pack(expand='true', fill='both', side='top')

    self.labelframeFilterBrowserFrame.config(height='200', text='Filtering', width='200')
    self.labelframeFilterBrowserFrame.pack(anchor='w', expand='false', fill='y', side='left')

    self.playerContainerFrame = ttk.Frame(self.frameFilterSelectionFrame)
    self.playerContainerFrame.config(cursor="crosshair")
    self.playerContainerFrame.pack(expand='true', fill='both', side='right')

    self.selectionOptionsFrame = ttk.Frame(self.playerContainerFrame)

    self.autocropButton = ttk.Button(self.selectionOptionsFrame)
    self.autocropButton.config(text='Autocrop')
    self.autocropButton.config(command=self.autoCrop)
    self.autocropButton.pack(side='left')

    self.volumeLabel = ttk.Label(self.selectionOptionsFrame)
    self.volumeLabel.config(text='Vol')
    self.volumeLabel.pack(expand='false', side='left')

    self.scaleVolume = ttk.Scale(self.selectionOptionsFrame,from_=0, to=100)
    self.scaleVolume.config(command=self.setVolume)
    self.scaleVolume.pack(fill="x", padx="2", side="left")

    self.fixSeectionArEnabledVar = tk.BooleanVar()
    self.fixSeectionArEnabledVar.set(False)
    self.arFixCheckbox = ttk.Checkbutton(self.selectionOptionsFrame,text="Restrict selection aspect ratio", variable=self.fixSeectionArEnabledVar)
    self.arFixCheckbox.pack(expand='false', side='left')
    
    self.fixSeectionArVar = tk.StringVar()
    self.fixSeectionArVar.set('1.7')
    self.spinBoxArRatio = ttk.Spinbox(self.selectionOptionsFrame,textvariable=self.fixSeectionArVar,from_=float('-inf'), to=float('inf'), increment=0.01)
    self.spinBoxArRatio.pack(expand='false', side='left')

    self.flipARButton = ttk.Button(self.selectionOptionsFrame,text="Flip AR", command=self.flipAR)
    self.flipARButton.pack(expand='false', side='left')

    self.fitToScreenVar = tk.BooleanVar()
    self.fitToScreenVar.trace('w',self.changeFitToScreen)
    self.fitToScreenVar.set(True)
    self.fitToScreenCheckbox = ttk.Checkbutton(self.selectionOptionsFrame,text="Fit to screen", variable=self.fitToScreenVar)
    self.fitToScreenCheckbox.pack(expand='false', side='left')

    self.volumeLabel = ttk.Label(self.selectionOptionsFrame)
    self.volumeLabel.config(text='0.0s')
    self.volumeLabel.pack(expand='false', side='left')

    self.templatePopupMenu = tk.Menu(self, tearoff=0)
    self.templatePopupMenu.add_command(label="No filter templates found")

    self.templateButton = ttk.Button(self.selectionOptionsFrame)
    self.templateButton.config(text='Apply Template')
    self.templateButton.config(command=self.showTemplateMenuPopup)

    self.templateButton.pack(side='right')

    self.importButton = ttk.Button(self.selectionOptionsFrame)
    self.importButton.config(text='Import Json')
    self.importButton.config(command=self.importJson)
    self.importButton.pack(side='right')

    self.exportButton = ttk.Button(self.selectionOptionsFrame)
    self.exportButton.config(text='Export Json')
    self.exportButton.config(command=self.exportJson)
    self.exportButton.pack(side='right')

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
    self.framePlayerFrame.pack(expand='true', fill='both', side='top')

    self.mouseRectDragging=False
    self.videoMouseRect=[None,None,None,None]
    self.screenMouseRect=[None,None,None,None]

    self.framePlayerFrame.bind("<Button-1>",          self.videomousePress)
    self.framePlayerFrame.bind("<ButtonRelease-1>",   self.videomousePress)
    self.framePlayerFrame.bind("<Motion>",            self.videomousePress)

    self.frameFilterSelectionFrame.config(height='200', width='200')
    self.frameFilterSelectionFrame.pack(expand='true', fill='both', side='top')
    
    self.timeline_canvas_popup_menu = tk.Menu(self, tearoff=0)
    self.timeline_canvas_popup_menu.add_command(label="Add key value",command=self.addKeyValue)
    self.timeline_canvas_popup_menu.add_command(label="Remove key value",command=self.removeKeyValue)

    self.frameValueTimelineFrame = ttk.Frame(self.frameFilterFrame)
    
    self.canvasValueTimeline = tk.Canvas(self.frameValueTimelineFrame)
    self.canvasValueTimeline.config(background='#373737', height='150',bg='#1E1E1E' ,highlightthickness='0', borderwidth=0,border=0,relief='flat')
    self.canvasValueTimeline.pack(expand='true', fill='both', side='top')
    
    self.timelineSeekHandle = self.canvasValueTimeline.create_line(-1, 20, -1, 175,fill="white") 

    self.canvasValueTimeline.bind("<Button-1>",          self.timelineClickHandler)
    self.canvasValueTimeline.bind("<Button-3>",          self.timelineClickHandler)
    self.canvasValueTimeline.bind("<ButtonRelease-1>",   self.timelineClickHandler)
    self.canvasValueTimeline.bind("<Motion>",            self.timelineClickHandler)
    self.canvasValueTimeline.bind("<MouseWheel>",        self.timelineMousewheel)

    self.canvasValueTimeline.bind("d",        self.keyboardD)

    self.canvasValueTimeline.bind("i",        self.keyboardI)

    self.canvasValueTimeline.focus_set()

    self.canvasValueTimeline.bind('<Up>',    self.keyboardUp)
    self.canvasValueTimeline.bind('<Down>',  self.keyboardDown)
    self.canvasValueTimeline.bind('<Left>',  self.keyboardLeft)
    self.canvasValueTimeline.bind('<Right>', self.keyboardRight)
    self.canvasValueTimeline.bind('<space>', self.keyboardSpace)

    self.canvasValueTimeline.bind('<Configure>',self.reconfigure)

    self.canvasMouseDown = False

    self.frameValueTimelineFrame.config(height='175', width='100')
    self.frameValueTimelineFrame.pack(expand='false', fill='x', side='bottom')
    

    self.frameFilterFrame.config(height='200', width='200')
    self.frameFilterFrame.pack(expand='true', fill='both', side='top')
    

    self.mainwindow = self.frameFilterFrame
    self.subclips={}
    self.subClipOrder=[]
    self.currentSubclipIndex=None
    self.filterClipboard=[]
    self.mouseRectMoving=False
    self.mouseRectMoveStart=(0,0)
    self.activeCommandFilterValuePair = None
    self.timeline_canvas_last_right_click_x=0
    self.interpolationFactor=0

  def keyboardI(self,e):
    self.interpolationFactor = (self.interpolationFactor+1)%10
    self.refreshtimeLineForNewClip()

  def keyboardD(self,e):
    if self.activeCommandFilterValuePair is not None:
      duration      = self.controller.getClipDuration()
      posSeconds = self.controller.getCurrentPlaybackPosition()
      posX = (posSeconds/duration)*self.canvasValueTimeline.winfo_width()

      for timeStamp,value,_ in self.activeCommandFilterValuePair.getKeyValues():
        tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
        if posX-5<tx<posX+5:
          self.activeCommandFilterValuePair.removeKeyValue(timeStamp)
          self.controller.seekToPercent(tx/self.canvasValueTimeline.winfo_width())
          self.refreshtimeLineForNewClip()
          break

  def keyboardUp(self,e):
    self.incrementAtCurrentPlaybackPosition(1,e)

  def keyboardDown(self,e):
    self.incrementAtCurrentPlaybackPosition(-1,e)
  
  def incrementAtCurrentPlaybackPosition(self,increment,e):
    ctrl  = (e.state & 0x4) != 0
    if self.activeCommandFilterValuePair is not None:
      duration      = self.controller.getClipDuration()
      posSeconds = self.controller.getCurrentPlaybackPosition()
      posX = (posSeconds/duration)*self.canvasValueTimeline.winfo_width()
      existingTS=None
      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues(interpolation=self.interpolationFactor):
        if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          if posX-5<tx<posX+5:
            existingTS=timeStamp
      if existingTS is None:
        self.activeCommandFilterValuePair.addKeyValue(posSeconds)
      self.activeCommandFilterValuePair.incrementKeyValue(posSeconds,increment*10 if ctrl else increment)
        
      self.refreshtimeLineForNewClip()

  def keyboardLeft(self,e):
    self.handleSeek(e,-0.05)
    
  def keyboardRight(self,e):
    self.handleSeek(e,0.05)

  def handleSeek(self,e,increment):
    ctrl  = (e.state & 0x4) != 0

    if ctrl:
      posSeconds = self.controller.getCurrentPlaybackPosition()
      points = [0,self.controller.getClipDuration()]
      points.extend([x[0] for x in self.activeCommandFilterValuePair.getKeyValues(interpolation=self.interpolationFactor) if x[2]])
      points = sorted(points)
      mids = [(x+y)/2 for x,y in zip(points[1:], points)]
      
      if increment<0:
        self.seekToTimelinePoint( [x for x in mids if x<posSeconds-0.05][-1]  )
      else:
        self.seekToTimelinePoint( [x for x in mids if x>posSeconds+0.05][0]  )

    else:
      self.controller.seekRelative(increment)
    

  def keyboardSpace(self,e):
    self.controller.togglePause()


  def addKeyValue(self):
    secondsClicked = (self.timeline_canvas_last_right_click_x/self.canvasValueTimeline.winfo_width())*self.controller.getClipDuration()
    if self.activeCommandFilterValuePair is not None:
      self.activeCommandFilterValuePair.addKeyValue(secondsClicked)
      self.refreshtimeLineForNewClip()
      self.controller.seekToPercent(self.timeline_canvas_last_right_click_x/self.canvasValueTimeline.winfo_width())

  def removeKeyValue(self):
    duration      = self.controller.getClipDuration()
    secondsClicked = (self.timeline_canvas_last_right_click_x/self.canvasValueTimeline.winfo_width())*self.controller.getClipDuration()
    if self.activeCommandFilterValuePair is not None:
      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues(interpolation=self.interpolationFactor):
        if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          if self.timeline_canvas_last_right_click_x-5<tx<self.timeline_canvas_last_right_click_x+5:
            self.activeCommandFilterValuePair.removeKeyValue(timeStamp)
            self.controller.seekToPercent(tx/self.canvasValueTimeline.winfo_width())
            self.refreshtimeLineForNewClip()
            break

  def timelineMousewheel(self,e):
    ctrl  = (e.state & 0x4) != 0
    duration      = self.controller.getClipDuration()
    secondsClicked = (e.x/self.canvasValueTimeline.winfo_width())*self.controller.getClipDuration()
    
    if self.activeCommandFilterValuePair is not None:
      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues(interpolation=self.interpolationFactor):
        if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          if e.x-5<tx<e.x+5:
            if e.delta>0:
              self.activeCommandFilterValuePair.incrementKeyValue(timeStamp,10 if ctrl else 1)
            else:
              self.activeCommandFilterValuePair.incrementKeyValue(timeStamp,-10 if ctrl else -1)
            self.refreshtimeLineForNewClip()
            self.timeline_canvas_last_right_click_x=e.x
            self.controller.seekToPercent(self.timeline_canvas_last_right_click_x/self.canvasValueTimeline.winfo_width())
            break

  def setActiveTimeLineValue(self,activeValuePair):
    for flt in self.filterSpecifications:
      flt.deselectNonMatchingFilterValuePairs(activeValuePair)
    self.activeCommandFilterValuePair = activeValuePair
    self.refreshtimeLineForNewClip()

  def timelineClickHandler(self,e):
    self.canvasValueTimeline.focus_set()
    if e.type == tk.EventType.ButtonPress and e.num==1:
      self.canvasMouseDown=True
    elif e.type == tk.EventType.ButtonRelease and e.num==1:
      self.canvasMouseDown=False

    if self.canvasMouseDown:
      self.controller.seekToPercent(e.x/self.canvasValueTimeline.winfo_width())

    if e.type == tk.EventType.ButtonPress:
      if e.num==3 and self.activeCommandFilterValuePair is not None:      
        self.timeline_canvas_last_right_click_x=e.x
        self.timeline_canvas_popup_menu.tk_popup(e.x_root,e.y_root)

  def updateSeekPositionThousands(self,value,seconds):
    tx = seconds/self.controller.getClipDuration()
    tx = tx*self.canvasValueTimeline.winfo_width()
    self.canvasValueTimeline.coords(self.timelineSeekHandle, tx, 20, tx, 175)  

  def reconfigure(self,e):
    self.refreshtimeLineForNewClip()

  def refreshtimeLineForNewClip(self):

    self.canvasValueTimeline.delete('ticks')
    duration      = self.controller.getClipDuration()
    tickStart     = 0
    tickIncrement =  duration/31

    tickStart = int((tickIncrement * round(tickStart/tickIncrement))-tickIncrement)

    while 1:
      tickStart+=tickIncrement
      tx = int((tickStart/duration)*self.canvasValueTimeline.winfo_width())
      if tx<0:
        pass
      elif tx>=self.winfo_width():
        break
      else:          
        tm = self.canvasValueTimeline.create_line(tx, 0, tx, 5,fill="white",tags='ticks') 
        tm = self.canvasValueTimeline.create_text(tx, 10,text="{:0.2f}".format(tickStart),fill="white",tags='ticks') 
    
    self.canvasValueTimeline.delete('ActiveFilterName')
    self.canvasValueTimeline.delete('KeyValuePoints')
    if self.activeCommandFilterValuePair is not None:
      self.canvasValueTimeline.create_text(5, 140, text="{}".format(self.activeCommandFilterValuePair.commandvarName),fill="white",tags='ActiveFilterName')

      valMax,valMin = float('-inf'),float('inf')

      if self.activeCommandFilterValuePair.vmin not in (float('-inf'),float('inf'),None):
        valMin=self.activeCommandFilterValuePair.vmin

      if self.activeCommandFilterValuePair.vmax not in (float('-inf'),float('inf'),None):
        valMax=self.activeCommandFilterValuePair.vmax

      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues(interpolation=self.interpolationFactor):
        valMax=max(valMax,value)
        valMin=min(valMin,value)
        if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          self.canvasValueTimeline.create_line(tx, 20, tx, 130,fill="#375e6b",width=5,tags='KeyValuePoints') 
          self.canvasValueTimeline.create_line(tx, 20, tx, 130,fill="#69bfdb",tags='KeyValuePoints') 

      valRange = abs(valMax-valMin)*0.25
      if valRange == 0:
        valRange = 0.25

      valMin -= valRange
      valMax += valRange

      valRange = abs(valMax-valMin)

      print(valMax,valMin)

      lastX,lastY=None,None

      effectiveHeight = self.canvasValueTimeline.winfo_height()-20
      heightOffset    = 10

      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues(interpolation=self.interpolationFactor):
        tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
        ty = heightOffset+(effectiveHeight-(((value-valMin)/valRange)*effectiveHeight))

        if lastX is None and lastY is None:
          lastX=0
          lastY=ty

        self.canvasValueTimeline.create_line(lastX, lastY, tx, ty,fill="#113a47",tags='KeyValuePoints')
        if real:
          self.canvasValueTimeline.create_oval(tx-5, ty-4, tx+5, ty+4,fill="#db6986",tags='KeyValuePoints')
        else:
          self.canvasValueTimeline.create_oval(tx-2, ty-2, tx+2, ty+1,fill="#6d3443",tags='KeyValuePoints')

        lastX,lastY=tx,ty
        if real:
          self.canvasValueTimeline.create_text(tx, 140,text="{:0.2f}".format(value),fill="white",tags='ticks')

      if lastX is not None and lastY is not None:
        self.canvasValueTimeline.create_line(lastX, lastY, self.canvasValueTimeline.winfo_width(), ty,fill="#113a47",tags='KeyValuePoints')

  def showTemplateMenuPopup(self):
    self.templatePopupMenu.tk_popup(self.winfo_pointerx(),self.winfo_poinstery())

  def getGlobalOptions(self):
    return self.controller.getGlobalOptions()
  
  def getCurrentPlaybackPosition(self):
    return self.controller.getCurrentPlaybackPosition()

  def getClipDuration(self):
    return self.controller.getClipDuration()

  def autoCropCallback(self,x,y,w,h):

    self.filterSpecificationCount+=1
    newFilter = None
    for spec in selectableFilters:
      if spec['name'] == 'crop':
        newFilter = FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        self.filterSpecifications.append( newFilter)
        break
    if newFilter is not None:
      newFilter.rectProps.get('x').set(int(x))
      newFilter.rectProps.get('y').set(int(y))
      newFilter.rectProps.get('w').set(int(w))
      newFilter.rectProps.get('h').set(int(h))
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters()

  def importJson(self,jsonOverride=None):
    if jsonOverride is None:
      s = self.clipboard_get()
      s = json.loads(s)
    else:
      s=jsonOverride

    if self.currentSubclipIndex is not None:
      rid = self.subClipOrder[self.currentSubclipIndex]
      self.subclips[rid]['filters'] = copy.deepcopy(s)
      for f in self.filterSpecifications:
        f.destroy()
      self.filterSpecifications=[]
      rid = self.subClipOrder[self.currentSubclipIndex]
      
      for spec in self.subclips[rid].setdefault('filters',[]):
        self.filterSpecificationCount+=1
        self.filterSpecifications.append( 
          FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        )
      self.recaculateFilters()

  def setVolume(self,value):
    self.controller.setVolume(value)

  def exportJson(self):
    self.clipboard_clear()
    self.clipboard_append(json.dumps(self.convertFilterstoSpecDefaults()))

  def flipAR(self):
    forceAR = float(self.fixSeectionArVar.get())
    forceAR = 1/forceAR
    self.fixSeectionArVar.set(forceAR)

  def autoCrop(self):
    rid = self.subClipOrder[self.currentSubclipIndex]
    subclip = self.subclips[rid]
    start    = subclip['start']
    end      =  subclip['end'] 
    filename = subclip['filename']
    mid = (start+end)/2
    self.controller.requestAutocrop(rid,mid,filename,self.autoCropCallback)

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

  def getVideoDimensions(self):
    return self.controller.getVideoDimensions()


  def getRectProperties(self):
    return self.videoMouseRect

  def applyScreenSpaceAR(self):
    forceAR = None

    if self.fixSeectionArEnabledVar.get():
      try:
        forceAR = float(self.fixSeectionArVar.get())
      except Exception as e:
        logging.error("applyScreenSpaceAR Exception",exc_info=e)

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

      if e.type == tk.EventType.ButtonPress:        
        if self.screenMouseRect[0] is not None and abs(((self.screenMouseRect[0]+self.screenMouseRect[2])/2)-e.x)<10 and abs(((self.screenMouseRect[1]+self.screenMouseRect[3])/2)-e.y)<10:
          self.mouseRectMoving=True
          self.mouseRectMoveStart=(e.x,e.y)
        else:
          logging.debug("videomousePress start")
          self.mouseRectDragging=True
          self.screenMouseRect[0]=e.x
          self.screenMouseRect[1]=e.y
      elif e.type in (tk.EventType.Motion,tk.EventType.ButtonRelease) and (self.mouseRectDragging or self.mouseRectMoving):
        logging.debug("videomousePress show")
        if self.mouseRectMoving:
          haw = abs(self.screenMouseRect[0]-self.screenMouseRect[2])//2
          hah = abs(self.screenMouseRect[1]-self.screenMouseRect[3])//2
          self.screenMouseRect[0]=e.x-haw
          self.screenMouseRect[1]=e.y-hah
          self.screenMouseRect[2]=e.x+haw
          self.screenMouseRect[3]=e.y+hah
          print(self.screenMouseRect)
        else:
          self.screenMouseRect[2]=e.x
          self.screenMouseRect[3]=e.y
        self.applyScreenSpaceAR()
        self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3])
      if e.type == tk.EventType.ButtonRelease:
        logging.debug("videomousePress release")
        self.mouseRectDragging=False
        self.mouseRectMoving=False

        vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
        vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 

        self.videoMouseRect=[vx1,vy1,vx2,vy2]
        self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3])
      
      if self.screenMouseRect[0] is not None and not self.mouseRectDragging and self.screenMouseRect[0]==self.screenMouseRect[2] and self.screenMouseRect[1]==self.screenMouseRect[3]:
        logging.debug("videomousePress clear")
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

  def updateSeekLabel(self,value):
    self.volumeLabel.config(text='{:0.2f}s'.format(value))

  def seekToTimelinePoint(self,ts):
    return self.controller.seekToTimelinePoint(ts)

  def normaliseTimestamp(self,ts):
    return self.controller.normaliseTimestamp(ts)


  def recaculateFilters(self):
    filterexpPreview=[]
    filterExpReal=[]
    filterExpEncodingStage=[]

    commandSet = {}

    for filter in self.filterSpecifications:

      commandSet.update(filter.getTimeLimeCommandValues())

      filterexpPreview.append(filter.getFilterExpression(preview=True)) 
      filterExpReal.append(filter.getFilterExpression(preview=False))
      if filter.encodingStageFilter:
        filterExpEncodingStage.append(filter.getFilterExpression(preview=False,encodingStage=True))

    print(commandSet)

    commandStr_preview = ""
    commandStr_real = ""

    lastCommandValues = {}

    for k,v in sorted(commandSet.items()):
      if len(v)>0:
        for cmdTarget,cmdProperty,cmdValue,interpolationMode in v:
          lastTime,lastValue,_ = lastCommandValues.get((cmdTarget,cmdProperty),(0,cmdValue,interpolationMode))

          norm_k = self.controller.normaliseTimestamp(k)
          norm_lastTime = self.controller.normaliseTimestamp(lastTime)

          if interpolationMode == 'lerp':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},TI)';\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},TI)';\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'lerp-sigmoid':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},sin(TI*(PI/2)))';\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},sin(TI*(PI/2)))';\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'lerp-smooth':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f}, (TI * TI * (3 - 2 * TI)) )';\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f}, (TI * TI * (3 - 2 * TI)) )';\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'lerp-smooth-inv':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f}, (0.5 - sin(asin(1.0 - 2.0 * TI) / 3.0)) )';\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f}, (0.5 - sin(asin(1.0 - 2.0 * TI) / 3.0)) )';\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)
                   
          elif interpolationMode == 'lerp-smooth-2nd':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f}, (TI * TI * TI * (TI * (TI * 6 - 15) + 10)) )';\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f}, (TI * TI * TI * (TI * (TI * 6 - 15) + 10)) )';\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'neighbour':
            commandStr_preview += "{k:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, cv=cmdValue)
            commandStr_real    += "{k:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty, cv=cmdValue)

          elif interpolationMode == 'neighbour-relative':
            commandStr_preview += "{k:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, cv=cmdValue)
            commandStr_real    += "{k:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty, cv=cmdValue-lastValue)

          lastCommandValues[(cmdTarget,cmdProperty)] = (k,cmdValue,interpolationMode)

    for (cmdTarget,cmdProperty),(lastTime,cmdValue,interpolationMode) in lastCommandValues.items():
      norm_lastTime = self.controller.normaliseTimestamp(lastTime)

      commandStr_preview += "{l:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=norm_lastTime, t=cmdTarget, p=cmdProperty, cv=cmdValue)

      if interpolationMode == 'neighbour-relative':
        commandStr_real    += "{l:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=lastTime,      t=cmdTarget, p=cmdProperty, cv=0.0)
      else:
        commandStr_real    += "{l:0.4f} [enter] {t} {p} {cv:0.4f};\n".format(l=lastTime,      t=cmdTarget, p=cmdProperty, cv=cmdValue)



    print(commandStr_preview)

    filterExpStrPreview = ','.join(filterexpPreview)
    filterExpStrReal = ','.join(filterExpReal)
    filterExpEncodingStage = ','.join(filterExpEncodingStage)

    if len(commandSet)>0:

      commandFilename_preview = os.path.join( self.controller.gettempVideoFilePath(), "commands_{}_preview.txt".format(id(self)) )
      with open(commandFilename_preview,'w') as cmdf:
        cmdf.write(commandStr_preview)

      commandFilename_real = os.path.join( self.controller.gettempVideoFilePath(), "commands_{}_real.txt".format(id(self)) )
      with open(commandFilename_real,'w') as cmdf:
        cmdf.write(commandStr_real)


      sndCmdFilter_preview = "sendcmd=f='{}',".format(cleanFilenameForFfmpeg(os.path.abspath(commandFilename_preview)).replace('\\','/').replace(':','\\:') )
      sndCmdFilter_real    = "sendcmd=f='{}',".format(cleanFilenameForFfmpeg(os.path.abspath(commandFilename_real)).replace('\\','/').replace(':','\\:') )


      filterExpStrPreview = sndCmdFilter_preview+filterExpStrPreview
      filterExpStrReal    = sndCmdFilter_real+filterExpStrReal
      

    if len(filterexpPreview)==0:
      self.controller.clearFilter()
    if len(filterexpPreview)>0:
      self.controller.setFilter(filterExpStrPreview)

    if self.currentSubclipIndex is not None:
      currentClip = self.getCurrentClip()
      if currentClip is not None:
        currentClip['filters'] = self.convertFilterstoSpecDefaults()
        currentClip['filterexp'] =filterExpStrReal
        currentClip['filterexpEncStage'] =filterExpEncodingStage

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
      for valPair in ifilter.filterValuePairs:
        for param in baseSpec['params']:
          if param['n'] == valPair.n and valPair.commandVarAvaliable:
            param['commandVarEnabled']=valPair.commandVarEnabled
            param['commandVarSelected']=valPair.commandVarSelected
            param['keyValues'] = valPair.keyValues

      baseSpec.setdefault('params',[]).extend(ifilter.getTimelineValuesAsSpecifications())
      filterstack.append(baseSpec)
    return filterstack


  def setController(self,controller):
    self.controller=controller

    if len(self.controller.getTemplateListing())==0:
      self.templateButton["state"] = "disabled"
    else:
      self.templatePopupMenu.delete(0)

    for name,value in self.controller.getTemplateListing():
      self.templatePopupMenu.add_command(label=name,command=lambda val=value:self.importJson(jsonOverride=val))


  def tabSwitched(self,tabName):
    if str(self) == tabName:
      self.recauclateSubclips()
      buttonState='normal'
      if len(self.subclips) == 0:
        buttonState='disabled'

      self.buttonVideoPickerPrevious['state'] = buttonState
      self.VideoPickerNext['state'] = buttonState
      self.buttonFilterActionClear['state'] = buttonState
      self.buttonOverrideFilters['state'] = buttonState
      self.buttonPasteFilters['state'] = buttonState
      self.buttonCopyFilters['state'] = buttonState
      self.buttonAddFilter['state'] = buttonState
      self.comboboxFilterSelection['state'] = buttonState

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

    print('tempSeclectedRid',tempSeclectedRid)
    print('self.subClipOrder',self.subClipOrder)

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
      logging.error("getCurrentClip Exception",exc_info=e)
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

  def overrideFilters(self):
    if self.currentSubclipIndex is not None:
      resp = messagebox.askyesno(title="Apply these filters to all clips?", message="This will clear the filters on all other clips and override them with these filters, are you sure?")
      if resp:
        tempfilterClipboard = self.convertFilterstoSpecDefaults()
        for rid in self.subClipOrder:
          self.subclips[rid]['filters'] = copy.deepcopy(tempfilterClipboard)
        self.recaculateFilters()

        currentClip = self.getCurrentClip()
        if currentClip is not None:
          filters           = copy.deepcopy(currentClip['filters'])
          filterexp         = copy.deepcopy(currentClip['filterexp'])
          filterexpEncStage = copy.deepcopy(currentClip['filterexpEncStage'])

          for clip in self.subclips.values():
            clip['filters']           = filters
            clip['filterexp']         = filterexp
            clip['filterexpEncStage'] = filterexpEncStage        

  def pasteFilters(self):
    if self.currentSubclipIndex is not None:
      rid = self.subClipOrder[self.currentSubclipIndex]
      self.subclips[rid]['filters'] = copy.deepcopy(self.filterClipboard)
      for f in self.filterSpecifications:
        f.destroy()
      self.filterSpecifications=[]
      rid = self.subClipOrder[self.currentSubclipIndex]
      
      for spec in self.subclips[rid].setdefault('filters',[]):
        self.filterSpecificationCount+=1
        self.filterSpecifications.append( 
          FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        )
      self.recaculateFilters()


  def setSubclipIndex(self,newIndex):
    self.recaculateFilters()
    if self.currentSubclipIndex is not None and len(self.subClipOrder)>0:
      try:
        rid = self.subClipOrder[self.currentSubclipIndex]
        self.subclips[rid]['filters'] = self.convertFilterstoSpecDefaults()
      except Exception as e:
        print(e,"Can't update old subclip by index")

    self.currentSubclipIndex = newIndex
    for f in self.filterSpecifications:
      f.destroy()
    self.filterSpecifications=[]

    if newIndex is not None and len(self.subClipOrder)>0:
      rid = self.subClipOrder[self.currentSubclipIndex]
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
      self.controller.playVideoFile(currentClip['filename'],s,e)

  def getPlayerFrameWid(self):
    return self.framePlayerFrame.winfo_id()

if __name__ == '__main__':
  import webmGenerator

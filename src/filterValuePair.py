

import tkinter as tk
import tkinter.ttk as ttk
import time
import numpy as np
from math import sqrt
from tkinter.filedialog import askopenfilename
import threading


def cubic_interp1d(x0, x, y):

    x = np.asfarray(x)
    y = np.asfarray(y)

    if np.any(np.diff(x) < 0):
        indexes = np.argsort(x)
        x = x[indexes]
        y = y[indexes]

    size = len(x)

    xdiff = np.diff(x)
    ydiff = np.diff(y)

    Li = np.empty(size)
    Li_1 = np.empty(size-1)
    z = np.empty(size)

    Li[0] = sqrt(2*xdiff[0])
    Li_1[0] = 0.0
    B0 = 0.0
    z[0] = B0 / Li[0]

    for i in range(1, size-1, 1):
        Li_1[i] = xdiff[i-1] / Li[i-1]
        Li[i] = sqrt(2*(xdiff[i-1]+xdiff[i]) - Li_1[i-1] * Li_1[i-1])
        Bi = 6*(ydiff[i]/xdiff[i] - ydiff[i-1]/xdiff[i-1])
        z[i] = (Bi - Li_1[i-1]*z[i-1])/Li[i]

    i = size - 1
    Li_1[i-1] = xdiff[-1] / Li[i-1]
    Li[i] = sqrt(2*xdiff[-1] - Li_1[i-1] * Li_1[i-1])
    Bi = 0.0
    z[i] = (Bi - Li_1[i-1]*z[i-1])/Li[i]

    
    i = size-1
    z[i] = z[i] / Li[i]
    for i in range(size-2, -1, -1):
        z[i] = (z[i] - Li_1[i-1]*z[i+1])/Li[i]

    
    index = x.searchsorted(x0)
    np.clip(index, 1, size-1, index)

    xi1, xi0 = x[index], x[index-1]
    yi1, yi0 = y[index], y[index-1]
    zi1, zi0 = z[index], z[index-1]
    hi1 = xi1 - xi0

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

    self.videoSpaceAxis = self.param.get('videoSpaceAxis',None)
    self.videoSpaceSign = self.param.get('videoSpaceSign',0)

    self.n = self.param['n']
    self.vmin,self.vmax = float('-inf'),float('inf')
    if param.get('rectProp') is not None:
      self.controller.registerRectProp(param.get('rectProp'),self.valueVar,param.get('type','int'))

    self.commandVarSelected  = False
    self.commandVarAvaliable = False 
    self.commandVarEnabled   = False
    self.commandvarName      = None
    self.interpolationFactor = param.get('interpolationFactor',0)
    self.commandInterpolationMode = param.get('interpMode','lerp')
    self.interpolationModes = param.get('restrictedInterpModes',['lerp','lerp-smooth','lerp-smooth-2nd','lerp-sigmoid','lerp-smooth-inv','neighbour','neighbour-relative'])
    self.interpVar = tk.StringVar()
    self.interpVar.set(self.commandInterpolationMode)

    self.interpVar.trace('w',self.interpolationChanged)

    self.commandVarTarget = []
    self.commandVarProperty = []

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

    self.commandVarSelected = self.param.get('commandVarSelected',False)
    self.commandVarEnabled  = self.param.get('commandVarEnabled',False)
    self.updateCommandButtonStyles()

  def updateCommandButtonStyles(self):
    if self.commandVarAvaliable:
      if self.commandVarSelected:
        self.commandSelectButton.config(style='smallOnecharenabled.TButton')
        self.config(style='selectedCommandFrame.TFrame')
        self.labelfilterValueLabel.config(style='selectedCommandFrame.TLabel')
        self.entryInterpValue['state']='disabled'
        self.entryFilterValueValue.pack_forget()
        self.entryInterpValue.pack(side='right')
      else:
        self.commandSelectButton.config(style='smallOnechar.TButton') 
        self.config(style='TFrame')
        self.labelfilterValueLabel.config(style='TLabel')
        self.entryInterpValue['state']='normal'
        self.entryInterpValue.pack_forget()
        self.entryFilterValueValue.pack(side='right')  

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
      self.controller.recaculateFilters('interpolationChanged')
    else:
      self.interpVar.set(self.commandInterpolationMode)

  def clearKeyValues(self):
    self.keyValues={}

  def addKeyValue(self,seconds,value=None,useIncrementMultiplier=False,isAsoluteValue=False):
    try:
      if isAsoluteValue and value is not None:
        self.keyValues[seconds]= self.convertKeyValueToType(  (float(self.param.get('inc',1)) if useIncrementMultiplier else 1)*value )
      else:

        incrementValue = 0
        if value is not None:
          incrementValue=value
        if useIncrementMultiplier:
          incrementValue=value*self.param.get('inc',1)

        kvs = self.getKeyValues()

        lower = [(k,v) for k,v,_ in kvs if k<seconds][-1:]
        upper = [(k,v) for k,v,_ in sorted(kvs,reverse=True) if k>seconds][-1:]

        if len(lower)==1 and len(upper)==1:
          neighbourRange    = upper[0][1]-lower[0][1]
          neighbourDuration = upper[0][0]-lower[0][0]
          percent = (seconds-lower[0][0])/neighbourDuration

          self.keyValues[seconds]= self.convertKeyValueToType(  lower[0][1]+(neighbourRange*percent)+incrementValue )
        
        elif len(lower)==1:
          self.keyValues[seconds]= self.convertKeyValueToType( lower[0][1]+incrementValue )
        elif len(upper)==1:
          self.keyValues[seconds]= self.convertKeyValueToType( upper[0][1]+incrementValue )
        else:
          valueVarInc=0
          try:
            valueVarInc+=self.convertKeyValueToType(self.valueVar.get())
          except Exception as e:
            print("valueVarInc Exception",e)
          self.keyValues[seconds]= self.convertKeyValueToType(valueVarInc+incrementValue)

    except Exception as e:
      self.keyValues[seconds]= self.convertKeyValueToType(self.param['d'])
      print('addKeyValue Exception',e)

    if self.commandInterpolationMode == 'neighbour-relative' and self.isInitialTS(seconds):
      self.valueVar.set(self.keyValues[seconds])
    self.valueUpdated()


  def removeKeyValue(self,seconds):
    del self.keyValues[seconds]
    self.valueUpdated()


  def isInitialTS(self,seconds):
    if len(self.keyValues)>0:
      return sorted(self.keyValues.keys())[0]==seconds
    else:
      return False

  def incrementKeyValue(self,seconds,valueOffset,useIncrementMultiplier=True,isAsoluteValue=False):
    if seconds in self.keyValues:
      
      if isAsoluteValue:
        newval = (valueOffset*(self.param['inc'] if useIncrementMultiplier else 1))
      else:
        newval = self.keyValues[seconds]+(valueOffset*(self.param['inc'] if useIncrementMultiplier else 1))

      newval = max(min(newval,self.vmax),self.vmin)

      self.keyValues[seconds] = self.convertKeyValueToType(newval)

      if self.commandInterpolationMode == 'neighbour-relative' and self.isInitialTS(seconds):
        self.valueVar.set(self.keyValues[seconds])
      self.valueUpdated()

  def convertKeyValueToType(self,value):
    if self.param['type'] == 'int':
      return int(value)
    elif self.param['type'] == 'float':
      return float(value)
    return value

  def getKeyValues(self,interpolation=True):
    
    sortedKVs = sorted(list(self.keyValues.items()).copy())
    try:
      if self.interpolationFactor>0 and interpolation and len(sortedKVs)>1:

        x = np.array([x[0] for x in sortedKVs])
        y = np.array([x[1] for x in sortedKVs])

        x_new = np.linspace(x[0], x[-1] , int((x[-1]-x[0])*int(self.interpolationFactor)) )
        x_new = np.append(x_new,list(self.keyValues.keys()))

        y_new  = cubic_interp1d(x_new, x, y)

        oldKVS = [(k,v,True) for k,v in sortedKVs]
        newKVS = [(k,v,False) for k,v, in zip(x_new,y_new) if k not in self.keyValues]

        return sorted( newKVS + oldKVS )
      else:
        return [(a,b,True) for a,b, in sortedKVs]
    except Exception as e:
      print('getKeyValues Exception',e)
    return [(a,b,True) for a,b, in sortedKVs]

  def deactivateTimeLineSection(self):
    if self.commandVarAvaliable:
      self.commandVarSelected   = False
      self.updateCommandButtonStyles()

  def toggleTimelineSelection(self):
    if self.commandVarAvaliable:
      if self.commandVarSelected:
        self.commandVarSelected   = False
        self.controller.setActiveTimeLineValue(None)
      else:
        self.commandVarSelected   = True
        self.controller.setActiveTimeLineValue(self)
      self.updateCommandButtonStyles()


  def toggleTimelineCmdMode(self):
    if self.commandVarAvaliable:
      if self.commandVarEnabled:
        self.commandVarEnabled  = False
        self.commandVarSelected =False
        self.controller.setActiveTimeLineValue(None)
        self.updateCommandButtonStyles()
      else:
        self.commandVarEnabled   = True
        self.toggleTimelineSelection()
        self.updateCommandButtonStyles()        
      self.controller.recaculateFilters('toggleTimelineCmdMode')

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
    self.controller.recaculateFilters('debounced valueUpdated')
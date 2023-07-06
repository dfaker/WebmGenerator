import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrolledframe import ScrolledFrame
import os
import copy

import logging

import colorsys

import threading

from tkinter import messagebox

import json

from .filterSpec import selectableFilters
from .encodingUtils import cleanFilenameForFfmpeg
from .filterValuePair import FilterValuePair

from .modalWindows import Tooltip

from math import atan2,pi

from threading import Lock

specCounter=0
def getSpecificationNumber():
  global specCounter
  specCounter+=1
  return specCounter

class FilterSpecification(ttk.Frame):
  def __init__(self, master,controller,spec, filterId, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.filterId=filterId
    self.enabled=spec.get('enabled',True)
    self.isAudioFilter=spec.get('isAudioFilter',False)
    self.spec=spec
    self.controller=controller
    self.frameFilterDetailsWidget = self

    print('self.isAudioFilter DONE')

    self.autoNumber = getSpecificationNumber()

    self.timelineReinit = self.spec.get('timelineReinit',False)
    
    self.labelFilterName = ttk.Label(self.frameFilterDetailsWidget)
    self.labelFilterName.config(text=spec['name'],style="Bold.TLabel")
    self.labelFilterName.pack(side='top')

    self.labelFilterDesc = None
    if spec.get('desc','') != '':
      self.labelFilterDesc = ttk.Label(self.frameFilterDetailsWidget)
      self.labelFilterDesc.config(text=spec.get('desc',''),wraplength=290,justify=tk.CENTER)
      self.labelFilterDesc.pack(side='top',fill="x",expand="true")

    self.frameFilterConfigFrame = ttk.Frame(self.frameFilterDetailsWidget)


    self.frameFilterActions = ttk.Frame(self.frameFilterConfigFrame)
    self.buttonfilterActionRemove = ttk.Button(self.frameFilterActions)
    self.buttonfilterActionRemove.config(text='Remove')
    self.buttonfilterActionRemove.config(command=self.remove)    
    
    Tooltip(self.buttonfilterActionRemove,text='Remove this filter form the filter stack.')

    self.buttonfilterActionRemove.pack(expand='true', fill='x', side='left')
    self.buttonfilterActionToggleEnabled = ttk.Button(self.frameFilterActions)
    self.buttonfilterActionToggleEnabled.config(text='Enabled', width='7')

    Tooltip(self.buttonfilterActionToggleEnabled,text='Disable this filter but keep it in the filter stack.')

    if not self.enabled:
      self.buttonfilterActionToggleEnabled.config(text='Disabled',style='filterDisabled.TButton')
      self.frameFilterDetailsWidget.config(style='filterDisabled.TFrame')
      self.labelFilterName.config(style='filterDisabled.TLabel')
      if self.labelFilterDesc is not None:
        self.labelFilterDesc.config(style='filterDisabled.TLabel')


    self.buttonfilterActionToggleEnabled.config(command=self.toggleEnabled)
    self.buttonfilterActionToggleEnabled.pack(expand='true', fill='x', side='left')
    self.buttonFilterActionDownStack = ttk.Button(self.frameFilterActions)
    self.buttonFilterActionDownStack.config(text='▼', width='2', command=self.moveFilterUpStack)
    self.buttonFilterActionDownStack.pack(side='left')
    self.buttonFilterActionUpStack = ttk.Button(self.frameFilterActions)
    self.buttonFilterActionUpStack.config(text='▲', width='2', command=self.moveFilterDownStack)
    self.buttonFilterActionUpStack.pack(side='left')
    self.frameFilterActions.config(height='200', width='200')
    self.frameFilterActions.pack(expand='true', fill='x', side='top')
    self.rectProps={}
    self.filterValuePairs= []
    self.timelineSupport = spec.get('timelineSupport',False)
    self.encodingStageFilter = spec.get('encodingStageFilter',False)
    self.timelineStart = tk.StringVar()
    self.timelineEnd   = tk.StringVar()

    self.presets = spec.get('presets',[])

    if self.timelineSupport:

      def timelineStartChanged(*args):
        self.recaculateFilters('timelineStartChanged')
        try:
          ts = float(self.timelineStart.get())
          self.controller.seekToTimelinePoint(ts)
        except:
          pass  

      def timelineEndChanged(*args):
        self.recaculateFilters('timelineEndChanged')
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


    if len(self.presets)>0:
      self.presetNames = ['--No preset--']
      for p in self.presets:
        self.presetNames.append(p['preset_name'])

      self.presetVar = tk.StringVar()
      self.entryPresetOptions = ttk.Combobox(self.frameFilterConfigFrame)
      self.entryPresetOptions.config(values=self.presetNames)
      self.entryPresetOptions.config(textvariable=self.presetVar)
      self.presetVar.set('--No preset--')
      self.entryPresetOptions.pack(expand='true', fill='x', side='top')

      self.presetVar.trace("w", self.presetUpdated)

    for param in spec.get('params',[]):    
      if param.get('type') == 'timelineStart':
        self.timelineStart.set(param.get('value',''))
      elif param.get('type') == 'timelineEnd':
        self.timelineEnd.set(param.get('value',''))
      else:
        self.filterValuePairs.append(FilterValuePair(self.frameFilterConfigFrame,self,param))


    if 'v360ViewHeadLogger' in spec.get('extensions',[]):
      self.buttonRunHeadMotionLogger = ttk.Button(self.frameFilterConfigFrame)
      self.buttonRunHeadMotionLogger.config(text='Run head motion logger')
      self.buttonRunHeadMotionLogger.config(command=self.headMotionLogger)
      self.buttonRunHeadMotionLogger.pack(expand='true', fill='x', side='top')

    if 'growShrinkBox' in spec.get('extensions',[]):
      self.growShrinkBoxFrame = ttk.Frame(self.frameFilterConfigFrame)

      self.shinkBoxLargeInc = ttk.Button(self.growShrinkBoxFrame,style="small.TButton",text='-10',command=lambda :self.incrementBox(-10))
      self.shinkBoxLargeInc.grid(row=0,column=0)

      self.shinkBoxSmallInc = ttk.Button(self.growShrinkBoxFrame,style="small.TButton",text='-1', command=lambda :self.incrementBox(-1))
      self.shinkBoxSmallInc.grid(row=0,column=1)

      self.growBoxSmallInc = ttk.Button(self.growShrinkBoxFrame,style="small.TButton", text='+1',   command=lambda :self.incrementBox(1))
      self.growBoxSmallInc.grid(row=0,column=2)

      self.growBoxLargeInc = ttk.Button(self.growShrinkBoxFrame,style="small.TButton", text='+10',  command=lambda :self.incrementBox(10))
      self.growBoxLargeInc.grid(row=0,column=3)

      self.growShrinkBoxFrame.pack(expand='true', fill='x', side='top')



    if len(self.rectProps)>0:
      self.buttonFilterValuesFromSelection = ttk.Button(self.frameFilterConfigFrame)
      self.buttonFilterValuesFromSelection.config(text='Populate from selection')
      self.buttonFilterValuesFromSelection.config(command=self.populateRectPropValues)
      self.buttonFilterValuesFromSelection.pack(expand='true', fill='x', side='top')
    self.frameFilterConfigFrame.config(height='200', width='200')
    self.frameFilterConfigFrame.pack(expand='true', fill='x', side='top')
    self.frameFilterDetailsWidget.config(height='200', padding='2', relief='groove', width='200')
    self.frameFilterDetailsWidget.pack(expand='false', fill='x', side='top')

    self.guideColour = colorsys.hsv_to_rgb( (self.autoNumber%20)/20.0,1.0,1.0)
    self.guideColour = int(self.guideColour[0]*255),int(self.guideColour[1]*255),int(self.guideColour[2]*255)
    self.guideColour = "#%02x%02x%02x" % (self.guideColour[0], self.guideColour[1], self.guideColour[2])
    self.guideColourFrame       = tk.Label(self.frameFilterDetailsWidget,text=' ',bg=self.guideColour,font=("Monospace",1),height=1)
    self.guideColourFrame.pack(expand='true', fill='x', side='bottom')


    self.packself()

  def presetUpdated(self,*args):
    newPreset = self.presetVar.get()
    print('newPreset',newPreset)
    for p in self.presets:
      print('preset',p)
      if p.get('preset_name','') == newPreset:
        for k,v in p.items():
          for fvp in self.filterValuePairs:
            print('k',k,'fvp',fvp.n,fvp.n == k)
            if fvp.n == k:
              fvp.valueVar.set(v)


  def getStringValue(self,valueToken):
    return self.controller.getStringValue(valueToken)

  def incrementBox(self,inc):
    videoAR = self.controller.getViideoAR()
    print(videoAR)
    for fvp in self.filterValuePairs:
      if fvp.rectProp is None:
        continue              

      _,value = fvp.getValuePair()
      value = int(value)

      if fvp.rectProp == 'x':
        fvp.valueVar.set(str(int(value-(inc*videoAR))))
        fvp.valueUpdated()
      elif fvp.rectProp == 'y':
        fvp.valueVar.set(str(value-inc))
        fvp.valueUpdated()
      elif fvp.rectProp == 'w':
        fvp.valueVar.set(str(int(value+((inc*videoAR)*2))))
        fvp.valueUpdated()
      elif fvp.rectProp == 'h':
        fvp.valueVar.set(str(value+(inc*2)))
        fvp.valueUpdated()


  def headMotionLogger(self):
    clip = self.controller.getCurrentClip()
    filename = clip['filename']
    abA = clip['start']
    abB = clip['end'] 
    
    self.controller.pause()

    import mpv

    

    player = mpv.MPV(loglevel='error',
                     loop='1',
                     mute=True,
                     background='#282828',
                     log_handler=print,
                     autofit_larger='1280',
                     autoload_files='no',
                     cover_art_auto='no',
                     audio_file_auto='no',
                     sub_auto='no')

    player.command('load-script',os.path.join('src','vrscript.lua'))
    self.headmotions=[]
    self.initivalues={}


    @player.message_handler('vrscript')
    def my_handler(cmdType,direction,timepos,value):

      cmdTypeStr   = cmdType
      directionStr = direction
      
      try:
        cmdTypeStr   = cmdType.decode('utf8')
        directionStr = direction.decode('utf8')
      except Exception as e:
        print(e)

      if cmdTypeStr == 'resetRecording':
        self.headmotions=[]
      elif cmdTypeStr=='setValue':
        self.headmotions.append( (float(timepos),directionStr,float(value)) )
      elif cmdTypeStr=='setInitValue':
        self.headmotions.append( (float(abA),directionStr,float(value)) )
        self.initivalues[directionStr]=float(value)
      elif cmdTypeStr=='exit':
        mpv.unregister_message_handler('vrscript')

      print(self.headmotions)
      print('MESSAGE',cmdTypeStr,directionStr,timepos,value)

    player.start=abA
    player.loop='inf'
    player.ab_loop_a=abA
    player.ab_loop_b=abB
    player.play(filename)

    player.wait_until_playing()

    iData = {}
    for fvp in self.filterValuePairs:
      fiparam,fivalue = fvp.getValuePair()
      iData[fiparam]=fivalue
    print(iData)

    player.command('script-message','vrscript_initialiseValues',
                    iData['in_proj'],
                    iData['out_proj'],
                    iData['in_trans'],
                    iData['out_trans'],
                    iData['h_flip'],
                    iData['ih_flip'],
                    iData['iv_flip'],
                    iData['in_stereo'],
                    iData['out_stereo'],
                    iData['w'],
                    iData['h'],
                    iData['yaw'], 
                    iData['pitch'], 
                    iData['roll'],
                    iData['d_fov'], 
                    iData['id_fov'], 
                    iData['interp']
                   )

    player.wait_for_shutdown()

    player.terminate()

    print(self.headmotions)


    if len(self.headmotions)>0:
      motionMaps = {}
      print(motionMaps)
      for ts,direction,val in sorted(self.headmotions):
        if abA <= ts <= abB:
          motionMaps.setdefault(direction,[]).append((ts-abA,val))
      print(motionMaps)

      firstfvp=None

      for k,v in motionMaps.items():
        print(k)
        for fvp in self.filterValuePairs:
          try:
            print(fvp,fvp.videoSpaceAxis,k,fvp.commandVarAvaliable)
            if fvp.videoSpaceAxis == k and fvp.commandVarAvaliable:
              if not fvp.commandVarEnabled:
                fvp.toggleTimelineCmdMode()
              
              firstfvp=fvp
              
              fvp.deactivateTimeLineSection()
              fvp.toggleTimelineSelection()
              fvp.keyValues=dict(v)
              fvp.valueUpdated()
              fvp.deactivateTimeLineSection()
          except Exception as e:
            print(e)     
      
      if firstfvp is not None:
        firstfvp.toggleTimelineSelection()

      self.controller.recaculateFilters('v360 update final')

      for direction,value in self.initivalues.items():
        for fvp in self.filterValuePairs:
          if fvp.videoSpaceAxis == direction and fvp.commandVarAvaliable:
            fvp.valueVar.set(str(value))
            fvp.valueUpdated()

    self.headmotions=[]
    self.controller.play()

  def packself(self):
    self.frameFilterDetailsWidget.pack(expand='false', fill='x', side='top')

  def cycleSelectedProperty(self,activeValuePair):
    enableablefilters = [x for x in self.filterValuePairs if x.commandVarEnabled]
    activeInd = enableablefilters.index(activeValuePair)
    nextEnabledFilter = enableablefilters[(activeInd+1)%len(enableablefilters)]
    if nextEnabledFilter != activeValuePair:
      nextEnabledFilter.toggleTimelineSelection()

  def setActiveTimeLineValue(self,activeValuePair):
    self.controller.setActiveTimeLineValue(activeValuePair)
    self.controller.canvasValueTimeline.focus_set()
  
  def moveFilterUpStack(self):
    self.controller.shiftFilterOnStack(self,1)

  def moveFilterDownStack(self):
    self.controller.shiftFilterOnStack(self,-1)

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
      xf=round(x1/iw,4),yf=round(y1/ih,4),
      wf=round((x2-x1)/iw,4),hf=round((y2-y1)/ih,4),

      cxf=((x1+x2)/2)/iw,cyf=((y1+y2)/2)/ih,

      px0=x1,py0=y1,
      px1=x2,py1=y1,
      px2=x1,py2=y2,
      px3=x2,py3=y2,
    )

    for k,v in rectDerivedProps.items():
      if k in self.rectProps:
        valVar,t = self.rectProps.get(k)
        if t == 'int':
          valVar.set(int(v))
        else:
          valVar.set(v)

  def registerRectProp(self,prop,var,var_type):
    self.rectProps[prop]=(var,var_type)



  def toggleEnabled(self):
    self.enabled = not self.enabled
    if self.enabled:
      self.buttonfilterActionToggleEnabled.config(text='Enabled',style='TButton')
      self.frameFilterDetailsWidget.config(style='TFrame')

      self.labelFilterName.config(style='TLabel')
      if self.labelFilterDesc is not None:
        self.labelFilterDesc.config(style='TLabel')

      
    else:
      self.buttonfilterActionToggleEnabled.config(text='Disabled',style='filterDisabled.TButton')
      self.frameFilterDetailsWidget.config(style='filterDisabled.TFrame')
      self.labelFilterName.config(style='filterDisabled.TLabel')
      if self.labelFilterDesc is not None:
        self.labelFilterDesc.config(style='filterDisabled.TLabel')


    self.controller.recaculateFilters('toggleEnabled')

  def getFilterExpression(self,preview=False,encodingStage=False):
    nullfilter='null'
    if self.isAudioFilter:
      nullfilter='anull'

    if not self.enabled:
      return nullfilter

    if preview:
      filterExp= self.spec.get("filterPreview",self.spec.get("filter",nullfilter))
    elif self.encodingStageFilter and encodingStage==False:
      return nullfilter
    else:
      filterExp= self.spec.get("filter",nullfilter)
    

    filerExprams=[]
    
    i=self.autoNumber

    values = dict( x.getValuePair() for x in self.filterValuePairs )
    formatDict={}

    for param in self.spec.get('params',[]):
      if param.get('n') is not None:
        if '{'+param['n']+'}' in filterExp:
          formatDict.update({'fn':i,param['n']:values[param['n']] },)
        elif self.spec.get('appendUnusedParams',True):
          try:
            if param['type'] == 'file':
              filerExprams.append(':{}=\'{}\''.format(param['n'],values[param['n']]) )
            elif param['type'] == 'float':
              try:
                floatVal=float(values[param['n']])
                if param.get('offsetClipStartSeconds',False) and preview:
                  floatVal= self.controller.normaliseTimestamp(floatVal)
                  print('offsetClipStartSeconds',param['n'],floatVal)
                filerExprams.append(':{}={:01.6f}'.format(param['n'],floatVal))
              except:
                filerExprams.append(':{}={:01.6f}'.format(param['n'],values[param['n']]) )

            elif param['type'] == 'int':
              try:
                filerExprams.append(':{}={}'.format(param['n'],int(values[param['n']])))
              except:
                filerExprams.append(':{}={:01.2f}'.format(param['n'],values[param['n']]) )
            else:
              filerExprams.append(':{}={}'.format(param['n'],values[param['n']]) )
          except:
            filerExprams.append(':{}=\'{}\''.format(param['n'],values[param['n']]) )

    if '{fn}' in filterExp:
      formatDict.update({'fn':i,})

    if len(formatDict)>0:
      filterExp = filterExp.format( **formatDict )

    for i,e in enumerate(filerExprams):
      if i==0:
        filterExp+= '='+e[1:]
      else:
        filterExp+= e

    if self.timelineSupport and filterExp != nullfilter and not self.encodingStageFilter:
      tsStart = None
      tsEnd   = None

      if self.timelineStart.get() != '':
        try:
          tsStart = float(self.timelineStart.get())
          if preview:
            tsStart = self.controller.normaliseTimestamp(tsStart)
        except Exception as e:
          print('timelineSupport tsStart Exception',e)

      if self.timelineEnd.get() != '':
        try:
          tsEnd = float(self.timelineEnd.get())
          if preview:
            tsEnd = self.controller.normaliseTimestamp(tsEnd)
        except Exception as e:
          print('timelineSupport tsEnd Exception',e)

      timelineExpression = ''
      if tsStart is not None and tsEnd is not None:
        timelineExpression = ":enable='between(t,{},{})'".format(tsStart,tsEnd)
      elif tsStart is not None:
        timelineExpression = ":enable='gte(t,{})'".format(tsStart)
      elif tsEnd is not None:
        timelineExpression = ":enable='lte(t,{})'".format(tsEnd)

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
          varTarget = varTarget.format(fn=self.autoNumber)
          for varProperty  in  fvp.commandVarProperty:
            for timeStamp,commandValue,_ in fvp.getKeyValues():
              commands.setdefault(timeStamp,[]).append((varTarget,varProperty,commandValue,fvp.commandInterpolationMode))

    return commands

  def recaculateFilters(self,caller):
    self.controller.recaculateFilters('recaculateFilters-FilterSpecification'+caller)

  def remove(self):
    for fvp in self.filterValuePairs:
      if fvp.commandVarSelected:
        self.controller.setActiveTimeLineValue(None)
    self.controller.removeFilter(self.filterId)


class FilterSelectionUi(ttk.Frame):
  def __init__(self, master=None, enableFaceDetection=False, globalOptions={}, *args, **kwargs):
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
    self.labelVideoPickerLabel.pack(expand='true', fill='x', side='left',anchor='w')
    self.VideoPickerNext = ttk.Button(self.frameVideoPickerFrame)
    self.VideoPickerNext.config(text='>', width='1')
    self.VideoPickerNext.config(command=self.goToNextSubclip)    
    self.VideoPickerNext.pack(anchor='nw', expand='false', side='right')
    self.frameVideoPickerFrame.config(height='200', width='200')
    self.frameVideoPickerFrame.pack(fill='x', padx='2', side='top')

    self.applyToAll_popup_menu = tk.Menu(self, tearoff=0)
    self.applyToAll_popup_menu.add_command(label="Append to all",command=self.appendFiltersToAll)

    self.frameFilterActionsGlobal = ttk.Frame(self.labelframeFilterBrowserFrame)
    
    self.buttonFilterActionClear = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonFilterActionClear.config(text='Clear')
    self.buttonFilterActionClear.config(command=self.clearFilters,style="smallTallSlim.TButton")
    Tooltip(self.buttonFilterActionClear,text='Clear all of the filters applied to the current clip.')
    self.buttonFilterActionClear.pack(expand='true', fill='x', side='left')

    self.buttonOverrideFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonOverrideFilters.config(text='Apply to all')
    self.buttonOverrideFilters.config(command=self.overrideFilters,style="smallTall.TButton")
    Tooltip(self.buttonOverrideFilters,text='Apply the current filters to all other clips, replacing their current filters.')
    self.buttonOverrideFilters.pack(expand='true', fill='x', side='right')
    self.buttonOverrideFilters.bind("<Button-3>",self.showAppendMenu)

    self.buttonPasteFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonPasteFilters.config(text='Paste')
    Tooltip(self.buttonPasteFilters,text='Paste filters from the internal clipboard replacing the current filters.')
    self.buttonPasteFilters.config(command=self.pasteFilters,style="smallTallSlim.TButton")
    self.buttonPasteFilters.pack(expand='true', fill='x', side='right')

    self.buttonAppendFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonAppendFilters.config(text='Append')
    Tooltip(self.buttonAppendFilters,text='Append filters from the internal clipboard so they appear after the current filters.')
    self.buttonAppendFilters.config(command=self.appendFilters,style="smallTallSlimMid.TButton")
    self.buttonAppendFilters.pack(expand='true', fill='x', side='right')

    self.buttonCopyFilters = ttk.Button(self.frameFilterActionsGlobal)
    self.buttonCopyFilters.config(text='Copy')
    self.buttonCopyFilters.config(command=self.copyfilters,style="smallTallSlim.TButton")
    Tooltip(self.buttonCopyFilters,text='Copy current filters to the internal clipboard.')
    self.buttonCopyFilters.pack(expand='true', fill='x', side='right')

    self.frameFilterActionsGlobal.config(height='200', width='200')
    self.frameFilterActionsGlobal.pack(fill='x', side='top')


    self.framefilterAdditionFrame = ttk.Frame(self.labelframeFilterBrowserFrame)
    self.buttonAddFilter = ttk.Button(self.framefilterAdditionFrame)
    self.buttonAddFilter.config(text='Add Filter')
    Tooltip(self.buttonAddFilter,text='Add the currently selected filter from the dropdown on the left to the current filter stack.')
    self.buttonAddFilter.config(command=self.addSelectedfilter)
    self.buttonAddFilter.pack(side='right')
    self.selectedFilter=tk.StringVar()
    self.selectableFilters = []

    self.selectedFilter.set('Crop')
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

    self.filterMenu = tk.Menu(self, tearoff=0)
    self.submenuMap = {}

    basicFilters=[]

    quickFilters = [x.strip().upper() for x in globalOptions.get('quickFilters','').split(',') if len(x.strip())>0]
    
    for fltx in sorted(selectableFilters,key=lambda x:x.get('name','').upper()):
      categories = fltx.get('category',['General'])

      if len(quickFilters) > 0:
        if fltx.get('name','ALL').upper() in quickFilters:
          basicFilters.append(fltx)  
      elif 'Basic' in categories:
        basicFilters.append(fltx)      
      
      if type(categories) != list:
        categories=[categories]
      for cat in categories:
        submenu = self.submenuMap.setdefault( cat, tk.Menu(self.filterMenu, tearoff=0) )
        submenu.add_command(label="{} - {}".format(fltx.get('name','UNAMED'),fltx.get('desc',fltx.get('name','UNAMED')+' filter')),command=lambda n=fltx.get('name','UNAMED') :self.selectedFilter.set(n))

    if len(quickFilters)>0:
       basicFilters = sorted(basicFilters,key=lambda x:quickFilters.index(x.get('name','').upper()))        

    for fltx in basicFilters:
      self.filterMenu.add_command(label="{} - {}".format(fltx.get('name','UNAMED'),fltx.get('desc',fltx.get('name','UNAMED')+' filter')),command=lambda n=fltx.get('name','UNAMED') :self.selectedFilter.set(n))
    self.filterMenu.add_separator()

    for k,v in sorted(self.submenuMap.items()):
      if k != 'Basic':
        self.filterMenu.add_cascade(label=k,  menu=v)

    self.comboboxFilterSelection.bind("<Button-1>",          self.showFilterMenu)
    self.comboboxFilterSelection.bind("<Button-3>",          self.showFilterMenu)


    self.labelframeFilterBrowserFrame.config(height='200', text='Filtering', width='200')
    self.labelframeFilterBrowserFrame.pack(anchor='w', expand='false', fill='y', side='left')

    self.playerContainerFrame = ttk.Frame(self.frameFilterSelectionFrame)
    self.playerContainerFrame.config(cursor="crosshair")
    self.playerContainerFrame.pack(expand='true', fill='both', side='right')

    self.selectionOptionsFrame = ttk.Frame(self.playerContainerFrame)

    self.autocropButton = ttk.Button(self.selectionOptionsFrame,style="smallMid.TButton")
    self.autocropButton.config(text='Autocrop')
    Tooltip(self.autocropButton,text='Run atomatic detection on the current clip to crop off any black borders.')
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
    self.arFixCheckbox = ttk.Checkbutton(self.selectionOptionsFrame,text="Force Aspect", variable=self.fixSeectionArEnabledVar)
    Tooltip(self.arFixCheckbox,text='Clamp the aspect ratio of dragged selections to match the current aspect ratio.')

    self.arFixCheckbox.pack(expand='false', side='left')
    
    self.fixSeectionArVar = tk.StringVar()
    self.fixSeectionArVar.set('1.7')
    self.spinBoxArRatio = ttk.Spinbox(self.selectionOptionsFrame,textvariable=self.fixSeectionArVar,from_=float('-inf'), to=float('inf'),width=6, increment=0.01)
    self.spinBoxArRatio.pack(expand='false', side='left')

    self.spinBoxArRatio.bind("<Button-3>",self.showAspectPopup)

    self.flipARButton = ttk.Button(self.selectionOptionsFrame,text="Flip AR",style="smallSlim.TButton", command=self.flipAR)
    Tooltip(self.flipARButton,text='Flip the aspect ratio effectively rotating the selection rectangle 90 degrees.')
    self.flipARButton.pack(expand='false', side='left')

    self.fitToScreenVar = tk.BooleanVar()
    self.fitToScreenVar.trace('w',self.changeFitToScreen)
    self.fitToScreenVar.set(True)
    self.fitToScreenCheckbox = ttk.Checkbutton(self.selectionOptionsFrame,text="Scale", variable=self.fitToScreenVar)
    Tooltip(self.fitToScreenCheckbox,text='Scale the video so that it fills the whole frame.')
    self.fitToScreenCheckbox.pack(expand='false', side='left')

    self.volumeLabel = ttk.Label(self.selectionOptionsFrame)
    self.volumeLabel.config(text='0.0s')
    self.volumeLabel.pack(expand='false', side='left')

    self.templatePopupMenu = tk.Menu(self, tearoff=0)
    self.templatePopupMenu.add_command(label="No filter templates found")

    self.templateButton = ttk.Button(self.selectionOptionsFrame)
    self.templateButton.config(text='Templates',style="smallMid.TButton")
    Tooltip(self.templateButton,text='Load and apply a json filter template from the filterTemplates folder.')
    self.templateButton.config(command=self.showTemplateMenuPopup)

    self.templateButton.pack(side='right')

    self.importButton = ttk.Button(self.selectionOptionsFrame)
    self.importButton.config(text='Import JSON',style="small.TButton")
    Tooltip(self.importButton,text='Load and apply a json filter from the system clipboard.')
    self.importButton.config(command=self.importJson)
    self.importButton.pack(side='right')

    self.exportButton = ttk.Button(self.selectionOptionsFrame)
    self.exportButton.config(text='Export JSON',style="small.TButton")
    Tooltip(self.exportButton,text='Coppy the current filters as to the system clipboard in json format.')
    self.exportButton.config(command=self.exportJson)
    self.exportButton.pack(side='right')

    self.speedVar = tk.StringVar()
    self.speedVar.trace('w',self.speedChange)
    self.speedVar.set('2.0')
    self.spinboxSpeed = ttk.Spinbox(self.selectionOptionsFrame,textvariable=self.speedVar,from_=float('0'), to=float('inf'), width=4,increment=0.1)
    Tooltip(self.spinboxSpeed,text='Adjust playback speed 1 being normal speed 2 being double speed.')
    self.spinboxSpeed.pack(expand='false', side='right')

    self.speedLabel = ttk.Label(self.selectionOptionsFrame)
    self.speedLabel.config(text='speed')
    self.speedLabel.pack(expand='false', side='right')

    self.selectionOptionsFrame.pack(expand='false', fill='x', side='top')

    self.framePlayerFrame = ttk.Frame(self.playerContainerFrame, style='PlayerFrame.TFrame')
    self.framePlayerFrame.config(height='200', width='200')
    self.framePlayerFrame.pack(expand='true', fill='both', side='top')

    self.mouseRectDragging=False
    self.videoMouseRect=[None,None,None,None]
    self.screenMouseRect=[None,None,None,None]


    self.video_canvas_popup_menu = tk.Menu(self, tearoff=0)
    self.video_canvas_popup_menu.add_command(label="Add Crosshair Registration Mark"        ,command=lambda :self.addRegistrationMark("cross"))
    self.video_canvas_popup_menu.add_command(label="Add Vertical Line Registration Mark"    ,command=lambda :self.addRegistrationMark("vline"))
    self.video_canvas_popup_menu.add_command(label="Add Horizontal Line Registration Mark"  ,command=lambda :self.addRegistrationMark("hline"))
    self.video_canvas_popup_menu.add_separator()
    self.video_canvas_popup_menu.add_command(label="Set target position for X and Y warping."  ,command=lambda :self.addRegistrationMark("tvec"))
    self.video_canvas_popup_menu.add_separator()
    self.video_canvas_popup_menu.add_command(label="Clear Registration Marks"               ,command=lambda :self.addRegistrationMark("clear"))

    self.video_canvas_popup_menu.add_separator()

    if enableFaceDetection:
      self.video_canvas_popup_menu.add_command(label="Add rect from face detector"                    ,command=self.addDetectedFaceRect)
      self.video_canvas_popup_menu.add_command(label="Centre selected rect from face detector"        ,command=self.centreDetectedFaceRect)
      self.video_canvas_popup_menu.add_command(label="Align eyes horizontal from face detector"       ,command=self.alignDetectedEyes)
    else:
      self.video_canvas_popup_menu.add_command(label="Add rect from face detector"                    ,command=lambda:1 , state='disabled')
      self.video_canvas_popup_menu.add_command(label="Align eyes horizontal from face detector"       ,command=lambda:1 , state='disabled')

    self.rect_aspect_popup_menu = tk.Menu(self, tearoff=0)
    self.rect_aspect_popup_menu.add_command(label="9:16 - Vertical video",command=lambda :self.setCropAspect(9/16))
    self.rect_aspect_popup_menu.add_command(label="1:1 - Square",command=lambda :self.setCropAspect(1/1))
    self.rect_aspect_popup_menu.add_command(label="4:3 - Standard tv",command=lambda :self.setCropAspect(4/3))
    self.rect_aspect_popup_menu.add_command(label="16:10 - Display or tablet",command=lambda :self.setCropAspect(16/10))
    self.rect_aspect_popup_menu.add_command(label="16:9 - Standard HDTV",command=lambda :self.setCropAspect(16/9))
    self.rect_aspect_popup_menu.add_command(label="2:1 - Superscope",command=lambda :self.setCropAspect(2/1))
    self.rect_aspect_popup_menu.add_separator()
    self.rect_aspect_popup_menu.add_command(label="Match video aspect",command=lambda :self.setCropAspect(None))


    self.framePlayerFrame.bind("<Button-1>",          self.videomousePress)
    self.framePlayerFrame.bind("<ButtonRelease-1>",   self.videomousePress)
    self.framePlayerFrame.bind("<Motion>",            self.videomousePress)

    self.lastVideoRCX=0
    self.lastVideoRCY=0
    self.framePlayerFrame.bind("<Button-3>",          self.showRegMarkMenu)
    self.framePlayerFrame.bind("<MouseWheel>",         self.videoMouseScroll)


    self.frameFilterSelectionFrame.config(height='200', width='200')
    self.frameFilterSelectionFrame.pack(expand='true', fill='both', side='top')
    
    self.timeline_canvas_popup_menu = tk.Menu(self, tearoff=0)
    self.timeline_canvas_popup_menu.add_command(label="Add key value",command=self.addKeyValue)
    self.timeline_canvas_popup_menu.add_command(label="Remove key value",command=self.removeKeyValue)
    self.timeline_canvas_popup_menu.add_command(label="Clear all key values",command=self.clearKeyValues)

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
    self.canvasValueTimeline.bind("n",        self.keyboardN)
    self.canvasValueTimeline.bind("c",        self.keyboardC)

    self.canvasValueTimeline.focus_set()

    self.canvasValueTimeline.bind('<Up>',    self.keyboardUp)
    self.canvasValueTimeline.bind('<Down>',  self.keyboardDown)
    self.canvasValueTimeline.bind('<Left>',  self.keyboardLeft)
    self.canvasValueTimeline.bind('<Right>', self.keyboardRight)
    self.canvasValueTimeline.bind('<space>', self.keyboardSpace)
    self.canvasValueTimeline.bind('<Configure>',self.reconfigure)


    self.framePlayerFrame.bind('<space>', self.keyboardSpace)
    self.framePlayerFrame.bind('<Left>',  self.keyboardLeft)
    self.framePlayerFrame.bind('<Right>', self.keyboardRight)

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
    self.mouseRectDragStart=(0,0)
    self.activeCommandFilterValuePair = None
    self.timeline_canvas_last_right_click_x=0

    self.sourceTargetVectorSet=False
    self.sourceRegistrationMark = [0,0]

    self.vrPanStartSet=False
    self.vrPanLastStart=[0,0]

    self.AngleDragStartSet=False
    self.sourceAngleDragStart   = [0,0]

    self.timelineModificationLock = Lock()
    self.filterFailed=False
    self.filterFailedResetTimer=None
    self.timelineFileIndex=0    
    self.keyValueSeparation=3

  def getStringValue(self,valueToken):
    return self.controller.getStringValue(valueToken)

  def getViideoAR(self):
    return self.controller.getViideoAR()

  def clearFilterFailure(self):
    self.filterFailed=False
    self.refreshtimeLineForNewClip()
    self.filterFailedResetTimer=None

  def filterFailure(self):
    print('SET FILTER FAILED')
    self.filterFailed=True
    if self.filterFailedResetTimer is None:
      self.filterFailedResetTimer = threading.Timer(2, self.clearFilterFailure)
      self.filterFailedResetTimer.start()
    else:
      self.filterFailedResetTimer.cancel()
      self.filterFailedResetTimer = threading.Timer(2, self.clearFilterFailure)
      self.filterFailedResetTimer.start()
      

    self.refreshtimeLineForNewClip()

  def applyVectorOffset(self,x1,y1,x2,y2,isAsoluteValue=False,isAngle=False):
    if self.activeCommandFilterValuePair is not None:
      horizD = x2-x1
      vertD  = y2-y1

      if isAngle:
        if self.activeCommandFilterValuePair.videoSpaceAxis ==  'deg':
          angle = 0
          angle = -atan2(y2-y1, x2-x1)

          snapPositions = 4
          minSnap=float('inf')
          snapOffset=0
          for i in range(snapPositions):
            snapAngle=(i*((2*pi)/snapPositions))
            if abs(angle-snapAngle)<minSnap:
              minSnap=abs(angle-snapAngle)
              snapOffset=snapAngle
          angle=angle-snapOffset

          self.incrementAtCurrentPlaybackPosition(angle*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=isAsoluteValue,applyImmediate=True)
      else:
        if isAsoluteValue:
          if self.activeCommandFilterValuePair.videoSpaceAxis ==  'x':
            self.incrementAtCurrentPlaybackPosition(x1*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=True,applyImmediate=True) 
          elif self.activeCommandFilterValuePair.videoSpaceAxis ==  'y':
            self.incrementAtCurrentPlaybackPosition(y1*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=True,applyImmediate=True)
        else:
          if self.activeCommandFilterValuePair.videoSpaceAxis ==  'x':
            self.incrementAtCurrentPlaybackPosition(horizD*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=False,applyImmediate=True) 
          elif self.activeCommandFilterValuePair.videoSpaceAxis ==  'y':
            self.incrementAtCurrentPlaybackPosition(vertD*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=False,applyImmediate=True)

          elif self.activeCommandFilterValuePair.videoSpaceAxis ==  'pitch' and abs(vertD) > 0.1:
            print('pitch',vertD)
            self.incrementAtCurrentPlaybackPosition(vertD*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=False,applyImmediate=True)
          elif self.activeCommandFilterValuePair.videoSpaceAxis ==  'yaw' and abs(horizD) > 0.1:
            self.incrementAtCurrentPlaybackPosition(horizD*self.activeCommandFilterValuePair.videoSpaceSign,False,useIncrementMultiplier=False,isAsoluteValue=False,applyImmediate=True)
            print('pitch',horizD)


  def addDetectedFaceRectCallback(self,sourceFile,timestamp,faces):
    print(sourceFile,timestamp)
    
    self.controller.addVideoRegMark(0,0,"clear")

    for face in faces:
      print(face)
      fx,fy,fs = face['face']['x'], face['face']['y'], face['face']['size']
      fvx,fvy = self.controller.videoSpaceToScreenSpace(fx,fy)
      fvx2,fvy2   = self.controller.videoSpaceToScreenSpace(fx+fs,fy+fs)

      print(fx,fy,fvx,fvy)

      self.videoMouseRect=[fx,fy,fx+fs,fy+fs]
      self.screenMouseRect=[fvx,fvy,fvx2,fvy2]

      self.controller.setVideoRect(fvx,fvy,fvx2,fvy2)
      """
      for eye in face['eyes']:
        x,y = eye['x'],eye['y']
        x,y = self.controller.videoSpaceToScreenSpace(x,y)
        self.controller.addVideoRegMark(x,y)
      """
      break


  def setCenteredFaceRectCallback(self,sourceFile,timestamp,faces):
    print(sourceFile,timestamp)
    
    self.controller.addVideoRegMark(0,0,"clear")

    for face in faces:
      print(face)
      fx,fy,fs = face['face']['x'], face['face']['y'], face['face']['size']
      fvx,fvy = self.controller.videoSpaceToScreenSpace(fx,fy)
      fvx2,fvy2   = self.controller.videoSpaceToScreenSpace(fx+fs,fy+fs)

      print(fx,fy,fvx,fvy)

      self.videoMouseRect=[fx,fy,fx+fs,fy+fs]
      self.screenMouseRect=[fvx,fvy,fvx2,fvy2]

      self.controller.setVideoRect(fvx,fvy,fvx2,fvy2)

      for eye in face['eyes']:
        x,y = eye['x'],eye['y']
        x,y = self.controller.videoSpaceToScreenSpace(x,y)
        self.controller.addVideoRegMark(x,y)

      break

  def alignDetectedEyesFaceRectCallback(self,sourceFile,timestamp,faces):

    eyepoints = []
    for face in faces:
      for eye in face['eyes']:
        x,y = eye['x'],eye['y']
        x,y = self.controller.videoSpaceToScreenSpace(x,y)
        eyepoints.append(x)
        eyepoints.append(y) 
      break

    if len(eyepoints)==4:
      self.applyVectorOffset(eyepoints[0],eyepoints[1],
                             eyepoints[2],eyepoints[3],isAsoluteValue=True,isAngle=True)

  def addDetectedFaceRect(self):
    self.controller.getFaceBoundingRect(self.addDetectedFaceRectCallback)

  def centreDetectedFaceRect(self):
    self.controller.getFaceBoundingRect(self.setCenteredFaceRectCallback)
  
  def alignDetectedEyes(self):
    self.controller.getFaceBoundingRect(self.alignDetectedEyesFaceRectCallback)

  def keyboardC(self,e):
    if self.activeCommandFilterValuePair is not None:
      self.activeCommandFilterValuePair.cycleSelectedProperty()

  def addRegistrationMark(self,markType):
    if markType=="tvec":
      vx,vy = self.controller.screenSpaceToVideoSpace(self.lastVideoRCX,self.lastVideoRCY)
      self.sourceRegistrationMark = [self.lastVideoRCX,self.lastVideoRCY]
      self.controller.addVideoRegMark(0,0,"clear")
      self.sourceTargetVectorSet=True
    if markType=="clear":
      self.sourceTargetVectorSet=False
    self.controller.addVideoRegMark(self.lastVideoRCX,self.lastVideoRCY,markType)


  def showFilterMenu(self,e):
    self.lastVideoRCX=e.x
    self.lastVideoRCY=e.y
    self.filterMenu.tk_popup(e.x_root,e.y_root)

  def showAspectPopup(self,e):
    self.rect_aspect_popup_menu.tk_popup(e.x_root,e.y_root)

  def showAppendMenu(self,e):
    self.applyToAll_popup_menu.tk_popup(e.x_root,e.y_root)

  def showRegMarkMenu(self,e):
    self.lastVideoRCX=e.x
    self.lastVideoRCY=e.y
    self.video_canvas_popup_menu.tk_popup(e.x_root,e.y_root)
      
  def keyboardI(self,e):
    if self.activeCommandFilterValuePair is not None:
      self.activeCommandFilterValuePair.interpolationFactor = (self.activeCommandFilterValuePair.interpolationFactor+1)%24
      self.recaculateFilters('keyboardI')
      self.refreshtimeLineForNewClip()

  def keyboardD(self,e):
    if self.activeCommandFilterValuePair is not None:
      duration      = self.controller.getClipDuration()
      posSeconds = self.controller.getCurrentPlaybackPosition()
      posX = (posSeconds/duration)*self.canvasValueTimeline.winfo_width()

      for timeStamp,value,_ in self.activeCommandFilterValuePair.getKeyValues():
        tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
        if posX-self.keyValueSeparation<tx<posX+self.keyValueSeparation:
          self.activeCommandFilterValuePair.removeKeyValue(timeStamp)
          self.controller.seekToPercent(tx/self.canvasValueTimeline.winfo_width())
          self.refreshtimeLineForNewClip()
          break

  def videoMouseScroll(self,e):
    if e.delta>0:
      self.controller.stepRelative(1)
    else:
      self.controller.stepRelative(-1)

  def keyboardUp(self,e):
    self.incrementAtCurrentPlaybackPosition(1,e)

  def keyboardDown(self,e):
    self.incrementAtCurrentPlaybackPosition(-1,e)
  


  def incrementAtCurrentPlaybackPosition(self,increment,e,useIncrementMultiplier=True,isAsoluteValue=False,applyImmediate=False):
    
    ctrl  = e and ((e.state & 0x4) != 0)

    if self.activeCommandFilterValuePair is not None:
      duration      = self.controller.getClipDuration()
      posSeconds = self.controller.getCurrentPlaybackPosition()
      posX = (posSeconds/duration)*self.canvasValueTimeline.winfo_width()
      existingTS=None
      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues(interpolation=False):
        tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
        if posX-self.keyValueSeparation<tx<posX+self.keyValueSeparation:
          existingTS=timeStamp
      if existingTS is None:
        self.activeCommandFilterValuePair.addKeyValue(posSeconds,value=increment,useIncrementMultiplier=useIncrementMultiplier,isAsoluteValue=isAsoluteValue)
      else:
        self.activeCommandFilterValuePair.incrementKeyValue(posSeconds,increment*10 if ctrl else increment,useIncrementMultiplier=useIncrementMultiplier,isAsoluteValue=isAsoluteValue)
        
      self.refreshtimeLineForNewClip()

  def keyboardLeft(self,e):
    self.handleSeek(e,-0.5)
    
  def keyboardRight(self,e):
    self.handleSeek(e,0.5)

  def pause(self):
    self.controller.pause()

  def play(self):
    self.controller.play()

  def keyboardN(self,e):
    self.controller.pause()
    points = [0,self.controller.getClipDuration()]
    
    existingPoints = sorted([x[0] for x in self.activeCommandFilterValuePair.getKeyValues() if x[2]])

    if len(existingPoints) < 1 or existingPoints[0] > 0.2:
      self.seekToTimelinePoint(0.1)
      self.refreshtimeLineForNewClip()
    elif existingPoints[-1] < self.controller.getClipDuration()-0.3:
      self.seekToTimelinePoint(self.controller.getClipDuration()-0.1)
      self.refreshtimeLineForNewClip()
    else:
      points.extend(existingPoints)
      points = sorted(points,reverse=True)
      mids = sorted([ (abs(x-y),(x+y)/2) for x,y in zip(points[1:], points)],reverse=True)[0][1]
      self.seekToTimelinePoint(mids)
      self.refreshtimeLineForNewClip()

  def handleSeek(self,e,increment):
    ctrl  = (e.state & 0x4) != 0
    shift = (e.state & 0x1) != 0

    if shift:
      self.controller.seekRelative(increment)
    elif ctrl:
      posSeconds = self.controller.getCurrentPlaybackPosition()
      points = [0,self.controller.getClipDuration()]
      points.extend([x[0] for x in self.activeCommandFilterValuePair.getKeyValues() if x[2]])
      points = sorted(points)
      mids = [(x+y)/2 for x,y in zip(points[1:], points)]
      
      if increment<0:
        self.seekToTimelinePoint( [x for x in mids if x<posSeconds-0.05][-1]  )
      else:
        self.seekToTimelinePoint( [x for x in mids if x>posSeconds+0.05][0]  )
    else:
      self.controller.stepRelative(increment)
    

  def keyboardSpace(self,e):
    self.controller.togglePause()

  def clearKeyValues(self):
    if self.activeCommandFilterValuePair is not None:
      self.activeCommandFilterValuePair.clearKeyValues()   
      self.refreshtimeLineForNewClip() 

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
      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues():
        if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          if self.timeline_canvas_last_right_click_x-self.keyValueSeparation<tx<self.timeline_canvas_last_right_click_x+self.keyValueSeparation:
            self.activeCommandFilterValuePair.removeKeyValue(timeStamp)
            self.controller.seekToPercent(tx/self.canvasValueTimeline.winfo_width())
            self.refreshtimeLineForNewClip()
            break

  def timelineMousewheel(self,e):
    ctrl  = (e.state & 0x4) != 0
    duration      = self.controller.getClipDuration()
    secondsClicked = (e.x/self.canvasValueTimeline.winfo_width())*self.controller.getClipDuration()
    
    if self.activeCommandFilterValuePair is not None:
      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues():
        if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          if e.x-self.keyValueSeparation<tx<e.x+self.keyValueSeparation:
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
    if self.filterFailed:      
      self.canvasValueTimeline.create_rectangle(0,(self.canvasValueTimeline.winfo_height()/2)-10,self.canvasValueTimeline.winfo_width(),(self.canvasValueTimeline.winfo_height()/2)+10,fill="#ff0000",tags='filterFailed')
      self.canvasValueTimeline.create_text(self.canvasValueTimeline.winfo_width()/2, self.canvasValueTimeline.winfo_height()/2,text="Filter Failed!",fill="white",tags='filterFailed') 
    else:
      self.canvasValueTimeline.delete('filterFailed')

  def reconfigure(self,e):
    self.refreshtimeLineForNewClip()

  def refreshtimeLineForNewClip(self):

    self.canvasValueTimeline.delete('ticks')
    duration      = self.controller.getClipDuration()
    if duration==0:
      return

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
      self.canvasValueTimeline.create_rectangle(0,130,self.canvasValueTimeline.winfo_width(),150,fill="#26414a",tags='ActiveFilterName')

      valMax,valMin = float('-inf'),float('inf')

      #if self.activeCommandFilterValuePair.vmin not in (float('-inf'),float('inf'),None):
      #  valMin=self.activeCommandFilterValuePair.vmin

      #if self.activeCommandFilterValuePair.vmax not in (float('-inf'),float('inf'),None):
      #  valMax=self.activeCommandFilterValuePair.vmax

      for timeStamp,value,real in self.activeCommandFilterValuePair.getKeyValues():
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

      lastX,lastY=None,None

      effectiveHeight = self.canvasValueTimeline.winfo_height()-20
      heightOffset    = 10


      keyList= self.activeCommandFilterValuePair.getKeyValues()
      for timeStamp,value,real in sorted(keyList):
        tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
        ty = heightOffset+(effectiveHeight-(((value-valMin)/valRange)*effectiveHeight))

        if lastX is None and lastY is None:
          lastX=0
          lastY=ty

        self.canvasValueTimeline.create_line(lastX, lastY, tx, ty,fill="#db6986",tags='KeyValuePoints')
        if real:
          self.canvasValueTimeline.create_oval(tx-5, ty-4, tx+5, ty+4,fill="#db6986",tags='KeyValuePoints')
        else:
          self.canvasValueTimeline.create_oval(tx-2, ty-2, tx+2, ty+1,fill="white",outline=None,tags='KeyValuePoints')

        lastX,lastY=tx,ty

      if lastX is not None and lastY is not None:
        self.canvasValueTimeline.create_line(lastX, lastY, self.canvasValueTimeline.winfo_width(), ty,fill="#db6986",tags='KeyValuePoints')


      posSeconds = self.controller.getCurrentPlaybackPosition()
      for timeStamp,value,real in sorted(keyList,key=lambda lent:abs(lent[0]-posSeconds),reverse=True):
       if real:
          tx = int((timeStamp/duration)*self.canvasValueTimeline.winfo_width())
          ty = heightOffset+(effectiveHeight-(((value-valMin)/valRange)*effectiveHeight))
          bbox = self.canvasValueTimeline.bbox(self.canvasValueTimeline.create_text(tx, 140,text="{:0.2f}".format(value),fill="black",tags='ticks'))
          self.canvasValueTimeline.create_rectangle(bbox, outline="#69bfdb", fill="#375e6b",tags='ticks')
          self.canvasValueTimeline.create_text(tx, 140,text="{:0.2f}".format(value),fill="white",tags='ticks')


      modeText='No Mode'
      if self.activeCommandFilterValuePair.videoSpaceAxis in ('yaw','pitch'):
        modeText='[VR Look Mode - Ctrl-Click once on video to control head {} with mouse.]'.format(self.activeCommandFilterValuePair.videoSpaceAxis)
      elif self.activeCommandFilterValuePair.videoSpaceAxis=='deg':
        modeText='[Angle Snap Mode - Ctrl click on video to difine a rotation angle, snapped to 90 degrees.]'
      elif self.sourceTargetVectorSet:
        modeText='[XY Warp Mode - Ctrl click a point on the video to warp it to the target position.]'

      self.canvasValueTimeline.create_text(2, 128, text="{} {} subdiv:{}".format(self.activeCommandFilterValuePair.commandvarName,modeText,self.activeCommandFilterValuePair.interpolationFactor),fill="white",tags='ActiveFilterName',anchor=tk.SW)

    if self.filterFailed:      
      self.canvasValueTimeline.create_rectangle(0,(self.canvasValueTimeline.winfo_height()/2)-10,self.canvasValueTimeline.winfo_width(),(self.canvasValueTimeline.winfo_height()/2)+10,fill="#ff0000",tags='filterFailed')
      self.canvasValueTimeline.create_text(self.canvasValueTimeline.winfo_width()/2, self.canvasValueTimeline.winfo_height()/2,text="Filter Failed!",fill="white",tags='filterFailed') 
    else:
      self.canvasValueTimeline.delete('filterFailed')

  def showTemplateMenuPopup(self):
    self.templatePopupMenu.tk_popup(self.winfo_pointerx(),self.winfo_pointery())

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
      if spec['name'] == 'Crop':
        newFilter = FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        self.filterSpecifications.append( newFilter)
        break
    if newFilter is not None:
      newFilter.rectProps.get('x')[0].set(int(x))
      newFilter.rectProps.get('y')[0].set(int(y))
      newFilter.rectProps.get('w')[0].set(int(w))
      newFilter.rectProps.get('h')[0].set(int(h))

    for spec in self.filterSpecifications:
      spec.packself()

    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters('autoCropCallback')

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
      self.recaculateFilters('importJson')

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

  def setCropAspect(self,ar):

    if ar is None:
      ar = self.controller.getViideoAR()

    self.fixSeectionArEnabledVar.set(True)
    self.fixSeectionArVar.set( ar  )

  def applyScreenSpaceAR(self,shift=False):
    forceAR = None

    if self.fixSeectionArEnabledVar.get():
      try:
        forceAR = float(self.fixSeectionArVar.get())
      except Exception as e:
        logging.error("applyScreenSpaceAR Exception",exc_info=e)

    if forceAR is not None:
      
      if shift:
        neww = abs(self.screenMouseRect[0]-self.screenMouseRect[2])
        newh = neww/forceAR

        midx,midy = (self.screenMouseRect[0]+self.screenMouseRect[2])/2,(self.screenMouseRect[1]+self.screenMouseRect[3])/2


        self.screenMouseRect[0] = midx-(neww/2)
        self.screenMouseRect[1] = midy-(newh/2)
        self.screenMouseRect[2] = midx+(neww/2)
        self.screenMouseRect[3] = midy+(newh/2)



      else:
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
      shift = (e.state & 0x1) != 0
      ctrl  = (e.state & 0x4) != 0
      
      if self.vrPanStartSet:
        if e.type == tk.EventType.Motion:
          x1,y1 = self.controller.screenSpaceToVideoSpace(int((self.playerContainerFrame.winfo_rootx())+(self.playerContainerFrame.winfo_width()/2)),
                                                          int((self.playerContainerFrame.winfo_y()+self.playerContainerFrame.winfo_rooty())+(self.playerContainerFrame.winfo_height()/2)) )
          x2,y2 = self.controller.screenSpaceToVideoSpace(self.playerContainerFrame.winfo_pointerx(),self.playerContainerFrame.winfo_pointery())
          self.applyVectorOffset(x1,y1,
                                 x2,y2,isAsoluteValue=False,isAngle=False)
          self.vrPanStartSet=False
          self.event_generate('<Motion>', warp=True, 
                                          x=int(self.playerContainerFrame.winfo_x()+(self.playerContainerFrame.winfo_width()/2)),
                                          y=int(self.playerContainerFrame.winfo_y()+(self.playerContainerFrame.winfo_height()/2))  

                                          )
          
          self.vrPanStartSet=True


        if e.type == tk.EventType.ButtonPress:
          self.playerContainerFrame.config(cursor="crosshair")
          self.controller.setVideoVector(0,0,0,0)
          self.vrPanStartSet=False

      elif self.AngleDragStartSet:
        if e.type == tk.EventType.Motion:
          self.controller.setVideoVector(self.sourceAngleDragStart[0],self.sourceAngleDragStart[1],e.x,e.y)

        elif e.type == tk.EventType.ButtonRelease:
          x1,y1 = self.controller.screenSpaceToVideoSpace(self.sourceAngleDragStart[0],self.sourceAngleDragStart[1])
          x2,y2 = self.controller.screenSpaceToVideoSpace(e.x,e.y)
          self.applyVectorOffset(x1,y1,
                                 x2,y2,isAsoluteValue=False,isAngle=True)
          self.controller.setVideoVector(0,0,0,0)
          self.AngleDragStartSet=False
          self.playerContainerFrame.config(cursor="crosshair")

          if ctrl and shift:
            self.controller.stepRelative(1)
          elif ctrl:
            self.keyboardN(e)
      if self.sourceTargetVectorSet:
        if e.type == tk.EventType.ButtonPress:
          x1,y1 = self.controller.screenSpaceToVideoSpace(self.sourceRegistrationMark[0],self.sourceRegistrationMark[1])
          x2,y2 = self.controller.screenSpaceToVideoSpace(e.x,e.y)
          self.applyVectorOffset(x1,y1,
                                 x2,y2,isAsoluteValue=False)
          if ctrl and shift:
            self.controller.stepRelative(1)
          elif ctrl:
            self.keyboardN(e)
      elif ctrl:

        if self.activeCommandFilterValuePair is not None and self.activeCommandFilterValuePair.videoSpaceAxis in ('yaw','pitch') and e.type == tk.EventType.ButtonPress:
          
          self.playerContainerFrame.configure(cursor='diamond_cross')
          self.event_generate('<Motion>', warp=True, 
                                          x=int(self.playerContainerFrame.winfo_x()+(self.playerContainerFrame.winfo_width()/2)),
                                          y=int(self.playerContainerFrame.winfo_y()+(self.playerContainerFrame.winfo_height()/2))  

                                          )
          self.vrPanStartSet=True

        if self.activeCommandFilterValuePair is not None and self.activeCommandFilterValuePair.videoSpaceAxis=='deg' and e.type == tk.EventType.ButtonPress:
          self.playerContainerFrame.config(cursor="none")
          self.AngleDragStartSet=True
          self.sourceAngleDragStart   = [e.x,e.y]

        elif  e.type == tk.EventType.ButtonPress:
          x2,y2 = self.controller.screenSpaceToVideoSpace(e.x,e.y)
          self.applyVectorOffset(x2,y2,0,0,isAsoluteValue=True)        
      
      else:

        videoOriginX,videoOriginY,videoMaxX,videoMaxY = self.controller.getvideoOSDExtents()

        if e.type == tk.EventType.ButtonPress:        
          if self.screenMouseRect[0] is not None and abs(((self.screenMouseRect[0]+self.screenMouseRect[2])/2)-e.x)<30 and abs(((self.screenMouseRect[1]+self.screenMouseRect[3])/2)-e.y)<30:
            self.mouseRectMoving=True
            self.mouseRectMoveStart=(e.x,e.y)
          else:
            logging.debug("videomousePress start")
            self.mouseRectDragging=True
            
            if self.mouseRectDragStart == (0,0): 
              self.mouseRectDragStart=(e.x,e.y)

            self.screenMouseRect[0]=e.x
            self.screenMouseRect[1]=e.y
        elif e.type in (tk.EventType.Motion,tk.EventType.ButtonRelease) and (self.mouseRectDragging or self.mouseRectMoving):
          logging.debug("videomousePress show")
          if self.mouseRectMoving:
            haw = abs(self.screenMouseRect[0]-self.screenMouseRect[2])//2
            hah = abs(self.screenMouseRect[1]-self.screenMouseRect[3])//2

            if haw*2 > videoMaxX-videoOriginX:
              haw = (videoMaxX-videoOriginX)//2
            if hah*2 > videoMaxY-videoOriginY:
              hah = (videoMaxY-videoOriginY)//2

            mcx,mcy = e.x,e.y

            if (mcx - haw) < videoOriginX:
              mcx = videoOriginX+haw
            if (mcy - hah) < videoOriginY:
              mcy = videoOriginY+hah
            if (mcx + haw) > videoMaxX:
              mcx = videoMaxX-haw
            if (mcy + hah) > videoMaxY:
              mcy = videoMaxY-hah


            self.screenMouseRect[0]=mcx-haw
            self.screenMouseRect[1]=mcy-hah
            self.screenMouseRect[2]=mcx+haw
            self.screenMouseRect[3]=mcy+hah


          else:
            if shift:
              dx=abs(self.mouseRectDragStart[0]-e.x)
              dy=abs(self.mouseRectDragStart[1]-e.y)
              self.screenMouseRect[0]=self.mouseRectDragStart[0]+dx
              self.screenMouseRect[1]=self.mouseRectDragStart[1]+dy
              self.screenMouseRect[2]=self.mouseRectDragStart[0]-dx
              self.screenMouseRect[3]=self.mouseRectDragStart[1]-dy
            else:
              if self.mouseRectDragStart[0]>0 and self.mouseRectDragStart[1]>0:
                self.screenMouseRect[0]=self.mouseRectDragStart[0]
                self.screenMouseRect[1]=self.mouseRectDragStart[1]
              self.screenMouseRect[2]=e.x
              self.screenMouseRect[3]=e.y
          self.applyScreenSpaceAR(shift)

          vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
          vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 

          self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3],desc='{}x{}'.format(int(abs(vx1-vx2)),int(abs(vy1-vy2))))
        if e.type == tk.EventType.ButtonRelease:
          logging.debug("videomousePress release")
          self.mouseRectDragging=False
          self.mouseRectMoving=False
          self.mouseRectDragStart = (0,0)

          vx1,vy1 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[0],self.screenMouseRect[1]) 
          vx2,vy2 = self.controller.screenSpaceToVideoSpace(self.screenMouseRect[2],self.screenMouseRect[3]) 

          self.videoMouseRect=[vx1,vy1,vx2,vy2]
          self.controller.setVideoRect(self.screenMouseRect[0],self.screenMouseRect[1],self.screenMouseRect[2],self.screenMouseRect[3],desc='{}x{}'.format(int(abs(vx1-vx2)),int(abs(vy1-vy2))) )
          
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
    for spec in self.filterSpecifications:
      spec.packself()
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters('addSelectedfilter')

  def removeFilter(self,filterId):
    for filter in self.filterSpecifications:
      if filter.filterId == filterId:
        filter.destroy()
    self.filterSpecifications = [x for x in self.filterSpecifications if x.filterId != filterId]
    for spec in self.filterSpecifications:
      spec.packself()
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters('removeFilter')

  def clearFilters(self):
    for filter in self.filterSpecifications:
      filter.destroy()
    self.filterSpecifications=[]
    self.scrolledframeFilterContainer.reposition()
    self.recaculateFilters('clearFilters')

  def updateSeekLabel(self,value):
    self.volumeLabel.config(text='{:0.2f}s'.format(value))

  def seekToTimelinePoint(self,ts):
    return self.controller.seekToTimelinePoint(ts)

  def normaliseTimestamp(self,ts):
    return self.controller.normaliseTimestamp(ts)


  def recaculateFilters(self,caller):
    filteraudioexpPreview=[]
    filteraudioexpReal=[]


    filterexpPreview=[]
    filterExpReal=[]
    filterExpEncodingStage=[]
    
    print('recaculateFilters',caller)
    commandSet = {}

    for filter in self.filterSpecifications:

      commandSet.update(filter.getTimeLimeCommandValues())

      if filter.isAudioFilter:
        filteraudioexpPreview.append(filter.getFilterExpression(preview=True)) 
        filteraudioexpReal.append(filter.getFilterExpression(preview=False))
      else:
        filterexpPreview.append(filter.getFilterExpression(preview=True)) 
        filterExpReal.append(filter.getFilterExpression(preview=False))
        if filter.encodingStageFilter:
          filterExpEncodingStage.append(filter.getFilterExpression(preview=False,encodingStage=True))

    audioCommandStr_preview = ""
    audioCommandStr_real = ""

    commandStr_preview = ""
    commandStr_real = ""

    lastCommandValues = {}

    useFile=True

    sep = ""
    if useFile:
      sep = "\n"

    for k,v in sorted(commandSet.items()):
      if len(v)>0:
        for cmdTarget,cmdProperty,cmdValue,interpolationMode in v:
          firstCommand = (cmdTarget,cmdProperty) not in lastCommandValues
          lastTime,lastValue,_ = lastCommandValues.get((cmdTarget,cmdProperty),(0,cmdValue,interpolationMode))
          norm_k = self.controller.normaliseTimestamp(k)
          norm_lastTime = self.controller.normaliseTimestamp(lastTime)

          if interpolationMode == 'lerp':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},TI)';{sep}".format(sep=sep, l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},TI)';{sep}".format(sep=sep, l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'lerp-sigmoid':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},sin(TI*(PI/2)))';{sep}".format(sep=sep, l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},sin(TI*(PI/2)))';{sep}".format(sep=sep, l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'lerp-smooth':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},(TI*TI*(3-2*TI)))';{sep}".format(sep=sep, l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},(TI*TI*(3-2*TI)))';{sep}".format(sep=sep, l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'lerp-smooth-inv':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},(0.5-sin(asin(1.0-2.0*TI)/3.0)))';{sep}".format(sep=sep, l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},(0.5-sin(asin(1.0-2.0*TI)/3.0)))';{sep}".format(sep=sep, l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)
                   
          elif interpolationMode == 'lerp-smooth-2nd':
            commandStr_preview += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},(TI*TI*TI*(TI*(TI*6-15)+10)))';{sep}".format(sep=sep, l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, lv=lastValue, cv=cmdValue)
            commandStr_real    += "{l:0.4f}-{k:0.4f} [expr] {t} {p} 'lerp({lv:0.4f},{cv:0.4f},(TI*TI*TI*(TI*(TI*6-15)+10)))';{sep}".format(sep=sep, l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty,  lv=lastValue, cv=cmdValue)

          elif interpolationMode == 'neighbour':
            commandStr_preview += "{k:0.4f} [enter] {t} {p} {cv:0.4f};{sep}".format(sep=sep, l=norm_lastTime,k=norm_k,t=cmdTarget,p=cmdProperty, cv=cmdValue)
            commandStr_real    += "{k:0.4f} [enter] {t} {p} {cv:0.4f};{sep}".format(sep=sep, l=lastTime,     k=k,     t=cmdTarget,p=cmdProperty, cv=cmdValue)

          lastCommandValues[(cmdTarget,cmdProperty)] = (k,cmdValue,interpolationMode)

    filterAudioExpStrPreview = ','.join(filteraudioexpPreview)
    filterAudioExpStrReal    = ','.join(filteraudioexpReal)

    filterExpStrPreview    = ','.join(filterexpPreview)
    filterExpStrReal       = ','.join(filterExpReal)
    filterExpEncodingStage = ','.join(filterExpEncodingStage)

    currentClip=0
    try:
      if self.currentSubclipIndex is not None:
        currentClip = self.subClipOrder[self.currentSubclipIndex]
    except Exception as e:
      print(e)
      return

    preLockClip = self.getCurrentClip()
    with self.timelineModificationLock:
      if len(commandSet)>0:

        if useFile:
          self.timelineFileIndex = (self.timelineFileIndex+1)%5
          commandFilename_preview = os.path.join( self.controller.gettempVideoFilePath(), "commands_{}_{}_{}_preview.txt".format(currentClip,self.timelineFileIndex,id(self)) )
          with open(commandFilename_preview,'w') as cmdf:
            cmdf.write(commandStr_preview)
          commandFilename_preview_clean = cleanFilenameForFfmpeg(os.path.abspath(commandFilename_preview)).replace('\\','/').replace(':','\\:') 

          commandFilename_real = os.path.join( self.controller.gettempVideoFilePath(), "commands_{}_{}_real.txt".format(currentClip,id(self)) )
          with open(commandFilename_real,'w') as cmdf:
            cmdf.write(commandStr_real)
          commandFilename_real_clean  = cleanFilenameForFfmpeg(os.path.abspath(commandFilename_real)).replace('\\','/').replace(':','\\:')
            
          sndCmdFilter_preview = "sendcmd=f='{}',".format(commandFilename_preview_clean)
          sndCmdFilter_real    = "sendcmd=f='{}',".format(commandFilename_real_clean)

        else:
          sndCmdFilter_preview = "sendcmd=c='{}',".format(commandStr_preview.replace("'","\'"))
          sndCmdFilter_real    = "sendcmd=c='{}',".format(commandStr_real.replace("'","\'"))


        filterExpStrPreview = sndCmdFilter_preview+filterExpStrPreview
        filterExpStrReal    = sndCmdFilter_real+filterExpStrReal
      postLockClip = self.getCurrentClip()

      if preLockClip != postLockClip or (len(filterexpPreview)==0 and len(filterAudioExpStrPreview) == 0):
        self.controller.clearFilter()
      else:
        self.controller.setFilter(filterExpStrPreview,filterAudioExpStrPreview)
      self.filterFailed=False

    if self.currentSubclipIndex is not None and preLockClip == postLockClip:
      currentClip = self.getCurrentClip()
      if currentClip is not None:
        currentClip['filters'] = self.convertFilterstoSpecDefaults()
        currentClip['filterexp'] =filterExpStrReal
        currentClip['filterexpaudio'] =filterAudioExpStrReal
        currentClip['filterexpEncStage'] =filterExpEncodingStage

  def convertFilterstoSpecDefaults(self):
    filterstack=[]
    for ifilter in self.filterSpecifications:
      baseSpec = None     
      for spec in selectableFilters:
        if spec['name'] == ifilter.spec['name']:
          baseSpec=copy.deepcopy(spec)
          baseSpec['enabled'] = ifilter.enabled
          break
      for n,v in [x.getValuePair(forFilter=False) for x in ifilter.filterValuePairs]:
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
            param['interpolationFactor']   = valPair.interpolationFactor
            param['interpMode']            = valPair.commandInterpolationMode
            param['restrictedInterpModes'] = valPair.interpolationModes

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
      self.buttonAppendFilters['state'] = buttonState
      self.buttonCopyFilters['state'] = buttonState
      self.buttonAddFilter['state'] = buttonState
      self.comboboxFilterSelection['state'] = buttonState
      self.refreshtimeLineForNewClip()

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

    tempSeclectedRid=None
    if self.currentSubclipIndex is not None:
      try:
        tempSeclectedRid = self.subClipOrder[self.currentSubclipIndex]
      except Exception as e:
        print('recauclateSubclips Exception',e) 

    for k in unusedRids:
      del self.subclips[k]

    self.subClipOrder = [k for k,v in sorted( self.subclips.items(), key=lambda x:(x[1]['filename'],x[1]['start']) ) ]

    print('tempSeclectedRid',tempSeclectedRid)
    print('self.subClipOrder',self.subClipOrder)

    if tempSeclectedRid in self.subClipOrder:
      self.setSubclipIndex(self.subClipOrder.index(tempSeclectedRid))
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
      if len(self.subclips)>0:
        return self.subclips[self.subClipOrder[self.currentSubclipIndex]]
    except Exception as e:
      logging.error("getCurrentClip Exception",exc_info=e)
    return None

  def jumpToFilterByRid(self,rid):
    self.recauclateSubclips()
    ridInd = self.subClipOrder.index(rid)
    self.setSubclipIndex( ridInd )
    self.updateFilterDisplay()
    self.refreshtimeLineForNewClip()
    self.controller.jumpToOwnTab()

  def goToNextSubclip(self):
    if self.currentSubclipIndex is not None:
      self.activeCommandFilterValuePair=None
      self.setSubclipIndex( (self.currentSubclipIndex+1)%len(self.subClipOrder) )
      self.updateFilterDisplay()
      self.refreshtimeLineForNewClip()

  def goToPreviousSubclip(self):
    if self.currentSubclipIndex is not None:
      self.activeCommandFilterValuePair=None
      self.setSubclipIndex( (self.currentSubclipIndex-1)%len(self.subClipOrder) )
      self.updateFilterDisplay()
      self.refreshtimeLineForNewClip()

  def copyfilters(self):
    if self.currentSubclipIndex is not None:
      self.filterClipboard = self.convertFilterstoSpecDefaults()
  
  def appendFiltersToAll(self):
    if self.currentSubclipIndex is not None:
      resp = messagebox.askyesno(title="Append these filters to all clips?", message="This will add the filters on this clip to the end of all other clips, are you sure?")    
      if resp:
        tempfilterClipboard = self.convertFilterstoSpecDefaults()
        for rid in self.subClipOrder:
          self.subclips[rid].setdefault('filters',[]).extend(copy.deepcopy(tempfilterClipboard))
        self.recaculateFilters('overrideFilters')

  def overrideFilters(self):
    if self.currentSubclipIndex is not None:
      resp = messagebox.askyesno(title="Apply these filters to all clips?", message="This will clear the filters on all other clips and override them with these filters, are you sure?")
      if resp:
        tempfilterClipboard = self.convertFilterstoSpecDefaults()
        for rid in self.subClipOrder:
          self.subclips[rid]['filters'] = copy.deepcopy(tempfilterClipboard)
        self.recaculateFilters('overrideFilters')

        currentClip = self.getCurrentClip()
        if currentClip is not None:
          filters           = copy.deepcopy(currentClip['filters'])
          filterexp         = copy.deepcopy(currentClip['filterexp'])
          filterexpEncStage = copy.deepcopy(currentClip['filterexpEncStage'])

          for clip in self.subclips.values():
            clip['filters']           = filters
            clip['filterexp']         = filterexp
            clip['filterexpEncStage'] = filterexpEncStage        

  def shiftFilterOnStack(self,filter,direction):
    filterInd = self.filterSpecifications.index(filter)
    print(filterInd,filterInd+direction,len(self.filterSpecifications))
    
    if filterInd+direction>=0 and (filterInd+direction)<=(len(self.filterSpecifications)-1):

      if direction==1:
        self.filterSpecifications.insert(filterInd+direction,self.filterSpecifications.pop(filterInd))
      elif direction==-1:
        self.filterSpecifications.insert(filterInd+direction,self.filterSpecifications.pop(filterInd))

      for flt in self.filterSpecifications:
        flt.pack_forget()
      for flt in self.filterSpecifications:
        flt.packself()

      self.recaculateFilters("shiftFilterOnStack")

  def appendFilters(self):
    if self.currentSubclipIndex is not None:
      rid = self.subClipOrder[self.currentSubclipIndex]
      self.subclips[rid]['filters'] += copy.deepcopy(self.filterClipboard)
      for f in self.filterSpecifications:
        f.destroy()
      self.filterSpecifications=[]
      rid = self.subClipOrder[self.currentSubclipIndex]
      
      for spec in self.subclips[rid].setdefault('filters',[]):
        self.filterSpecificationCount+=1
        self.filterSpecifications.append( 
          FilterSpecification(self.filterContainer,self,spec,self.filterSpecificationCount) 
        )
      self.recaculateFilters('appendFilters')

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
      self.recaculateFilters('pasteFilters')


  def setSubclipIndex(self,newIndex):
    self.recaculateFilters('setSubclipIndex')
    if self.currentSubclipIndex is not None and len(self.subClipOrder)>0:
      try:
        rid = self.subClipOrder[self.currentSubclipIndex]
        self.subclips[rid]['filters'] = self.convertFilterstoSpecDefaults()
      except Exception as e:
        print(e,"Can't update old subclip by index")

    if self.currentSubclipIndex != newIndex:
      self.canvasValueTimeline.coords(self.timelineSeekHandle, -1, 20, -1, 175) 
      self.activeCommandFilterValuePair=None
    
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
      self.recaculateFilters('setSubclipIndex')

  def updateFilterDisplay(self):
    currentClip = self.getCurrentClip()
    if currentClip is None:
      pass
    else:
      basename = os.path.basename(currentClip['filename'])[:16]
      s=currentClip['start']
      e=currentClip['end']
      rid = self.subClipOrder[self.currentSubclipIndex]
      print(currentClip)
      newLabel = '#{r} {n} {s:0.2f}-{e:0.2f} {i}/{len}'.format(r=rid, n=basename,
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

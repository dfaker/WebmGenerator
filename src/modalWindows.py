
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import subprocess as sp
import string
import re
import os
import logging
import sys

import threading

try:
  from .encodingUtils import cleanFilenameForFfmpeg
except:
  from encodingUtils import cleanFilenameForFfmpeg

from datetime import datetime

try:
  scriptPath = os.path.dirname(os.path.abspath(__file__))
  
  parentScriptPath = os.path.split( os.path.dirname(os.path.abspath(__file__)))[0]

  basescriptPath = os.path.split(scriptPath)[0]
  scriptPath_frozen = os.path.dirname(os.path.abspath(sys.executable))


  os.environ["PATH"] = scriptPath + os.pathsep + parentScriptPath + os.pathsep + scriptPath_frozen + os.pathsep + os.environ["PATH"]
  print(scriptPath)
  print(scriptPath_frozen)

  os.add_dll_directory(basescriptPath)
  os.add_dll_directory(scriptPath)
  os.add_dll_directory(scriptPath_frozen)
except AttributeError as e:
  print(e)
except Exception as e:
  print(e)
  logging.error("scriptPath Exception",exc_info=e)

import mpv

import numpy as np

import re


def read_pgm(inbuffer, byteorder='>'):
    buffer = inbuffer[::]
    try:
        header, width, height, maxval = re.search(
            b"(^P6\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n]\s)*)", buffer).groups()
    except AttributeError:
        raise ValueError("Not a raw PGM file: '%s'" % filename)
    return np.frombuffer(buffer,
                            dtype='u1' if int(maxval) < 256 else byteorder+'u2',
                            count=int(width)*int(height)*3,
                            offset=len(header)
                            ).reshape((int(height), int(width), 3))

class AdvancedDropModal(tk.Toplevel):

  def __init__(self, master=None, dataDestination=None, *args):
    tk.Toplevel.__init__(self, master)
    self.data = dataDestination
    self.master=master

    self.title('Advanced drop file filtering')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,100)

    self.columnconfigure(0, weight=1)
    self.columnconfigure(1, weight=1)

    self.labelSort = ttk.Label(self)
    self.labelSort.config(text='Sort loaded files by')
    self.labelSort.grid(row=0,column=0,sticky='new',padx=5,pady=5)
    self.varSort   = tk.StringVar(self,'None')
    self.varSort.set('None') 
    self.entrySort =  ttk.Combobox(self,textvariable=self.varSort)
    self.entrySort.config(values=['None'
                                 ,'Filename ascending',       'Filename descending'
                                 ,'Path ascending',           'Path descending'
                                 ,'File Size ascending',      'File Size descending'
                                 ,'Created date ascending',   'Created date descending'
                                 ,'Modified date ascending',  'Modified date descending'
                                 ,'Access date ascending',    'Access date descending'
                          ])
    self.entrySort.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.substringLabel = ttk.Label(self)
    self.substringLabel.config(text='File name filter')
    self.substringLabel.grid(row=1,column=0,sticky='new',padx=0,pady=0)
    self.substringVar   = tk.StringVar(self,0)
    self.substringVar.set('') 
    self.substringCheck =  ttk.Entry(self,textvariable=self.substringVar)
    self.substringCheck.grid(row=1,column=1,sticky='new',padx=0,pady=0)

    self.applyCmd = ttk.Button(self)
    self.applyCmd.config(text='Apply',command=self.applyOptions)
    self.applyCmd.grid(row=10,column=0,columnspan=2,sticky='nesw')
    
    self.attributes('-topmost', True)
    self.update()

  def applyOptions(self):
    
    self.data['sort']   = self.varSort.get()
    self.data['filter'] = self.substringVar.get()

    self.attributes('-topmost', False)
    self.update()
    self.destroy()
    self.master.update()
    print('self.destroy()')


class AdvancedEncodeFlagsModal(tk.Toplevel):

  def __init__(self, master=None, controller=None, *args):
    tk.Toplevel.__init__(self, master)
    self.controller = controller

    options = {
                'forceBestDeadline':False,
                'disableVP9Tiling':False,
                'forceGifFPS':True,
                'forceFPS':-1,
                'earlyPSNRWidthReduction':-1,
                'earlyPSNRWindowLength':5,
                'earlyPSNRSkipSamples':5,
                'cqMode':False,
                'qmaxOverride':-1,
                'svtav1Preset':8,
                'bitRateControl':'Average'
              }
    
    if self.controller is not None:
      tempOptions = self.controller.getAdvancedFlags()
      for k,v in options.items():
        if k in tempOptions:
          if type(v) == bool:
            options[k] = bool(tempOptions[k])
          elif type(v) == int:
            options[k] = int(tempOptions[k])
          elif type(v) == str:
            options[k] = str(tempOptions[k])
      for k in tempOptions:
        if k.startswith('encoder-option-'):
          options[k] = str(tempOptions[k])


    self.title('Advanced Encoding Flags')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,100)

    self.columnconfigure(0, weight=1)
    self.columnconfigure(1, weight=1)

    self.bestDeadlineLabel = ttk.Label(self)
    self.bestDeadlineLabel.config(text='Force "best" deadline (Will be slower, can occasionally produce worse output)')
    self.bestDeadlineLabel.grid(row=0,column=0,sticky='new',padx=0,pady=0)
    self.bestDeadlineVar   = tk.IntVar(self,0)
    self.bestDeadlineVar.set(int(options['forceBestDeadline']))
    self.bestDeadlineCheck =  ttk.Checkbutton(self,text='',var=self.bestDeadlineVar)
    self.bestDeadlineCheck.grid(row=0,column=1,sticky='new',padx=0,pady=0)

    self.disableTilingLabel = ttk.Label(self)
    self.disableTilingLabel.config(text='Disable VP9 column tiling (Better quality but no multi-threading can be used)')
    self.disableTilingLabel.grid(row=1,column=0,sticky='new',padx=0,pady=0)
    self.disableTilingVar   = tk.IntVar(self,0)
    self.disableTilingVar.set(int(options['disableVP9Tiling'])) 
    self.disableTilingCheck =  ttk.Checkbutton(self,text='',var=self.disableTilingVar)
    self.disableTilingCheck.grid(row=1,column=1,sticky='new',padx=0,pady=0)

    self.forceGifFPSLabel = ttk.Label(self)
    self.forceGifFPSLabel.config(text='Force 18fps output on gifs (too high fps in gifs can slow down playback)')
    self.forceGifFPSLabel.grid(row=2,column=0,sticky='new',padx=0,pady=0)
    self.forceGifFPSVar   = tk.IntVar(self,1)
    self.forceGifFPSVar.set(int(options['forceGifFPS'])) 
    self.forceGifFPSCheck =  ttk.Checkbutton(self,text='',var=self.forceGifFPSVar)
    self.forceGifFPSCheck.grid(row=2,column=1,sticky='new',padx=0,pady=0)

    self.forceFPSLabel = ttk.Label(self)
    self.forceFPSLabel.config(text='Force final fixed frames per second on all encodes')
    self.forceFPSLabel.grid(row=3,column=0,sticky='new',padx=0,pady=0)
    self.forceFPSVar   = tk.StringVar(self,1)
    self.forceFPSVar.set(str(int(options['forceFPS']))) 
    self.forceFPSCheck =  ttk.Spinbox(self,text='',textvariable=self.forceFPSVar,from_=float('-1'),to=float('inf'))
    self.forceFPSCheck.grid(row=3,column=1,sticky='new',padx=0,pady=0)

    self.earlyPSNRLabel = ttk.Label(self)
    self.earlyPSNRLabel.config(text='Use running average rather than final PSNR (may be innacurate)')
    self.earlyPSNRLabel.grid(row=4,column=0,sticky='new',padx=0,pady=0)
    self.earlyPSNRVar   = tk.IntVar(self,0)
    self.earlyPSNRVar.set(int(options['earlyPSNRWidthReduction']))
    self.earlyPSNRCheck =  ttk.Checkbutton(self,text='',var=self.earlyPSNRVar)
    self.earlyPSNRCheck.grid(row=4,column=1,sticky='new',padx=0,pady=0)

    self.earlyPSNRSampleLabel = ttk.Label(self)
    self.earlyPSNRSampleLabel.config(text='Number of PSNR samples to average')
    self.earlyPSNRSampleLabel.grid(row=5,column=0,sticky='new',padx=0,pady=0)
    self.earlyPSNRSampleVar   = tk.StringVar(self,0)
    self.earlyPSNRSampleVar.set(str(int(options['earlyPSNRWindowLength']))) 
    self.earlyPSNRSampleCheck =  ttk.Spinbox(self,text='',textvariable=self.earlyPSNRSampleVar,from_=float('1'),to=float('inf'))
    self.earlyPSNRSampleCheck.grid(row=5,column=1,sticky='new',padx=0,pady=0)

    self.earlyPSNRSampleSkipLabel = ttk.Label(self)
    self.earlyPSNRSampleSkipLabel.config(text='Number of initial PSNR samples to skip')
    self.earlyPSNRSampleSkipLabel.grid(row=6,column=0,sticky='new',padx=0,pady=0)
    self.earlyPSNRSampleSkipVar   = tk.StringVar(self,0)
    self.earlyPSNRSampleSkipVar.set(str(int(options['earlyPSNRSkipSamples']))) 
    self.earlyPSNRSampleSkipCheck =  ttk.Spinbox(self,text='',textvariable=self.earlyPSNRSampleSkipVar,from_=float('1'),to=float('inf'))
    self.earlyPSNRSampleSkipCheck.grid(row=6,column=1,sticky='new',padx=0,pady=0)

    self.forceCQLabel = ttk.Label(self)
    self.forceCQLabel.config(text='Use Constant Quality Mode where supported')
    self.forceCQLabel.grid(row=7,column=0,sticky='new',padx=0,pady=0)
    self.forceCQVar   = tk.IntVar(self,1)
    self.forceCQVar.set(int(options['cqMode'])) 
    self.forceCQCheck =  ttk.Checkbutton(self,text='',var=self.forceCQVar)
    self.forceCQCheck.grid(row=7,column=1,sticky='new',padx=0,pady=0)

    self.qmaxOverrideLabel = ttk.Label(self)
    self.qmaxOverrideLabel.config(text='Qmax override')
    self.qmaxOverrideLabel.grid(row=8,column=0,sticky='new',padx=0,pady=0)
    self.qmaxOverrideVar   = tk.StringVar(self,0)
    self.qmaxOverrideVar.set(str(int(options['qmaxOverride']))) 
    self.qmaxOverrideCheck =  ttk.Spinbox(self,text='',textvariable=self.qmaxOverrideVar,from_=float('-1'),to=float('100'))
    self.qmaxOverrideCheck.grid(row=8,column=1,sticky='new',padx=0,pady=0) 

    self.sv1avPresetLabel = ttk.Label(self)
    self.sv1avPresetLabel.config(text='SVT-AV1 Preset')
    self.sv1avPresetLabel.grid(row=9,column=0,sticky='new',padx=0,pady=0)
    self.sv1avPresetVar   = tk.StringVar(self)
    self.sv1avPresetVar.set(str(int(options['svtav1Preset']))) 
    self.sv1avPresetCheck =  ttk.Spinbox(self,text='',textvariable=self.sv1avPresetVar,from_=float('0'),to=float('12'))
    self.sv1avPresetCheck.grid(row=9,column=1,sticky='new',padx=0,pady=0) 

    self.bitrateControlLabel = ttk.Label(self)
    self.bitrateControlLabel.config(text='Bitrate constraint mode')
    self.bitrateControlLabel.grid(row=10,column=0,sticky='new',padx=0,pady=0)
    self.bitrateControlVar   = tk.StringVar(self)

    self.bitrateControlVar.set(options['bitRateControl']) 

    self.bitrateControlCheck = ttk.Combobox(self,textvariable=self.bitrateControlVar) 
    self.bitrateControlCheck['state'] = 'readonly'
    self.bitrateControlCheck.config(values=['Average',
                                            'Limit Maximum',
                                            'Constant'])
    self.bitrateControlVar.set(options['bitRateControl']) 
    
    self.bitrateControlCheck.grid(row=10,column=1,sticky='new',padx=0,pady=0) 

    row=10+1

    spec = self.controller.customEncoderspecs.get(self.controller.outputFormatValue)
    print('SPEC INIT',self.controller.outputFormatValue)
    self.specLookup = {}
    if spec is not None:
        if len(spec.getExtraEncoderParams()) > 0:
            self.encoderOptsLabel = ttk.Label(self)
            self.encoderOptsLabel.config(text='Encoder Options for '+self.controller.outputFormatValue+'')
            self.encoderOptsLabel.grid(row=row,column=0,sticky='new',columnspan=2,padx=0,pady=0)
            row+=1

        for param in spec.getExtraEncoderParams():
            print(param)
            if param['type'] == 'choice':
                customVarLabel = ttk.Label(self)
                customVarLabel.config(text=param['label'])
                customVarLabel.grid(row=row,column=0,sticky='new',padx=0,pady=0)
                customVar   = tk.StringVar(self)
                customVal = ttk.Combobox(self,textvariable=customVar) 
                customVal['state'] = 'readonly'
                customVal.config(values=param.get('options',[]))
                customVar.set( options.get( 'encoder-option-'+param['name'],   param.get('default','None')))
                customVal.grid(row=row,column=1,sticky='new',padx=0,pady=0) 
                self.specLookup[param['name']] = (customVarLabel,customVar,customVal)
            elif param['type'] == 'int':
                customVarLabel = ttk.Label(self)
                customVarLabel.config(text=param['label'])
                customVarLabel.grid(row=row,column=0,sticky='new',padx=0,pady=0)
                customVar   = tk.StringVar(self)
                customVar.set(str(int(options.get('encoder-option-'+param['name'],   param.get('default','None')))))
                customVal =  ttk.Spinbox(self,text='',textvariable=customVar)
                customVal.grid(row=row,column=1,sticky='new',padx=0,pady=0) 
                self.specLookup[param['name']] = (customVarLabel,customVar,customVal)
            row+=1

    self.applyCmd = ttk.Button(self)
    self.applyCmd.config(text='Apply',command=self.applyOptions)
    self.applyCmd.grid(row=row,column=0,columnspan=2,sticky='nesw')

    try:
      self.attributes('-topmost', True)
      self.update()      
    except:
      pass

  def applyOptions(self):
    options = {
                'forceBestDeadline':False,
                'disableVP9Tiling':False,
                'forceGifFPS':True,
                'forceFPS':-1,
                'earlyPSNRWidthReduction':False,
                'earlyPSNRWindowLength':5,
                'earlyPSNRSkipSamples':5,
                'cqMode':False,
                'qmaxOverride':-1,
                'svtav1Preset':8,
                'bitRateControl':'Average'
              }

    try:
      options['forceBestDeadline'] = int(self.bestDeadlineVar.get()) == 1
    except Exception as e: 
      print(e)

    try:
      options['disableVP9Tiling'] = int(self.disableTilingVar.get()) == 1
    except Exception as e: 
      print(e)

    try:
      options['forceGifFPS'] = int(self.forceGifFPSVar.get()) == 1
    except Exception as e: 
      print(e)

    try:
      options['forceFPS'] = int(self.forceFPSVar.get())
    except Exception as e: 
      print(e)

    try:
      options['earlyPSNRWidthReduction'] = int(self.earlyPSNRVar.get()) == 1
    except Exception as e: 
      print(e)

    try:
      options['earlyPSNRWindowLength'] = int(self.earlyPSNRSampleVar.get())
    except Exception as e: 
      print(e)

    try:
      options['earlyPSNRSkipSamples'] = int(self.earlyPSNRSampleSkipVar.get())
    except Exception as e: 
      print(e)

    try:
      options['cqMode'] = int(self.forceCQVar.get()) == 1
    except Exception as e: 
      print(e)

    try:
      options['qmaxOverride'] = int(float(self.qmaxOverrideVar.get()))
    except Exception as e: 
      print(e)

    try:
      options['svtav1Preset'] = int(float(self.sv1avPresetVar.get()))
    except Exception as e: 
      print(e)

    try:
      options['bitRateControl'] = self.bitrateControlVar.get()
    except Exception as e: 
      print(e)

    for name,(label,var,val) in self.specLookup.items():
        options['encoder-option-'+name] = var.get()
        label.grid_forget()
        val.grid_forget()

    if self.controller is not None:
      self.controller.setAdvancedFlags(options)

    self.destroy()


class EditSubclipModal(tk.Toplevel):
  def __init__(self, master=None, controller=None, rid=None, *args):
    tk.Toplevel.__init__(self, master)

    self.title('Edit Subclip')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,100)

    self.controller = controller
    self.rid = rid

    self.columnconfigure(0, weight=0)
    self.columnconfigure(1, weight=1)

    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)

    self.grab_set()
    self.title('Edit Subclip {}'.format(rid))
    self.s, self.e = self.controller.getRangeDetails(rid)


    self.nameLabel = ttk.Label(self)
    self.nameLabel.config(text='Quick Label')
    self.nameLabel.grid(row=0,column=0,sticky='new',padx=5,pady=5)

    self.nameVar   = tk.StringVar(self,self.controller.getLabelForRid(self.rid))
    self.entryname = ttk.Entry(self,textvariable=self.nameVar)
    self.entryname.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.startTsLabel = ttk.Label(self)
    self.startTsLabel.config(text='Start')
    self.startTsLabel.grid(row=1,column=0,sticky='new',padx=5,pady=5)

    self.startTsVar   = tk.StringVar(self,str(self.s))
    self.entrystartTs = ttk.Spinbox(self,text='',textvariable=self.startTsVar,from_=float('-1'),to=float('inf'))
    self.entrystartTs.grid(row=1,column=1,sticky='new',padx=5,pady=5)

    self.endTsLabel = ttk.Label(self)
    self.endTsLabel.config(text='End')
    self.endTsLabel.grid(row=2,column=0,sticky='new',padx=5,pady=5)

    self.endtTsVar   = tk.StringVar(self,str(self.e))
    self.entryendTs = ttk.Spinbox(self,text='',textvariable=self.endtTsVar,from_=float('-1'),to=float('inf'))
    self.entryendTs.grid(row=2,column=1,sticky='new',padx=5,pady=5)

    self.anchorLabel = ttk.Label(self)
    self.anchorLabel.config(text='Anchor')
    self.anchorLabel.grid(row=3,column=0,sticky='new',padx=5,pady=5)
    self.anchorOptions = ['Start','Middle','End']
    self.anchorVar   = tk.StringVar(self,'Middle')
    self.entryanchor = ttk.Spinbox(self,text='',textvariable=self.endtTsVar,from_=float('-1'),to=float('inf'))
    self.entryanchor = ttk.Combobox(self,textvariable=self.anchorVar,values=self.anchorOptions,state='readonly')
    self.entryanchor.grid(row=3,column=1,sticky='new',padx=5,pady=5)

    self.durTsLabel = ttk.Label(self)
    self.durTsLabel.config(text='Duration')
    self.durTsLabel.grid(row=4,column=0,sticky='new',padx=5,pady=5)

    self.durTsVar   = tk.StringVar(self,str(self.e-self.s))
    self.entrydurTs = ttk.Spinbox(self,text='',textvariable=self.durTsVar,from_=float('-1'),to=float('inf'))
    self.entrydurTs.grid(row=4,column=1,sticky='new',padx=5,pady=5)

    self.startTsVar.trace('w',self.startChange)
    self.endtTsVar.trace('w',self.endChange)
    self.durTsVar.trace('w',self.durChange)
    self.nameVar.trace('w',self.nameChange)
    self.blockUpdate = False

  def nameChange(self,*args):
    self.controller.updateLabelForRid(self.rid, self.nameVar.get())

  def startChange(self,*args):
    self.controller.updatePointForRid(self.rid,'s',float(self.startTsVar.get()))
    self.durTsVar.set((float(self.endtTsVar.get()) - float(self.startTsVar.get())))

  def endChange(self,*args):
    self.controller.updatePointForRid(self.rid,'e',float(self.endtTsVar.get()))
    self.durTsVar.set((float(self.endtTsVar.get()) - float(self.startTsVar.get())))

  def durChange(self,*args):
    if self.anchorVar.get() == 'Start':
        self.endtTsVar.set( float(self.startTsVar.get()) + float(self.durTsVar.get()) )
    elif self.anchorVar.get() == 'End':
        self.startTsVar.set( float(self.endtTsVar.get()) - float(self.durTsVar.get()) )
    else:
        mid = (float(self.endtTsVar.get()) + float(self.startTsVar.get()))/2
        half = float(self.durTsVar.get())/2
        self.startTsVar.set( mid-half )
        self.endtTsVar.set( mid+half )

  def updateValue(self):
    pass

  def applyOptions(self):
    pass


class SliceCreationUtilsModal(tk.Toplevel):

  def __init__(self, master=None, controller=None, *args):
    tk.Toplevel.__init__(self, master)
    
    self.title('Subclip Creation Utilities')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,400)

    self.sliceStyleLabel = ttk.Label(self)
    self.sliceStyleLabel.config(text='Slice Style')
    self.sliceStyleLabel.grid(row=0,column=0,sticky='new',padx=5,pady=5)
    self.sliceStyleVar   = tk.StringVar(self,'By Subclip Duration')
    self.entrysliceStyle =  ttk.Combobox(self,textvariable=self.sliceStyleVar,state='readonly')
    self.entrysliceStyle.config(values=['By Subclip Duration', 'By Subclip Count'])
    self.entrysliceStyle.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.sliceDurationLabel = ttk.Label(self)
    self.sliceDurationLabel.config(text='Subclip Duration (seconds)')
    self.sliceDurationLabel.grid(row=1,column=0,sticky='new',padx=5,pady=5)
    self.sliceDurationVar   = tk.StringVar(self,'10.0')
    self.entrysliceDuration = ttk.Entry(self,textvariable=self.sliceDurationVar)
    self.entrysliceDuration.grid(row=1,column=1,sticky='new',padx=5,pady=5)

    self.sliceCountLabel = ttk.Label(self)
    self.sliceCountLabel.config(text='Subclip Count')
    self.sliceCountLabel.grid(row=2,column=0,sticky='new',padx=5,pady=5)
    self.sliceCountVar   = tk.StringVar(self,'10')
    self.entrysliceCount = ttk.Entry(self,textvariable=self.sliceCountVar)
    self.entrysliceCount.grid(row=2,column=1,sticky='new',padx=5,pady=5)

    self.sliceGapLabel = ttk.Label(self)
    self.sliceGapLabel.config(text='Seconds gap between subclips')
    self.sliceGapLabel.grid(row=3,column=0,sticky='new',padx=5,pady=5)
    self.sliceGapVar   = tk.StringVar(self,'0')
    self.entrysliceGap = ttk.Entry(self,textvariable=self.sliceGapVar)
    self.entrysliceGap.grid(row=3,column=1,sticky='new',padx=5,pady=5)

    self.sliceSkipLabel = ttk.Label(self)
    self.sliceSkipLabel.config(text='Skip every x Subclips')
    self.sliceSkipLabel.grid(row=4,column=0,sticky='new',padx=5,pady=5)
    self.sliceSkipVar   = tk.StringVar(self,'0')
    self.entrysliceSkip = ttk.Entry(self,textvariable=self.sliceSkipVar)
    self.entrysliceSkip.grid(row=4,column=1,sticky='new',padx=5,pady=5)

    self.sliceSkipOffsetLabel = ttk.Label(self)
    self.sliceSkipOffsetLabel.config(text='Skip starting at offset')
    self.sliceSkipOffsetLabel.grid(row=5,column=0,sticky='new',padx=5,pady=5)
    self.sliceSkipOffsetVar   = tk.StringVar(self,'0')
    self.entrysliceSkipOffset = ttk.Entry(self,textvariable=self.sliceSkipOffsetVar)
    self.entrysliceSkipOffset.grid(row=5,column=1,sticky='new',padx=5,pady=5)

    self.sliceMultiplierLabel = ttk.Label(self)
    self.sliceMultiplierLabel.config(text='Multiplier for duration after each subclip')
    self.sliceMultiplierLabel.grid(row=6,column=0,sticky='new',padx=5,pady=5)
    self.sliceMultiplierVar   = tk.StringVar(self,'1')
    self.entrysliceMultiplier = ttk.Entry(self,textvariable=self.sliceMultiplierVar)
    self.entrysliceMultiplier.grid(row=6,column=1,sticky='new',padx=5,pady=5)



class VideoAudioSync(tk.Frame):
  def __init__(self, uiParent=None, master=None, controller=None, sequencedClips=[], dubFile=None, dubOffsetVar=None, fadeVar=None, mixVar=None, globalOptions={}, *args):

    tk.Frame.__init__(self, uiParent)
    
    self.uiParent = uiParent
    try:
      self.uiParent.title('Sequence Preview and Audio Track Sync')
      self.uiParent.minsize(600,100)
    except:
      pass

    self.bind('<Enter>',self.onEnter)
    self.bind('<Leave>',self.onLeave)

    self.controller=controller
    self.master=master

    self.style = ttk.Style()
    self.style.theme_use('clam')

    self.isActive=True

    self.playerFrame = ttk.Frame(self,style='PlayerFrame.TFrame',height='400', width='200')
    self.playerFrame.grid(row=0,column=0,sticky='nesw',padx=0,pady=(2,0),columnspan=14)


    self.visStyles={
      "Spectrum - Lin:Log":"showspectrumpic=s={width}x80:legend=0:fscale=log:scale=log",
      "Spectrum - Log:Log":"showspectrumpic=s={width}x80:legend=0:fscale=log:scale=log",
      "Spectrum - Lin:Square root":"showspectrumpic=s={width}x80:legend=0:fscale=lin:scale=sqrt",
      "Spectrum - Lin:Cube root":"showspectrumpic=s={width}x80:legend=0:fscale=lin:scale=cbrt",
      "Spectrum - Middle pass filter - Log:Log":"highpass=f=200,lowpass=f=3000,showspectrumpic=s={width}x80:legend=0:fscale=log:scale=log",
      "Spectrum - Compressor - Log:Log":"acompressor=threshold=.5:ratio=5:2:attack=0.01:release=0.01,showspectrumpic=s={width}x80:legend=0:fscale=log:scale=log",

      "Spectrum - Bass Boost Norm - Log:Log":"bass=g=3:f=110:w=0.6,showspectrumpic=s={width}x80:legend=0:fscale=log:scale=log",

      "Spectrum - Bass Isolate - Log:Log":"acompressor=threshold=.5:ratio=5:2:attack=0.01:release=0.01,showspectrumpic=s={width}x80:legend=0:fscale=log:scale=log",


      "Waves":"asplit[sa][sb],[sa]showwavespic=s={width}x80:colors=5C5CAE:filter=peak[pa],[sb]showwavespic=s={width}x80:colors=b8b8dc:filter=average[pb],[pa][pb]overlay=0:0",
      "Waves - Middle pass filter":"asplit[sa][sb],[sa]showwavespic=s={width}x80:colors=5C5CAE:filter=peak[pa],[sb]highpass=f=200,lowpass=f=3000,showwavespic=s={width}x80:colors=b8b8dc:filter=average[pb],[pa][pb]overlay=0:0",
      "Waves - Compressor":"asplit[sa][sb],[sa]showwavespic=s={width}x80:colors=5C5CAE:filter=peak[pa],[sb]acompressor=threshold=.5:ratio=5:2:attack=0.01:release=0.01,showwavespic=s={width}x80:colors=b8b8dc:filter=average[pb],[pa][pb]overlay=0:0",
    }
        
    self.lastAppliedSpetra=None
    self.visStylesList= sorted(list(self.visStyles.keys()))
    self.visStyleVar = tk.StringVar()
    self.visStyleVar.set(self.visStylesList[0]) 
    self.visStyle=self.visStyles[self.visStyleVar.get()]
    self.visStyleVar.trace("w",self.visStyleChanged)

    self.visStyleCombo = ttk.Combobox(self,textvariable=self.visStyleVar,values=self.visStylesList,state='readonly')
    self.visStyleCombo.grid(row=1,column=0,sticky='nesw',padx=0,pady=(0,0),columnspan=14)

    self.timeline_canvas = tk.Canvas(self,width=200, height=120, bg='black',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=2,column=0,columnspan=14,sticky="nesw")
    
    self.timeline_canvas.bind("<Button-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<ButtonRelease-1>", self.timelineMousePress)
    self.timeline_canvas.bind("<B1-Motion>", self.timelineMousePress)

    self.timeline_canvas.bind("<MouseWheel>", self.timelineMousewheel)
    self.timeline_canvas.bind("<Motion>", self.timelineMouseMotion)

    self.canvasBackground = self.timeline_canvas.create_rectangle(0, 0, self.timeline_canvas.winfo_width(), 20,fill="#1E1E1E")

    self.canvasZoomBG          = self.timeline_canvas.create_rectangle(-1, 0, -1, 20,fill="#3F3F7F")
    self.canvasZoomBGRange     = self.timeline_canvas.create_rectangle(-1, 0, -1, 20,fill="#9E9E9E")
    self.canvasZoomRangeMid    = self.timeline_canvas.create_line(-1, 0, -1, 20,fill="#3F3F7F")

    self.canvasSeekPointer      = self.timeline_canvas.create_line(-1, 0, -1, self.timeline_canvas.winfo_height(),fill="white")
    self.canvasUpperSeekPointer = self.timeline_canvas.create_rectangle(-1, 0, -1, self.timeline_canvas.winfo_height(),fill="#c5c5d8",outline='white')

    self.draggingblockTargetRect = self.timeline_canvas.create_rectangle(-1, 0, -1, 0,fill="white",outline='white') 

    self.playerwid = self.playerFrame.winfo_id()

    self.dubFile   = dubFile
    self.dubOffsetVar = dubOffsetVar
    self.fadeVar      = fadeVar
    self.sequencedClips = sequencedClips
    self.volumeVar = tk.StringVar()
    self.seekOffsetVar = tk.StringVar()
    self.seekOffsetVar.set(-1)
    self.speedVar = tk.StringVar()
    self.speedVar.set(1)
    self.textInfo = tk.StringVar()
    self.textInfo.set('offset=0.00')

    self.mixVar = mixVar

    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=1)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=0)

    self.columnconfigure(0, weight=1)
    self.columnconfigure(1, weight=1)
    self.columnconfigure(2, weight=1)
    self.columnconfigure(3, weight=1)
    self.columnconfigure(4, weight=1)
    self.columnconfigure(5, weight=1)
    self.columnconfigure(6, weight=1)
    self.columnconfigure(7, weight=1)

    self.columnconfigure(8, weight=1)



    self.tickColours=["#a9f9b9","#7dc4ed","#f46350","#edc1a6","#dfff91","#0f21e0","#f73dc8","#8392db","#72dbb4","#cc8624","#88ed71","#d639be"]

    self.player = mpv.MPV(loop='inf',
                          mute=False,
                          volume=0,
                          loglevel='debug',
                          autofit_larger='1280', wid=str(self.playerwid))

    self.currentTotalDuration=None
    self.currentTimePos=None
    self.ticktimestamps=[]
    self.tickXpos=[]
    self.colourMap={}
    self.ridListing=[]

    self.player.observe_property('time-pos', self.handleMpvTimePosChange)
    self.player.observe_property('duration', self.handleMpvDurationChange)
    self.player.observe_property('af-metadata',self.handleMpvafMetdata)

    self.labeldubFile = ttk.Label(self)
    self.labeldubFile.config(anchor='e',  text='Dubbing file:')
    self.labeldubFile['padding']=1
    self.labeldubFile.grid(row=3,column=0,sticky='ew')
    self.entrydubFile = ttk.Button(self,text='None',command=self.selectAudioOverride,width=40)
    self.entrydubFile['padding']=1
    Tooltip(self.entrydubFile,text='An mp3 audio file to use to replace the original video audio.')
    self.entrydubFile.grid(row=3,column=1,sticky='ew')



    self.labelpostSeekOffset = ttk.Label(self)
    self.labelpostSeekOffset.config(anchor='e',  text='Edit Seek Offset')
    self.labelpostSeekOffset.grid(row=3,column=2,sticky='ew')
    self.entrypostSeekOffset = ttk.Spinbox(self, textvariable=self.seekOffsetVar,from_=float('-inf'), 
                                          to=float('inf'), 
                                          increment=0.1)
    Tooltip(self.entrypostSeekOffset,text='Edit Seek Offset')
    self.entrypostSeekOffset.grid(row=3,column=3,sticky='ew')

    self.labelpostAudioVolume = ttk.Label(self)
    self.labelpostAudioVolume.config(anchor='e',  text='Volume')
    self.labelpostAudioVolume.grid(row=3,column=4,sticky='ew')
    self.entrypostAudioVolume = ttk.Spinbox(self, textvariable=self.volumeVar,from_=0, 
                                          to=100, 
                                          increment=5)
    Tooltip(self.entrypostAudioVolume,text='Audio Volume.')
    self.entrypostAudioVolume.grid(row=3,column=5,sticky='ew')
    self.volumeVar.trace('w',self.valueChangeVolume)
    self.volumeVar.set(0)

    if self.dubFile.get() is not None and os.path.exists(self.dubFile.get()):
      self.entrydubFile.config(text=os.path.basename(self.dubFile.get()))
      self.volumeVar.set(20)


    self.labelpostAudioOverrideDelay = ttk.Label(self)
    self.labelpostAudioOverrideDelay.config(anchor='e',  text='Dub Delay (seconds)')
    self.labelpostAudioOverrideDelay.grid(row=3,column=6,sticky='ew')
    self.entrypostAudioOverrideDelay = ttk.Spinbox(self, textvariable=self.dubOffsetVar,from_=float('-inf'), 
                                          to=float('inf'), 
                                          increment=0.05)
    Tooltip(self.entrypostAudioOverrideDelay,text='Delay before the start of the mp3 dub audio.')
    self.entrypostAudioOverrideDelay.grid(row=3,column=7,columnspan=2, sticky='ew')
    self.entrypostAudioOverrideDelay.bind('<MouseWheel>',self.checkCtrl)
    self.dubOffsetVar.trace('w',self.valueChangeCallback)      


    self.entryalign = ttk.Button(self,text='Auto-Align',command=self.alignToBeats,width=40)
    self.entryalign['padding']=1
    Tooltip(self.entryalign,text='Snap all visible markers to the closest beat.')
    self.entryalign.grid(row=3,column=9,sticky='ew')

    self.labelTransDuration = ttk.Label(self)
    self.labelTransDuration.config(anchor='e', padding='2', text='Transition Duration')
    self.labelTransDuration.grid(row=4,column=0,sticky='ew')
    self.entryTransDuration = ttk.Spinbox(self, 
                                          from_=0, 
                                          to=float('inf'), 
                                          increment=0.01,
                                          textvariable=self.fadeVar)

    self.entryTransDuration.grid(row=4,column=1,sticky='ew')
    self.fadeVar.trace('w',self.valueChangeCallback)

    self.labelPlaybackSpeed = ttk.Label(self)
    self.labelPlaybackSpeed.config(anchor='e', padding='2', text='Playback Speed')
    self.labelPlaybackSpeed.grid(row=4,column=2,sticky='ew')
    self.entrySpeed = ttk.Spinbox(self, 
                                          from_=0, 
                                          to=50, 
                                          increment=0.1,
                                          textvariable=self.speedVar)
    self.entrySpeed.grid(row=4,column=3,sticky='ew')
    self.speedVar.trace('w',self.speedChange)

    self.labelMixBias = ttk.Label(self)
    self.labelMixBias.config(anchor='e', padding='2', text='Audio Mix')
    self.labelMixBias.grid(row=4,column=4,sticky='ew')
    self.entryMixBias = ttk.Spinbox(self,
                                          from_=0, 
                                          to=1, 
                                          increment=0.1,
                                          textvariable=self.mixVar)
    self.entryMixBias.grid(row=4,column=5,sticky='ew')
    self.mixVar.trace('w',self.valueChangeCallback)

    self.keepDurationCondtantVar = tk.BooleanVar()
    self.keepDurationCondtantVar.set(True)
    self.entryKeepDurationConstant = ttk.Checkbutton(self,text='Resize Neighbouring sections',onvalue=True, offvalue=False,variable=self.keepDurationCondtantVar)
    self.entryKeepDurationConstant.grid(row=4,column=6,sticky='ew',columnspan=1)

    self.resizeToMiddleVar = tk.BooleanVar()
    self.resizeToMiddleVar.set(True)
    self.entryresizeToMiddle = ttk.Checkbutton(self,text='Resize Towards Midpoints',onvalue=True, offvalue=False,variable=self.resizeToMiddleVar)
    self.entryresizeToMiddle.grid(row=4,column=7,sticky='ew',columnspan=1)

    self.pauseOnLoseFocusVar = tk.BooleanVar()
    self.pauseOnLoseFocusVar.set(True)
    self.entrypauseOnLoseFocus = ttk.Checkbutton(self,text='Pause on Focus switch',onvalue=True, offvalue=False,variable=self.pauseOnLoseFocusVar)
    self.entrypauseOnLoseFocus.grid(row=4,column=8,sticky='ew',columnspan=1)

    self.dynamicSublipDurVar = tk.BooleanVar()
    self.dynamicSublipDurVar.set(True)
    self.dynamicSublipDur = ttk.Checkbutton(self,text='Dynamic Subclip Dur',onvalue=True, offvalue=False,variable=self.dynamicSublipDurVar)
    self.dynamicSublipDur.grid(row=4,column=9,sticky='ew',columnspan=1)


    try:
      self.uiParent.attributes('-topmost', True)
      self.uiParent.update()      
    except:
      pass

    self.edlBytes=b''
    self.edlStreamFunc=None

    self.keepWidth=False
    self.blockSpectrumUpdates=False
    self.durationForScale=0
    self.redrawTimer=None
    self.lastseekPos=0

    self.timelineZoomFactor=1
    self.currentZoomRangeMidpoint=0.5
    self.rangeHeaderClickStart = None

    self.lastAppliedSpetra = None

    self.lastSpectraStart=None
    self.lastSpectraDubDelay=0
    self.lastSpectraZoomFactor=1
    self.canvasSpectraImg=None
    self.canvasSpectraData=None
    self.waveAsPicImage=None

    self.imgo = None 
    self.spectrumWorkLock = threading.Lock()

    self.draggingTickIndex=None
    self.draggingTickOffset=0

    self.draggingBlockIndex = None

    self.ctrlDragStartSeconds = None

    self.valuesChanged=True

    def quitFunc(key_state, key_name, key_char):
      self.isActive=False

      try:
        self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('duration', self.handleMpvDurationChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('af-metadata', self.handleMpvafMetdata)
      except Exception as e:
        print(e)

      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()
      self.isActive=False

      try:
        self.uiParent.attributes('-topmost', False)
        self.uiParent.update()
      except:
        pass


      self.playerReaperfunc = playerReaper

    self.player.register_key_binding("CLOSE_WIN", quitFunc)
    self.bind('<Configure>', self.reconfigureWindow)

    self.recalculateEDLTimings()

  def cleanup(self):
    try:
      self.playerReaperfunc()
    except Exception as e:
      print(e)

  def visStyleChanged(self,*args):
    self.visStyle=self.visStyles[self.visStyleVar.get()]
    self.lastAppliedSpetra=None
    self.generateSpectrum()

  @staticmethod
  def pureGetClampedCenterPosAndRange(totalDuration,zoomFactor,currentMidpoint):

    outputDuration = totalDuration*(1/zoomFactor)
    minPercent     = (1/zoomFactor)/2
    center         = min(max(minPercent,currentMidpoint),1-minPercent)
    lowerRange     = (totalDuration*center)-(outputDuration/2)
    return outputDuration,center,lowerRange

  def getClampedCenterPosAndRange(self,update=True,negative=False):

    duration = self.currentTotalDuration
    if duration is None:
      duration = self.durationForScale
    if duration is None:
      duration=0

    result  = self.pureGetClampedCenterPosAndRange(duration,
                                                   self.timelineZoomFactor,
                                                   self.currentZoomRangeMidpoint)
    
    outputDuration,center,lowerRange = result
    if update:
      self.currentZoomRangeMidpoint=center

    return center,lowerRange,outputDuration

  def onEnter(self,e):
    if self.pauseOnLoseFocusVar.get():
      self.controller.broadcastModalFocus()
      self.player.pause=False
      try:
        #self.uiParent.attributes('-alpha',1.0)
        pass
      except:
        pass

  def onLeave(self,e):
    if self.pauseOnLoseFocusVar.get():
      self.controller.broadcastModalLoseFocus()
      self.player.pause=True
      try:
        #self.uiParent.attributes('-alpha',0.3)
        pass
      except:
        pass

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


  def checkCtrl(self,e):      
    ctrl  = (e.state & 0x4) != 0
    shift = (e.state & 0x1) != 0
    if ctrl:
      self.entrypostAudioOverrideDelay.config(increment=1)
    elif shift:
      self.entrypostAudioOverrideDelay.config(increment=5)
    else:
      self.entrypostAudioOverrideDelay.config(increment=0.05)

  def timelineMousewheel(self,e):
      ctrl  = (e.state & 0x4) != 0
      shift = (e.state & 0x1) != 0
      if e.y<20:

        factor = 0.10
        if shift:
          factor=0.25
        if ctrl:
          factor=1

        if e.delta>0:
          self.currentZoomRangeMidpoint += factor/self.timelineZoomFactor
          self.recalculateEDLTimings()
          self.generateSpectrum()
          return
        else:
          self.currentZoomRangeMidpoint -= factor/self.timelineZoomFactor
          self.recalculateEDLTimings()
          self.generateSpectrum()
          return
      else:
        dirty=False
        newZoomFactor = self.timelineZoomFactor
        if e.delta>0:
          newZoomFactor *= 1.5 if ctrl else 1.01
          dirty=True
        else:
          newZoomFactor *= 0.666 if ctrl  else 0.99
          dirty=True
        newZoomFactor = min(max(1,newZoomFactor),150)

        if newZoomFactor == self.timelineZoomFactor:
          return
        if dirty:
          self.timelineZoomFactor=newZoomFactor
          self.recalculateEDLTimings()
          self.generateSpectrum()

  def generateSpectrum(self,force=False):
    print('generateSpectrum',self.blockSpectrumUpdates)
    
    if self.lastSpectraStart is not None and self.canvasSpectraImg is not None and self.lastSpectraZoomFactor == self.timelineZoomFactor:
      oldx = self.secondsToXcoord(self.lastSpectraStart+( self.lastSpectraDubDelay-float(self.dubOffsetVar.get())) )
      self.timeline_canvas.coords(self.canvasSpectraImg,oldx,self.timeline_canvas.winfo_height()-80)

    if self.dubFile.get() is not None and os.path.exists(self.dubFile.get()) and self.currentTotalDuration is not None:
      t = threading.Thread(target=self.generateSpectrum_async,args=(force,),daemon=True)
      t.start()

  def generateSpectrum_async(self,force=False):
    with self.spectrumWorkLock:
      print('generateSpectrum_async',self.blockSpectrumUpdates)
      if self.dubFile.get() is not None and os.path.exists(self.dubFile.get()) and self.currentTotalDuration is not None:
        
        

        startoffset=self.xCoordToSeconds(0)
        try:
          startoffset = float(self.dubOffsetVar.get())+self.xCoordToSeconds(0)
        except:
          pass

        orig_height = self.timeline_canvas.winfo_height()
        orig_width = self.timeline_canvas.winfo_width()

        orig_startoffset = startoffset
        orig_currentTotalDuration = (self.xCoordToSeconds(orig_width)-self.xCoordToSeconds(0))

        spectraSpec = orig_height,orig_width,orig_startoffset,orig_currentTotalDuration,self.dubFile.get(),

        if spectraSpec == self.lastAppliedSpetra:
          return

        print(self.visStyle)

        proc = sp.Popen(['ffmpeg', '-y', '-i', cleanFilenameForFfmpeg(self.dubFile.get()), '-filter_complex', "[0:a]atrim={start}:{end},apad=whole_dur={padto},{visStyle}".format(start=orig_startoffset,end=orig_currentTotalDuration+orig_startoffset,padto=orig_currentTotalDuration,width=orig_width,visStyle=self.visStyle.format(start=orig_startoffset,end=orig_currentTotalDuration+orig_startoffset,padto=orig_currentTotalDuration,width=orig_width,visStyle=self.visStyle)), '-c:v', 'ppm', '-f', 'rawvideo', '-'],stdout=sp.PIPE)
        

        outs,errs = proc.communicate()        

        print(proc.poll())

        startoffset=self.xCoordToSeconds(0)
        try:
          startoffset = float(self.dubOffsetVar.get())+self.xCoordToSeconds(0)
        except:
          pass
        newTotalDuration = (self.xCoordToSeconds(orig_width)-self.xCoordToSeconds(0))

        if force or (orig_startoffset == startoffset and orig_currentTotalDuration == newTotalDuration and orig_width == self.timeline_canvas.winfo_width()):
        
          self.lastAppliedSpetra = spectraSpec
          self.lastSpectraStart = self.xCoordToSeconds(0)
          self.lastSpectraDubDelay = float(self.dubOffsetVar.get())
          self.lastSpectraZoomFactor=self.timelineZoomFactor
        
          self.canvasSpectraData = outs
          self.imgo = None

          if self.waveAsPicImage is None:
            self.waveAsPicImage = tk.PhotoImage(data=outs)
          else:
            self.waveAsPicImage.config(data=outs)

          if self.canvasSpectraImg is None:
            self.canvasSpectraImg = self.timeline_canvas.create_image(0,orig_height-80,image=self.waveAsPicImage,anchor='nw',tags='waveAsPicImage')
          else:
            self.timeline_canvas.coords(self.canvasSpectraImg,0,orig_height-80)
            
          self.timeline_canvas.lower(self.canvasSpectraImg)
  
  def alignToBeats(self):
    if self.imgo is None:
        self.imgo = np.mean(read_pgm(self.canvasSpectraData )[:,:,:],axis=(0,2))**2
    
    n= 30
    for tx,tidx in self.tickXpos[::-1]:
        tx = int(tx)
        xl  = [float(x) for x in self.imgo[tx-n:tx+n]]
        xl  = [x* (len(xl)-abs((i-len(xl)/2)) )   for i,x in enumerate(xl)]

        am = np.argmax(xl)
        xpos = int(tx-n+am)
        timestamp = self.xCoordToSeconds(xpos)
        self.updateRegionsOnDrag(tidx,timestamp)


        self.timeline_canvas.delete('dragTick')
        self.timeline_canvas.delete('ticksLine{}'.format(tidx))
        

        self.timeline_canvas.create_polygon(  xpos,    20+20+2, 
                                              xpos-7,  20+20+2+5, 
                                              xpos,    20+20+2+11,
                                              xpos+7,  20+20+2+5,
                                            fill='white',tags='dragTick')

        self.timeline_canvas.create_line(xpos, 20+0, 
                                         xpos, 200,fill='white',tags='dragTick')
        fadeDist = 0

        try:
          fadeDur  = float(self.fadeVar.get())
          fadeDist = self.secondsToXcoord(fadeDur/2)-self.secondsToXcoord(0) 
        except:
          pass

        if fadeDist > 0:
          self.timeline_canvas.create_line(xpos-fadeDist, 20+0, 
                                           xpos-fadeDist, 20+200,
                                           fill='blue',tags='dragTick')
          self.timeline_canvas.create_line(xpos+fadeDist, 20+0, 
                                           xpos+fadeDist, 20+200,
                                           fill='blue',tags='dragTick')
    self.recalculateEDLTimings()


  def speedChange(self,*args):
    newspeed = min(max(0,float(self.speedVar.get())),50)
    self.player.speed = str(newspeed)


  def handleMpvafMetdata(self,name,value):
    print(name,value)


  def toggleBoringMode(self,boringMode):
    if boringMode:
      self.playerFrame.grid_forget()
      if self.dubFile.get() is None or self.dubFile.get() == 'None' or (not os.path.exists(self.dubFile.get())):
        self.player.volume=0
    else:
      self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0,columnspan=9)

  def selectAudioOverride(self):

    try:
      self.uiParent.attributes('-topmost', False)
      self.uiParent.update()
    except:
      pass

    files = askopenfilename(multiple=False,filetypes=[('mp3','*.mp3',),('wav','*.wav')])
  
    try:
      self.uiParent.attributes('-topmost', True)
      self.uiParent.update()
    except:
      pass

    if files is None or len(files)==0:
      self.dubFile.set('None')
      self.entrydubFile.config(text='None')
      self.timeline_canvas.delete('waveAsPicImage')
      self.canvasSpectraImg=None
    else:
      self.entrydubFile.config(text=os.path.basename(str(files)))
      self.dubFile.set(str(files))
    
    self.valuesChanged = True

    self.recalculateEDLTimings()
    self.generateSpectrum(force=True)

  def updateRegionsOnDrag(self,index,timestamp):
    movestart=moveend=ots=sv=otsn=svn = False

    if index>=0:
      movestart=True
      ots = self.ticktimestamps[index]
      sv  = self.sequencedClips[index]

    if self.keepDurationCondtantVar.get():
      if index+2<=len(self.ticktimestamps):
        moveend=True
        svn  = self.sequencedClips[index+1]

    self.keepWidth=True
    if movestart:
      self.controller.updateSubclipBoundry(sv,ots,timestamp,'e',towardsMiddle=self.resizeToMiddleVar.get())
    if moveend:
      self.controller.updateSubclipBoundry(svn,ots,timestamp,'s',towardsMiddle=self.resizeToMiddleVar.get())

    self.master.synchroniseCutController(sv.rid,0)

  def timelineMouseMotion(self,e):  
    if e.y<20:
      self.timeline_canvas.config(cursor="sb_h_double_arrow")
      return
    elif 20+20<e.y<20+20+15:
      for tx,tidx in self.tickXpos:
        if tx-6-5-4<e.x<tx+6+5+4:
          self.timeline_canvas.config(cursor="sb_h_double_arrow")
          return
      else:
        tlw=self.timeline_canvas.winfo_width()
        if e.x>tlw-6-5-4:
          self.timeline_canvas.config(cursor="sb_h_double_arrow")
          return
    elif 20<e.y<20+5:
      self.timeline_canvas.config(cursor="sb_h_double_arrow")
      return
    elif 20+5<e.y<20+20:
      for tx,tidx in self.tickXpos:
        if tx-6-5-4<e.x<tx:
          self.timeline_canvas.config(cursor="right_side")
          return
        elif tx<e.x<tx+6+5+4:
          self.timeline_canvas.config(cursor="left_side")
          return
    
    self.timeline_canvas.config(cursor="arrow")

  def setDragDur(self,dur):
    self.controller.setDragDur(dur)

  def timelineMousePress(self,e):  

    ctrl  = (e.state & 0x4) != 0
    shift = (e.state & 0x1) != 0

    xpos = e.x

    if not shift:
        n= 20
        try:
            if self.imgo is None:
                self.imgo = np.mean(read_pgm(self.canvasSpectraData )[:,:,:],axis=(0,2))**2

            
            xl  = [float(x) for x in self.imgo[e.x-n:e.x+n]]
            xl  = [x* (len(xl)-abs((i-len(xl)/2)) )   for i,x in enumerate(xl)]

            am = np.argmax(xl)

            xpos = int(e.x-n+am)
            print(e.x,am,xpos)
        except Exception as imgoe:
            print(imgoe)

    pressSeconds = self.xCoordToSeconds(xpos)


    if ctrl:
      if e.type == tk.EventType.ButtonPress:
        self.ctrlDragStartSeconds = pressSeconds
      elif e.type == tk.EventType.ButtonRelease:
        if self.ctrlDragStartSeconds is not None:
          dur = abs(self.ctrlDragStartSeconds-pressSeconds)
          self.setDragDur(dur)
        self.ctrlDragStartSeconds = None
      return

    self.ctrlDragStartSeconds = None


    print(e.type)

    if e.type == tk.EventType.ButtonPress:
      if 20+20<e.y<20+20+15:
        for tx,tidx in self.tickXpos:
          if tx-6-5-4<e.x<tx+6+5+4:
            self.draggingTickIndex=tidx
            self.draggingTickOffset=e.x-tx
        else:
          endpc=0
          try:
            timelineWidth = self.timeline_canvas.winfo_width()
            endpc = self.xCoordToSeconds(timelineWidth)/self.currentTotalDuration
          except Exception as e:
            print(e)
          if endpc >= 0.999:
            tlw=self.timeline_canvas.winfo_width()
            if e.x>tlw-6-5-4:
              self.draggingTickIndex=len(self.tickXpos)
              self.draggingTickOffset=e.x-tlw
      elif e.y<20:
        self.rangeHeaderClickStart = self.currentZoomRangeMidpoint-(e.x/self.winfo_width())
      elif 20<e.y<20+5:
        self.draggingBlockIndex=0
        for tx,tidx in self.tickXpos[::-1]:
          if e.x>tx:
            self.draggingBlockIndex=tidx+1
            break
        self.timeline_canvas.itemconfigure(self.draggingblockTargetRect,fill=self.colourMap[self.sequencedClips[self.draggingBlockIndex].rid])    
      elif 20+5<e.y<20+20:
        for tx,tidx in self.tickXpos:
          if tx-6-5-4<e.x<tx:
            print(tidx,'+1')
            self.master.moveSequencedClipByIndex(tidx,+1)
            return
          elif tx<e.x<tx+6+5+4:
            print(tidx+1,'-1')
            self.master.moveSequencedClipByIndex(tidx+1,-1)
            return

      print(self.draggingTickIndex)

    elif e.type == tk.EventType.Motion:
      if self.rangeHeaderClickStart is not None:
        self.currentZoomRangeMidpoint = (e.x/self.winfo_width())+self.rangeHeaderClickStart
        self.recalculateEDLTimings()
        self.generateSpectrum()
      elif self.draggingBlockIndex is not None:
        for tx,tidx in self.tickXpos[::-1]:
          if e.x>tx:
            self.timeline_canvas.coords(self.draggingblockTargetRect, tx-5,20,tx+5,30)
            self.timeline_canvas.lift(self.draggingblockTargetRect)
            break
      elif self.draggingTickIndex is not None:
        


        self.timeline_canvas.delete('dragTick')
        self.timeline_canvas.delete('ticksLine{}'.format(self.draggingTickIndex))
        

        self.timeline_canvas.create_polygon(  xpos,    20+20+2, 
                                              xpos-7,  20+20+2+5, 
                                              xpos,    20+20+2+11,
                                              xpos+7,  20+20+2+5,
                                            fill='white',tags='dragTick')

        self.timeline_canvas.create_line(xpos, 20+0, 
                                         xpos, 200,fill='white',tags='dragTick')
        fadeDist = 0

        try:
          fadeDur  = float(self.fadeVar.get())
          fadeDist = self.secondsToXcoord(fadeDur/2)-self.secondsToXcoord(0) 
        except:
          pass

        if fadeDist > 0:
          self.timeline_canvas.create_line(xpos-fadeDist, 20+0, 
                                           xpos-fadeDist, 20+200,
                                           fill='blue',tags='dragTick')
          self.timeline_canvas.create_line(xpos+fadeDist, 20+0, 
                                           xpos+fadeDist, 20+200,
                                           fill='blue',tags='dragTick')


    elif e.type == tk.EventType.ButtonRelease:
      if self.draggingBlockIndex is not None:
        tagretId=0
        for tx,tidx in self.tickXpos[::-1]:

          if xpos>tx:
            tagretId=tidx+1
            print('tagretId=tidx',xpos,tx,tidx)
            break

        if tagretId != self.draggingBlockIndex:
          print('self.draggingBlockIndex',self.draggingBlockIndex,tagretId,tagretId-self.draggingBlockIndex)
          self.master.moveSequencedClipByIndex(self.draggingBlockIndex,tagretId-self.draggingBlockIndex)
        self.draggingBlockIndex = None
        self.timeline_canvas.coords(self.draggingblockTargetRect, -1,20,-1,30)

      if self.rangeHeaderClickStart is not None:
        self.rangeHeaderClickStart=None

      if self.draggingTickIndex is not None:
        self.updateRegionsOnDrag(self.draggingTickIndex,pressSeconds)
        self.draggingTickIndex=None
        try:
          self.blockSpectrumUpdates=False
          self.redrawTimer.cancel()
        except:
          pass
        self.restoreKeepWidthAndRecaulate()
      self.draggingTickIndex=None
      self.timeline_canvas.delete('dragTick')
      return


    self.timeline_canvas.focus_set()

    seekFailure=False
    
    if e.type in  (tk.EventType.ButtonPress,tk.EventType.Motion):

      if self.rangeHeaderClickStart is None:
        if self.currentTotalDuration is None:
          self.player.command('seek','0','absolute-percent','exact')
        else:
          seekTarget = min(max(0,self.xCoordToSeconds(xpos)),self.currentTotalDuration)
          try:
            self.player.command('seek',self.xCoordToSeconds(xpos),'absolute','exact')
          except Exception as e:
            print(e)
            try:
              self.player.command('seek',0,'absolute')
            except Exception as e2:
              seekFailure=True
              print(e2)

        if self.draggingTickIndex is None:
          for st,et,rid in self.ridListing:
            if st<pressSeconds<et:
              startoffset = pressSeconds-st
              self.master.synchroniseCutController(rid,startoffset)
              break

    if seekFailure:
      self.valuesChanged=True
      self.recalculateEDLTimings()
      self.player.command('seek',0,'absolute')


  def handleMpvTimePosChange(self,name,value):
    
    timelineWidth = self.timeline_canvas.winfo_width()
    timelineHeight = self.timeline_canvas.winfo_height()

    if value is not None:
      self.currentTimePos = value
      if self.currentTotalDuration is not None:
        currentPlaybackX = self.secondsToXcoord(self.currentTimePos) 

        if self.draggingTickIndex is None:
          self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,0,currentPlaybackX,timelineHeight )
          upperseekx = (self.currentTimePos/self.currentTotalDuration)*timelineWidth
          self.timeline_canvas.coords(self.canvasUpperSeekPointer, upperseekx-2,0,upperseekx+2,20 )
        else:
          self.timeline_canvas.coords(self.canvasSeekPointer,      -1,0,-1,timelineHeight )
          self.timeline_canvas.coords(self.canvasUpperSeekPointer, -1,0,-1,timelineHeight )


        for st,et,rid in self.ridListing:
          if st<self.currentTimePos<et:
            self.textInfo.set('offset={:0.4f}'.format(self.currentTimePos-st))
            break

  def handleMpvDurationChange(self,name,value):
    if value is not None:
      if value != self.currentTotalDuration: 
        self.currentTotalDuration=value
        self.recalculateEDLTimings()
        self.generateSpectrum()

  def valueChangeVolume(self,*args):
    self.player.volume = int(self.volumeVar.get())

  def valueChangeCallback(self,*args):
    if self.player:
      self.valuesChanged = True
      self.recalculateEDLTimings()
      self.generateSpectrum()

  def performReconfigureActions(self):    
    self.recalculateEDLTimings(seekAfter=self.currentTimePos)
    self.generateSpectrum()

  def reconfigureWindow(self,e):
    self.timeline_canvas.coords(self.canvasBackground,0,0,self.timeline_canvas.winfo_width(),20)
    self.after(1, self.performReconfigureActions)

  def restoreKeepWidthAndRecaulate(self):
    if self.draggingTickIndex is not None:
      self.redrawTimer = threading.Timer(0.8, self.restoreKeepWidthAndRecaulate)
      self.redrawTimer.start()
      return

    self.keepWidth=False
    self.blockSpectrumUpdates=False
    self.recalculateEDLTimings()
    self.generateSpectrum()

  def recalculateEDLTimings(self,rid=None,pos=None,seekAfter=None):

    try:
      self.redrawTimer.cancel()
    except:
      pass

    if self.keepWidth:
      self.blockSpectrumUpdates=True
      self.redrawTimer = threading.Timer(0.8, self.restoreKeepWidthAndRecaulate)
      self.redrawTimer.start()

    if len(self.sequencedClips)==0:
      self.timeline_canvas.delete('ticks')
      self.timeline_canvas.delete('upperticks')
      self.player.stop()
      return

    edlstr = '# mpv EDL v0\n'
    endOffset=0
    startoffset=0
    audioFilename=self.dubFile.get()

    seekTarget=None
    seekOffset =  0
    try:
      seekOffset = float(self.seekOffsetVar.get())
    except:
      pass

    

    self.timeline_canvas.delete('ticks')
    self.timeline_canvas.delete('upperticks')

    self.ticktimestamps=[]
    self.tickXpos=[]
    self.ridListing=[]

    if audioFilename is not None and os.path.exists(audioFilename):
      endOffset    = float(self.dubOffsetVar.get())
      startoffset = float(self.dubOffsetVar.get())
      audioFilename = cleanFilenameForFfmpeg(audioFilename)
      audioFilename = audioFilename.replace('\\','/').replace(':','\\:').replace("'","'\\\\\\''")
      print(audioFilename)
    else:
      audioFilename=None

    tickCounter=0

    entries=0
    totaldur=0

    for sv in self.sequencedClips:
      fn = sv.filename
      start = sv.s
      end = sv.e
      entries+=1
      totaldur+=end-start

      if rid is not None and rid==sv.rid:
        print(rid,sv.rid)
        if pos == 'e':
          seekTarget = tickCounter+(end-start)+seekOffset
        else:
          seekTarget = tickCounter+seekOffset

      if float(self.fadeVar.get()) < (end-start):
        start += (float(self.fadeVar.get())/2)
        end   -= (float(self.fadeVar.get())/2)
      tempTickCounter=tickCounter
      tickCounter += (end-start)
      self.ridListing.append( (tempTickCounter,tickCounter,sv.rid) )

      self.ticktimestamps.append(tickCounter)
      endOffset += end-start

      edlstr += '%{}%{},{},{}\n'.format(len(fn.encode('utf8')),fn,start,end-start)
    
    if self.dynamicSublipDurVar.get() and entries>0:
        self.setDragDur(totaldur/entries)

    timelineWidth = self.timeline_canvas.winfo_width()

    startpc,endpc = 0,1

    if self.currentTotalDuration is not None:
      startpc = self.xCoordToSeconds(0)/self.currentTotalDuration
      endpc   = self.xCoordToSeconds(timelineWidth)/self.currentTotalDuration

    self.timeline_canvas.coords(self.canvasZoomBG,      0,0,  timelineWidth,20 )
    self.timeline_canvas.coords(self.canvasZoomBGRange, int(startpc*timelineWidth),0,(endpc*timelineWidth),20 )

    mid = (startpc+endpc)/2

    self.timeline_canvas.coords(self.canvasZoomRangeMid, int(mid*timelineWidth),0,int(mid*timelineWidth),20 )


    lastTick=0

    if not self.keepWidth:
      self.durationForScale=tickCounter

    fadeDist = 0

    try:
      fadeDur  = float(self.fadeVar.get())
      fadeDist = self.secondsToXcoord(fadeDur/2)-self.secondsToXcoord(0) 
    except:
      pass

    idx=-1
    yo=20
    for idx,tick in enumerate(self.ticktimestamps[:-1]):

      tickrid = self.sequencedClips[idx].rid
      tickColour = self.colourMap.get(tickrid)
      if tickColour is None:
        tickColour = self.tickColours[0]
        self.colourMap[tickrid]=tickColour
        self.tickColours.append(self.tickColours.pop(0))

      utx = (tick/self.durationForScale)*timelineWidth
      self.timeline_canvas.create_line(utx,0,utx,20,fill='white',tags='upperticks')
      self.timeline_canvas.create_rectangle(utx-5, 0,
                                            utx+5, 4,
                                            fill='white',tags='upperticks')


      txl = self.secondsToXcoord(lastTick)
      tx  = self.secondsToXcoord(tick)

      self.tickXpos.append((tx,idx))

      self.timeline_canvas.create_rectangle(txl, yo+0,
                                            tx,  yo+5,
                                            fill=tickColour,tags='ticks')
      
      self.timeline_canvas.create_polygon(tx-6-5,    yo+9, 
                                          tx-6-5,    yo+9+10, 
                                          tx-4,      yo+9+5, 
                                          fill='grey',tags='ticks')
      
      self.timeline_canvas.create_polygon(tx+6+5,    yo+9, 
                                          tx+6+5,    yo+9+10, 
                                          tx+4,      yo+9+5, 
                                          fill='grey',tags='ticks')

      print(self.draggingTickIndex,idx)
      self.timeline_canvas.create_rectangle(tx-6-5-4, yo+20,
                                            tx+6+5+4, yo+20+15,
                                            outline='grey',tags='ticks')

      self.timeline_canvas.create_polygon(  tx,    yo+20+2, 
                                            tx-7,  yo+20+2+5, 
                                            tx,    yo+20+2+11,
                                            tx+7,  yo+20+2+5,

                                          fill='white',tags='ticks')

      self.timeline_canvas.create_line(tx, yo+0, 
                                       tx, yo+200,
                                       fill='white',tags=['ticks','ticksLine{}'.format(idx)])


      if fadeDist > 0:
        self.timeline_canvas.create_line(tx-fadeDist, yo+0, 
                                         tx-fadeDist, yo+200,
                                         fill='blue',tags=['ticks','ticksLine{}'.format(idx)],dash=(2,1))
        self.timeline_canvas.create_line(tx+fadeDist, yo+0, 
                                         tx+fadeDist, yo+200,
                                         fill='blue',tags=['ticks','ticksLine{}'.format(idx)],dash=(2,1))

      self.timeline_canvas.create_line(tx-6-5-4, yo+5, 
                                       tx-6-5-4, yo+20,
                                       fill='grey',tags='ticks')
      
      self.timeline_canvas.create_line(tx+6+5+4, yo+5, 
                                       tx+6+5+4, yo+20,
                                       fill='grey',tags='ticks')

      self.tempRangePreviewDurationLabel = self.timeline_canvas.create_text(int((txl+tx)/2), 50, text='{:0.3f}'.format(tick-lastTick),fill="#69bfdb",tags='ticks')
      
      lastTick=tick

    tx = timelineWidth

    if endpc>0.999:
      self.timeline_canvas.create_rectangle(tx-6-5-4, yo+20,
                                            tx+6+5+4, yo+20+15,
                                            outline='grey',tags='ticks')

      self.timeline_canvas.create_polygon(  tx,    yo+20+2, 
                                            tx-7,  yo+20+2+5, 
                                            tx,    yo+20+2+11,
                                            tx+7,  yo+20+2+5,

                                          fill='white',tags='ticks')



    self.timeline_canvas.create_line(0,             yo+20, 
                                     timelineWidth, yo+20,
                                     fill='grey',tags='ticks')

    tick = self.xCoordToSeconds(timelineWidth)
    txl = self.secondsToXcoord(lastTick)

    self.tempRangePreviewDurationLabel = self.timeline_canvas.create_text(int((txl+tx)/2), 50, text='{:0.3f}'.format(tick-lastTick),fill="#69bfdb",tags='ticks')
      

    tickrid = self.sequencedClips[idx+1].rid
    tickColour = self.colourMap.get(tickrid)
    if tickColour is None:
      tickColour = self.tickColours[0]
      self.colourMap[tickrid]=tickColour
      self.tickColours.append(self.tickColours.pop(0))

    self.timeline_canvas.create_rectangle(txl, yo+0,
                                          tx,  yo+5,
                                          fill=tickColour,tags='ticks')

    self.timeline_canvas.tag_lower('ticks', self.canvasSeekPointer)

    

    edlBytes = edlstr.encode('utf8')

    if self.valuesChanged or edlBytes != self.edlBytes:
      self.valuesChanged = False

      if seekAfter is not None:
        seekAfter = max(min(seekAfter,endOffset),0)
        self.player.start=str(seekAfter)

      if seekTarget is not None:
        seekTarget = max(min(seekTarget,endOffset),0)
        self.player.start=str(seekTarget) 

      self.edlBytes = edlBytes
      self.player._python_streams = {}
      @self.player.python_stream('edlStream',len(self.edlBytes))
      def edlstream():
        yield self.edlBytes

      self.player.play('python://edlStream')

    if audioFilename is not None:

      audioOverrideBias = float(self.mixVar.get())
      weightDub    = audioOverrideBias
      weightSource = 1-audioOverrideBias

      origpauseState = self.player.pause
      self.player.pause = True
      self.player.lavfi_complex="amovie=filename='{fn}',atrim=start={starts}:end={endts},asetpts=PTS-STARTPTS[ao]".format(fn=audioFilename,starts=startoffset,endts=endOffset,wd=weightDub,ws=weightSource)
      self.player.pause = origpauseState
    else:
      origpauseState = self.player.pause
      self.player.pause = True
      self.player.lavfi_complex=''
      self.player.pause = origpauseState

class CutSpecificationPlanner(tk.Toplevel):

  def __init__(self, master=None, controller=None, *args):
    tk.Toplevel.__init__(self, master)
    
    self.title('Audio Sync Specification Planner')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,400)


    self.loadbutton = ttk.Button(self,text='Load Audio',command=self.selectFile)
    self.loadbutton.grid(row=0,column=0,sticky='nesw',padx=0,pady=0,columnspan=9)


    self.playerFrame = ttk.Frame(self,style='PlayerFrame.TFrame',height='200', width='200')
    self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0,columnspan=9)

    self.timeline_canvas = tk.Canvas(self,width=200, height=130, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.timeline_canvas.grid(row=2,column=0,columnspan=9,sticky="nesw")
    
    self.timeline_canvas.bind("<Button-1>", self.timelineMousePress)


    self.canvasSeekPointer = self.timeline_canvas.create_line(0, 0, 0, self.timeline_canvas.winfo_height(),fill="white")

    self.playerwid = self.playerFrame.winfo_id()

    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=1)
    self.rowconfigure(2, weight=0)

    self.columnconfigure(0, weight=1)

    self.currentTimePos=None
    self.currentTotalDuration=None

    self.player = mpv.MPV(loop='inf',
                          mute=False,
                          volume=50,
                          autofit_larger='1280', wid=str(self.playerwid))

    self.player.lavfi_complex="[aid1]asplit[as1][as2],[as1]showcqt=s=640x518[vo],[as2]anull[ao]"

    self.attributes('-topmost', True)
    self.update()

    self.player.observe_property('time-pos', self.handleMpvTimePosChange)
    self.player.observe_property('duration', self.handleMpvDurationChange)



    def quitFunc(key_state, key_name, key_char):
    
      try:
        self.player.unobserve_property('time-pos', self.handleMpvTimePosChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('duration', self.handleMpvDurationChange)
      except Exception as e:
        print(e)

      try:
        self.player.unobserve_property('af-metadata', self.handleMpvafMetdata)
      except Exception as e:
        print(e)

      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()
      self.attributes('-topmost', False)
      self.update()




  def timelineMousePress(self,e):  
    self.player.command('seek',str((e.x/self.timeline_canvas.winfo_width())*100),'absolute-percent','exact')


  def handleMpvafMetdata(self,name,value):
    print(name,value)

  def handleMpvTimePosChange(self,name,value):
    
    timelineWidth = self.timeline_canvas.winfo_width()
    timelineHeight = self.timeline_canvas.winfo_height()

    if value is not None:
      self.currentTimePos = value
      if self.currentTotalDuration is not None:
        currentPlaybackX = int((self.currentTimePos/self.currentTotalDuration)*timelineWidth)
        self.timeline_canvas.coords(self.canvasSeekPointer, currentPlaybackX,0,currentPlaybackX,timelineHeight )

  def handleMpvDurationChange(self,name,value):
    if value is not None:
      self.currentTotalDuration=value

  def selectFile(self):
    self.file = askopenfilename(multiple=False,filetypes=[('All files','*.*',)])
    if os.path.isfile(self.file):
      self.player.play(self.file)

class Tooltip:

  def __init__(self, widget,
               *,
               bg='#a7d9ea',
               fg='#282828',
               pad=(5, 3, 5, 3),
               text='widget info',
               waittime=400,
               wraplength=450):

    self.waittime = waittime  # in miliseconds, originally 500
    self.wraplength = wraplength  # in pixels, originally 180
    self.widget = widget
    self.text = text
    self.widget.bind("<Enter>", self.onEnter)
    self.widget.bind("<Leave>", self.onLeave)
    self.widget.bind("<ButtonPress>", self.onLeave)
    self.bg = bg
    self.fg=fg
    self.pad = pad
    self.id = None
    self.tw = None

  def onEnter(self, event=None):
    self.schedule()

  def onLeave(self, event=None):
    self.unschedule()
    self.hide()

  def schedule(self):
    self.unschedule()
    self.id = self.widget.after(self.waittime, self.show)

  def unschedule(self):
    id_ = self.id
    self.id = None
    if id_:
      self.widget.after_cancel(id_)

  def show(self):
    def tip_pos_calculator(widget, label,
                           *,
                           tip_delta=(10, 5), pad=(5, 3, 5, 3)):

        w = widget

        s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

        width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                         pad[1] + label.winfo_reqheight() + pad[3])

        mouse_x, mouse_y = w.winfo_pointerxy()

        x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
        x2, y2 = x1 + width, y1 + height

        x_delta = x2 - s_width
        if x_delta < 0:
          x_delta = 0
        y_delta = y2 - s_height
        if y_delta < 0:
          y_delta = 0

        offscreen = (x_delta, y_delta) != (0, 0)

        if offscreen:
          if x_delta:
            x1 = mouse_x - tip_delta[0] - width
          if y_delta:
            y1 = mouse_y - tip_delta[1] - height

        offscreen_again = y1 < 0  # out on the top

        if offscreen_again:
          y1 = 0

        return x1, y1

    bg = self.bg
    pad = self.pad
    widget = self.widget

    # creates a toplevel window
    self.tw = tk.Toplevel(widget)

    # Leaves only the label and removes the app window
    self.tw.wm_overrideredirect(True)

    win = tk.Frame(self.tw,
                   background=bg,
                   borderwidth=0)
    label = tk.Label(win,
                      text=self.text,
                      justify=tk.LEFT,
                      background=bg,
                      relief=tk.SOLID,
                      borderwidth=0,
                      wraplength=self.wraplength)

    label.grid(padx=(pad[0], pad[2]),
               pady=(pad[1], pad[3]),
               sticky=tk.NSEW)
    win.grid()

    x, y = tip_pos_calculator(widget, label)

    self.tw.wm_geometry("+%d+%d" % (x, y))

  def hide(self):
    tw = self.tw
    if tw:
      tw.destroy()
    self.tw = None

class V360HeadTrackingModal(tk.Toplevel):
  def __init__(self, master=None, controller=None, filterReference=None, *args):
    tk.Toplevel.__init__(self, master)
    self.title('Record VR head motions')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,600)

    self.labelInstructions = ttk.Label(self)
    self.labelInstructions.config(text='Click in video to capture mouse, press Space to start recording motions.',anchor="center")
    self.labelInstructions.grid(row=0,column=0,sticky='new',padx=0,pady=0)

    self.playerFrame = ttk.Frame(self,style='PlayerFrame.TFrame',height='200', width='200')
    self.playerFrame.grid(row=1,column=0,sticky='nesw',padx=0,pady=0)

    self.applyButton = ttk.Button(self, text='Apply')
    self.applyButton.grid(row=2,column=0,sticky='nesw',padx=5,pady=5)

    self.columnconfigure(0, weight=1)
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=1)
    self.rowconfigure(2, weight=0)

    self.playerwid = self.playerFrame.winfo_id()


class VoiceActivityDetectorModal(tk.Toplevel):


  def __init__(self, master=None,controller=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Detect voice activity')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,40)
    self.controller=controller
    self.columnconfigure(0, weight=0)
    self.columnconfigure(1, weight=1)

    self.labelSampleLength = ttk.Label(self)
    self.labelSampleLength.config(text='Sample length (ms) [10,20,30]')
    self.labelSampleLength.grid(row=0,column=0,sticky='new',padx=5,pady=5)
    self.varSampleLength   = tk.StringVar(self,'20')
    self.entrySampleLength = ttk.Entry(self,textvariable=self.varSampleLength)
    self.entrySampleLength.grid(row=0,column=1,sticky='new',padx=5,pady=5)


    self.labelAggresiveness = ttk.Label(self)
    self.labelAggresiveness.config(text='Recognition Aggressiveness [0.0-3.0]')
    self.labelAggresiveness.grid(row=2,column=0,sticky='new',padx=5,pady=5)

    self.varAggresiveness   = tk.StringVar(self,'3')
    self.entryAggresiveness  = ttk.Entry(self,textvariable=self.varAggresiveness)
    self.entryAggresiveness.grid(row=2,column=1,sticky='new',padx=5,pady=5)


    self.labelWindowLength = ttk.Label(self)
    self.labelWindowLength.config(text='Rolling confidence window length')
    self.labelWindowLength.grid(row=3,column=0,sticky='new',padx=5,pady=5)

    self.varWindowLength   = tk.StringVar(self,'1.5')
    self.entryWindowLength  = ttk.Entry(self,textvariable=self.varWindowLength)
    self.entryWindowLength.grid(row=3,column=1,sticky='new',padx=5,pady=5)


    self.labelMinimimDuration = ttk.Label(self)
    self.labelMinimimDuration.config(text='Minumum speech duration')
    self.labelMinimimDuration.grid(row=4,column=0,sticky='new',padx=5,pady=5)

    self.varMinimimDuration   = tk.StringVar(self,'2.0')
    self.entryMinimimDuration  = ttk.Entry(self,textvariable=self.varMinimimDuration)
    self.entryMinimimDuration.grid(row=4,column=1,sticky='new',padx=5,pady=5)


    self.labelBridgeDistance = ttk.Label(self)
    self.labelBridgeDistance.config(text='Bridge gaps of at most (s)')
    self.labelBridgeDistance.grid(row=5,column=0,sticky='new',padx=5,pady=5)

    self.varBridgeDistance  = tk.StringVar(self,'2.0')
    self.entryBridgeDistance = ttk.Entry(self,textvariable=self.varBridgeDistance)
    self.entryBridgeDistance.grid(row=5,column=1,sticky='new',padx=5,pady=5)


    self.labelCondidenceStart = ttk.Label(self)
    self.labelCondidenceStart.config(text='Confidence to trigger start speech')
    self.labelCondidenceStart.grid(row=6,column=0,sticky='new',padx=5,pady=5)

    self.varCondidenceStart    = tk.StringVar(self,'98.0')
    self.entryCondidenceStart   = ttk.Entry(self,textvariable=self.varCondidenceStart )
    self.entryCondidenceStart .grid(row=6,column=1,sticky='new',padx=5,pady=5)


    self.labelCondidenceEnd = ttk.Label(self)
    self.labelCondidenceEnd.config(text='Confidence to trigger end speech')
    self.labelCondidenceEnd.grid(row=7,column=0,sticky='new',padx=5,pady=5)

    self.varCondidenceEnd    = tk.StringVar(self,'80.0')
    self.entryCondidenceEnd   = ttk.Entry(self,textvariable=self.varCondidenceEnd )
    self.entryCondidenceEnd .grid(row=7,column=1,sticky='new',padx=5,pady=5)

    self.labelMinZcr= ttk.Label(self)
    self.labelMinZcr.config(text='Minimum zero crossing rate (-1 to skip)')
    self.labelMinZcr.grid(row=8,column=0,sticky='new',padx=5,pady=5)

    self.varMinZcr    = tk.StringVar(self,'-1')
    self.entryMinZcr   = ttk.Entry(self,textvariable=self.varMinZcr )
    self.entryMinZcr .grid(row=8,column=1,sticky='new',padx=5,pady=5)

    self.labelMaxZcr= ttk.Label(self)
    self.labelMaxZcr.config(text='Maximum zero crossing rate (-1 to skip)')
    self.labelMaxZcr.grid(row=9,column=0,sticky='new',padx=5,pady=5)

    self.varMaxZcr    = tk.StringVar(self,'-1')
    self.entryMaxZcr   = ttk.Entry(self,textvariable=self.varMaxZcr )
    self.entryMaxZcr .grid(row=9,column=1,sticky='new',padx=5,pady=5)

    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Scan and Add SubClips',command=self.addSublcips)
    self.downloadCmd.grid(row=10,column=0,columnspan=2,sticky='nesw')

    self.resizable(False, False) 

  def addSublcips(self):
    sampleLength    = float(self.varSampleLength.get())
   
    aggresiveness   = float(self.varAggresiveness.get())
    windowLength    = float(self.varWindowLength.get())
    minimimDuration = float(self.varMinimimDuration.get())
    bridgeDistance  = float(self.varBridgeDistance.get())
    condidenceStart = float(self.varCondidenceStart.get())
    condidenceEnd   = float(self.varCondidenceEnd.get())
    minZcr          = float(self.varMinZcr.get())
    maxZcr          = float(self.varMaxZcr.get())

    self.controller.runVoiceActivityDetection(sampleLength,aggresiveness,windowLength,minimimDuration,bridgeDistance,condidenceStart,condidenceEnd,minZcr,maxZcr)
    self.destroy()

class TimestampModal(tk.Toplevel):
  
  def __init__(self, master=None,controller=None,initialValue='',videoDuration=0, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Cut the video at these timestamps')
    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.minsize(600,40)
    self.controller=controller
    self.videoDuration=videoDuration


    self.columnconfigure(0, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=2)


    self.labelInstruction = ttk.Label(self)
    self.labelInstruction.config(text='Add timestamp in "HH:MM:SS.ss - HH:MM:SS.ss" format')
    self.labelInstruction.grid(row=0,column=0,sticky='new',padx=5,pady=5)

    self.varTimestamps   = tk.StringVar(self,initialValue)
    self.entryTimestamps = ttk.Entry(self,textvariable=self.varTimestamps)
    self.entryTimestamps.grid(row=1,column=0,sticky='new',padx=5,pady=5)
    self.varTimestamps.trace('w',self.valueUpdated)

    self.varnegativeTS = tk.IntVar(self,0)
    self.checknegativeTS =  ttk.Checkbutton(self,text='Interpret as negative timestamps from end of clip.',var=self.varnegativeTS)
    self.checknegativeTS.grid(row=2,column=0,sticky='new',padx=5,pady=5)
    self.varnegativeTS.trace('w',self.valueUpdated)

    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Add SubClip',command=self.addSublcip,state='disabled')
    self.downloadCmd.grid(row=3,column=0,sticky='nesw')
    self.rowconfigure(5, weight=1)

    self.resizable(False, False) 

    self.entryTimestamps.focus()
    self.entryTimestamps.select_range(0, 'end')
    self.entryTimestamps.icursor('end')

    self.start = None
    self.end   = None

    self.valueUpdated()

  def valueUpdated(self,*args):
    self.start = None
    self.end   = None
    isIsNegative = bool(self.varnegativeTS.get())
    self.downloadCmd.config(state='disabled')
    rawRange = self.varTimestamps.get()

    multipliers = [1,60,60*60,60*60*60]

    startTS=0
    endTS=0

    if rawRange is not None:
      startText = ""
      endText   = ""

      isStart = True
      for char in rawRange.strip():
        if char in '1234567890.:':
          if isStart:
            startText += char
          else:
            endText += char
        else:
          isStart=False

      if len(startText)>0 and len(endText)>0:
        for mult,val in zip(multipliers,startText.split(':')[::-1]):
          startTS += mult*float(val)
        for mult,val in zip(multipliers,endText.split(':')[::-1]):
          endTS += mult*float(val)


    if (startTS != 0 or endTS != 0) and endTS != startTS:
      self.start = startTS
      self.end   = endTS     
      if isIsNegative:
        self.start = self.videoDuration-startTS
        self.end   = self.videoDuration-endTS
      self.start,self.end = sorted([self.start,self.end])
      self.downloadCmd.config(state='normal',text='Add SubClip from {}s to {}s ({}s)'.format(self.start,self.end,self.end-self.start))
    else:
      self.downloadCmd.config(state='disabled',text='Add SubClip')

  def addSublcip(self):
    if self.start != None and self.end != None:
      self.controller.addNewSubclip(max(self.start,0), min(self.end,self.videoDuration))


youtubeDLModalState = {
  'varPlayListLimit':'',
  'varUsername':'',
  'varPassword':'',
  'useCookies':0,
  'varBrowserCookies':''

}

class YoutubeDLModal(tk.Toplevel):
  
  def __init__(self, master=None,controller=None,initialUrl='', *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Download a video with youtube-dlp')
    self.style = ttk.Style()
    self.style.theme_use('clam')

    self.minsize(600,140)
    self.controller=controller

    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)

    self.labelUrl = ttk.Label(self)
    self.labelUrl.config(text='Url')
    self.labelUrl.grid(row=0,column=0,sticky='new',padx=5,pady=5)
    self.varUrl   = tk.StringVar(self,initialUrl)
    self.entryUrl = ttk.Entry(self,textvariable=self.varUrl)
    self.entryUrl.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.labelPlaylistLimit = ttk.Label(self)
    self.labelPlaylistLimit.config(text='Max download count')
    self.labelPlaylistLimit.grid(row=1,column=0,sticky='new',padx=5,pady=5)
    self.varPlayListLimit   = tk.StringVar(self,'')
    self.entryPlayListLimit = ttk.Entry(self,textvariable=self.varPlayListLimit)
    self.entryPlayListLimit.grid(row=1,column=1,sticky='new',padx=5,pady=5)

    self.labelUsername = ttk.Label(self)
    self.labelUsername.config(text='Username')
    self.labelUsername.grid(row=2,column=0,sticky='new',padx=5,pady=5)
    self.varUsername   = tk.StringVar(self,'')
    self.entryUsername = ttk.Entry(self,textvariable=self.varUsername)
    self.entryUsername.grid(row=2,column=1,sticky='new',padx=5,pady=5)

    self.labelPassword = ttk.Label(self)
    self.labelPassword.config(text='Password')
    self.labelPassword.grid(row=3,column=0,sticky='new',padx=5,pady=5)
    self.varPassword   = tk.StringVar(self,'')
    self.entryPassword = ttk.Entry(self,textvariable=self.varPassword)
    self.entryPassword.grid(row=3,column=1,sticky='new',padx=5,pady=5)

    self.labelCookies = ttk.Label(self)
    self.labelCookies.config(text='Use cookies.txt')
    self.labelCookies.grid(row=4,column=0,sticky='new',padx=5,pady=5)
    
    self.useCookies = tk.IntVar(self,0)
    self.entryCookies =  ttk.Checkbutton(self,text='Send credentials from cookies.txt',var=self.useCookies)
    if not os.path.exists('cookies.txt'):
      self.entryCookies['state']='disabled'
      self.entryCookies['text']='cookies.txt not found.'

    self.entryCookies.grid(row=4,column=1,sticky='new',padx=5,pady=5)

    self.labelBrowserCookies = ttk.Label(self)
    self.labelBrowserCookies.config(text='Get Cookies from Browser')
    self.labelBrowserCookies.grid(row=5,column=0,sticky='new',padx=5,pady=5)
    self.varBrowserCookies   = tk.StringVar(self,'')
    self.entryBrowserCookies =  ttk.Combobox(self,textvariable=self.varBrowserCookies)
    self.entryBrowserCookies.config(values=['brave', 'chrome', 'chromium', 'edge', 'firefox', 'opera', 'safari', 'vivaldi'])
    self.entryBrowserCookies.grid(row=5,column=1,sticky='new',padx=5,pady=5)


    self.labelQualitySort = ttk.Label(self)
    self.labelQualitySort.config(text='Video quality selection rule')
    self.labelQualitySort.grid(row=6,column=0,sticky='new',padx=5,pady=5)
    self.varQualitySort   = tk.StringVar(self,'default')
    self.entryQualitySort =  ttk.Combobox(self,textvariable=self.varQualitySort)
    self.entryQualitySort.config(values=['default', 'bestvideo+bestaudio/best', 'bestvideo*+bestaudio/best', 'best'])
    self.entryQualitySort.grid(row=6,column=1,sticky='new',padx=5,pady=5)


    self.downloadCmd = ttk.Button(self)
    self.downloadCmd.config(text='Download',command=self.download)
    self.downloadCmd.grid(row=7,column=0,columnspan=2,sticky='nesw')
    self.rowconfigure(5, weight=1)

    self.entryUrl.focus()
    self.entryUrl.select_range(0, 'end')
    self.entryUrl.icursor('end')

    self.resizable(False, False) 

  def download(self):
    url=self.varUrl.get()
    fileLimit=0
    username=self.varUsername.get()
    password=self.varPassword.get()
    useCookies = bool(self.useCookies.get())
    browserCookies=self.varBrowserCookies.get()
    qualitySort=self.varQualitySort.get()

    try:
      fileLimit = int(float(self.varPlayListLimit.get()))
    except Exception as e:
      print(e)
    self.controller.loadVideoYTdlCallback(url,fileLimit,username,password,useCookies,browserCookies,qualitySort)
    self.destroy()



class PerfectLoopScanModal(tk.Toplevel):
  
  def __init__(self, master=None,useRange=False,controller=None,starttime=0,endtime=0, *args):

    tk.Toplevel.__init__(self, master)

    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.style.configure ("warning.TLabel", font = ('Sans','10','bold'),textcolor='red')

    self.grab_set()
    self.title('Scan for perfect loops')


    self.controller=controller

    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=0)
    self.rowconfigure(5, weight=0)
    self.rowconfigure(6, weight=0)
    self.rowconfigure(7, weight=0)
    
    self.useRange = useRange

    initThreshold    = 10
    initMidThreshold = 18
    initMinLength    = 1.5
    initMaxLength    = 4.0
    initTimeSkip     = 1.0

    r=0

    self.labelWarning = ttk.Label(self)
    self.labelWarning.config(text='Experimental - can take a very long time and still return no loops.',style='warning.TLabel')
    self.labelWarning.grid(row=r,column=0,sticky='new',padx=5,pady=5,columnspan=2)


    r+=1

    if self.useRange:

      self.labelStartTime = ttk.Label(self)
      self.labelStartTime.config(text='Scan start timestamp')
      self.labelStartTime.grid(row=r,column=0,sticky='new',padx=5,pady=5)

      self.varStartTime   = tk.StringVar(self,starttime)
      self.entryStartTime = ttk.Entry(self,textvariable=self.varStartTime)
      self.entryStartTime.grid(row=r,column=1,sticky='new',padx=5,pady=5)

      r+=1

      self.labelEndTime = ttk.Label(self)
      self.labelEndTime.config(text='Scan end timestamp')
      self.labelEndTime.grid(row=r,column=0,sticky='new',padx=5,pady=5)

      self.varEndTime   = tk.StringVar(self,endtime)
      self.entryEndTime = ttk.Entry(self,textvariable=self.varEndTime)
      self.entryEndTime.grid(row=r,column=1,sticky='new',padx=5,pady=5)

      r += 1


    self.labelThreshold = ttk.Label(self)
    self.labelThreshold.config(text='Max loop difference threshold')
    self.labelThreshold.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varThreshold   = tk.StringVar(self,initThreshold)
    self.entryThreshold = ttk.Entry(self,textvariable=self.varThreshold)
    self.entryThreshold.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelMidThreshold = ttk.Label(self)
    self.labelMidThreshold.config(text='Min inbetween threshold')
    self.labelMidThreshold.grid(row=r,column=0,sticky='new',padx=5,pady=5)


    self.varMidThreshold   = tk.StringVar(self,initMidThreshold)
    self.entryMidThreshold = ttk.Entry(self,textvariable=self.varMidThreshold)
    self.entryMidThreshold.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelIfdMode = ttk.Label(self)
    self.labelIfdMode.config(text='IFD offset mode')
    self.labelIfdMode.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varIfdMode   = tk.IntVar(self,1)
    self.entryIfdMode = ttk.Checkbutton(self,text='Treat thresholds as offset from mean inter-frame-distance',var=self.varIfdMode)
    self.entryIfdMode.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelMinLength = ttk.Label(self)
    self.labelMinLength.config(text='Min loop length')
    self.labelMinLength.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varMinLength   = tk.StringVar(self,initMinLength)
    self.entryMinLength = ttk.Entry(self,textvariable=self.varMinLength)
    self.entryMinLength.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelMaxLength = ttk.Label(self)
    self.labelMaxLength.config(text='Max loop length')
    self.labelMaxLength.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varMaxLength   = tk.StringVar(self,initMaxLength)
    self.entryMaxLength = ttk.Entry(self,textvariable=self.varMaxLength)
    self.entryMaxLength.grid(row=r,column=1,sticky='new',padx=5,pady=5)


    r += 1

    self.labelTimeSkip = ttk.Label(self)
    self.labelTimeSkip.config(text='Time to skip between loops')
    self.labelTimeSkip.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varTimeSkip   = tk.StringVar(self,initTimeSkip)
    self.entryTimeSkip = ttk.Entry(self,textvariable=self.varTimeSkip)
    self.entryTimeSkip.grid(row=r,column=1,sticky='new',padx=5,pady=5)

    r += 1

    self.labelfilterMode = ttk.Label(self)
    self.labelfilterMode.config(text='Final match selection mode')
    self.labelfilterMode.grid(row=r,column=0,sticky='new',padx=5,pady=5)

    self.varfilterMode   = tk.StringVar(self,'bestFirst')
    self.entryfilterMode = ttk.Combobox(self)
    self.entryfilterMode.config(textvariable=self.varfilterMode)
    self.entryfilterMode.config(values=['bestFirst','earliestFirst'])
    self.entryfilterMode.grid(row=r,column=1,sticky='new',padx=5,pady=5)


    r += 1

    self.scanCmd = ttk.Button(self)
    self.scanCmd.config(text='Scan for loops',command=self.scanForLoops)
    self.scanCmd.grid(row=r,column=0,columnspan=2,sticky='nesw')
    self.rowconfigure(r, weight=1)

    self.resizable(False, False) 

  def scanForLoops(self):
    threshold = float(self.varThreshold.get())
  
    midThreshold = float(self.varMidThreshold.get())
    minLength = float(self.varMinLength.get())
    maxLength = float(self.varMaxLength.get())
    timeSkip  = float(self.varTimeSkip.get())
    ifdmode   = bool(self.varIfdMode.get())
    selectionMode = self.varfilterMode.get()

    

    useRange=self.useRange
    if self.useRange:
      rangeStart=float(self.varStartTime.get())
      rangeEnd=float(self.varEndTime.get())
    else:
      rangeStart=None
      rangeEnd=None

    self.controller.submitFullLoopSearch(midThreshold=midThreshold,
                                         minLength=minLength,
                                         maxLength=maxLength,
                                         timeSkip=timeSkip,
                                         threshold=threshold,
                                         addCuts=True,
                                         useRange=useRange,
                                         rangeStart=rangeStart,
                                         ifdmode=ifdmode,
                                         rangeEnd=rangeEnd,
                                         selectionMode=selectionMode)
    self.destroy()


class SubtitleExtractionModal(tk.Toplevel):

  def __init__(self, master=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Extract Subtitles')
    self.minsize(600,150)
    


    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=0)
    self.rowconfigure(5, weight=1)
    self.rowconfigure(6, weight=0)
    

    self.labelFilename = ttk.Label(self)
    self.file=''
    self.labelFilename.config(text='Source file')
    self.labelFilename.grid(row=0,column=0,sticky='new',padx=5,pady=5)

    self.varFilename   = tk.StringVar()
    self.varFilename.set('None')
    self.entryFilename = ttk.Button(self)
    self.entryFilename.config(text='File: {}'.format(self.varFilename.get()[-20:]),command=self.selectFile)
    self.entryFilename.grid(row=0,column=1,sticky='new',padx=5,pady=5)

    self.labelStream = ttk.Label(self)
    self.labelStream.config(text='Stream Index')
    self.labelStream.grid(row=1,column=0,sticky='new',padx=5,pady=5)

    self.varStream   = tk.StringVar()
    self.varStream.trace('w',self.streamChanged)
    self.entryStream = ttk.Combobox(self)
    self.entryStream.config(textvariable=self.varStream,state='disabled')
    self.entryStream.config(values=[])
    self.entryStream.grid(row=1,column=1,sticky='new',padx=5,pady=5)

    self.stripXmlLabel = ttk.Label(self)
    self.stripXmlLabel.config(text='Strip hardcoded font and size attributes if present')
    self.stripXmlLabel.grid(row=2,column=0,sticky='new',padx=0,pady=0)
    self.stripXmlVar   = tk.IntVar(self,0)
    self.stripXmlVar.set(1)
    self.stripXmlCheck =  ttk.Checkbutton(self,text='',var=self.stripXmlVar)
    self.stripXmlCheck.grid(row=2,column=1,sticky='new',padx=0,pady=0)

    self.labelOutputName = ttk.Label(self)
    self.labelOutputName.config(text='Output Name:')
    self.labelOutputName.grid(row=3,column=0,sticky='new',padx=5,pady=5)

    self.labelOutputFileName = ttk.Label(self)
    self.labelOutputFileName.config(text='None')
    self.labelOutputFileName.grid(row=3,column=1,sticky='new',padx=5,pady=5)

    self.labelProgress = ttk.Label(self)
    self.labelProgress.config(text='Idle')
    self.labelProgress.grid(row=4,column=0,columnspan=2,sticky='new',padx=5,pady=5)


    self.extractCmd = ttk.Button(self)
    self.extractCmd.config(text='Extract',command=self.extract,state='disabled')
    self.extractCmd.grid(row=5,column=0,columnspan=2,sticky='nesw')


    self.statusProgress = ttk.Progressbar(self)
    self.statusProgress['value'] = 0
    self.statusProgress.grid(row=6,column=0,columnspan=2,sticky='nesw')
    self.statusProgress.config(style="Green.Horizontal.TProgressbar")


    self.resizable(False, False) 

    self.outputFilename=''
    self.streamInd=0
    self.subtitleThread=None
    self.close=False

    self.protocol("WM_DELETE_WINDOW", self.closeThreads)


  def selectFile(self):
    self.file = askopenfilename(multiple=False,filetypes=[('All files','*.*',)])
    subn=0
    self.statusProgress['value']=0
    if os.path.isfile(self.file):
      outs,errs = sp.Popen(['ffmpeg','-i',cleanFilenameForFfmpeg(self.file)],stderr=sp.PIPE).communicate()
      print(outs,errs)
      self.subs=[]
      for line in errs.split(b'\n'):
        if b'Stream #' in line and b'Subtitle' in line:
          self.subs.append( str(subn) +' - ' + line.strip().decode('utf8',errors='ignore'))
          subn+=1

      self.entryStream.config(values=self.subs)
      if len(self.subs)>0:
        self.varStream.set(self.subs[0])
        self.entryStream.config(state='normal')
        self.entryFilename.config(text='File: {}'.format(self.file[-100:]))
      else:
        self.varStream.set('')
        self.entryStream.config(state='disabled')
        self.entryFilename.config(text='File: None')
    else:
        self.varStream.set('')
        self.entryStream.config(state='disabled')      
        self.entryFilename.config(text='File: None')

  def streamChanged(self,*args):
    self.outputFilename=''
    self.statusProgress['value']=0
    if os.path.isfile(self.file) and self.varStream.get().split('-')[0].strip().isdigit():
      self.extractCmd.config(state='normal')
      filename = os.path.split(self.file)[-1]
      filename = os.path.splitext(filename)[0]
      streamName = self.varStream.get().split(':')
      self.streamInd = int(streamName[0].split(' ')[0])
      self.outputFilename = ''.join([x for x in filename+'.subs.'+str(self.streamInd)+'.'+streamName[1]+'.srt' if x in string.ascii_letters+string.digits+'. '])
      self.labelOutputFileName.config(text=self.outputFilename)
    else:
      self.extractCmd.config(state='disabled')
      if len(self.subs)==0:
        self.labelOutputFileName.config(text='No subtitle track found')
      else:
        self.labelOutputFileName.config(text='None')

  def watchsubtitleProgress(self):
    l=b''
    expectedLength=None
    self.statusProgress['value']=0
    while 1:
      c = self.proc.stderr.read(1)
      if self.close:
        break
      if len(c)==0:
        break
      if c in b'\n\r':
        print(l)
        try:
          if b'Duration: ' in l and expectedLength is None:
            expectedLength=l.split(b'Duration: ')[1].split(b',')[0]
            expectedLength = datetime.strptime(expectedLength.decode('utf8'),'%H:%M:%S.%f')
            expectedLength = expectedLength.microsecond/1000000 + expectedLength.second + expectedLength.minute*60 + expectedLength.hour*3600
          elif b'time=' in l and expectedLength is not None:
            currentReadPos=l.split(b'time=')[1].split(b' ')[0]
            currentReadPos = datetime.strptime(currentReadPos.decode('utf8'),'%H:%M:%S.%f')
            currentReadPos = currentReadPos.microsecond/1000000 + currentReadPos.second + currentReadPos.minute*60 + currentReadPos.hour*3600
            if not self.close:
              self.statusProgress['value']=(currentReadPos/expectedLength)*100
          self.labelProgress.config(text=l)
        except Exception as e:
          print(e)
        l=b''
      else:
        l+=c
    if not self.close:

      if self.stripXmlVar.get()==1:
        regex = r"size=\"[^\"]*\"|face=\"[^\"]*\""

        try:
          subtext = open(self.outputFilename,'r').read()
          subtext = re.sub(
             regex, 
             "", 
             subtext
          )
          open(self.outputFilename,'w').write(subtext)
        except Exception as e:
          print(e)

      self.statusProgress['value']=100
      self.entryStream.config(state='normal')     
      self.entryFilename.config(state='normal')
      self.extractCmd.config(state='normal')

  def closeThreads(self):
    self.close=True
    substhread = self.subtitleThread
    self.subtitleThread=None
    self.destroy()

  def extract(self):
    self.proc = sp.Popen(['ffmpeg','-y','-i', self.file, '-map', '0:s:{}'.format(self.streamInd), '-vsync', '0', '-an', '-vn' , '-f', 'srt' , self.outputFilename],stderr=sp.PIPE)
    self.subtitleThread = threading.Thread(target=self.watchsubtitleProgress)
    self.subtitleThread.daemon = True
    
    self.entryStream.config(state='disabled')     
    self.entryFilename.config(state='disabled')
    self.extractCmd.config(state='disabled')

    self.subtitleThread.start()


class OptionsDialog(tk.Toplevel):
  def __init__(self, master=None, optionsDict={}, changedProperties={}, changeCallback=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Options')
    self.minsize(600,140)
    self.optionsDict=optionsDict
    self.changedProperties=changedProperties
    self.changeCallback=changeCallback
    self.entryMap={}
    self.varMap={}
    self.validatorMap={}
    
    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    self.columnconfigure(2, weight=0)    
    self.columnconfigure(3, weight=1)
    self.columnconfigure(4, weight=0)    
    self.columnconfigure(5, weight=1)
    i=0

    columnHeight=25
    maxcol=1

    for i,(k,v) in enumerate(optionsDict.items()):
      print(i,k,v)
      labelValue = ttk.Label(self)
      labelValue.config(text=k)

      column = i//columnHeight
      column = column*2
      maxcol= max(maxcol,maxcol+1)
      row = i%columnHeight

      labelValue.grid(row=row,column=column,sticky='new',padx=5,pady=1)

      if type(v) == bool:

        valueVar   = tk.BooleanVar(self)
        self.varMap[k]=valueVar

        entryValue = ttk.Checkbutton(self,text="", variable=self.varMap[k])

        #okayCommand = self.register(lambda val,t=type(v):self.validateType(t,val))  
        #self.validatorMap[k]=okayCommand
        #entryValue.config(validate='key',validatecommand=(okayCommand ,'%P'))

        valueVar.set(v)

      else:
        valueVar   = tk.StringVar(self)
        self.varMap[k]=valueVar
        entryValue = ttk.Entry(self,textvariable=self.varMap[k])
      
        okayCommand = self.register(lambda val,t=type(v):self.validateType(t,val))  
        self.validatorMap[k]=okayCommand
        entryValue.config(validate='key',validatecommand=(okayCommand ,'%P'))

        valueVar.set(str(v))

      entryValue.grid(row=row,column=column+1,sticky='new',padx=5,pady=0)
      self.entryMap[k]=entryValue
      valueVar.set(str(v))
      valueVar.trace('w',lambda *args,k=k:self.valueChanged(k))

    self.saveChanges = ttk.Button(self,text='Save Changes',command=self.saveChanges)
    self.rowconfigure(i+1, weight=1)
    self.saveChanges.grid(row=i+1,column=0,columnspan=maxcol+2,sticky='nesw')


    self.resizable(True, False) 

  def validateType(self,fieldtype,nextVal):
    if nextVal=='':
      return 1
    try:
      fieldtype(nextVal)
      return 1
    except:
      return 0

  def saveChanges(self):
    print(self.changeCallback,self.changedProperties)
    if self.changeCallback is not None:
      print(self.changedProperties)
      self.changeCallback(self.changedProperties)
    self.destroy()

  def valueChanged(self,valueKey):
    originalValue = self.optionsDict[valueKey]
    try:
      if type(originalValue) == int:
        self.changedProperties[valueKey] = int(self.varMap.get(valueKey).get())
      elif type(originalValue) == float:
        self.changedProperties[valueKey] = float(self.varMap.get(valueKey).get())
      elif type(originalValue) == bool:
        self.changedProperties[valueKey] = bool(self.varMap.get(valueKey).get())
      else:
        self.changedProperties[valueKey] = self.varMap.get(valueKey).get()
    except Exception as e:
      try:
        del self.changedProperties[valueKey]
      except Exception as e:
        print(e)
    print(valueKey)

if __name__ == "__main__":
  app = AdvancedEncodeFlagsModal()
  app.mainloop()
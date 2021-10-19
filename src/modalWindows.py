

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import subprocess as sp
import string
import os
import threading
try:
  from .encodingUtils import cleanFilenameForFfmpeg
except:
  from encodingUtils import cleanFilenameForFfmpeg
from datetime import datetime

class SubtitleExtractionModal(tk.Toplevel):

  def __init__(self, master=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Extract Subtitles')
    self.minsize(600,140)
    self.maxsize(600,140)


    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=0)
    self.rowconfigure(4, weight=1)
    self.rowconfigure(5, weight=0)
    

    self.labelFilename = ttk.Label(self)
    self.file=''
    self.labelFilename.config(text='Source file')
    self.labelFilename.grid(row=0,column=0,sticky='new')

    self.varFilename   = tk.StringVar()
    self.varFilename.set('None')
    self.entryFilename = ttk.Button(self)
    self.entryFilename.config(text='File: {}'.format(self.varFilename.get()[-20:]),command=self.selectFile)
    self.entryFilename.grid(row=0,column=1,sticky='new')

    self.labelStream = ttk.Label(self)
    self.labelStream.config(text='Stream Index')
    self.labelStream.grid(row=1,column=0,sticky='new')

    self.varStream   = tk.StringVar()
    self.varStream.trace('w',self.streamChanged)
    self.entryStream = ttk.Combobox(self)
    self.entryStream.config(textvariable=self.varStream,state='disabled')
    self.entryStream.config(values=[])
    self.entryStream.grid(row=1,column=1,sticky='new')

    self.labelOutputName = ttk.Label(self)
    self.labelOutputName.config(text='Output Name:')
    self.labelOutputName.grid(row=2,column=0,sticky='new')

    self.labelOutputFileName = ttk.Label(self)
    self.labelOutputFileName.config(text='None')
    self.labelOutputFileName.grid(row=2,column=1,sticky='new')

    self.labelProgress = ttk.Label(self)
    self.labelProgress.config(text='Idle')
    self.labelProgress.grid(row=3,column=0,columnspan=2,sticky='new')


    self.extractCmd = ttk.Button(self)
    self.extractCmd.config(text='Extract',command=self.extract,state='disabled')
    self.extractCmd.grid(row=4,column=0,columnspan=2,sticky='nesw')


    self.statusProgress = ttk.Progressbar(self)
    self.statusProgress['value'] = 0
    self.statusProgress.grid(row=5,column=0,columnspan=2,sticky='nesw')
    self.statusProgress.config(style="Green.Horizontal.TProgressbar")

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
        l=b''
      else:
        l+=c
    if not self.close:
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
    self.optionsDict=optionsDict
    self.changedProperties=changedProperties
    self.changeCallback=changeCallback
    self.entryMap={}
    self.varMap={}
    self.validatorMap={}
    
    self.columnconfigure(0, weight=0)    
    self.columnconfigure(1, weight=1)

    for i,(k,v) in enumerate(optionsDict.items()):
      print(i,k,v)
      labelValue = ttk.Label(self)
      labelValue.config(text=k)
      labelValue.grid(row=i,column=0,sticky='new')
      valueVar   = tk.StringVar(self)
      self.varMap[k]=valueVar
      entryValue = ttk.Entry(self,textvariable=self.varMap[k])
    
      okayCommand = self.register(lambda val,t=type(v):self.validateType(t,val))  
      self.validatorMap[k]=okayCommand
      entryValue.config(validate='key',validatecommand=(okayCommand ,'%P'))

      valueVar.set(str(v))
      entryValue.grid(row=i,column=1,sticky='new')
      self.entryMap[k]=entryValue
      valueVar.set(str(v))
      valueVar.trace('w',lambda *args,k=k:self.valueChanged(k))

    self.saveChanges = ttk.Button(self,text='Save Changes',command=self.saveChanges)
    self.rowconfigure(i+1, weight=1)
    self.saveChanges.grid(row=i+1,column=0,columnspan=2,sticky='nesw')

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
  app = OptionsDialog(master=None,optionsDict={'test':1.0,'test2':"two"},changedProperties={})
  app.mainloop()
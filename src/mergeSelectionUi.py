import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrolledframe import ScrolledFrame
import os
import string 
import mpv
from tkinter.filedialog import askopenfilename
import random
import time
from collections import deque
import logging 
import json
import threading
from .modalWindows import Tooltip

class EncodeProgress(ttk.Frame):

  def __init__(self, master=None, *args, encodeRequestId=None,controller=None, targetSize=0.0, **kwargs):
    ttk.Frame.__init__(self, master)
    self.frameEncodeProgressWidget = self
    self.encodeRequestId = encodeRequestId
    self.cancelled = False
    self.controller = controller
    self.config(padding='2', relief='raised')

    self.frameEncodeProgressWidget.columnconfigure(0, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(1, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(2, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(3, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(4, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(5, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(6, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(7, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(8, weight=1)
    self.frameEncodeProgressWidget.columnconfigure(9, weight=1)
    self.frameEncodeProgressWidget.rowconfigure(0, weight=1)

    self.labelRequestId = ttk.Label(self.frameEncodeProgressWidget)
    self.labelRequestId.config(text='Request #{}'.format(encodeRequestId), relief='flat')
    self.labelRequestId.grid(row=0,column=0,sticky='nesw')

    self.labelRequestStatus = ttk.Label(self.frameEncodeProgressWidget)
    self.labelRequestStatus.config(text='Idle', relief='flat')
    self.labelRequestStatus.grid(row=0,column=1,sticky='nesw',columnspan=9)

    self.labelEncodeStage = ttk.Label(self.frameEncodeProgressWidget)
    self.labelEncodeStage.config(text='Stage: Submitted Idle', relief='flat')
    self.labelEncodeStage.grid(row=1,column=0,sticky='nesw')

    self.labelEncodePass = ttk.Label(self.frameEncodeProgressWidget)
    self.labelEncodePass.config(text='Pass: Preparation Cutting Clips', relief='flat')
    self.labelEncodePass.grid(row=1,column=1,sticky='nesw')

    self.labelTargetSize = ttk.Label(self.frameEncodeProgressWidget)
    if targetSize <= 0.0:
      self.labelTargetSize.config(text='Target Size: -', relief='flat')
    else:
      self.labelTargetSize.config(text='Target Size: {}M'.format(targetSize), relief='flat')
    self.labelTargetSize.grid(row=1,column=2,sticky='nesw')

    self.labelLastEncodedSize = ttk.Label(self.frameEncodeProgressWidget)
    self.labelLastEncodedSize.config(text='Size: -', relief='flat')
    self.labelLastEncodedSize.grid(row=1,column=3,sticky='nesw')

    self.labelLastEncodedBR = ttk.Label(self.frameEncodeProgressWidget)
    self.labelLastEncodedBR.config(text='Bitrate: -', relief='flat')
    self.labelLastEncodedBR.grid(row=1,column=4,sticky='nesw')

    self.labelLastBuff = ttk.Label(self.frameEncodeProgressWidget)
    self.labelLastBuff.config(text='Buffer: -', relief='flat')
    self.labelLastBuff.grid(row=1,column=5,sticky='nesw')

    self.labelLastWR = ttk.Label(self.frameEncodeProgressWidget)
    self.labelLastWR.config(text='Width Change: -', relief='flat')
    self.labelLastWR.grid(row=1,column=6,sticky='nesw')

    self.labelTimeLeft  = ttk.Label(self.frameEncodeProgressWidget)
    self.labelTimeLeft.config(text='Idle', width='19')
    self.labelTimeLeft.grid(row=1,column=7,sticky='nesw')

    self.labelLastEncodedPSNR = ttk.Label(self.frameEncodeProgressWidget)
    self.labelLastEncodedPSNR.config(text='Quality: -', relief='flat')
    self.labelLastEncodedPSNR.grid(row=1,column=8,sticky='nesw')

    self.progressbarEncodeProgressLabel = ttk.Progressbar(self.frameEncodeProgressWidget)
    self.progressbarEncodeProgressLabel.config(mode='determinate', orient='horizontal')
    self.progressbarEncodeProgressLabel.grid(row=2,column=0,sticky='nesw',columnspan=9)


    self.progressbarEncodeCancelButton = ttk.Button(self.frameEncodeProgressWidget)
    self.progressbarEncodeCancelButton.config(text='Cancel')
    self.progressbarEncodeCancelButton.config(command=self.cancelEncodeRequest)
    self.progressbarEncodeCancelButton.config(style="small.TButton")
    self.progressbarEncodeCancelButton.grid(row=2,column=9,sticky='nesw')


    self.progressbarPlayButton = ttk.Button(self.frameEncodeProgressWidget)
    self.progressbarPlayButton.config(text='Play')
    self.progressbarPlayButton.config(command=self.playFinal)
    self.progressbarPlayButton.config(style="small.TButton")
    

    self.frameEncodeProgressWidget.pack(anchor='nw', expand='false',padx=0,pady=5, fill='x', side='top')
    
    self.progresspercent = 0
    self.encodeStartTime = None
    self.progressQueue    = deque([],10)
    self.timestampQueue   = deque([],10)
    self.finalFilename    = None
    self.player = None
    self.lastProgress=0

    self.updateStatus(None, None, requestStatus=None, encodeStage=None, encodePass=None, lastEncodedBR=None, lastEncodedSize=None, lastEncodedPSNR=None, lastBuff=None, lastWR=None)


  def playFinal(self):
    if self.finalFilename is not None:

      if self.player is not None:
        self.player.terminate()

      self.player = mpv.MPV(loop='inf',
                            mute=True,
                            volume=0,
                            autofit_larger='1280')

      self.player.play(self.finalFilename)

      def quitFunc(key_state, key_name, key_char):
        def playerReaper():
          print('ReaperKill')
          player=self.player
          self.player=None
          player.terminate()
          player.wait_for_shutdown()
        self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
        self.playerReaper.start()

      self.quitFunc = quitFunc

      self.player.register_key_binding("q", quitFunc)
      self.player.register_key_binding("Q", quitFunc)        
      self.player.register_key_binding("CLOSE_WIN", quitFunc)
      
  def cancelEncodeRequest(self):
    self.cancelled = True
    self.progressbarEncodeProgressLabel.config(style="Red.Horizontal.TProgressbar")
    self.progressbarEncodeProgressLabel['value']=100
    self.labelTimeLeft.config(text='Cancelled')
    self.progresspercent = 100
    self.progressbarEncodeCancelButton.state(["disabled"])
    self.controller.cancelEncodeRequest(self.encodeRequestId)

  def sizeof_fmt(self,inum, suffix='B'):
    num = float(inum)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

  def updateStatus(self,status,percent,finalFilename=None,requestStatus=None, encodeStage=None, encodePass=None, lastEncodedBR=None, lastEncodedSize=None, lastEncodedPSNR=None, lastBuff=None, lastWR=None):

    if self.cancelled:
      return

    if requestStatus is not None:
      self.labelRequestStatus.config(text=str(requestStatus))

    if encodeStage == 'Encode Failed':
      self.progressbarEncodeProgressLabel.config(style="Red.Horizontal.TProgressbar")
      self.progressbarEncodeProgressLabel['value']=100
      self.labelTimeLeft.config(text='Failed')
      self.progresspercent = 100
      self.progressbarEncodeCancelButton.state(["disabled"])
      self.cancelled = True


    if encodeStage is not None:
      self.labelEncodeStage.config(text='Stage: {}'.format(encodeStage), relief='flat')

    if encodePass is not None:
      self.labelEncodePass.config(text='Pass: {}'.format(encodePass), relief='flat')
    
    if lastEncodedSize is not None:
      lastEncodedSizeHuman = self.sizeof_fmt(lastEncodedSize,'B')  
      self.labelLastEncodedSize.config(text='Size: {}'.format(lastEncodedSizeHuman), relief='flat')
    
    if lastEncodedBR is not None:
      lastEncodedBRHuman = self.sizeof_fmt(lastEncodedBR,'B')
      self.labelLastEncodedBR.config(text='Bitrate: {}'.format(lastEncodedBRHuman), relief='flat')

    if lastEncodedPSNR is not None:
      PSNRGrade = 'Terrible'
      self.labelLastEncodedPSNR.config(style='PSNRTerrible.TLabel')

      if int(lastEncodedPSNR) >= 48:
        PSNRGrade = 'Excellent'
        self.labelLastEncodedPSNR.config(style='PSNRExcellent.TLabel')
      elif int(lastEncodedPSNR) >= 40:
        PSNRGrade = 'Good'
        self.labelLastEncodedPSNR.config(style='PSNRGood.TLabel')
      elif int(lastEncodedPSNR) >= 38:
        PSNRGrade = 'fair'
        self.labelLastEncodedPSNR.config(style='PSNRFair.TLabel')
      elif int(lastEncodedPSNR) >= 30:
        PSNRGrade = 'Poor'
        self.labelLastEncodedPSNR.config(style='PSNRPoor.TLabel')
      
      self.labelLastEncodedPSNR.config(text='Quality: {} ({})'.format(lastEncodedPSNR,PSNRGrade), relief='flat')
    
    if lastBuff is not None:
      lastBuffSizeHuman = self.sizeof_fmt(lastBuff,'B') 
      self.labelLastBuff.config(text='Buffer: {}'.format(lastBuffSizeHuman), relief='flat')
    
    if lastWR is not None:
      self.labelLastWR.config(text='Width Change: {:0.2f}%'.format(lastWR*100), relief='flat')

    if self.cancelled:
      return
    
    if finalFilename is not None:
      self.finalFilename = finalFilename

    if percent is not None:
      if percent<self.lastProgress:
        self.progressQueue    = deque([],10)
        self.timestampQueue   = deque([],10)

      self.lastProgress = percent

      self.progressQueue.append(percent)
      self.timestampQueue.append(time.time())

      if self.encodeStartTime is None:
        self.encodeStartTime = self.timestampQueue[-1]

      if len(self.progressQueue)>=2:
        
        currentValue = self.progressQueue[-1]
        oldestValue  = self.progressQueue[0]
        
        currentKey   = self.timestampQueue[-1]
        oldestKey    = self.timestampQueue[0]

        try:
          remaining = (1.0 - currentValue) * (currentKey - oldestKey) / (currentValue - oldestValue)
          self.labelTimeLeft.config(text=str(round(remaining,2))+'s left ({:.0%})'.format(percent))
        except:
          pass
      
      if status is not None:
        self.labelRequestStatus.config(text=status)
      self.progressbarEncodeProgressLabel['value']=percent*100
      self.progresspercent = percent*100

      if percent >= 1:
        self.labelTimeLeft.config(text='Complete in {}s'.format( str(round(time.time() - self.encodeStartTime,2)) ))
        self.progressbarEncodeCancelButton.grid_forget()
        if self.finalFilename is not None:
          self.progressbarEncodeProgressLabel.config(style="Green.Horizontal.TProgressbar")
          self.progressbarPlayButton.grid(row=2,column=9,sticky='nesw')
      else:
        self.progressbarEncodeProgressLabel.config(style="Blue.Horizontal.TProgressbar")
        self.progressbarEncodeCancelButton.grid(row=2,column=9,sticky='nesw') 

      if percent is not None:
        self.winfo_toplevel().title('webmGenerator: encoding: {:0.2f}%'.format(percent*100))

  def remove(self):
    if self.progresspercent == 100:
      self.pack_forget()
      del self


class SequencedVideoEntry(ttk.Frame):
  def __init__(self, master,controller,sourceClip, *args,direction='LEFT_RIGHT',**kwargs):
    ttk.Frame.__init__(self, master)

    self.rid=sourceClip.rid
    self.s=sourceClip.s
    self.e=sourceClip.e
    self.controller=controller
    self.player = None
    
    self.filename=sourceClip.filename
    self.filterexp=sourceClip.filterexp
    self.filterexpEnc=sourceClip.filterexpEnc
    self.basename = sourceClip.basename
    self.previewImage=sourceClip.previewImage

    self.frameSequenceVideoEntry = self
    if direction == 'LEFT_RIGHT':
      self.labelSequenceVideoName = ttk.Label(self.frameSequenceVideoEntry)
      self.labelSequenceVideoName.config(text='{:0.2f}-{:0.2f} {:0.2f}s'.format(self.s,self.e,self.e-self.s))
      self.labelSequenceVideoName.pack(side='top')
    self.frameOrderingButtons = ttk.Frame(self.frameSequenceVideoEntry)

    if direction == 'LEFT_RIGHT':
      self.buttonSequencePushEntryBack = ttk.Button(self.frameOrderingButtons)
      self.buttonSequencePushEntryBack.config(text='⯇', width='2')
      self.buttonSequencePushEntryBack.config(command=self.moveBack)
      self.buttonSequencePushEntryBack.pack(expand='true', fill='both', side='left')
    
    self.canvasSequencePreview = ttk.Label(self.frameOrderingButtons)
    self.canvasSequencePreview.config(image=self.previewImage)
    self.canvasSequencePreview.pack(side='left')

    if direction == 'LEFT_RIGHT':
      self.buttonSequencePushEntryForwards = ttk.Button(self.frameOrderingButtons)
      self.buttonSequencePushEntryForwards.config(text='⯈', width='2')
      self.buttonSequencePushEntryForwards.config(command=self.moveForwards)
      self.buttonSequencePushEntryForwards.pack(expand='true', fill='both', side='left')
    
    self.frameOrderingButtons.config(height='200', width='200')
    self.frameOrderingButtons.pack(side='top')
    self.buttonSequenceEntryPreview = ttk.Button(self.frameSequenceVideoEntry)
    self.buttonSequenceEntryPreview.config(text='Preview ⯈')
    self.buttonSequenceEntryPreview.config(command=self.preview)
    self.buttonSequenceEntryPreview.config(style="small.TButton")
    if direction == 'LEFT_RIGHT':
      self.buttonSequenceEntryPreview.pack(expand='true', fill='both', side='left')
    else:
      self.buttonSequenceEntryPreview.pack(expand='true', fill='x', side='left')


    self.buttonSequenceEntryREmove = ttk.Button(self.frameSequenceVideoEntry)
    self.buttonSequenceEntryREmove.config(text='Remove ✖')
    self.buttonSequenceEntryREmove.config(command=self.remove)
    self.buttonSequenceEntryREmove.config(style="small.TButton")
    if direction == 'LEFT_RIGHT':
      self.buttonSequenceEntryREmove.pack(expand='true', fill='both', side='left')
    else:
      self.buttonSequenceEntryREmove.pack(expand='true', fill='x', side='left')


    self.frameSequenceVideoEntry.config(height='200', padding='2', relief='groove', width='200')

    if direction == 'LEFT_RIGHT':
      self.frameSequenceVideoEntry.pack(expand='false', fill='y', side='left')
    elif direction == 'UP_DOWN':
      self.frameSequenceVideoEntry.pack(expand='false', fill='y', side='top')

  def preview(self):
    if self.player is not None:
      self.player.terminate()

    self.player = mpv.MPV(loop='inf',
                          mute=True,
                          volume=0,
                          autofit_larger='1280')

    self.player.play(self.filename)
    

    self.player.ab_loop_a = self.s
    self.player.ab_loop_b = self.e
    self.player.start = self.s
    self.player.time_pos  = self.s

    def quitFunc(key_state, key_name, key_char):
      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()

    self.quitFunc = quitFunc

    self.player.register_key_binding("q", quitFunc)
    self.player.register_key_binding("Q", quitFunc)        
    self.player.register_key_binding("CLOSE_WIN", quitFunc)

  def moveForwards(self):
    self.controller.moveSequencedClip(self,1)    

  def moveBack(self):
    self.controller.moveSequencedClip(self,-1)

  def remove(self):
    self.controller.removeSequencedClip(self)

  def setPreviewImage(self,photoImage):
    self.previewImage=photoImage
    self.canvasSequencePreview.config(image=self.previewImage)

  def update(self,s,e,filterexp,filterexpEnc):
    self.s=s
    self.e=e
    self.filterexp=filterexp
    self.filterexpEnc = filterexpEnc
    self.labelSequenceVideoName.config(text='{:0.2f}-{:0.2f} {:0.2f}s'.format(self.s,self.e,self.e-self.s))
    self.controller.requestPreviewFrame(self.rid,self.filename,(self.e+self.s)/2,self.filterexp)


class GridColumn(ttk.Labelframe):
  def __init__(self, master,controller):
    ttk.Labelframe.__init__(self, master)
    self.master=master
    self.controller=controller
    self.config(relief='groove',padding='4')

    self.buttonFrame = ttk.Frame(self)

    self.buttonFrame.columnconfigure(0, weight=10)
    self.buttonFrame.columnconfigure(1, weight=10)
    self.buttonFrame.rowconfigure(0,    weight=10)
    self.buttonFrame.rowconfigure(1,    weight=10)


    """
    self.nestRowBtn = ttk.Button(self.buttonFrame,text='Nest Row ⇄',command=self.nestRow)
    self.nestRowBtn.config(style="small.TButton",state='disabled')
    self.nestRowBtn.grid(column=0,row=0, sticky='nsew')

    self.nestColumnBtn = ttk.Button(self.buttonFrame,text='Nest Col ⇅',command=self.nestColumn)
    self.nestColumnBtn.config(style="small.TButton",state='disabled')
    self.nestColumnBtn.grid(column=1,row=0, sticky='nsew')
    """

    self.selectColumnBtn = ttk.Button(self.buttonFrame,text='Select ✔',command=self.selectColumn)
    self.selectColumnBtn.config(style="small.TButton")
    self.selectColumnBtn.grid(column=0,row=1, sticky='nsew')

    self.removeColumnBtn = ttk.Button(self.buttonFrame,text='Remove ✖',command=self.removeColumn)
    self.removeColumnBtn.config(style="small.TButton")
    self.removeColumnBtn.grid(column=1,row=1, sticky='nsew')

    self.buttonFrame.pack(expand='false', fill='x', side='bottom')

    self.pack(expand='false', fill='y', side='left')

  def setSelected(self,isSelected):
    if isSelected:
      self.config(relief='sunken',text='Selected')
      self.selectColumnBtn.config(text='Selected ✔',style="smallBlue.TButton")

    else:
      self.config(relief='groove',text='')
      self.selectColumnBtn.config(text='Select ✔',style="small.TButton")


  def nestColumn(self):
    pass

  def nestRow(self):
    pass

  def selectColumn(self):
    self.controller.selectColumn(self)

  def removeColumn(self):
    self.controller.removeColumn(self)


class SelectableVideoEntry(ttk.Frame):
  def __init__(self, master,controller,filename,rid,s,e,filterexp,filterexpEnc, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.master=master
    self.rid=rid
    self.s=s
    self.e=e
    self.controller=controller
    self.filename=filename
    self.filterexp=filterexp
    self.filterexpEnc = filterexpEnc

    self.basename = os.path.basename(filename)[:14]
    self.player=None
    
    self.frameInputCutWidget = self
    self.labelInputCutName = ttk.Label(self.frameInputCutWidget)
    self.labelInputCutName.config(text='#{} {:0.2f}-{:0.2f} {:0.2f}s'.format(self.rid,self.s,self.e,self.e-self.s))
    self.labelInputCutName.pack(side='top')
    
    self.previewData = "P5\n124 80\n255\n"+("0"*80*124)
    self.previewImage= tk.PhotoImage(data=self.previewData)  

    try:
      self.previewImage = tk.PhotoImage(file=".\\resources\\cutPreview.png")
    except Exception as e:
      print(e)

    self.canvasInputCutPreview = ttk.Label(self.frameInputCutWidget)
    self.canvasInputCutPreview.config(text='No Preview loaded')
    self.canvasInputCutPreview.config(image=self.previewImage)
    self.canvasInputCutPreview.pack(side='top')

    self.controller.requestPreviewFrame(self.rid,self.filename,(self.e+self.s)/2,self.filterexp)

    self.buttonInputPreview = ttk.Button(self.frameInputCutWidget)
    self.buttonInputPreview.config(text='preview ⯈')
    self.buttonInputPreview.config(command=self.preview)
    self.buttonInputPreview.pack(expand='true', fill='both', side='top')
    
    self.buttonInputCutAdd = ttk.Button(self.frameInputCutWidget)
    self.buttonInputCutAdd.config(text='Add to Sequence ⯆')
    self.buttonInputCutAdd.config(command=self.addClipToSequence)
    self.buttonInputCutAdd.pack(expand='true', fill='both', side='top')

    self.frameInputCutWidget.config(padding='2', relief='groove', width='200')
    self.frameInputCutWidget.pack(anchor='nw', expand='false', fill='y', side='left')

  def setPreviewImage(self,photoImage):
    self.previewImage=photoImage
    self.canvasInputCutPreview.config(image=self.previewImage)

  def update(self,s,e,filterexp,filterexpEnc):
    self.s=s
    self.e=e
    self.filterexp=filterexp
    self.filterexpEnc = filterexpEnc
    self.labelInputCutName.config(text='{:0.2f}-{:0.2f} {:0.2f}s'.format(self.s,self.e,self.e-self.s))
    self.controller.requestPreviewFrame(self.rid,self.filename,(self.e+self.s)/2,self.filterexp)

  def addClipToSequence(self):
    self.controller.addClipToSequence(self)

  def preview(self):
    if self.player is not None:
      self.player.terminate()

    self.player = mpv.MPV(loop='inf',
                          mute=True,
                          volume=0,
                          autofit_larger='1280')

    self.player.play(self.filename)
    
    self.player.ab_loop_a = self.s
    self.player.ab_loop_b = self.e
    self.player.start = self.s
    self.player.time_pos  = self.s

    def quitFunc(key_state, key_name, key_char):
      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()

    self.quitFunc = quitFunc

    self.player.register_key_binding("q", quitFunc)
    self.player.register_key_binding("Q", quitFunc)        
    self.player.register_key_binding("CLOSE_WIN", quitFunc)


class MergeSelectionUi(ttk.Frame):

  def __init__(self, master=None,defaultProfile='None', *args, **kwargs):
    ttk.Frame.__init__(self, master)

    self.master=master
    self.controller=None
    self.defaultProfile=defaultProfile

    self.outserScrolledFrame = ScrolledFrame(self, scrolltype='vertical')
    self.outserScrolledFrame.pack(expand='true', fill='both', padx='0', pady='0', side='top')

    self.frameMergeSelection = self.outserScrolledFrame.innerframe

    self.mergeStyleFrame = ttk.Frame(self.frameMergeSelection)

    self.mergestyleLabel = ttk.Label(self.mergeStyleFrame,text='Merge Style',width='12')
    self.mergestyleLabel.pack(expand='false', fill='x', side='left')

    self.mergeStyleVar = tk.StringVar()
    self.mergeStyles   = ['Individual Files - Output each individual subclip as a separate file.',                          
                          'Sequence - Join the subclips into a sequence.',
                          'Grid - Pack videos into variably sized grid layouts.',
                          'Stream Copy - Ignore all filters and percorm no conversions, just slice the clips.']

    self.mergeStyleVar.set(self.mergeStyles[0])
    

    self.mergeStyleCombo = ttk.OptionMenu(self.mergeStyleFrame,self.mergeStyleVar,self.mergeStyleVar.get(),*self.mergeStyles)
    self.mergeStyleCombo['padding']=2
    self.mergeStyleCombo.pack(expand='true', fill='x', side='right')

    self.mergeStyleFrame.pack(expand='false', fill='x', padx='5', pady='0', side='top')



    self.profileFrame = ttk.Frame(self.frameMergeSelection)

    self.profileLabel = ttk.Label(self.profileFrame,text='Profile',width='12')
    self.profileLabel.pack(expand='false', fill='x', side='left')

    self.profileVar = tk.StringVar()
    self.profileSpecs = [
      {'name':'None','editable':False},
      {'name':'Default max quality mp4','editable':False,'outputFormat':'mp4:x264','maximumSize':'0.0'},
      {'name':'Sub 4M max quality vp8 webm','editable':False,'outputFormat':'webm:VP8','maximumSize':'4.0'},
      {'name':'Sub 100M max quality mp4','editable':False,'outputFormat':'mp4:x264','maximumSize':'100.0'}
    ]

    self.profileVar = tk.StringVar()
    self.profiles   = [x.get('name') for x in self.profileSpecs if x.get('name') is not None ]


    if self.defaultProfile in self.profiles:
      self.profileVar.set(defaultProfile)
    else:
      self.profileVar.set(self.profiles[0])

    self.profileCombo = ttk.OptionMenu(self.profileFrame,self.profileVar,self.profileVar.get(),*self.profiles)
    self.profileCombo['padding']=2
    self.profileCombo.pack(expand='true', fill='x', side='left')


    self.profileDelete = ttk.Button(self.profileFrame, command=self.deleteProfile)
    self.profileDelete.configure(text='Delete Profile')
    self.profileDelete['padding']=2
    self.profileDelete.state(["disabled"])
    self.profileDelete.pack(expand='false', side='right')

    self.profileSave = ttk.Button(self.profileFrame, command=self.saveProfile)
    self.profileSave['padding']=2
    self.profileSave.configure(text='Save New Profile')
    self.profileSave.pack(expand='false', side='right')

    self.profileFrame.pack(expand='false', fill='x', padx='5', pady='0  ', side='top')

    self.profileVar.trace('w',self.profileChanged)

    self.labelframeInputCutSelection = ttk.Labelframe(self.frameMergeSelection)
    
    self.scrolledframeInputCustContainer = ScrolledFrame(self.labelframeInputCutSelection, scrolltype='horizontal')


    self.selectableVideosContainer = ttk.Frame(self.scrolledframeInputCustContainer.innerframe)

    self.selectableVideosContainer.pack(expand='true', fill='x', padx='0', pady='0', side='top')

    self.scrolledframeInputCustContainer.innerframe.config(padding='5')
    self.scrolledframeInputCustContainer.configure(usemousewheel=False)
    self.scrolledframeInputCustContainer.pack(anchor='n', expand='true', fill='x', padx='0', pady='0', side='top')

    self.labelframeInputCutSelection.config(height='0', text='Avalaible Cuts', width='500')
    self.labelframeInputCutSelection.pack(expand='false', fill='x', padx='0', pady='0', side='top')

    self.addAddClipsFrame = ttk.Frame(self.frameMergeSelection)

    self.addAllClipsbutton = ttk.Button(self.addAddClipsFrame,text='⯆ Add all clips in timeline order ⯆')
    self.addAllClipsbutton.config(command=self.addAllClipsInTimelineOrder)
    self.addAllClipsbutton.config(style="small.TButton")
    self.addAllClipsbutton.pack(expand='true', fill='x', padx='0', pady='3', side='left')

    self.addAllClipsRandombutton = ttk.Button(self.addAddClipsFrame,text=' Add all clips in random order ')
    self.addAllClipsRandombutton.config(command=self.addAllClipsInRandomOrder)
    self.addAllClipsRandombutton.config(style="small.TButton")
    self.addAllClipsRandombutton.pack(expand='false', fill='x', padx='0', pady='3', side='right')

    self.addAllClipsSmartRandombutton = ttk.Button(self.addAddClipsFrame,text=' Add all clips in non-sequential order ')
    self.addAllClipsSmartRandombutton.config(command=self.addAllClipsInSmartRandomOrder)
    self.addAllClipsSmartRandombutton.config(style="small.TButton")
    self.addAllClipsSmartRandombutton.pack(expand='false', fill='x', padx='0', pady='3', side='right')

    self.addAllClipsInterpsersed = ttk.Button(self.addAddClipsFrame,text=' Add all clips interspsersed')
    self.addAllClipsInterpsersed.config(command=self.addAllClipsInInterspersedOrder)
    self.addAllClipsInterpsersed.config(style="small.TButton")
    self.addAllClipsInterpsersed.pack(expand='false', fill='x', padx='0', pady='3', side='right')

    self.addAddClipsFrame.pack(expand='false', fill='x', padx='0', pady='0', side='top')

    self.labelframeSequenceFrame = ttk.Labelframe(self.frameMergeSelection)

    self.outputPlanningContainer = ttk.Frame(self.labelframeSequenceFrame)
    self.outputPlanningContainer.pack(expand='false', fill='both', padx='0', pady='0', side='top')

    self.labelframeSequenceFrame.config(height='20', text='Output Plan', width='200')
    self.labelframeSequenceFrame.pack(expand='true',fill='both', padx='5', pady='5', side='top')

    self.gridSequenceContainer = ttk.Frame(self.outputPlanningContainer)
    self.gridSequenceContainer.pack(expand='true', fill='both', padx='5', pady='0', side='top')


    self.gridColumnContainer = ttk.Frame(self.gridSequenceContainer)
    self.gridColumnContainer.pack(expand='true', fill='x', padx='0', pady='0', side='top')

    self.gridColumns = []

    #self.gridSequenceContainerAddRow = ttk.Button(self.gridSequenceContainer,text='Add Row ⇄', command=self.addRow)
    #self.gridSequenceContainerAddRow.config(style="small.TButton")
    #self.gridSequenceContainerAddRow.pack(expand='true', fill='x', padx='0', pady='0', side='left')

    self.gridSequenceContainerAddColumn = ttk.Button(self.gridSequenceContainer,text='Add Column ⇅', command=self.addColumn)
    self.gridSequenceContainerAddColumn.config(style="small.TButton")
    self.gridSequenceContainerAddColumn.pack(expand='true', fill='x', padx='0', pady='0', side='right')
    self.gridSequenceContainer.pack_forget()

    self.scrolledframeSequenceContainer = ScrolledFrame(self.outputPlanningContainer, scrolltype='horizontal')

    self.sequenceContainer = ttk.Frame(self.scrolledframeSequenceContainer.innerframe)
    self.sequenceContainer.pack(expand='true', fill='both', padx='0', pady='0', side='top')

    self.mergeStyleVar.trace('w',self.mergeStyleChanged)
    
    self.sequencedClips = []

    self.scrolledframeSequenceContainer.configure(usemousewheel=False)
    self.scrolledframeSequenceContainer.innerframe.config(padding='5')
    self.scrolledframeSequenceContainer.pack(expand='true', fill='both', padx='5', pady='0', side='top')

    self.frameSequenceSummary = ttk.Frame(self.labelframeSequenceFrame)
    self.labelSequenceSummary = ttk.Label(self.frameSequenceSummary)
    self.labelSequenceSummary.config(anchor='center', text='Number of Subclips: 0 Total subclip duration 0s Output Duration 0s')
    self.labelSequenceSummary.pack(expand='false', fill='x', side='top', pady='0')
    self.frameSequenceSummary.config(height='10', width='200')
    self.frameSequenceSummary.pack(expand='false', fill='x', side='top', pady='0')
    
    

    self.frameEncodeSettings = ttk.Frame(self.labelframeSequenceFrame)
    self.frameSequenceValues = ttk.Frame(self.frameEncodeSettings)

    self.automaticFileNamingVar    = tk.BooleanVar()
    self.interpolateSpeedChangeVar = tk.BooleanVar()
    self.loopStartAndendVar        = tk.BooleanVar()

    self.filenamePrefixVar        = tk.StringVar()
    self.outputFormatVar          = tk.StringVar()
    self.frameSizeStrategyVar     = tk.StringVar()
    self.maximumSizeVar           = tk.StringVar()
    self.initialbitrateVar        = tk.StringVar()
    self.maxbitrateVar            = tk.StringVar()
    self.maximumWidthVar          = tk.StringVar()
    self.minimumPSNRVar           = tk.StringVar()
    self.optimizerVar             = tk.StringVar()

    self.transDurationVar         = tk.StringVar()
    self.transStyleVar            = tk.StringVar()
    self.speedAdjustmentVar       = tk.StringVar() 
    self.audioChannelsVar         = tk.StringVar()
    self.audioMergeOptionsVar     = tk.StringVar()
    self.gridLoopMergeOptionsVar  = tk.StringVar()
    self.gridPadColourOptionsVar  = tk.StringVar()
    self.gridPadWidthVar  = tk.StringVar()
    self.postProcessingFilterVar  = tk.StringVar()

    self.audioOverrideVar         = tk.StringVar()
    self.audiOverrideDelayVar     = tk.StringVar()
    self.audiOverrideBiasVar      = tk.StringVar()

    self.automaticFileNamingVar.trace('w',self.valueChange)
    self.interpolateSpeedChangeVar.trace('w',self.valueChange)
    self.loopStartAndendVar.trace('w',self.valueChange)
    self.filenamePrefixVar.trace('w',self.valueChange)
    self.outputFormatVar.trace('w',self.valueChange)
    self.frameSizeStrategyVar.trace('w',self.valueChange)
    self.maximumSizeVar.trace('w',self.valueChange)
    self.initialbitrateVar.trace('w',self.valueChange)
    self.maxbitrateVar.trace('w',self.valueChange)
    self.maximumWidthVar.trace('w',self.valueChange)
    self.transDurationVar.trace('w',self.valueChange)
    self.transStyleVar.trace('w',self.valueChange)
    self.speedAdjustmentVar.trace('w',self.valueChange)
    self.audioChannelsVar.trace('w',self.valueChange)
    self.audioMergeOptionsVar.trace('w',self.valueChange)
    self.gridLoopMergeOptionsVar.trace('w',self.valueChange)
    self.gridPadColourOptionsVar.trace('w',self.valueChange)
    self.gridPadWidthVar.trace('w',self.valueChange)
    self.postProcessingFilterVar.trace('w',self.valueChange)
    self.minimumPSNRVar.trace('w',self.valueChange)
    self.optimizerVar.trace('w',self.valueChange)
    self.audiOverrideBiasVar.trace('w',self.valueChange)





    self.optimziers = [
      'Linear Search',
      'Nelder-Mead - Early Exit',
      'Nelder-Mead - Exhaustive',
    ]

    self.optimizerVar.set(self.optimziers[0])

    self.editableProfileVars = [
      'outputFormat',
      'frameSizeStrategy',
      'maximumSize',
      'maximumWidth',
      'transDuration',
      'transStyle',
      'speedAdjustment',
      'audioChannels',
      'audioMergeOptions',
      'gridLoopMergeOptions'
    ]

    self.audioOverrideVar.trace('w',self.valueChange)
    self.audiOverrideDelayVar.trace('w',self.valueChange)

    self.automaticFileNamingVar.set(True)
    self.interpolateSpeedChangeVar.set(False)
    self.loopStartAndendVar.set(True)
    self.filenamePrefixVar.set('')

    self.audioOverrideVar.set('None')
    self.audiOverrideDelayVar.set('0')

    self.outputFormats = [
      'mp4:x264',
      'mp4:x264_Nvenc',
      'mp4:H265_Nvenc',
      'mp4:AV1',
      'webm:VP8',
      'webm:VP9',
      'gif',      
      'apng',
    ]
    self.outputFormatVar.set(self.outputFormats[0])


    self.frameSizeStrategies = [
      'Rescale to largest with black bars',
      'Rescale to largest and center crop smaller',    
    ]
    self.frameSizeStrategyVar.set(self.frameSizeStrategies[0])


    self.frameSizeStrategies = [
      'Rescale to largest with black bars',
      'Rescale to largest and center crop smaller',    
    ]
    self.frameSizeStrategyVar.set(self.frameSizeStrategies[0])

    self.maximumSizeVar.set('0.0')
    self.initialbitrateVar.set('2000.0')
    self.maxbitrateVar.set('6000.0')

    self.minimumPSNRVar.set('0.0')
    self.maximumWidthVar.set('1280')
    self.transDurationVar.set('0.0')       

    self.transStyles = [
                        'circleclose',
                        'circlecrop',
                        'circleopen',
                        'diagbl',
                        'diagbr',
                        'diagtl',
                        'diagtr',
                        'dissolve',
                        'distance',
                        'fade',
                        'fadeblack',
                        'fadegrays',
                        'fadewhite',
                        'hblur',
                        'hlslice',
                        'horzclose',
                        'horzopen',
                        'hrslice',
                        'pixelize',
                        'radial',
                        'rectcrop',
                        'slidedown',
                        'slideleft',
                        'slideright',
                        'slideup',
                        'smoothdown',
                        'smoothleft',
                        'smoothright',
                        'smoothup',
                        'squeezeh',
                        'squeezev',
                        'vdslice',
                        'vertclose',
                        'vertopen',
                        'vuslice',
                        'wipebl',                        
                        'wipebr',
                        'wipedown',
                        'wipeleft',
                        'wiperight',
                        'wipetl',
                        'wipetr',
                        'wipeup',
                        'zoomin',

                        'circleopen, circleclose',
                        'fadewhite, fadeblack',
                        'slideleft, slideright', 
                        'smoothdown, smoothup',
                        'smoothleft, smoothright',
                        'wipetl, wipetr, wipebl, wipebr', 
                        ]
    
    self.transStyleVar.set('fade')
    self.speedAdjustmentVar.set(1.0)


    self.audioChannelsOptions = [
       'Stereo - Low    48 kbps'
      ,'Stereo - Medium 64 kbps'
      ,'Stereo - High   96 kbps'
      ,'Stereo - HD     128 kbps'
      ,'Stereo - Ultra  192 kbps'
      ,'Mono - Low    48 kbps'
      ,'Mono - Medium 64 kbps'
      ,'Mono - High   96 kbps'
      ,'Mono - HD     128 kbps'
      ,'Mono - Ultra  192 kbps'
      #,'Directly Copy Source'
      ,'No audio'
    ]

    self.audioChannelsVar.set(self.audioChannelsOptions[6])    

    self.audioMergeOptions = ['Merge Normalize All','Merge Original Volume','Selected Column Only','Largest Cell by Area','Adaptive Loudest Cell']
    self.audioMergeOptionsVar.set(self.audioMergeOptions[0]) 

    self.audiOverrideBiasVar.set('1.0')

    self.gridLoopMergeOptions = ['End on shortest Clip','Loop shorter clips to match longest']
    self.gridLoopMergeOptionsVar.set(self.gridLoopMergeOptions[0])

    self.gridPadColourOptions = ['Black','White','DeepPink','MintCream','DarkGray']
    self.gridPadColourOptionsVar.set(self.gridPadColourOptions[0])

    self.gridPadWidthVar.set('0')


    self.postProcessingFilterOptions = ['None','Disable all filters']
    if os.path.exists('postFilters'):
      for f in os.listdir('postFilters'):
        if f.upper().endswith('TXT') and f.upper().startswith('POSTFILTER-'):
          self.postProcessingFilterOptions.append(f)

    

    for filterElem in self.postProcessingFilterOptions:
      if 'DEFAULT' in filterElem.upper():
        self.postProcessingFilterVar.set(filterElem)
        break
    else:
      self.postProcessingFilterVar.set('None')


    self.frameSequenceActions = ttk.Frame(self.frameEncodeSettings)
    self.buttonSequenceClear = ttk.Button(self.frameSequenceActions)
    self.buttonSequenceClear.config(text='Clear Sequence',style='small.TButton')
    self.buttonSequenceClear.config(command=self.clearSequence)
    self.buttonSequenceClear.pack(side='top')


    self.buttonSequenceEncode = ttk.Button(self.frameSequenceActions)
    self.buttonSequenceEncode.config(text='Encode')
    self.buttonSequenceEncode.config(command=self.encodeCurrent)
    self.buttonSequenceEncode.pack(expand='true', fill='both', side='top')


    self.buttonSequenceCancel = ttk.Button(self.frameSequenceActions)
    self.buttonSequenceCancel.config(text='Cancel all',style='small.TButton')
    self.buttonSequenceCancel.config(command=self.cancelAllEncodes)
    self.buttonSequenceCancel.pack(fill='x',side='top')


    self.frameSequenceActions.config(height='200', width='200')
    self.frameSequenceActions.pack(expand='false', fill='both', side='right')


    self.frameMergeStyleSettings = ttk.Frame(self.labelframeSequenceFrame)

    self.frameMergeStyleSettings.pack(fill='x', ipadx='0', side='top')

    # Settings for Transitions Starts
    self.frameTransitionSettings = ttk.Frame(self.frameMergeStyleSettings)
    self.frameTransitionSettings.config(height='200', padding='5', relief='groove', width='200')

    self.frameTransDuration = ttk.Frame(self.frameTransitionSettings)
    self.labelTransDuration = ttk.Label(self.frameTransDuration)
    self.labelTransDuration.config(anchor='e', padding='2', text='Transition Duration', width='25')
    self.labelTransDuration.pack(side='left')
    self.entryTransDuration = ttk.Spinbox(self.frameTransDuration, 
                                          from_=0, 
                                          to=float('inf'), 
                                          increment=0.1,
                                          textvariable=self.transDurationVar)
    self.entryTransDuration.config(width='5')

    self.entryTransDuration.pack(expand='true', fill='both', side='left')

    self.frameTransDuration.pack(expand='true', fill='x', side='top')

    self.frameTransStyle = ttk.Frame(self.frameTransitionSettings)
    self.labelTransStyle = ttk.Label(self.frameTransStyle)
    self.labelTransStyle.config(anchor='e', padding='2', text='Transition Style', width='25')
    self.labelTransStyle.pack(side='left')
    self.frameTransStyle.pack(expand='true', fill='x', side='bottom')

    
    # Settings for Transitions Ends

    # Settings for Grid Merge Starts

    self.frameGridSettings = ttk.Frame(self.frameMergeStyleSettings)
    self.frameGridSettings.config(height='200', padding='5', relief='groove', width='200')

    self.frameAudioMerge = ttk.Frame(self.frameGridSettings)

    self.labelAudioMerge = ttk.Label(self.frameAudioMerge)
    self.labelAudioMerge.config(anchor='e', padding='2', text='Grid Audio Merge', width='25')
    self.labelAudioMerge.pack(side='left')
    
    self.entryAudioMerge = ttk.OptionMenu(self.frameAudioMerge,self.audioMergeOptionsVar,self.audioMergeOptionsVar.get(),*self.audioMergeOptions)
    self.entryAudioMerge['padding']=2
    self.entryAudioMerge.pack(expand='true', fill='both', side='left')

    self.frameAudioMerge.pack(fill='x', side='top')


    self.frameGridLoopOptions = ttk.Frame(self.frameGridSettings)

    self.labelGridLoopOptions = ttk.Label(self.frameGridLoopOptions)
    self.labelGridLoopOptions.config(anchor='e', padding='2', text='Grid Loop Option', width='25')
    self.labelGridLoopOptions.pack(side='left')
    
    self.entryGridLoopOptions = ttk.OptionMenu(self.frameGridLoopOptions,self.gridLoopMergeOptionsVar,self.gridLoopMergeOptionsVar.get(),*self.gridLoopMergeOptions)
    self.entryGridLoopOptions['padding']=2
    self.entryGridLoopOptions.pack(expand='true', fill='both', side='left')
    self.frameGridLoopOptions.pack(fill='x', side='bottom')


    self.frameGridLoopPadColourOptions = ttk.Frame(self.frameGridSettings)

    self.labelPadColourOptions = ttk.Label(self.frameGridLoopPadColourOptions)
    self.labelPadColourOptions.config(anchor='e', padding='2', text='Grid Pad Colour', width='25')
    self.labelPadColourOptions.pack(side='left')

    self.gridPadColourOptions = ttk.OptionMenu(self.frameGridLoopPadColourOptions,self.gridPadColourOptionsVar,self.gridPadColourOptionsVar.get(),*self.gridPadColourOptions)
    self.gridPadColourOptions['padding']=2
    self.gridPadColourOptions.pack(expand='true', fill='both', side='left')
    self.frameGridLoopPadColourOptions.pack(fill='x', side='bottom')

    self.frameGridLoopPadWidthOptions = ttk.Frame(self.frameGridSettings)

    self.labelPadWidthOptions = ttk.Label(self.frameGridLoopPadWidthOptions)
    self.labelPadWidthOptions.config(anchor='e', padding='2', text='Grid Pad width', width='25')
    self.labelPadWidthOptions.pack(side='left')

    self.gridPadWidthOptions = ttk.Spinbox(self.frameGridLoopPadWidthOptions, 
                                             from_=0, 
                                             to=float('inf'), 
                                             increment=1,
                                             textvariable=self.gridPadWidthVar)    
    self.gridPadWidthOptions.pack(expand='true', fill='both', side='left')
    self.frameGridLoopPadWidthOptions.pack(fill='x', side='bottom')


    # Settings for Grid Merge Ends


    self.frameEncodeSettings.config(height='200', padding='5', relief='groove', width='200')
    self.frameEncodeSettings.pack(fill='x', expand=True, ipadx='3', side='top')

    #self.frameSequenceValuesLeft = ttk.Frame(self.frameSequenceValues)
    #self.frameSequenceValuesRight = ttk.Frame(self.frameSequenceValues)

    # two column menu below

    self.frameSequenceValues.columnconfigure(0, weight=1)
    self.frameSequenceValues.columnconfigure(1, weight=100)
    self.frameSequenceValues.columnconfigure(2, weight=1)
    self.frameSequenceValues.columnconfigure(3, weight=100)


    self.frameSequenceValues.rowconfigure(0, weight=1)
    self.frameSequenceValues.rowconfigure(1, weight=1)
    self.frameSequenceValues.rowconfigure(2, weight=1)
    self.frameSequenceValues.rowconfigure(3, weight=1)
    self.frameSequenceValues.rowconfigure(4, weight=1)
    self.frameSequenceValues.rowconfigure(5, weight=1)


    self.labelOutputFormat = ttk.Label(self.frameSequenceValues)
    self.labelOutputFormat.config(anchor='e', text='Output format')
    self.labelOutputFormat.grid(row=0,column=0,sticky='e')

    self.comboboxOutputFormat= ttk.OptionMenu(self.frameSequenceValues,self.outputFormatVar,self.outputFormatVar.get(),*self.outputFormats)

    Tooltip(self.comboboxOutputFormat,text='The output format of the rendered video, nvenc GPU accelerated options require a nvidia graphics card.')

    self.comboboxOutputFormat['padding']=2
    self.comboboxOutputFormat.grid(row=0,column=1,sticky='ew')


    self.labelInitialBitrate = ttk.Label(self.frameSequenceValues)
    self.labelInitialBitrate.config(anchor='e', text='Initial Bitrate estimate (KB/s)', width='25')
    self.labelInitialBitrate.grid(row=1,column=0,sticky='e')

    self.entryInitialBitrate = ttk.Spinbox(self.frameSequenceValues, from_=0, to=float('inf'), increment=0.1)
    self.entryInitialBitrate.config(textvariable=self.initialbitrateVar)
    Tooltip(self.entryInitialBitrate,text='The initial bitrate guess, is overriden if you specify a maximum file size, otherwise used directly if maximum file size is zero.')
    self.entryInitialBitrate.grid(row=1,column=1,sticky='ew')


    self.labelMaxBitrate = ttk.Label(self.frameSequenceValues)
    self.labelMaxBitrate.config(anchor='e', text='Bitrate Cap (KB/s)', width='25')
    self.labelMaxBitrate.grid(row=2,column=0,sticky='e')

    self.entryMaxBitrate = ttk.Spinbox(self.frameSequenceValues, from_=0, to=float('inf'), increment=0.1)
    self.entryMaxBitrate.config(textvariable=self.maxbitrateVar)
    Tooltip(self.entryMaxBitrate,text='The maximum bitrate that will be tried.')
    self.entryMaxBitrate.grid(row=2,column=1,sticky='ew')


    self.labelFilenamePrefix = ttk.Label(self.frameSequenceValues)
    self.labelFilenamePrefix.config(anchor='e', text='Output filename prefix')
    self.labelFilenamePrefix.grid(row=0,column=2,sticky='e')

    self.filenamePrefixFrame = ttk.Frame(self.frameSequenceValues)

    self.entryFilenamePrefix = ttk.Entry(self.filenamePrefixFrame)
    self.entryFilenamePrefix.config(textvariable=self.filenamePrefixVar)
    Tooltip(self.entryFilenamePrefix,text='Manually specify the output filename (is also used as video \'title\' metdata).')
    self.entryFilenamePrefix.grid(row=0,column=0,sticky='ew')

    self.entryAutomaticFileNaming = ttk.Checkbutton(self.filenamePrefixFrame,text='Auto-name',onvalue=True, offvalue=False)
    self.entryAutomaticFileNaming.config(variable=self.automaticFileNamingVar)
    Tooltip(self.entryAutomaticFileNaming,text='When checked will attempt to use the input filename to automatically create the output filename.')
    self.entryAutomaticFileNaming.grid(row=0,column=1,sticky='ew')

    self.filenamePrefixFrame.columnconfigure(0, weight=100)
    self.filenamePrefixFrame.columnconfigure(1, weight=1)
    self.filenamePrefixFrame.rowconfigure(0, weight=1)

    self.filenamePrefixFrame.grid(row=0,column=3,sticky='ew')


  
    self.labelSizeStrategy = ttk.Label(self.frameSequenceValues)
    self.labelSizeStrategy.config(anchor='e',  text='Size Match Strategy')
    self.labelSizeStrategy.grid(row=1,column=2,sticky='e')
    
    self.comboboxSizeStrategy = ttk.OptionMenu(self.frameSequenceValues,self.frameSizeStrategyVar,self.frameSizeStrategyVar.get(),*self.frameSizeStrategies)
    Tooltip(self.comboboxSizeStrategy,text='When two clips of different aspect ratios are sequenced once after another, how the system attempts to manage the different in their frame sizes.')
    self.comboboxSizeStrategy['padding']=2
    self.comboboxSizeStrategy.grid(row=1,column=3,sticky='ew')

    self.labelMaximumSize = ttk.Label(self.frameSequenceValues)
    self.labelMaximumSize.config(anchor='e', text='Maximum File Size (MB)')
    self.labelMaximumSize.grid(row=3,column=0,sticky='e')

    self.entryMaximumSize = ttk.Spinbox(self.frameSequenceValues, from_=0, to=float('inf'), increment=0.1)
    Tooltip(self.entryMaximumSize,text='The maximum allowable fiel size for the output file, bitrate and other parameters will be tuned to get the maximumum quality but with a file size no greather than this, set as 0.0 to allow any size.')
    self.entryMaximumSize.config(textvariable=self.maximumSizeVar)
    self.entryMaximumSize.grid(row=3,column=1,sticky='ew')



    self.labelMaximumWidth = ttk.Label(self.frameSequenceValues)
    self.labelMaximumWidth.config(anchor='e', text='Limit largest dimension')
    self.labelMaximumWidth.grid(row=2,column=2,sticky='e')


    self.defaultMaxWidthWidthOptions = ['3840', '2560', '2048', '1920', '1600', '1440', '1280', '1024', '960', '854', '720', '640', '480']
    self.entryMaximumWidth = ttk.Combobox(self.frameSequenceValues)
    self.entryMaximumWidth.config(textvariable=self.maximumWidthVar)
    self.entryMaximumWidth.config(values=self.defaultMaxWidthWidthOptions)
    Tooltip(self.entryMaximumWidth,text='The maximum width or height, if either is greater the video will be scaled down, smaller videos left untouched.')
    self.entryMaximumWidth.grid(row=2,column=3,sticky='ew')



    self.labelAudioChannels = ttk.Label(self.frameSequenceValues)
    self.labelAudioChannels.config(anchor='e', padding='2', text='Audio Channels')
    self.labelAudioChannels.grid(row=4,column=0,sticky='e')
    self.entryAudioChannels = ttk.OptionMenu(self.frameSequenceValues,self.audioChannelsVar,self.audioChannelsVar.get(),*self.audioChannelsOptions)
    Tooltip(self.entryAudioChannels,text='The audio quality of the final video.')
    self.entryAudioChannels['padding']=2
    self.entryAudioChannels.grid(row=4,column=1,sticky='ew')




    self.labelSpeedChange = ttk.Label(self.frameSequenceValues)
    self.labelSpeedChange.config(anchor='e', text='Speed adjustment')
    self.labelSpeedChange.grid(row=3,column=2,sticky='e')




    self.speedChangeContainer = ttk.Frame(self.frameSequenceValues)

    self.entrySpeedChange = ttk.Spinbox(self.speedChangeContainer, 
                                         from_=0.5, 
                                         to=2.0, 
                                         increment=0.01,
                                         textvariable=self.speedAdjustmentVar)
    Tooltip(self.entrySpeedChange,text='Speed up or slow down the final video and audio.')
    self.entrySpeedChange.grid(row=0,column=0,sticky='ew')



    self.speedChangeInterpolate = ttk.Checkbutton(self.speedChangeContainer,text='Interpolate',onvalue=True, offvalue=False)
    self.speedChangeInterpolate.config(variable=self.interpolateSpeedChangeVar)
    Tooltip(self.speedChangeInterpolate,text='Use motion interpolation to speed up or slow down the final video.')
    self.speedChangeInterpolate.grid(row=0,column=1,sticky='e')

    self.speedChangeContainer.columnconfigure(0, weight=100)
    self.speedChangeContainer.columnconfigure(1, weight=1)
    self.speedChangeContainer.rowconfigure(0, weight=1)


    self.speedChangeContainer.grid(row=3,column=3,sticky='ew')    


    self.labelminimumPSNR = ttk.Label(self.frameSequenceValues)
    self.labelminimumPSNR.config(anchor='e', text='Minumum PSNR')
    self.labelminimumPSNR.grid(row=5,column=0,sticky='e')
    self.entryminimumPSNR = ttk.Spinbox(self.frameSequenceValues, 
                                         from_=0, 
                                         to=48, 
                                         increment=1,
                                         textvariable=self.minimumPSNRVar)
    Tooltip(self.entryminimumPSNR,text='Minimum acceptable video quality leave as zero to ignore.')
    self.entryminimumPSNR.grid(row=5,column=1,sticky='ew')


    self.labelpostOptimiser = ttk.Label(self.frameSequenceValues)
    self.labelpostOptimiser.config(anchor='e', text='Optimiser')
    self.labelpostOptimiser.grid(row=4,column=2,sticky='e')
    self.entrypostOptimiser = ttk.OptionMenu(self.frameSequenceValues,self.optimizerVar,self.optimizerVar.get(),*self.optimziers)
    Tooltip(self.entrypostOptimiser,text='Video optimiser to use to search for best video parameters.')
    self.entrypostOptimiser['padding']=2
    self.entrypostOptimiser.grid(row=4,column=3,sticky='ew')


    self.labelpostAudioOverride = ttk.Label(self.frameSequenceValues)
    self.labelpostAudioOverride.config(anchor='e',  text='Audio Dub')
    self.labelpostAudioOverride.grid(row=6,column=0,sticky='e')
    self.entrypostAudioOverride = ttk.Button(self.frameSequenceValues,textvariable=self.audioOverrideVar,command=self.selectAudioOverride)
    Tooltip(self.entrypostAudioOverride,text='An mp3 audio file to use to replace the original video audio.')
    self.entrypostAudioOverride['padding']=2
    self.entrypostAudioOverride.grid(row=6,column=1,sticky='ew')



    self.labelpostAudioOverrideDelay = ttk.Label(self.frameSequenceValues)
    self.labelpostAudioOverrideDelay.config(anchor='e',  text='Dub Delay (seconds)')
    self.labelpostAudioOverrideDelay.grid(row=5,column=2,sticky='e')
    self.entrypostAudioOverrideDelay = ttk.Spinbox(self.frameSequenceValues, textvariable=self.audiOverrideDelayVar,from_=float('-inf'), 
                                          to=float('inf'), 
                                          increment=0.5)
    Tooltip(self.entrypostAudioOverrideDelay,text='Delay before the start of the mp3 dub audio.')
    self.entrypostAudioOverrideDelay.grid(row=5,column=3,sticky='ew')

    

    self.labelaudiOverrideBias = ttk.Label(self.frameSequenceValues)
    self.labelaudiOverrideBias.config(anchor='e', text='Dub Mix Bias')
    self.labelaudiOverrideBias.grid(row=7,column=0,sticky='e')
    self.entryaudiOverrideBias = ttk.Spinbox(self.frameSequenceValues, 
                                         from_=0.0, 
                                         to=1.0, 
                                         increment=0.05,
                                         textvariable=self.audiOverrideBiasVar)
    Tooltip(self.entryaudiOverrideBias,text='Mix between the original video audio and the provided dub audio, 1 being all dub, 0 being all original video audio, 0.5 being a 50/50 mix.')
    self.entryaudiOverrideBias.grid(row=7,column=1,sticky='ew')



    self.labelpostProcessingFilter = ttk.Label(self.frameSequenceValues)
    self.labelpostProcessingFilter.config(anchor='e', text='Post filter')
    self.labelpostProcessingFilter.grid(row=6,column=2,sticky='e')
    self.entrypostProcessingFilter = ttk.OptionMenu(self.frameSequenceValues,self.postProcessingFilterVar,self.postProcessingFilterVar.get(),*self.postProcessingFilterOptions)
    Tooltip(self.entryaudiOverrideBias,text='A custom final filter to apply to all clips.')
    self.entrypostProcessingFilter['padding']=2
    self.entrypostProcessingFilter.grid(row=6,column=3,sticky='ew')


    
    self.comboboxTransStyle = ttk.Combobox(self.frameTransStyle,textvariable=self.transStyleVar,values=self.transStyles)
    #self.comboboxTransStyle['padding']=2
    Tooltip(self.comboboxTransStyle,text='The transition style to use between cuts, comma delimited lists are allowed and will cycle through multiple styles.')

    self.entryTransLoop = ttk.Checkbutton(self.frameTransStyle,text='Loop start to end',onvalue=True, offvalue=False)
    self.entryTransLoop.config(variable=self.loopStartAndendVar)
    self.entryTransLoop['padding']=2
    Tooltip(self.entryTransLoop,text='Trim a little from the start of the sequence and add it to a fade at the end so that it cycles as a perfect loop.')

    self.entryTransLoop.pack(expand='false', fill='x', side='right')

    self.buttonPreviewSequence = ttk.Button(self.frameTransStyle,text='Preview sequence timings',command=self.previewSequencetimings,style='small.TButton')
    self.buttonPreviewSequence.pack(expand='true', fill='x', side='bottom')

    self.comboboxTransStyle.pack(expand='true', fill='x', side='right')

    self.frameTransStyle.config(height='200', width='100')
    self.frameTransStyle.pack(expand='true', fill='x', side='top')

    self.frameSequenceValues.config(height='200', padding='2', width='200')
    self.frameSequenceValues.pack(anchor='nw', expand='true', fill='both', ipady='3', side='left')




    #self.frameSequenceValuesLeft.pack(expand='true', fill='x', side='left')
    #self.frameSequenceValuesRight.pack(expand='true', fill='x', side='left')


    self.labelframeEncodeProgress = ttk.Frame(self.labelframeSequenceFrame)

    self.encoderProgress=[
      
    ]

    self.labelframeEncodeProgress.config(height='10', width='200')
    self.labelframeEncodeProgress.pack(anchor='ne', expand='true', fill='x', padx='5', pady='5', side='top')
    self.frameMergeSelection.config(height='200', width='200')
    self.frameMergeSelection.pack(expand='true',fill='both', side='top')
    self.mainwindow = self.frameMergeSelection
    self.encodeRequestId=0
    self.selectableVideos={}
    self.selectedColumn = None
    self.player=None

  def previewSequencetimings(self):
    edlstr = '# mpv EDL v0\n'
    for sv in self.sequencedClips:
      fn = sv.filename
      start = sv.s
      end = sv.e
      if self.transDurationValue < (end-start):
        start += (self.transDurationValue/2)
        end   -= (self.transDurationValue/2)

      edlstr += '{},{},{}\n'.format(fn,start,end-start)
    open('pl.edl','wb').write(edlstr.encode('utf8'))

    if self.player is not None:
      self.player.terminate()

    self.player = mpv.MPV(loop='inf',
                          mute=True,
                          volume=0,
                          autofit_larger='1280')

    self.player.play('pl.edl')

    def quitFunc(key_state, key_name, key_char):
      def playerReaper():
        print('ReaperKill')
        player=self.player
        self.player=None
        player.terminate()
        player.wait_for_shutdown()
      self.playerReaper = threading.Thread(target=playerReaper,daemon=True)
      self.playerReaper.start()

    self.quitFunc = quitFunc
    self.player.register_key_binding("q", quitFunc)
    self.player.register_key_binding("Q", quitFunc)        
    self.player.register_key_binding("CLOSE_WIN", quitFunc)

  def deleteProfile(self):
    pass

  def saveProfile(self):
    pass

  def selectAudioOverride(self):
    files = askopenfilename(multiple=False,filetypes=[('mp3','*.mp3',),('wav','*.wav')])
    if files is None or len(files)==0:
      self.audioOverrideVar.set('None')
    else:
      self.audioOverrideVar.set(str(files))


  def addRow(self):
    column = GridColumn(self.gridColumnContainer,self)
    self.gridColumns.append({'column':column,'clips':[]})

  def addColumn(self):
    column = GridColumn(self.gridColumnContainer,self)
    self.gridColumns.append({'column':column,'clips':[]})

  def selectColumn(self,col):
    selectedCol = [x for x in self.gridColumns if x['column'] == col][0]
    if self.selectedColumn is not None:
      self.selectedColumn['column'].setSelected(False)
      self.selectedColumn = None
    self.selectedColumn = selectedCol
    self.selectedColumn['column'].setSelected(True)


  def removeColumn(self,col):
    colToRemove = [x for x in self.gridColumns if x['column'] == col][0]
    self.gridColumns.remove(colToRemove)
    col.pack_forget()
    if self.selectedColumn == colToRemove:
      self.selectedColumn = None


  def clearSequence(self):
    for sv in self.sequencedClips:
      sv.destroy()
    for col in self.gridColumns[::-1]:
      self.gridColumns.remove(col)
      col['column'].pack_forget()
    self.sequencedClips=[]
    self.gridColumns=[]
    for e in self.encoderProgress:
      e.remove()

  def profileChanged(self,*args):
    profileName = self.profileVar.get()

    for p in self.profileSpecs:
      if p['name'] == profileName:

        if p.get('editable',False):
          self.profileDelete.state(["disabled"])
        else:
          self.profileDelete.state(["!disabled"])

        for k,v in p.items():
          if k in self.editableProfileVars:
            attrName = k+'Var'
            if hasattr(self, attrName) and hasattr(getattr(self, attrName),'set'):
               print(attrName,getattr(self, attrName).get())
               getattr(self, attrName).set(v)
               print(attrName,getattr(self, attrName).get())

  def valueChange(self,*args):
    try:
      self.automaticFileNamingValue = self.automaticFileNamingVar.get()
      if self.automaticFileNamingValue:
        self.entryFilenamePrefix.state(["disabled"]) 
        self.labelFilenamePrefix.state(["disabled"]) 
      else:
        self.entryFilenamePrefix.state(["!disabled"]) 
        self.labelFilenamePrefix.state(["!disabled"]) 

    except:
      pass

    try:
      self.audioOverrideValue = self.audioOverrideVar.get()
      if self.audioOverrideValue.upper() == 'NONE':
        self.audioOverrideValue = None

    except:
      pass

    try:
      self.loopStartAndendValue = self.loopStartAndendVar.get()
    except:
      pass

    try:
      self.interpolateSpeedChangeValue = self.interpolateSpeedChangeVar.get()
    except:
      pass

    try:
      self.audiOverrideDelayValue = self.audiOverrideDelayVar.get()
    except:
      pass

    try:
      self.filenamePrefixValue = self.filenamePrefixVar.get()
    except:
      pass
    try:
      self.outputFormatValue = self.outputFormatVar.get()
    except:
      pass
    
    try:
      self.frameSizeStrategyValue = self.frameSizeStrategyVar.get()
    except:
      pass

    try:
      self.initialbitrateValue = float(self.initialbitrateVar.get())*1024
    except:
      pass

    try:
      self.maxbitrateValue = float(self.maxbitrateVar.get())*1024
    except:
      pass


    try:
      self.maximumSizeValue = float(self.maximumSizeVar.get())
    except:
      pass

    try:
      self.maximumWidthValue = int(float(self.maximumWidthVar.get()))
    except:
      pass

    try:
      self.transDurationValue = float(self.transDurationVar.get())
    except:
      pass

    try:
      self.transStyleValue = self.transStyleVar.get()
    except:
      pass

    try:
      self.speedAdjustmentValue = self.speedAdjustmentVar.get()
    except:
      pass

    try:
      self.audioChannels = self.audioChannelsVar.get()
    except:
      pass

    try:
      self.audioMerge = self.audioMergeOptionsVar.get()
    except:
      pass

    try:
      self.postProcessingFilter = self.postProcessingFilterVar.get()
    except:
      pass

    try:
      self.gridLoopMergeOption = self.gridLoopMergeOptionsVar.get()
    except:
      pass

    try:
      self.gridPadColour = self.gridPadColourOptionsVar.get()
    except:
      self.gridPadColour='Black'
      pass

    try:
      self.gridPadWidth = int(self.gridPadWidthVar.get())
    except:
      self.gridPadWidth=0
      pass

    try:
      self.minimumPSNR = self.minimumPSNRVar.get()
    except:
      pass

    try:
      self.optimizer = self.optimizerVar.get()
    except:
      pass

    try:
      self.audiOverrideBiasValue = max(0.0,min(1.0,float(self.audiOverrideBiasVar.get())),0)
    except:
      pass

    self.updatedPredictedDuration()
  

  def cancelEncodeRequest(self,requestId):
    self.controller.cancelEncodeRequest(requestId)

  def cancelAllEncodes(self):
    for epw in self.encoderProgress:
      epw.cancelEncodeRequest()

  def encodeCurrent(self):

    nullfilter = ''
    disableFilters = self.postProcessingFilterVar.get() == 'Disable all filters'

    if (not self.automaticFileNamingValue) and self.filenamePrefixValue is None or self.filenamePrefixValue.strip() == '':
      self.filenamePrefixValue = 'output'

    if self.mergeStyleVar.get().split('-')[0].strip()=='Stream Copy':
     
      for clip in self.sequencedClips:
        encodeSequence = []
        self.encodeRequestId+=1
        definition = (clip.rid,clip.filename,clip.s,clip.e,nullfilter if disableFilters else clip.filterexp,nullfilter if disableFilters else clip.filterexpEnc)
        encodeSequence.append(definition)
        if len(encodeSequence)>0:
          encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress,encodeRequestId=self.encodeRequestId,controller=self)
          self.encoderProgress.append(encodeProgressWidget)
          outputPrefix = self.filenamePrefixValue
          if self.automaticFileNamingValue:
            outputPrefix = self.convertFilenameToBaseName(clip.filename)
          self.controller.encode(self.encodeRequestId,
                                 'STREAMCOPY',
                                 encodeSequence,
                                 {},
                                 outputPrefix,
                                 encodeProgressWidget.updateStatus) 


    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      encodeSequence = []
      
      selectedColumnInd = 0

      for i,column in enumerate(self.gridColumns):
        outcol = []
        for clip in column['clips']:
          definition = (clip.rid,clip.filename,clip.s,clip.e,nullfilter if disableFilters else clip.filterexp, nullfilter if disableFilters else clip.filterexpEnc)
          outcol.append(definition)
          if column == self.selectedColumn:
            selectedColumnInd=i
        if len(outcol)>0:
          encodeSequence.append(outcol)
      if len(encodeSequence)==0:
        return

      self.encodeRequestId+=1
      options={
        'frameSizeStrategy':self.frameSizeStrategyValue,
        'maximumSize':self.maximumSizeValue,
        'initialBitrate':self.initialbitrateValue,
        'maximumBitrate':self.maxbitrateValue,
        'maximumWidth':self.maximumWidthValue,
        'transDuration':self.transDurationValue,
        'transStyle':self.transStyleValue,
        'speedAdjustment':self.speedAdjustmentValue,
        'speedAdjustmentInterploate':self.interpolateSpeedChangeValue,
        'outputFormat':self.outputFormatValue,
        'audioChannels':self.audioChannels,
        'audioMerge':self.audioMerge,
        'postProcessingFilter':self.postProcessingFilter,
        'selectedColumn':selectedColumnInd,
        'audioOverride':self.audioOverrideValue,
        'audiOverrideDelay':self.audiOverrideDelayValue,
        'gridLoopMergeOption':self.gridLoopMergeOption,
        'minimumPSNR':self.minimumPSNR,
        'optimizer':self.optimizer,
        'audioOverrideBias':self.audiOverrideBiasValue,
        'gridPaddingWidth':self.gridPadWidth,
        'gridPadColour':self.gridPadColour
      }

      encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress,encodeRequestId=self.encodeRequestId,controller=self,targetSize=self.maximumSizeValue)
      self.encoderProgress.append(encodeProgressWidget)
      outputPrefix = self.filenamePrefixValue
      if self.automaticFileNamingValue:
        try:
          print(encodeSequence)
          outputPrefix = self.convertFilenameToBaseName(encodeSequence[0][0][1])
        except Exception as e:
          print(e)

      self.controller.encode(self.encodeRequestId,
                             'GRID',
                             encodeSequence,
                             options.copy(),
                             outputPrefix,
                             encodeProgressWidget.updateStatus) 


    if self.mergeStyleVar.get().split('-')[0].strip() == 'Sequence':
      encodeSequence = []
      self.encodeRequestId+=1
      for clip in self.sequencedClips:
        definition = (clip.rid,clip.filename,clip.s,clip.e,nullfilter if disableFilters else clip.filterexp, nullfilter if disableFilters else clip.filterexpEnc)
        encodeSequence.append(definition)
      if len(encodeSequence)>0:
        options={
          'frameSizeStrategy':self.frameSizeStrategyValue,
          'maximumSize':self.maximumSizeValue,
          'initialBitrate':self.initialbitrateValue,
          'maximumBitrate':self.maxbitrateValue,
          'maximumWidth':self.maximumWidthValue,
          'transDuration':self.transDurationValue,
          'transStyle':self.transStyleValue,
          'speedAdjustment':self.speedAdjustmentValue,
          'speedAdjustmentInterploate':self.interpolateSpeedChangeValue,
          'outputFormat':self.outputFormatValue,
          'audioChannels':self.audioChannels,
          'audioMerge':self.audioMerge,
          'postProcessingFilter':self.postProcessingFilter,
          'audioOverride':self.audioOverrideValue,
          'audiOverrideDelay':self.audiOverrideDelayValue,
          'gridLoopMergeOption':self.gridLoopMergeOption,
          'minimumPSNR':self.minimumPSNR,
          'optimizer':self.optimizer,
          'audioOverrideBias':self.audiOverrideBiasValue,
          'loopStartAndEnd':self.loopStartAndendValue,
        }

        encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress,encodeRequestId=self.encodeRequestId,controller=self,targetSize=self.maximumSizeValue)
        self.encoderProgress.append(encodeProgressWidget)

        outputPrefix = self.filenamePrefixValue
        if self.automaticFileNamingValue:
          try:
            outputPrefix = self.convertFilenameToBaseName(self.sequencedClips[0].filename)
          except:
            pass

        self.controller.encode(self.encodeRequestId,
                               'CONCAT',
                               encodeSequence,
                               options.copy(),
                               outputPrefix,
                               encodeProgressWidget.updateStatus)

    if self.mergeStyleVar.get().split('-')[0].strip() == 'Individual Files':
      
      for clip in self.sequencedClips:
        encodeSequence = []
        self.encodeRequestId+=1
        definition = (clip.rid,clip.filename,clip.s,clip.e,nullfilter if disableFilters else clip.filterexp,nullfilter if disableFilters else clip.filterexpEnc)
        encodeSequence.append(definition)
        if len(encodeSequence)>0:
          options={
            'frameSizeStrategy':self.frameSizeStrategyValue,
            'maximumSize':self.maximumSizeValue,
            'initialBitrate':self.initialbitrateValue,
            'maximumBitrate':self.maxbitrateValue,
            'maximumWidth':self.maximumWidthValue,
            'transDuration':0.0,
            'transStyle':self.transStyleValue,
            'speedAdjustment':self.speedAdjustmentValue,
            'speedAdjustmentInterploate':self.interpolateSpeedChangeValue,
            'outputFormat':self.outputFormatValue,
            'audioChannels':self.audioChannels,
            'audioMerge':self.audioMerge,
            'postProcessingFilter':self.postProcessingFilter,
            'audioOverride':self.audioOverrideValue,
            'audiOverrideDelay':self.audiOverrideDelayValue,
            'gridLoopMergeOption':self.gridLoopMergeOption,
            'minimumPSNR':self.minimumPSNR,
            'optimizer':self.optimizer,
            'audioOverrideBias':self.audiOverrideBiasValue,
          }

          encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress,encodeRequestId=self.encodeRequestId,controller=self,targetSize=self.maximumSizeValue)
          self.encoderProgress.append(encodeProgressWidget)
          outputPrefix = self.filenamePrefixValue
          if self.automaticFileNamingValue:
            outputPrefix = self.convertFilenameToBaseName(clip.filename)

          self.controller.encode(self.encodeRequestId,
                                 'CONCAT',
                                 encodeSequence,
                                 options.copy(),
                                 outputPrefix,
                                 encodeProgressWidget.updateStatus) 
    self.outserScrolledFrame.reposition()


  def mergeStyleChanged(self,*args):
    if self.mergeStyleVar.get().split('-')[0].strip()=='Grid':
      self.scrolledframeSequenceContainer.pack_forget()
      self.gridSequenceContainer.pack(expand='true', fill='both', padx='5', pady='5', side='top')
      self.frameGridSettings.pack(fill='x', ipadx='3', side='top')
      self.frameTransStyle.pack_forget()
      self.frameTransDuration.pack_forget()
      self.frameTransitionSettings.pack_forget()
      self.frameMergeStyleSettings.pack(fill='x', ipadx='0', side='top')
      self.profileCombo.state(["!disabled"])
      self.frameSequenceValues.pack(anchor='nw', expand='true', fill='both', ipady='3', side='left')
    elif self.mergeStyleVar.get().split('-')[0].strip()=='Individual Files':
      self.gridSequenceContainer.pack_forget()
      self.frameGridSettings.pack_forget()
      self.frameTransDuration.pack_forget()
      self.frameTransStyle.pack_forget()
      self.frameTransitionSettings.pack_forget()
      self.frameMergeStyleSettings.pack(fill='x', ipadx='0', side='top')
      self.profileCombo.state(["!disabled"])
      self.scrolledframeSequenceContainer.pack(expand='true', fill='both', padx='0', pady='0', side='top')
      self.frameSequenceValues.pack(anchor='nw', expand='true', fill='both', ipady='3', side='left')
    elif self.mergeStyleVar.get().split('-')[0].strip()=='Sequence':
      self.gridSequenceContainer.pack_forget()
      self.frameGridSettings.pack_forget()
      self.scrolledframeSequenceContainer.pack(expand='true', fill='both', padx='0', pady='0', side='top')
      self.frameTransStyle.pack(expand='true', fill='x', side='top')
      self.frameTransDuration.pack(expand='true', fill='x', side='top')
      self.frameTransitionSettings.pack(fill='x', ipadx='3', side='top')
      self.frameMergeStyleSettings.pack(fill='x', ipadx='0', side='top')
      self.profileCombo.state(["!disabled"]) 
      self.frameSequenceValues.pack(anchor='nw', expand='true', fill='both', ipady='3', side='left')
    elif self.mergeStyleVar.get().split('-')[0].strip()=='Stream Copy':
      self.gridSequenceContainer.pack_forget()
      self.frameGridSettings.pack_forget()
      self.frameTransDuration.pack_forget()
      self.frameTransStyle.pack_forget()
      self.frameTransitionSettings.pack_forget()
      self.frameMergeStyleSettings.pack_forget()
      self.frameSequenceValues.pack_forget()
      self.profileVar.set('None')
      self.profileCombo.state(["disabled"]) 


      self.scrolledframeSequenceContainer.pack(expand='true', fill='both', padx='0', pady='0', side='top')

      
  def updatedPredictedDuration(self):
    totalTime=0
    timeTrimmedByFade=0
    for sv in self.sequencedClips:
      totalTime+=(sv.e-sv.s)
      timeTrimmedByFade+=self.transDurationValue 

    self.labelSequenceSummary.config(text='Number of Subclips: {n} Total subclip duration {td:0.2f}s Output Duration {tdext:0.2f}s'.format(
                                     n=len(self.sequencedClips),
                                     td=totalTime,
                                     tdext=totalTime-timeTrimmedByFade
                                    ))
    if self.automaticFileNamingVar.get():
      for sv in self.sequencedClips[:1]:        
        self.filenamePrefixVar.set( self.convertFilenameToBaseName(sv.filename) )
      else:
        namefound=False
        for col in self.gridColumns:
          for sv in col['clips']:
            try:
              self.filenamePrefixVar.set( self.convertFilenameToBaseName(sv.filename) )
              namefound = True
              break
            except Exception as e:
              print(e)
          if namefound:
            break 

  def convertFilenameToBaseName(self,filename):
    whitespaceChars = '-_. '
    usableChars = string.ascii_letters+string.digits+whitespaceChars
    basenameList = ''.join(x for x in os.path.basename(filename).rpartition('.')[0] if x in usableChars)
    for c in whitespaceChars:
      basenameList = basenameList.replace(c,'-')
    basename = ''
    for c in basenameList:
      if len(basename) == 0 or (basename[-1] != c and c == '-') or c != '-':
        basename = basename+c
    if len(basename)==0:
      basename='output'
    return basename

  def setController(self,controller):
    self.controller=controller
    self.updateProfileSpecs()

    for filterElem in self.postProcessingFilterOptions:
      if filterElem.upper() == self.controller.getDefaultPostFilter().upper():
        self.postProcessingFilterVar.set(filterElem)
        break



  def updateProfileSpecs(self):
    self.profileSpecs = self.controller.getProfiles()
    self.profiles = [x.get('name') for x in self.profileSpecs if x.get('name') is not None ]

    menu = self.profileCombo["menu"]
    menu.delete(0, "end")
    for string in self.profiles:
      menu.add_command(label=string,command=lambda value=string: self.profileVar.set(value))

    print(self.profiles)

    if self.defaultProfile in self.profiles:
      self.profileVar.set(self.defaultProfile)
    else:
      self.profileVar.set(self.profiles[0])


  def previewFrameCallback(self,requestId,timestamp,size,imageData):
    photoImage = tk.PhotoImage(data=imageData)
    for sv in self.selectableVideos.values():
      if sv.rid==requestId:
        sv.setPreviewImage(photoImage)
    for sv in self.sequencedClips:
      if sv.rid==requestId:
        sv.setPreviewImage(photoImage)

    self.scrolledframeInputCustContainer.reposition()
    self.scrolledframeSequenceContainer.reposition()

  def requestPreviewFrame(self,rid,filename,timestamp,filterexp):
    self.controller.requestPreviewFrame(rid,filename,timestamp,filterexp,(-1,80),self.previewFrameCallback)

  def addClipToSequence(self,clip):
    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      if self.selectedColumn == None:
        pass
      else:
        self.selectedColumn['clips'].append(
          SequencedVideoEntry(self.selectedColumn['column'],self,clip,direction='UP_DOWN'),
        )

    else:
      self.sequencedClips.append(
        SequencedVideoEntry(self.sequenceContainer,self,clip),
      )
      #self.scrolledframeInputCustContainer.xview(mode='moveto',value=0)
      #self.scrolledframeSequenceContainer.xview(mode='moveto',value=0)
      self.scrolledframeInputCustContainer._scrollBothNow()
      self.scrolledframeSequenceContainer._scrollBothNow()
    self.updatedPredictedDuration()

  def moveSequencedClip(self,clip,move):
    currentIndex = self.sequencedClips.index(clip)
    
    if 0<=currentIndex+move<len(self.sequencedClips):
      self.sequencedClips[currentIndex],self.sequencedClips[currentIndex+move] = self.sequencedClips[currentIndex+move],self.sequencedClips[currentIndex]
      for c in self.sequencedClips:
        c.pack_forget()
      for c in self.sequencedClips:
        c.pack(expand='false', fill='y', side='left')

    self.scrolledframeInputCustContainer.reposition()
    self.scrolledframeSequenceContainer.reposition()
    self.scrolledframeInputCustContainer._scrollBothNow()
    self.scrolledframeSequenceContainer._scrollBothNow()
      
  def removeSequencedClip(self,clip):
    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      for column in self.gridColumns:
        try:
          currentIndex = column['clips'].index(clip)
          removedClip = column['clips'].pop(currentIndex)
          removedClip.pack_forget()
          removedClip.destroy()
        except Exception as e:
          logging.error("removeSequencedClip Exception",exc_info=e)
    else:
      currentIndex = self.sequencedClips.index(clip)
      removedClip = self.sequencedClips.pop(currentIndex)
      removedClip.pack_forget()
      removedClip.destroy()
      #self.scrolledframeSequenceContainer.xview(mode='moveto',value=0)
      self.scrolledframeInputCustContainer._scrollBothNow()
      self.scrolledframeSequenceContainer._scrollBothNow()
      self.updatedPredictedDuration()

  def tabSwitched(self,tabName):
    if str(self) == tabName:
      unusedRids=set(self.selectableVideos.keys())
      for filename,rid,s,e,filterexp,filterexpEnc in sorted(self.controller.getFilteredClips(),key=lambda x:(x[0],x[2]) ):
        if rid in self.selectableVideos:
          unusedRids.remove(rid)
        if rid not in self.selectableVideos:
          self.selectableVideos[rid] = SelectableVideoEntry(self.selectableVideosContainer,self,filename,rid,s,e,filterexp,filterexpEnc)
        elif self.selectableVideos[rid].s != s or self.selectableVideos[rid].e != e or self.selectableVideos[rid].filterexp != filterexp:
           self.selectableVideos[rid].update(s,e,filterexp,filterexpEnc)

        for sv in self.sequencedClips:
          if sv.rid==rid:
            sv.update(s,e,filterexp,filterexpEnc)

      for rid in unusedRids:
        self.selectableVideos[rid].destroy()
        del self.selectableVideos[rid]
      self.updatedPredictedDuration()
    self.scrolledframeInputCustContainer.xview(mode='moveto',value=0)
    self.scrolledframeSequenceContainer.xview(mode='moveto',value=0)

    self.scrolledframeInputCustContainer._scrollBothNow()
    self.scrolledframeSequenceContainer._scrollBothNow()

  def addAllClipsInInterspersedOrder(self):
    finalOrder=[]
    clipsByFile  = {}
    for clip in sorted(self.selectableVideos.values(),key=lambda x:x.s,reverse=True):
      clipsByFile.setdefault(clip.filename,[]).append(clip)
    clipsByFile = list(clipsByFile.values())
    random.shuffle(clipsByFile)

    while sum([len(x) for x in clipsByFile])>0:
      for fileClips in clipsByFile:
        if len(fileClips)>0:
          finalOrder.append(fileClips.pop())

    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      self.clearAllColumns()
      for ind,clip in enumerate(finalOrder):
        self.gridColumns[ind%len(self.gridColumns)]['clips'].append(
          SequencedVideoEntry(self.gridColumns[ind%len(self.gridColumns)]['column'],self,clip,direction='UP_DOWN'),
        )
    else:
      self.clearSequence()
      for clip in finalOrder:
        self.addClipToSequence(clip)


  def addAllClipsInSmartRandomOrder(self):
    smartOrder = []
    smartCats  = {}
    for clip in sorted(self.selectableVideos.values(),key=lambda x:random.random()):
      smartCats.setdefault(clip.filename,[]).append(clip)
    smartCats = list(smartCats.values())
    random.shuffle(smartCats)

    lastList=None
    while sum([len(x) for x in smartCats])>0:
      smartCats = [x for x in smartCats if len(x)>0]
      if len(smartCats)==1:
        lastList=smartCats[0]
        smartOrder.append(lastList.pop())
      else:
        othercats = [x for x in smartCats if x != lastList]
        lastList = random.choice(othercats)
        smartOrder.append(lastList.pop())

    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      self.clearAllColumns()
      for ind,clip in enumerate(smartOrder):
        self.gridColumns[ind%len(self.gridColumns)]['clips'].append(
          SequencedVideoEntry(self.gridColumns[ind%len(self.gridColumns)]['column'],self,clip,direction='UP_DOWN'),
        )
    else:
      self.clearSequence()
      for clip in smartOrder:
        self.addClipToSequence(clip)



  def addAllClipsInRandomOrder(self):
    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      self.clearAllColumns()
      for ind,clip in enumerate(sorted(self.selectableVideos.values(),key=lambda x:random.random())):
        self.gridColumns[ind%len(self.gridColumns)]['clips'].append(
          SequencedVideoEntry(self.gridColumns[ind%len(self.gridColumns)]['column'],self,clip,direction='UP_DOWN'),
        )
    else:
      self.clearSequence()
      for clip in sorted(self.selectableVideos.values(),key=lambda x:random.random()):
        self.addClipToSequence(clip)

  def clearAllColumns(self):
    for column in self.gridColumns:
      while len(column['clips'])>0:
        removedClip = column['clips'].pop()
        removedClip.pack_forget()
        removedClip.destroy()    

  def addAllClipsInTimelineOrder(self):
    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      self.clearAllColumns()
      for ind,clip in enumerate(sorted(self.selectableVideos.values(),key=lambda x:(x.filename,x.s))):
        self.gridColumns[ind%len(self.gridColumns)]['clips'].append(
          SequencedVideoEntry(self.gridColumns[ind%len(self.gridColumns)]['column'],self,clip,direction='UP_DOWN'),
        )

    else:
      self.clearSequence()
      for clip in sorted(self.selectableVideos.values(),key=lambda x:(x.filename,x.s)):
        self.addClipToSequence(clip)



if __name__ == '__main__':
  import webmGenerator

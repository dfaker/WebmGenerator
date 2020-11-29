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


class EncodeProgress(ttk.Frame):
  def __init__(self, master=None, *args, encodeRequestId=None,controller=None, **kwargs):
    ttk.Frame.__init__(self, master)
    self.frameEncodeProgressWidget = self
    self.encodeRequestId = encodeRequestId
    self.cancelled = False
    self.controller = controller

    self.labelEncodeProgressLabel = ttk.Label(self.frameEncodeProgressWidget)
    self.labelEncodeProgressLabel.config(text='Encode request submitted', width='60')
    self.labelEncodeProgressLabel.pack(side='left')
    self.progressbarEncodeProgressLabel = ttk.Progressbar(self.frameEncodeProgressWidget)
    self.progressbarEncodeProgressLabel.config(mode='determinate', orient='horizontal')
    self.progressbarEncodeProgressLabel.pack(expand='true',padx=10, fill='x', side='left')

    self.labelTimeLeft  = ttk.Label(self.frameEncodeProgressWidget)
    self.labelTimeLeft.config(text='', width='19')
    self.labelTimeLeft.pack(side='left')

    self.progressbarEncodeCancelButton = ttk.Button(self.frameEncodeProgressWidget)
    self.progressbarEncodeCancelButton.config(text='Cancel', width=10)
    self.progressbarEncodeCancelButton.config(command=self.cancelEncodeRequest)
    self.progressbarEncodeCancelButton.config(style="small.TButton")
    self.progressbarEncodeCancelButton.pack(expand='false',padx=0, fill='x', side='left')


    self.progressbarPlayButton = ttk.Button(self.frameEncodeProgressWidget)
    self.progressbarPlayButton.config(text='Play', width=10)
    self.progressbarPlayButton.config(command=self.playFinal)
    self.progressbarPlayButton.config(style="small.TButton")
    

    self.frameEncodeProgressWidget.config(height='200', width='200')
    self.frameEncodeProgressWidget.pack(anchor='nw', expand='false',padx=10,pady=10, fill='x', side='top')
    self.progresspercent = 0
    self.encodeStartTime = None
    self.progressQueue    = deque([],10)
    self.timestampQueue   = deque([],10)
    self.finalFilename    = None
    self.player = None

  def playFinal(self):
    if self.finalFilename is not None:

      if self.player is not None:
        self.player.terminate()

      self.player = mpv.MPV(loop='inf',
                            mute=True,
                            volume=0,
                            autofit_larger='1280')

      self.player.play(self.finalFilename)

      def quit(key_state, key_name, key_char):
        self.player.terminate()
        self.player = None
      
      self.player.register_key_binding("q", quit) 
      self.player.register_key_binding("Q", quit)        
      self.player.register_key_binding("CLOSE_WIN", quit)

  def cancelEncodeRequest(self):
    self.cancelled = True
    self.progressbarEncodeProgressLabel.config(style="Red.Horizontal.TProgressbar")
    self.progressbarEncodeProgressLabel['value']=100
    self.labelTimeLeft.config(text='Cancelled')
    self.progresspercent = 100
    self.progressbarEncodeCancelButton.pack_forget()
    self.labelEncodeProgressLabel.config(text='Cancelled')
    self.controller.cancelEncodeRequest(self.encodeRequestId)

  def updateStatus(self,status,percent,finalFilename=None):
    if self.cancelled:
      return
    if finalFilename is not None:
      self.finalFilename = finalFilename
    print(finalFilename)


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
        self.labelTimeLeft.config(text=str(round(remaining,2))+'s left')
      except:
        pass
      
    self.labelEncodeProgressLabel.config(text=status)
    self.progressbarEncodeProgressLabel['value']=percent*100
    self.progresspercent = percent*100

    if percent >= 1:
      self.labelTimeLeft.config(text='Complete in {}s'.format( str(round(time.time() - self.encodeStartTime,2)) ))
      self.progressbarEncodeProgressLabel.config(style="Green.Horizontal.TProgressbar")
      self.progressbarEncodeCancelButton.pack_forget()
      if self.finalFilename is not None:
        self.progressbarPlayButton.pack(expand='false',padx=0, fill='x', side='left')
    else:
      self.progressbarEncodeProgressLabel.config(style="Blue.Horizontal.TProgressbar")
      self.progressbarEncodeCancelButton.pack(expand='false',padx=0, fill='x', side='left')

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

    self.player.register_key_binding("CLOSE_WIN", "quit")
    
    def quit(key_state, key_name, key_char):
      self.player.terminate()
            
    self.player.register_key_binding("CLOSE_WIN", quit)

  def moveForwards(self):
    self.controller.moveSequencedClip(self,1)    

  def moveBack(self):
    self.controller.moveSequencedClip(self,-1)

  def remove(self):
    self.controller.removeSequencedClip(self)

  def setPreviewImage(self,photoImage):
    self.previewImage=photoImage
    self.canvasSequencePreview.config(image=self.previewImage)

  def update(self,s,e,filterexp):
    self.s=s
    self.e=e
    self.filterexp=filterexp
    self.labelSequenceVideoName.config(text='{:0.2f}-{:0.2f} {:0.2f}s'.format(self.s,self.e,self.e-self.s))
    self.controller.requestPreviewFrame(self.rid,self.filename,(self.e+self.s)/2,self.filterexp)


class GridColumn(ttk.Labelframe):
  def __init__(self, master,controller):
    ttk.Labelframe.__init__(self, master)
    self.master=master
    self.controller=controller
    self.config(relief='groove',padding='4')

    self.buttonFrame = ttk.Frame(self)
    self.selectColumnBtn = ttk.Button(self.buttonFrame,text='Select ✔',command=self.selectColumn)
    self.selectColumnBtn.config(style="small.TButton")
    self.selectColumnBtn.pack(expand='true', fill='x', side='left')


    self.removeColumnBtn = ttk.Button(self.buttonFrame,text='Remove ✖',command=self.removeColumn)
    self.removeColumnBtn.config(style="small.TButton")
    self.removeColumnBtn.pack(expand='true', fill='x', side='left')

    self.buttonFrame.pack(expand='false', fill='x', side='bottom')

    self.pack(expand='false', fill='y', side='left')

  def setSelected(self,isSelected):
    if isSelected:
      self.config(relief='sunken',text='Selected')
      self.selectColumnBtn.config(text='Selected ✔',style="smallBlue.TButton")

      
    else:
      self.config(relief='groove',text='')
      self.selectColumnBtn.config(text='Select ✔',style="small.TButton")


  def selectColumn(self):
    self.controller.selectColumn(self)

  def removeColumn(self):
    self.controller.removeColumn(self)


class SelectableVideoEntry(ttk.Frame):
  def __init__(self, master,controller,filename,rid,s,e,filterexp, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.master=master
    self.rid=rid
    self.s=s
    self.e=e
    self.controller=controller
    self.filename=filename
    self.filterexp=filterexp
    self.basename = os.path.basename(filename)[:14]
    self.player=None

    self.frameInputCutWidget = self
    self.labelInputCutName = ttk.Label(self.frameInputCutWidget)
    self.labelInputCutName.config(text='{:0.2f}-{:0.2f} {:0.2f}s'.format(self.s,self.e,self.e-self.s))
    self.labelInputCutName.pack(side='top')
    
    self.previewData = "P5\n124 80\n255\n"+("0"*80*124)
    self.previewImage= tk.PhotoImage(data=self.previewData)  
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

  def update(self,s,e,filterexp):
    self.s=s
    self.e=e
    self.filterexp=filterexp
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

    self.player.register_key_binding("CLOSE_WIN", "quit")
    
    def quit(key_state, key_name, key_char):
      self.player.terminate()
            
    self.player.register_key_binding("CLOSE_WIN", quit)


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

    self.profiles   = [x['name'] for x in self.profileSpecs]

    if self.defaultProfile in self.profiles:
      self.profileVar.set(defaultProfile)
    else:
      self.profileVar.set(self.profiles[0])

    self.profileCombo = ttk.OptionMenu(self.profileFrame,self.profileVar,self.profileVar.get(),*self.profiles)
    self.profileCombo.pack(expand='true', fill='x', side='right')

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

    self.addAddClipsFrame.pack(expand='false', fill='x', padx='0', pady='0', side='top')

    self.labelframeSequenceFrame = ttk.Labelframe(self.frameMergeSelection)

    self.outputPlanningContainer = ttk.Frame(self.labelframeSequenceFrame)
    self.outputPlanningContainer.pack(expand='false', fill='both', padx='0', pady='0', side='top')

    self.labelframeSequenceFrame.config(height='200', text='Output Plan', width='200')
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

    self.automaticFileNamingVar   = tk.BooleanVar() 
    self.filenamePrefixVar        = tk.StringVar()
    self.outputFormatVar          = tk.StringVar()
    self.frameSizeStrategyVar     = tk.StringVar()
    self.maximumSizeVar           = tk.StringVar()
    self.maximumWidthVar          = tk.StringVar()
    self.transDurationVar         = tk.StringVar()
    self.transStyleVar            = tk.StringVar()
    self.speedAdjustmentVar       = tk.StringVar() 
    self.audioChannelsVar         = tk.StringVar()
    self.audioMergeOptionsVar     = tk.StringVar()
    self.gridLoopMergeOptionsVar  = tk.StringVar()
    self.postProcessingFilterVar  = tk.StringVar()

    self.audioOverrideVar         = tk.StringVar()
    self.audiOverrideDelayVar     = tk.StringVar()

    self.automaticFileNamingVar.trace('w',self.valueChange)
    self.filenamePrefixVar.trace('w',self.valueChange)
    self.outputFormatVar.trace('w',self.valueChange)
    self.frameSizeStrategyVar.trace('w',self.valueChange)
    self.maximumSizeVar.trace('w',self.valueChange)
    self.maximumWidthVar.trace('w',self.valueChange)
    self.transDurationVar.trace('w',self.valueChange)
    self.transStyleVar.trace('w',self.valueChange)
    self.speedAdjustmentVar.trace('w',self.valueChange)
    self.audioChannelsVar.trace('w',self.valueChange)
    self.audioMergeOptionsVar.trace('w',self.valueChange)
    self.gridLoopMergeOptionsVar.trace('w',self.valueChange)
    self.postProcessingFilterVar.trace('w',self.valueChange)

    self.audioOverrideVar.trace('w',self.valueChange)
    self.audiOverrideDelayVar.trace('w',self.valueChange)

    self.automaticFileNamingVar.set(True)
    self.filenamePrefixVar.set('Sequence')

    self.audioOverrideVar.set('None')
    self.audiOverrideDelayVar.set('0')

    self.outputFormats = [
      'mp4:x264',
      'webm:VP8',
      'webm:VP9',
      'gif',      
    ]
    self.outputFormatVar.set(self.outputFormats[0])

    self.frameSizeStrategies = [
      'Rescale to largest with black bars',
      'Rescale to largest and center crop smaller',    
    ]
    self.frameSizeStrategyVar.set(self.frameSizeStrategies[0])

    self.maximumSizeVar.set('0.0')
    self.maximumWidthVar.set('1280')
    self.transDurationVar.set('0.0')       

    self.transStyles = ['fade','wipeleft','wiperight','wipeup'
    ,'wipedown','slideleft','slideright','slideup','slidedown'
    ,'circlecrop','rectcrop','distance','fadeblack','fadewhite'
    ,'radial','smoothleft','smoothright','smoothup','smoothdown'
    ,'circleopen','circleclose','vertopen','vertclose','horzopen'
    ,'horzclose','dissolve','pixelize','diagtl','diagtr','diagbl'
    ,'diagbr','hlslice','hrslice','vuslice','vdslice']
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
      ,'No audio'
    ]

    self.audioChannelsVar.set(self.audioChannelsOptions[6])    

    self.audioMergeOptions = ['Merge Normalize All','Merge Original Volume','Selected Column Only','Largest Cell by Area','Adaptive Loudest Cell']
    self.audioMergeOptionsVar.set(self.audioMergeOptions[0]) 

    self.gridLoopMergeOptions = ['End on shortest Clip','Loop shorter clips to match longest']
    self.gridLoopMergeOptionsVar.set(self.gridLoopMergeOptions[0])

    self.postProcessingFilterOptions = ['None']
    for f in os.listdir('.'):
      if f.upper().endswith('TXT') and f.upper().startswith('POSTFILTER-'):
        self.postProcessingFilterOptions.append(f)
    self.postProcessingFilterVar.set(self.postProcessingFilterOptions[0])
    for filterElem in self.postProcessingFilterOptions:
      if 'DEFAULT' in filterElem.upper():
        self.postProcessingFilterVar.set(filterElem)

    self.frameSequenceActions = ttk.Frame(self.frameEncodeSettings)
    self.buttonSequenceClear = ttk.Button(self.frameSequenceActions)
    self.buttonSequenceClear.config(text='Clear Sequence')
    self.buttonSequenceClear.config(command=self.clearSequence)
    self.buttonSequenceClear.pack(side='top')

    self.buttonSequenceEncode = ttk.Button(self.frameSequenceActions)
    self.buttonSequenceEncode.config(text='Encode')
    self.buttonSequenceEncode.config(command=self.encodeCurrent)
    self.buttonSequenceEncode.pack(expand='true', fill='both', side='top')
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
    self.entryAudioMerge.pack(expand='true', fill='both', side='left')

    self.frameAudioMerge.pack(fill='x', side='top')


    self.frameGridLoopOptions = ttk.Frame(self.frameGridSettings)

    self.labelGridLoopOptions = ttk.Label(self.frameGridLoopOptions)
    self.labelGridLoopOptions.config(anchor='e', padding='2', text='Grid Loop Option', width='25')
    self.labelGridLoopOptions.pack(side='left')
    
    self.entryGridLoopOptions = ttk.OptionMenu(self.frameGridLoopOptions,self.gridLoopMergeOptionsVar,self.gridLoopMergeOptionsVar.get(),*self.gridLoopMergeOptions)
    self.entryGridLoopOptions.pack(expand='true', fill='both', side='left')
    self.frameGridLoopOptions.pack(fill='x', side='bottom')


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

    self.labelAutomaticFileNaming = ttk.Label(self.frameSequenceValues)
    self.labelAutomaticFileNaming.config(anchor='e', padding='2', text='Automatically name output files', width='25')
    self.labelAutomaticFileNaming.grid(row=0,column=0,sticky='e')

    self.entryAutomaticFileNaming = ttk.Checkbutton(self.frameSequenceValues,text='',onvalue=True, offvalue=False)
    self.entryAutomaticFileNaming.config(width='5',variable=self.automaticFileNamingVar)
    self.entryAutomaticFileNaming.grid(row=0,column=1,sticky='ew')

    self.labelFilenamePrefix = ttk.Label(self.frameSequenceValues)
    self.labelFilenamePrefix.config(anchor='e', padding='2', text='Output filename prefix')
    self.labelFilenamePrefix.grid(row=0,column=2,sticky='e')

    self.entryFilenamePrefix = ttk.Entry(self.frameSequenceValues)
    self.entryFilenamePrefix.config(textvariable=self.filenamePrefixVar)
    self.entryFilenamePrefix.grid(row=0,column=3,sticky='ew')

    self.labelOutputFormat = ttk.Label(self.frameSequenceValues)
    self.labelOutputFormat.config(anchor='e', padding='2', text='Output format')
    self.labelOutputFormat.grid(row=1,column=0,sticky='e')

    self.comboboxOutputFormat= ttk.OptionMenu(self.frameSequenceValues,self.outputFormatVar,self.outputFormatVar.get(),*self.outputFormats)
    self.comboboxOutputFormat.grid(row=1,column=1,sticky='ew')

  
    self.labelSizeStrategy = ttk.Label(self.frameSequenceValues)
    self.labelSizeStrategy.config(anchor='e', padding='2', text='Size Match Strategy')
    self.labelSizeStrategy.grid(row=1,column=2,sticky='e')
    
    self.comboboxSizeStrategy = ttk.OptionMenu(self.frameSequenceValues,self.frameSizeStrategyVar,self.frameSizeStrategyVar.get(),*self.frameSizeStrategies)
    self.comboboxSizeStrategy.grid(row=1,column=3,sticky='ew')

    self.labelMaximumSize = ttk.Label(self.frameSequenceValues)
    self.labelMaximumSize.config(anchor='e', padding='2', text='Maximum File Size (MB)')
    self.labelMaximumSize.grid(row=2,column=0,sticky='e')

    self.entryMaximumSize = ttk.Spinbox(self.frameSequenceValues, from_=0, to=float('inf'), increment=0.1)
    self.entryMaximumSize.config(textvariable=self.maximumSizeVar)
    self.entryMaximumSize.grid(row=2,column=1,sticky='ew')



    self.labelMaximumWidth = ttk.Label(self.frameSequenceValues)
    self.labelMaximumWidth.config(anchor='e', padding='2', text='Limit largest dimension')
    self.labelMaximumWidth.grid(row=2,column=2,sticky='e')
    self.entryMaximumWidth = ttk.Spinbox(self.frameSequenceValues, 
                                         from_=0, 
                                         to=float('inf'), 
                                         increment=1,
                                         textvariable=self.maximumWidthVar)
    self.entryMaximumWidth.grid(row=2,column=3,sticky='ew')



    self.labelAudioChannels = ttk.Label(self.frameSequenceValues)
    self.labelAudioChannels.config(anchor='e', padding='2', text='Audio Channels')
    self.labelAudioChannels.grid(row=3,column=0,sticky='e')
    self.entryAudioChannels = ttk.OptionMenu(self.frameSequenceValues,self.audioChannelsVar,self.audioChannelsVar.get(),*self.audioChannelsOptions)
    self.entryAudioChannels.grid(row=3,column=1,sticky='ew')


    self.labelSpeedChange = ttk.Label(self.frameSequenceValues)
    self.labelSpeedChange.config(anchor='e', padding='2', text='Speed adjustment')
    self.labelSpeedChange.grid(row=3,column=2,sticky='e')
    self.entrySpeedChange = ttk.Spinbox(self.frameSequenceValues, 
                                         from_=0.5, 
                                         to=2.0, 
                                         increment=0.01,
                                         textvariable=self.speedAdjustmentVar)
    self.entrySpeedChange.grid(row=3,column=3,sticky='ew')


    self.labelpostProcessingFilter = ttk.Label(self.frameSequenceValues)
    self.labelpostProcessingFilter.config(anchor='e', padding='2', text='Post filter')
    self.labelpostProcessingFilter.grid(row=4,column=2,sticky='e')
    self.entrypostProcessingFilter = ttk.OptionMenu(self.frameSequenceValues,self.postProcessingFilterVar,self.postProcessingFilterVar.get(),*self.postProcessingFilterOptions)
    self.entrypostProcessingFilter.grid(row=4,column=3,sticky='ew')


    self.labelpostAudioOverride = ttk.Label(self.frameSequenceValues)
    self.labelpostAudioOverride.config(anchor='e', padding='2', text='Audio Dub')
    self.labelpostAudioOverride.grid(row=5,column=0,sticky='e')
    self.entrypostAudioOverride = ttk.Button(self.frameSequenceValues,textvariable=self.audioOverrideVar,command=self.selectAudioOverride)
    self.entrypostAudioOverride.grid(row=5,column=1,sticky='ew')



    self.labelpostAudioOverrideDelay = ttk.Label(self.frameSequenceValues)
    self.labelpostAudioOverrideDelay.config(anchor='e', padding='2', text='Dub Delay (seconds)')
    self.labelpostAudioOverrideDelay.grid(row=5,column=2,sticky='e')
    self.entrypostAudioOverrideDelay = ttk.Spinbox(self.frameSequenceValues, textvariable=self.audiOverrideDelayVar,from_=float('-inf'), 
                                          to=float('inf'), 
                                          increment=0.5)
    self.entrypostAudioOverrideDelay.grid(row=5,column=3,sticky='ew')

    






    
    self.comboboxTransStyle = ttk.OptionMenu(self.frameTransStyle,self.transStyleVar,self.transStyleVar.get(),*self.transStyles)

    self.comboboxTransStyle.pack(expand='true', fill='x', side='right')

    self.frameTransStyle.config(height='200', width='100')
    self.frameTransStyle.pack(expand='true', fill='x', side='top')

    self.frameSequenceValues.config(height='200', padding='2', width='200')
    self.frameSequenceValues.pack(anchor='nw', expand='true', fill='both', ipady='3', side='left')




    #self.frameSequenceValuesLeft.pack(expand='true', fill='x', side='left')
    #self.frameSequenceValuesRight.pack(expand='true', fill='x', side='left')


    self.labelframeEncodeProgress = ScrolledFrame(self.labelframeSequenceFrame,usemousewheel=True,scrolltype='vertical',)

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

  def selectAudioOverride(self):
    files = askopenfilename(multiple=False,filetypes=[('mp3','*.mp3',),('wav','*.wav')])
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
        for k,v in p.items():
          attrName = k+'Var'
          if hasattr(self, attrName) and hasattr(getattr(self, attrName),'set'):
             getattr(self, attrName).set(v)

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


    self.updatedPredictedDuration()
  

  def cancelEncodeRequest(self,requestId):
    self.controller.cancelEncodeRequest(requestId)

  def encodeCurrent(self):


    if self.mergeStyleVar.get().split('-')[0].strip()=='Stream Copy':
     
      for clip in self.sequencedClips:
        encodeSequence = []
        self.encodeRequestId+=1
        definition = (clip.rid,clip.filename,clip.s,clip.e,clip.filterexp)
        encodeSequence.append(definition)
        if len(encodeSequence)>0:
          encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress.innerframe,encodeRequestId=self.encodeRequestId,controller=self)
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
          self.labelframeEncodeProgress.reposition()


    if self.mergeStyleVar.get().split('-')[0].strip() == 'Grid':
      encodeSequence = []
      
      selectedColumnInd = 0

      for i,column in enumerate(self.gridColumns):
        outcol = []
        for clip in column['clips']:
          definition = (clip.rid,clip.filename,clip.s,clip.e,clip.filterexp)
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
        'maximumWidth':self.maximumWidthValue,
        'transDuration':self.transDurationValue,
        'transStyle':self.transStyleValue,
        'speedAdjustment':self.speedAdjustmentValue,
        'outputFormat':self.outputFormatValue,
        'audioChannels':self.audioChannels,
        'audioMerge':self.audioMerge,
        'postProcessingFilter':self.postProcessingFilter,
        'selectedColumn':selectedColumnInd,
        'audioOverride':self.audioOverrideValue,
        'audiOverrideDelay':self.audiOverrideDelayValue,
        'gridLoopMergeOption':self.gridLoopMergeOption
      }

      encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress.innerframe,encodeRequestId=self.encodeRequestId,controller=self)
      self.encoderProgress.append(encodeProgressWidget)
      outputPrefix = self.filenamePrefixValue
      if self.automaticFileNamingValue:
        try:
          outputPrefix = self.convertFilenameToBaseName(encodeSequence[0][0].filename)
        except:
          pass
      self.controller.encode(self.encodeRequestId,
                             'GRID',
                             encodeSequence,
                             options.copy(),
                             outputPrefix,
                             encodeProgressWidget.updateStatus) 
      self.labelframeEncodeProgress.reposition()


    if self.mergeStyleVar.get().split('-')[0].strip() == 'Sequence':
      encodeSequence = []
      self.encodeRequestId+=1
      for clip in self.sequencedClips:
        definition = (clip.rid,clip.filename,clip.s,clip.e,clip.filterexp)
        encodeSequence.append(definition)
      if len(encodeSequence)>0:
        options={
          'frameSizeStrategy':self.frameSizeStrategyValue,
          'maximumSize':self.maximumSizeValue,
          'maximumWidth':self.maximumWidthValue,
          'transDuration':self.transDurationValue,
          'transStyle':self.transStyleValue,
          'speedAdjustment':self.speedAdjustmentValue,
          'outputFormat':self.outputFormatValue,
          'audioChannels':self.audioChannels,
          'audioMerge':self.audioMerge,
          'postProcessingFilter':self.postProcessingFilter,
          'audioOverride':self.audioOverrideValue,
          'audiOverrideDelay':self.audiOverrideDelayValue,
          'gridLoopMergeOption':self.gridLoopMergeOption
        }

        encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress.innerframe,encodeRequestId=self.encodeRequestId,controller=self)
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

        self.labelframeEncodeProgress.reposition()

    if self.mergeStyleVar.get().split('-')[0].strip() == 'Individual Files':
      
      for clip in self.sequencedClips:
        encodeSequence = []
        self.encodeRequestId+=1
        definition = (clip.rid,clip.filename,clip.s,clip.e,clip.filterexp)
        encodeSequence.append(definition)
        if len(encodeSequence)>0:
          options={
            'frameSizeStrategy':self.frameSizeStrategyValue,
            'maximumSize':self.maximumSizeValue,
            'maximumWidth':self.maximumWidthValue,
            'transDuration':0.0,
            'transStyle':self.transStyleValue,
            'speedAdjustment':self.speedAdjustmentValue,
            'outputFormat':self.outputFormatValue,
            'audioChannels':self.audioChannels,
            'audioMerge':self.audioMerge,
            'postProcessingFilter':self.postProcessingFilter,
            'audioOverride':self.audioOverrideValue,
            'audiOverrideDelay':self.audiOverrideDelayValue,
            'gridLoopMergeOption':self.gridLoopMergeOption
          }

          encodeProgressWidget = EncodeProgress(self.labelframeEncodeProgress.innerframe,encodeRequestId=self.encodeRequestId,controller=self)
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
          self.labelframeEncodeProgress.reposition()

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
      timeTrimmedByFade+=self.transDurationValue*2 

    self.labelSequenceSummary.config(text='Number of Subclips: {n} Total subclip duration {td}s Output Duration {tdext}s'.format(
                                     n=len(self.sequencedClips),
                                     td=totalTime,
                                     tdext=totalTime-timeTrimmedByFade
                                    ))
    if self.filenamePrefixVar.get().strip() in ('','Sequence'):
      for sv in self.sequencedClips[:1]:        
        self.filenamePrefixVar.set( self.convertFilenameToBaseName(sv.filename) )

  def convertFilenameToBaseName(self,filename):
    usableChars = string.ascii_letters+string.digits+'-_'
    basename = ''.join(x for x in os.path.basename(filename).rpartition('.')[0] if x in usableChars)
    return basename

  def setController(self,controller):
    self.controller=controller

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
      self.scrolledframeInputCustContainer.xview(mode='moveto',value=0)
      self.scrolledframeSequenceContainer.xview(mode='moveto',value=0)
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
      self.scrolledframeSequenceContainer.xview(mode='moveto',value=0)
      self.scrolledframeInputCustContainer._scrollBothNow()
      self.scrolledframeSequenceContainer._scrollBothNow()
      self.updatedPredictedDuration()

  def tabSwitched(self,tabName):
    if str(self) == tabName:
      unusedRids=set(self.selectableVideos.keys())
      for filename,rid,s,e,filterexp in sorted(self.controller.getFilteredClips(),key=lambda x:(x[0],x[2]) ):
        if rid in self.selectableVideos:
          unusedRids.remove(rid)
        if rid not in self.selectableVideos:
          self.selectableVideos[rid] = SelectableVideoEntry(self.selectableVideosContainer,self,filename,rid,s,e,filterexp)
        elif self.selectableVideos[rid].s != s or self.selectableVideos[rid].e != e or self.selectableVideos[rid].filterexp != filterexp:
           self.selectableVideos[rid].update(s,e,filterexp)

        for sv in self.sequencedClips:
          if sv.rid==rid:
            sv.update(s,e,filterexp)

      for rid in unusedRids:
        self.selectableVideos[rid].destroy()
        del self.selectableVideos[rid]
      self.updatedPredictedDuration()
    self.scrolledframeInputCustContainer.xview(mode='moveto',value=0)
    self.scrolledframeSequenceContainer.xview(mode='moveto',value=0)

    self.scrolledframeInputCustContainer._scrollBothNow()
    self.scrolledframeSequenceContainer._scrollBothNow()

  def addAllClipsInRandomOrder(self):
    self.clearSequence()
    for clip in sorted(self.selectableVideos.values(),key=lambda x:random.random()):
      self.addClipToSequence(clip)

  def addAllClipsInTimelineOrder(self):
    self.clearSequence()
    for clip in sorted(self.selectableVideos.values(),key=lambda x:(x.filename,x.s)):
      self.addClipToSequence(clip)



if __name__ == '__main__':
  import webmGenerator

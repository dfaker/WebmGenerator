#!/usr/bin/env python3

from tkinter import Tk,Menu,END,LEFT,PhotoImage
import tkinter.ttk as ttk
import webbrowser
from tkinter.filedialog import askopenfilename,asksaveasfilename
import sys
import logging
import urllib.request
import json
import threading
import os

RELEASE_NUMVER = 'v3.9.0'

class WebmGeneratorUi:

  def __init__(self,controller,master=None):

    bg='#181e37'
    lbg='#2f344b'
    fg='#69dbdb'

    self.controller = controller

    self.style = ttk.Style()
    self.style.theme_use('clam')
    self.style.configure('PlayerFrame.TFrame', 
                           background='#282828',
                           foreground=fg,
                           border=0,
                           highlightcolor=bg,
                           activehighlightcolor=bg,
                           relief='flat')

    self.style.configure ("Bold.TLabel", font = ('Sans','10','bold'))


    self.style.configure("SelectedColumn.TFrame", 
                          background='blue',lightcolor='blue',darkcolor='blue')

    self.style.configure("Red.Horizontal.TProgressbar", 
                           background='red',lightcolor='red',darkcolor='red',border=0,relief='flat')
    self.style.configure("Blue.Horizontal.TProgressbar", 
                           background='blue',lightcolor='blue',darkcolor='blue',border=0,relief='flat')
    self.style.configure("Green.Horizontal.TProgressbar", 
                           background='green',lightcolor='green',darkcolor='green',border=0,relief='flat')

    self.style.configure("PlayerLabel.TLabel",background='#282828')


    self.style.configure('subtle.TEntry', border=0, padding=(0,0),background='#282828',foreground='white',lightcolor='#282828',darkcolor='#282828',fieldbackground='#282828',relief='flat')
    self.style.configure('small.TButton', padding=0)
    self.style.configure('smallOnechar.TButton', padding=(-28,0))
    self.style.configure('smallOnecharenabled.TButton', padding=(-28,0),background='green',foreground='white',lightcolor='green',darkcolor='green')

    self.style.configure('smallTall.TButton', padding=(0,10))
    self.style.configure('smallBlue.TButton', padding=0,background='blue',foreground='white',lightcolor='blue',darkcolor='blue',border=0)
    self.style.configure('smallextra.TButton', padding=-20)

    self.panes=[]
    self.master=master

    self.master.title('WebmGenerator')
    self.master.minsize(1024,900)

    self.iconLookup = {}

    try:
      for iconFileName in os.listdir(os.path.join("resources","icons")):
        key = iconFileName[:-4]
        try:
          self.iconLookup[key] = PhotoImage(file=os.path.join("resources","icons","{}.png".format(key)))
        except Exception as e:
          print(e)
    except Exception as e:
      print(e)

    try:
      self.master.state('zoomed')
    except Exception as e:
      logging.error('Zoomed state not avaliable, possibly on some linux distros?',exc_info=e)
      try:
        m = self.master.maxsize()
        self.master.geometry('{}x{}+0+0'.format(*m))
      except Exception as e:
        logging.error('self.master.geometryException',exc_info=e)

    self.menubar = Menu(self.master)
    
    self.filemenu = Menu(self.menubar, tearoff=0, postcommand=self.updateDownloadCounts)

    self.filemenu.add_command(label="New Project",  command=self.newProject   ,image=self.iconLookup.get('icons8-file-24'), compound=LEFT)
    
    self.filemenu.add_command(label="Open Project", command=self.openProject  ,image=self.iconLookup.get('icons8-file-24'), compound=LEFT)
    self.filemenu.add_command(label="Save Project", command=self.saveProject  ,image=self.iconLookup.get('icons8-file-24'), compound=LEFT)
    self.filemenu.add_separator()

    if self.controller.autoSaveExists():
      self.filemenu.add_command(label="Load last autosave", command=self.controller.loadAutoSave)
    else:
      self.filemenu.add_command(label="Load last autosave", command=self.controller.loadAutoSave, state='disabled')

    self.filemenu.add_separator()

    self.filemenu.add_command(label="Load Video from File", command=self.loadVideoFiles,image=self.iconLookup.get('file-video-solid'), compound=LEFT)
    self.filemenu.add_command(label="Load Video from youtube-dlp supported url", command=self.loadVideoYTdl,image=self.iconLookup.get('youtube-brands'), compound=LEFT)
    self.filemenu.add_command(label="Load Image as static video", command=self.loadImageFile,image=self.iconLookup.get('file-image-solid'), compound=LEFT)
    self.filemenu.add_separator()
    
    if hasattr(os.sys, 'winver'):
      self.filemenu.add_command(label="Start screen capture", command=self.startScreencap)
    else:
      self.filemenu.add_command(label="Start screen capture", command=self.startScreencap, state='disabled')

    self.filemenu.add_separator()
    self.filemenu.add_command(label="Watch clipboard and automatically add urls", command=self.loadClipboardUrls)
    self.filemenu.add_separator()
    self.filemenu.add_command(label="Cancel current youtube-dlp download", command=self.cancelCurrentYoutubeDl)

    self.filemenu.add_separator()
    self.filemenu.add_command(label="Update youtube-dlp", command=self.updateYoutubeDl)
    self.filemenu.add_separator()

    self.filemenu.add_command(label="Delete all downloaded files", command=self.clearDownloadedfiles)
    self.clearTempMenuIndex = self.filemenu.index(END) 
    self.filemenu.entryconfigure(self.clearTempMenuIndex, label="Delete all downloaded files")

    self.filemenu.add_separator()
    self.filemenu.add_command(label="Exit", command=self.exitProject)
    self.menubar.add_cascade(label="File",  menu=self.filemenu)

    self.showStreamPreviews = False

    def versioncheck():
      try:
        req = urllib.request.Request('https://api.github.com/repos/dfaker/WebmGenerator/releases')
        req.add_header('Referer', 'http://localhost/dfaker/WebmGenerator/updateCheck')
        with urllib.request.urlopen(req) as f:
          data = json.loads(f.read())
          leadTag = data[0]['tag_name']
          if leadTag != RELEASE_NUMVER:
            self.menubar.add_command(label="New Version {} avaliable!".format(leadTag), command=self.gotoReleasesPage, background='red',activeforeground='red', foreground='red')
          else:
            self.menubar.add_command(label="You're on the most recent version {}".format(leadTag), command=self.gotoReleasesPage, background='red',activeforeground='red', foreground='red')

      except Exception as e:
        logging.error(versioncheck,exc_info=e)
        self.menubar.add_command(label="Version check failed!", command=self.gotoReleasesPage, background='red',activeforeground='red', foreground='red')

    self.commandmenu = Menu(self.menubar, tearoff=0)
    self.commandmenu.add_command(label="Split clip into n equal Subclips",      command=self.splitClipIntoNEqualSections)
    self.commandmenu.add_command(label="Split clip into subclips of n seconds", command=self.splitClipIntoSectionsOfLengthN)
    self.commandmenu.add_separator()

    self.commandmenu.add_command(label="Run scene change detection and add Marks", command=self.controller.runSceneChangeDetection)
    self.commandmenu.add_command(label="Run scene change detection and add SubClips", command=self.controller.runSceneChangeDetectionCuts)
    self.commandmenu.add_separator()

    self.commandmenu.add_command(label="Run audio loudness threshold detection", command=self.scanAndAddLoudSections)
    self.commandmenu.add_separator()

    self.commandmenu.add_checkbutton(label="Generate audio spectra", command=self.generateSoundWaveBackgrounds)
    self.commandmenu.add_separator()

    self.commandmenu.add_command(label="Clear all SubClips on current clip", command=self.clearAllSubclipsOnCurrentClip)
    self.commandmenu.add_command(label="Clear all Interest Marks on current clip", command=self.clearAllInterestMarksOnCurrentClip)
    self.commandmenu.add_separator()
    
    self.commandmenu.add_command(label="Add subclip by text range", command=self.addSubclipByTextRange)


    self.menubar.add_cascade(label="Commands", menu=self.commandmenu)

    self.helpmenu = Menu(self.menubar, tearoff=0)
    self.helpmenu.add_command(label="Open Check for new version", command=versioncheck)
    self.helpmenu.add_command(label="Open Documentation", command=self.openDocs)
    self.menubar.add_cascade(label="Help", menu=self.helpmenu)


    self.master.config(menu=self.menubar)
    
    self.notebook = ttk.Notebook(self.master)
    
    self.statusFrame = ttk.Frame(self.master,height='20')

    self.statusCancel = ttk.Button(self.statusFrame,text='Stop',state='disabled',style='smallextra.TButton',command=self.cancelAction)
    self.statusCancel.pack(expand=False, fill='y',side='left')    

    self.statusSplit = ttk.Button(self.statusFrame,text='Split',state='disabled',style='smallextra.TButton',command=self.splitStream)
    self.statusSplit.pack(expand=False, fill='y',side='left')   

    self.statusPreview = ttk.Button(self.statusFrame,text='Preview',state='disabled',style='small.TButton',command=self.togglePreview)
    self.statusPreview.pack(expand=False, fill='y',side='left')    

    self.statusLabel = ttk.Label(self.statusFrame,text='Idle no background task')
    self.statusLabel.pack(expand=True, fill='both',side='left')

    self.statusProgress = ttk.Progressbar(self.statusFrame)
    self.statusProgress['value'] = 0
    self.statusProgress.pack(expand=1,side='right', fill='x')
    self.statusProgress.config(style="Green.Horizontal.TProgressbar")

    self.statusFrame.pack(expand=0, fill='x',side='bottom')

    self.notebook.pack(expand=1, fill='both')
    self.notebook.bind('<<NotebookTabChanged>>',self._notebokSwitched)

  def sizeof_fmt(self,num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

  def updateDownloadCounts(self):
    count,sz = self.controller.getDownloadFilesCountAndsize()
    if count==0:
      self.filemenu.entryconfigure(self.clearTempMenuIndex, label="Delete all downloaded files (Downloads empty)")
      self.filemenu.entryconfigure(self.clearTempMenuIndex, state='disabled')
    else:
      self.filemenu.entryconfigure(self.clearTempMenuIndex, label="Delete all downloaded files ({} files {})".format(count,self.sizeof_fmt(sz)))
      self.filemenu.entryconfigure(self.clearTempMenuIndex, state='normal')

  def splitClipIntoNEqualSections(self):
    self.controller.splitClipIntoNEqualSections()

  def scanAndAddLoudSections(self):
    self.controller.scanAndAddLoudSections()

  def splitClipIntoSectionsOfLengthN(self):
    self.controller.splitClipIntoSectionsOfLengthN()

  def generateSoundWaveBackgrounds(self):
    self.controller.generateSoundWaveBackgrounds()

  def clearAllSubclipsOnCurrentClip(self):
    self.controller.clearAllSubclipsOnCurrentClip()

  def clearAllInterestMarksOnCurrentClip(self):
    self.controller.clearAllInterestMarksOnCurrentClip()

  def addSubclipByTextRange(self):
    self.controller.addSubclipByTextRange()

  def gotoReleasesPage(self):
    webbrowser.open('https://github.com/dfaker/WebmGenerator/releases', new=2)

  def loadVideoFiles(self):
    self.controller.cutselectionUi.loadVideoFiles()

  def loadClipboardUrls(self):
    self.controller.cutselectionUi.loadClipboardUrls()

  def cancelCurrentYoutubeDl(self):
    self.controller.cancelCurrentYoutubeDl()

  def clearDownloadedfiles(self):
    self.controller.clearDownloadedfiles()
    self.updateDownloadCounts()

  def loadVideoYTdl(self):
    self.controller.cutselectionUi.loadVideoYTdl()

  def startScreencap(self):
    self.controller.cutselectionUi.startScreencap()

  def loadImageFile(self):
    self.controller.cutselectionUi.loadImageFile()

  def switchTab(self,ind):
    self.notebook.select(ind)

  def newProject(self):
    self.controller.newProject()
    self.notebook.select(0)
    self.statusLabel['text']='Idle no background task'
    self.statusProgress['value'] = 0


  def openProject(self):
    filename = askopenfilename(title='Open WebmGenerator Project',filetypes=[('WebmGenerator Project','*.webgproj')])
    self.controller.openProject(filename)

  def saveProject(self):
    filename = asksaveasfilename(title='Save WebmGenerator Project',filetypes=[('WebmGenerator Project','*.webgproj')])
    if filename is not None:
      if not filename.endswith('.webgproj'):
        filename = filename+'.webgproj'
      self.controller.saveProject(filename)

  def splitStream(self):
    self.controller.splitStream()

  def togglePreview(self):
    self.showStreamPreviews = not self.showStreamPreviews
    self.controller.toggleYTPreview(self.showStreamPreviews)
    
    if self.showStreamPreviews:
      self.controller.cutselectionUi.updateProgressPreview("P5\n220 130\n255\n" + ("127" * 220 * 130))
    else:
      self.controller.cutselectionUi.updateProgressPreview(None)

  def updateYoutubeDl(self):
    self.controller.updateYoutubeDl()

  def exitProject(self):
    sys.exit()

  def openDocs(self):
    webbrowser.open('https://github.com/dfaker/WebmGenerator/blob/master/README.md', new=2)

  def cancelAction(self):
    self.controller.cancelCurrentYoutubeDl()
    self.statusCancel['state']='disabled'

  def updateGlobalStatus(self,message,percentage,progressPreview=None):

    if progressPreview is not None and self.showStreamPreviews:
      self.controller.cutselectionUi.updateProgressPreview(progressPreview)
    elif message is not None and 'streaming' not in message:
      self.controller.cutselectionUi.updateProgressPreview(None)

    if message is not None:
      if 'streaming' in message:
        self.statusPreview['state']='enabled'
        self.statusSplit['state']='enabled'
      else:
        self.statusPreview['state']='disabled'
        self.statusSplit['state']='disabled'
        
      if 'Download progress' in message or 'streaming' in message:
        self.statusCancel['state']='enabled'
      else:
        self.statusCancel['state']='disabled'
      self.statusLabel['text']=message
    if percentage is not None:
      if percentage < 0:
        self.statusProgress['mode']='indeterminate'
        self.statusProgress.start()
      else:
        self.statusProgress.stop()
        self.statusProgress['mode']='determinate'
        self.statusProgress['value'] = max(0,min(100,percentage*100))

  def addPane(self,pane,name):
    self.panes.append(pane)
    self.notebook.add(pane, text=name)
  
  def _notebokSwitched(self,e):
    selectedTab = self.notebook.select()
    for pane in self.panes:
      pane.tabSwitched(selectedTab)

  def run(self):
    self.master.mainloop()
  
  def close_ui(self):
    self.controller.cancelCurrentYoutubeDl()
    try:
      self.master.destroy()
      del self.master
      logging.debug('webmGeneratorUi destroyed')
    except:
      pass

if __name__ == '__main__':
  import webmGenerator

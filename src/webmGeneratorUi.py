#!/usr/bin/env python3

from tkinter import Tk,Menu
import tkinter.ttk as ttk
import webbrowser
from tkinter.filedialog import askopenfilename,asksaveasfilename
import sys
import logging
import urllib.request
import json

RELEASE_NUMVER = 'v3.1.0'

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

    self.style.configure("SelectedColumn.TFrame", 
                          background='blue',lightcolor='blue',darkcolor='blue')

    self.style.configure("Red.Horizontal.TProgressbar", 
                           background='red',lightcolor='red',darkcolor='red',border=0,relief='flat')
    self.style.configure("Blue.Horizontal.TProgressbar", 
                           background='blue',lightcolor='blue',darkcolor='blue',border=0,relief='flat')
    self.style.configure("Green.Horizontal.TProgressbar", 
                           background='green',lightcolor='green',darkcolor='green',border=0,relief='flat')


    self.style.configure('small.TButton', padding=0)
    self.style.configure('smallTall.TButton', padding=(0,10))
    self.style.configure('smallBlue.TButton', padding=0,background='blue',foreground='white',lightcolor='blue',darkcolor='blue',border=0)
    self.style.configure('smallextra.TButton', padding=-20)

    self.panes=[]
    self.master=master

    self.master.title('WebmGenerator')
    self.master.minsize(1024,900)
    

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
    
    self.filemenu = Menu(self.menubar, tearoff=0)
    self.filemenu.add_command(label="New Project",  command=self.newProject)
    self.filemenu.add_command(label="Open Project", command=self.openProject)
    self.filemenu.add_command(label="Save Project", command=self.saveProject)
    self.filemenu.add_separator()

    self.filemenu.add_command(label="Run scene change detection", command=self.controller.runSceneChangeDetection)
    self.filemenu.add_separator()

    self.filemenu.add_command(label="Load Video from File", command=self.loadVideoFiles)
    self.filemenu.add_command(label="Load Video from youtube-dl supported url", command=self.loadVideoYTdl)
    self.filemenu.add_command(label="Load Image as static video", command=self.loadImageFile)

    self.filemenu.add_separator()
    self.filemenu.add_command(label="Watch clipboard and automatically add urls", command=self.loadClipboardUrls)

    self.filemenu.add_separator()
    self.filemenu.add_command(label="Update youtube-dl", command=self.updateYoutubeDl)
    self.filemenu.add_separator()
    self.filemenu.add_command(label="Exit", command=self.exitProject)
    self.menubar.add_cascade(label="File",  menu=self.filemenu)

    def versioncheck():
      try:
        with urllib.request.urlopen('https://api.github.com/repos/dfaker/WebmGenerator/releases') as f:
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
    self.commandmenu.add_command(label="Toggle Generation of audio spectra", command=self.generateSoundWaveBackgrounds)
    self.commandmenu.add_separator()
    self.commandmenu.add_command(label="Clear all subclips on current clip", command=self.clearAllSubclipsOnCurrentClip)
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

    self.statusLabel = ttk.Label(self.statusFrame,text='Idle no background task')
    self.statusLabel.pack(expand=True, fill='both',side='left')

    self.statusProgress = ttk.Progressbar(self.statusFrame)
    self.statusProgress['value'] = 0
    self.statusProgress.pack(expand=1,side='right', fill='x')
    self.statusProgress.config(style="Green.Horizontal.TProgressbar")

    self.statusFrame.pack(expand=0, fill='x',side='bottom')

    self.notebook.pack(expand=1, fill='both')
    self.notebook.bind('<<NotebookTabChanged>>',self._notebokSwitched)

  def splitClipIntoNEqualSections(self):
    self.controller.splitClipIntoNEqualSections()

  def splitClipIntoSectionsOfLengthN(self):
    self.controller.splitClipIntoSectionsOfLengthN()

  def generateSoundWaveBackgrounds(self):
    self.controller.generateSoundWaveBackgrounds()

  def clearAllSubclipsOnCurrentClip(self):
    self.controller.clearAllSubclipsOnCurrentClip()

  def addSubclipByTextRange(self):
    self.controller.addSubclipByTextRange()

  def gotoReleasesPage(self):
    webbrowser.open('https://github.com/dfaker/WebmGenerator/releases', new=2)

  def loadVideoFiles(self):
    self.controller.cutselectionUi.loadVideoFiles()

  def loadClipboardUrls(self):
    self.controller.cutselectionUi.loadClipboardUrls()

  def loadVideoYTdl(self):
    self.controller.cutselectionUi.loadVideoYTdl()

  def loadImageFile(self):
    self.controller.cutselectionUi.loadImageFile()

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

  def updateYoutubeDl(self):
    self.controller.updateYoutubeDl()

  def exitProject(self):
    sys.exit()

  def openDocs(self):
    webbrowser.open('https://github.com/dfaker/WebmGenerator/blob/master/README.md', new=2)

  def updateGlobalStatus(self,message,percentage):
    if message is not None:
      self.statusLabel['text']=message
    if percentage is not None:
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
    try:
      self.master.destroy()
      del self.master
      logging.debug('webmGeneratorUi destroyed')
    except:
      pass

if __name__ == '__main__':
  import webmGenerator
#!/usr/bin/env python3

from tkinter import Tk,Menu
import tkinter.ttk as ttk
import webbrowser
from tkinter.filedialog import askopenfilename,asksaveasfilename

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
    self.style.configure('smallextra.TButton', padding=-20)

    self.panes=[]
    self.master=master

    self.master.title('WebmGenerator')
    self.master.minsize(1024,900)
    

    try:
      self.master.state('zoomed')
    except Exception as e:
      print(e)
      try:
        m = self.master.maxsize()
        self.master.geometry('{}x{}+0+0'.format(*m))
      except Exception as e:
        print(e)

    self.menubar = Menu(self.master)
    
    self.filemenu = Menu(self.menubar, tearoff=0)
    self.filemenu.add_command(label="New Project",  command=self.newProject)
    self.filemenu.add_command(label="Open Project", command=self.openProject)
    self.filemenu.add_command(label="Save Project", command=self.saveProject)
    self.filemenu.add_separator()

    self.filemenu.add_command(label="Load Video from File", command=self.loadVideoFiles)
    self.filemenu.add_command(label="Load Video from youtube-dl supported url", command=self.loadVideoYTdl)
    self.filemenu.add_command(label="Load Image as static video", command=self.loadImageFile)

    self.filemenu.add_separator()
    self.filemenu.add_command(label="Update youtube-dl", command=self.updateYoutubeDl)
    self.filemenu.add_separator()
    self.filemenu.add_command(label="Exit", command=self.exitProject)
    self.menubar.add_cascade(label="File",  menu=self.filemenu)

    self.helpmenu = Menu(self.menubar, tearoff=0)
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

  def loadVideoFiles(self):
    self.controller.cutselectionUi.loadVideoFiles()

  def loadVideoYTdl(self):
    self.controller.cutselectionUi.loadVideoYTdl()

  def loadImageFile(self):
    self.controller.cutselectionUi.loadImageFile()

  def newProject(self):
    self.controller.newProject()
    self.notebook.select(0)

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
    exit()

  def openDocs(self):
    webbrowser.open('https://github.com/dfaker/WebmGenerator/blob/master/README.md', new=2)

  def updateGlobalStatus(self,message,percentage):
    print(message,percentage)
    self.statusLabel['text']=message
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
      print('destroyed')
    except:
      pass

if __name__ == '__main__':
  import webmGenerator
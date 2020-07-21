
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
    self.style.configure("Red.Horizontal.TProgressbar", 
                           background='red')

    self.style.configure('small.TButton', padding=0)
    self.style.configure('smallextra.TButton', padding=-20)

    self.panes=[]
    self.master=master

    self.master.title('WebmGenerator')
    self.master.minsize(1525,800)
    self.master.state('zoomed')

    self.menubar = Menu(self.master)
    
    self.filemenu = Menu(self.menubar, tearoff=0)
    self.filemenu.add_command(label="New Project",  command=self.newProject)
    self.filemenu.add_command(label="Open Project", command=self.openProject)
    self.filemenu.add_command(label="Save Project", command=self.saveProject)
    self.filemenu.add_separator()
    self.filemenu.add_command(label="Exit", command=self.exitProject)
    self.menubar.add_cascade(label="File",  menu=self.filemenu)

    self.helpmenu = Menu(self.menubar, tearoff=0)
    self.helpmenu.add_command(label="Open Documentation", command=self.openDocs)
    self.menubar.add_cascade(label="Help", menu=self.helpmenu)

    self.master.config(menu=self.menubar)


    self.notebook = ttk.Notebook(self.master)
    self.notebook.pack(expand=1, fill='both')

    self.statusFrame = ttk.Frame(self.master)

    self.statusLabel = ttk.Label(self.statusFrame,text='Idle no background task',width=60)
    self.statusLabel.pack(expand=0, fill='x',side='left')

    self.statusProgress = ttk.Progressbar(self.statusFrame)
    self.statusProgress.pack(expand=0,side='right', fill='x')

    self.statusFrame.pack(expand=0, fill='x')

    self.notebook.bind('<<NotebookTabChanged>>',self._notebokSwitched)

  def newProject(self):
    self.controller.newProject()

  def openProject(self):
    filename = askopenfilename(title='Open WebmGenerator Project',filetypes=[('WebmGenerator Project','*.webgproj')])
    self.controller.openProject(filename)

  def saveProject(self):
    filename = asksaveasfilename(title='Save WebmGenerator Project',filetypes=[('WebmGenerator Project','*.webgproj')])
    if filename is not None:
      if not filename.endswith('.webgproj'):
        filename = filename+'.webgproj'
      self.controller.saveProject(filename)

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
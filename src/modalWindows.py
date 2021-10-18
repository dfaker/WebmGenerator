

import tkinter as tk
from tkinter import ttk


class SubtitleExtractionModal(tk.Toplevel):

  def __init__(self, master=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Extract Subtitles')
    self.minsize(400,100)
    self.maxsize(400,100)


    self.columnconfigure(0, weight=1)    
    self.columnconfigure(1, weight=1)
    
    self.rowconfigure(0, weight=0)
    self.rowconfigure(1, weight=0)
    self.rowconfigure(2, weight=0)
    self.rowconfigure(3, weight=1)
    

    self.labelFilename = ttk.Label(self)
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

    self.extractCmd = ttk.Button(self)
    self.extractCmd.config(text='Extract',command=self.extract,state='disabled')
    self.extractCmd.grid(row=3,column=0,columnspan=2,sticky='nesw')


  def selectFile(self):
    pass

  def extract(self):
    pass

class OptionsDialog(tk.Toplevel):
  def __init__(self, master=None, *args):
    tk.Toplevel.__init__(self, master)
    self.grab_set()
    self.title('Options')

if __name__ == "__main__":
  app = SubtitleExtractionModal()
  app.mainloop()
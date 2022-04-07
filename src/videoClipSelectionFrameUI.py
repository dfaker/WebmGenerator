
import tkinter as tk
import tkinter.ttk as ttk

import datetime
import threading
from math import floor
import time
import logging
from threading import Lock



class VideoClipSelectionFrameUI(ttk.Frame):

  def __init__(self, master, controller, globalOptions={}, *args, **kwargs):
    ttk.Frame.__init__(self, master)
    self.controller = controller
    self.globalOptions=globalOptions

    self.clip_canvas = tk.Canvas(self,width=200, height=200, bg='#1E1E1E',borderwidth=0,border=0,relief='flat',highlightthickness=0)
    self.clip_canvas.grid(row=1,column=0,sticky="nesw")
    self.grid_rowconfigure(1, weight=1)
    self.grid_columnconfigure(0, weight=1)

    self.uiDirty=True

if __name__ == '__main__':
  import webmGenerator
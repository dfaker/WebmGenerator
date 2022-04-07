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



class ComposeUi(ttk.Frame):

  def __init__(self, master=None,defaultProfile='None', *args, **kwargs):
    ttk.Frame.__init__(self, master)

    self.master=master
    self.controller=None
    self.defaultProfile=defaultProfile

  def setController(self,controller):
    self.controller=controller

  def tabSwitched(self,tabName):
    pass


if __name__ == '__main__':
  import webmGenerator

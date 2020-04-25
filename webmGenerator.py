
import os
import sys

import fileScan
import interface
import encoder

from tkinter import Tk
from tkinter.filedialog import askopenfilename

try:
  if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
  else:
    application_path = os.path.dirname(os.path.realpath(__file__))

  os.chdir(application_path)
  os.environ["PATH"] = application_path + os.pathsep + os.environ["PATH"]

  args = sys.argv[1:]

  if len(args)==0:
    Tk().withdraw()
    filename = askopenfilename()
    args.append(filename)

  print('Scanning args')
  videoFiles    = fileScan.gatherArgs(args)
  print('Starting selection UI')
  selectedClips = interface.selectClips(videoFiles)
  print('Starting processing')
  encoder.processClips(selectedClips)
except Exception as e:
  print(e)
  input('ERROR [Enter] to close.')
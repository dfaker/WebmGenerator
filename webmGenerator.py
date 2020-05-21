
import os
import sys

import fileScan
import interface
import encoder

from tkinter import Tk
from tkinter.filedialog import askopenfilename

import threading
import queue

if getattr(sys, 'frozen', False):
  application_path = os.path.dirname(sys.executable)
else:
  application_path = os.path.dirname(os.path.realpath(__file__))

os.chdir(application_path)
os.environ["PATH"] = application_path + os.pathsep + os.environ["PATH"]

threads=0

def main():
  filterargs = []
  config={}

  for arg in sys.argv[1:]:
    if arg.startswith('--'):
      config[arg.replace('--','')]=True
    else:
      filterargs.append(arg)

  if len(filterargs)==0:
    Tk().withdraw()
    filename = askopenfilename()
    filterargs.append(filename)

  q = queue.Queue()

  if threads>0:
    t = threading.Thread(target=encoder.processClips,args=(q,),daemon=True)
    print('Starting processing queue')
    t.start()

  print('Scanning args')
  videoFiles    = fileScan.gatherArgs(filterargs)
  print('Starting selection UI')
  interface.selectClips(videoFiles,q)
  
  if threads>0:
    q.join()
  else:
    q.put(None)
    encoder.processClips(q)

try:
  main()
except Exception as e:
  print(e)
  input('ERROR [Enter] to close.')
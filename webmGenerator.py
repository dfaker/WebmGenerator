
import sys
from webmGeneratorController import WebmGeneratorController
import threading
from tkinter import Tk
import tkinter.ttk as ttk
import traceback

initialFiles = sys.argv[1:]
try:
  webmGenerator = WebmGeneratorController(initialFiles)
  webmGenerator()
  del webmGenerator
except Exception as e:
  print(e)
  
  traceback.print_exc()
  input('ENTER TO QUIT>>>')

print('DONE')
sys.exit('QUIT')
os.kill()
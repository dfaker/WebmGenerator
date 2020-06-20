
import sys
from webmGeneratorController import WebmGeneratorController
import mpv
import threading
from tkinter import Tk
import tkinter.ttk as ttk

print(threading.current_thread())
print(mpv)

initialFiles = sys.argv[1:]
webmGenerator = WebmGeneratorController(initialFiles)
webmGenerator()
del webmGenerator

print('DONE')
sys.exit('QUIT')
os.kill()
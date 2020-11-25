#!/usr/bin/env python3

try:
  import logging

  logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
  )  

  logging.info('Startup.')

  import sys
  from webmGeneratorController import WebmGeneratorController
  import threading
  from tkinter import Tk
  import tkinter.ttk as ttk
  import traceback

  initialFiles = sys.argv[1:]

  webmGenerator = WebmGeneratorController(initialFiles)
  webmGenerator()

  del webmGenerator
except Exception as e:
  logging.error('Startup Exception',exc_info=e)
  logging.error(traceback.format_exc())

logging.info('DONE')
sys.exit('QUIT')
os.kill()
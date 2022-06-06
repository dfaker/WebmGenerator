#!/usr/bin/env python3

try:
  import logging
  import sys
  import os
  import traceback

  print("Initial working directory", os.getcwd())

  if getattr(sys, 'frozen', False):
    os.chdir(os.path.abspath(os.path.realpath(os.path.dirname(sys.executable))))
  else:
    os.chdir(os.path.abspath(os.path.realpath(os.path.dirname(__file__))))
  
  print("Current working directory", os.getcwd())

  logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
  )  

  logging.info('Startup.')

  from src.webmGeneratorController import WebmGeneratorController
  
  initialFiles = sys.argv[1:]
  webmGenerator = WebmGeneratorController(initialFiles)
  webmGenerator()

  del webmGenerator
except Exception as e:
  logging.error('Startup Exception',exc_info=e)
  logging.error(traceback.format_exc())

logging.info('DONE')
sys.exit()
os.kill()

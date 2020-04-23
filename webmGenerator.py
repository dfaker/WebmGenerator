
import os
import sys

import fileScan
import interface
import encoder

if getattr(sys, 'frozen', False):
  application_path = os.path.dirname(sys.executable)
else:
  application_path = os.path.dirname(os.path.realpath(__file__))

os.chdir(application_path)
os.environ["PATH"] = application_path + os.pathsep + os.environ["PATH"]

videoFiles    = fileScan.gatherArgs(sys.argv[1:])

print(videoFiles)

selectedClips = interface.selectClips(videoFiles)
print(selectedClips)
encoder.processClips(selectedClips)

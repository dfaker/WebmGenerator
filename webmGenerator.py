
import sys

import fileScan
import interface
import encoder

videoFiles    = fileScan.gatherArgs(sys.argv[1:])
selectedClips = interface.selectClips(videoFiles)
print(selectedClips)
encoder.processClips(selectedClips)

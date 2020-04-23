
from win32api import GetSystemMetrics
from mpvAndCV2Player import MpvAndCV2Player

def selectClips(videoFiles):
  print(videoFiles)
  selections=[]
  endSelections=False
  for cat,filename in videoFiles:
    if endSelections:
      break
    while 1:
      player = MpvAndCV2Player(cat,filename)
      selection = player.playVideo()
      if selection is None:
        endSelections=True
        break
      elif len(selection)==0:
        break
      elif len(selection)>0:
        selections.extend(selection)
      else:
        break
  return selections
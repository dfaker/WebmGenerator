

from mpvAndCV2Player import MpvAndCV2Player

class SessionProperties():
  def __init__(self):
    self.showLogo=True
    self.showFooter=False
    self.cycles = [
      {'key':'1','text':'FPS Max {} [1]',           'cycle':['24','30','60','None'],                 'default':'30',   'prop':'fpsLimit'},
      {'key':'2','text':'Size Max {} [2]',          'cycle':['4M','6M','20M','None'],                'default':'4M',   'prop':'sizeLimit'},
      {'key':'3','text':'Audio {} [3]',             'cycle':['32k','64k','128k','192k','No Audio'],  'default':'32k',  'prop':'audioBR'},
      {'key':'4','text':'Max Video Bitrate {} [4]', 'cycle':['3M','6M','20M',"None"],                'default':'None', 'prop':'videoBrMax'},
      {'key':'5','text':'Max Width {} [5]',         'cycle':['720','1280','1920','None'],            'default':'1280', 'prop':'maxVWidth'},
      {'key':'6','text':'Min Width {} [6]',         'cycle':['0','6M','20M'],                        'default':'0',    'prop':'minVWidth'},
    ]
    for property in self.cycles:
      setattr(self,property['prop'],property['default'])

def selectClips(videoFiles,q):
  endSelections=False
  sessionProperties = SessionProperties()
  for cat,filename in videoFiles:
    if endSelections:
      break
    while 1:
      print('Playing',cat,filename)
      player = MpvAndCV2Player(cat,filename,sessionProperties)
      selection = player.playVideo()
      if selection is None:
        endSelections=True
        break
      elif len(selection)==0:
        break
      elif len(selection)>0:
        for clip in selection:
          q.put(clip)
      else:
        break

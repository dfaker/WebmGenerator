
import os

class ColorProvider():

  def __init__(self):

    """ Defualt """
    self.color_bg          = (0,0,0)
    self.color_button      = (10,250,10)
    self.color_button_text = (10,250,10)

    self.color_seekCentre  = (220,220,220)
    self.color_seekEdge    = (120,120,120)

    self.color_seekerHeader = (90,90,90)
    self.color_seekEndTab   = (120,120,220)
    self.color_seekStartTab = (220,120,120)

    self.color_seekercurrentTime = (250,250,250)

    self.color_cycleBarBg = (10,60,10)

    self.color_timelineTick = (120,120,120)
    self.color_timelineText = (50,255,50)
    
    self.color_scrbBg = (90,10,10)

    self.color_scrubcurrentTime   = (255,255,255)
    self.color_scrubSelectedRange = (100,10,10)
    self.color_scrubcurentRange   = (250,10,10)

    self.color_buttonBarBg = (10,60,10)
    
    self.processStringDefinition("""
bg                    181e37

button                309c9c
button_text           69dbdb

seekCentre            dcc7be
seekEdge              dcc7be
seekerHeader          dcc7be

seekEndTab            21448c
seekStartTab          8c2121

seekercurrentTime     3f3f3f
cycleBarBg            252F5B

timelineTick          F8FAFA
timelineText          F8FAFA

scrbBg                485854
scrubcurrentTime      11e7b1
scrubSelectedRange    0fae86
scrubcurentRange      316558

buttonBarBg           252F5B

    """)

    try:
      self.processStringDefinition(open('colortheme.txt','r').read())
    except Exception as e:
      print(e)



  def processStringDefinition(self,string):
    for line in string.split('\n'):
      try:
        if line.strip() == '':
          continue
        parts = line.strip().split(' ')
        name,color = parts[0],parts[-1]
        color = int(color[4:6], 16),int(color[2:4], 16),int(color[0:2], 16)
        setattr(self,'color_'+name,color)
      except Exception as e:
        print(e,line)
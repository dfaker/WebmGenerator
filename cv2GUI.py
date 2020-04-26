
import mpv
import os
import cv2
import numpy as np
import colortheme
from tkinter import Tk
from videoFilter import VideoFilter


def get_curr_screen_width():
    root = Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    x = int(geometry.split('x')[0])
    y = int(geometry.split('x')[1].split('+')[0])
    return x,y


class Cv2GUI():

  def __init__(self,player):
    self.screenx,self.screeny = get_curr_screen_width()

    self.seekerimshape = (126,self.screenx-100,3)
    self.seeker = np.zeros(self.seekerimshape,np.uint8)

    self.filtersimshape = (self.screeny-600,300,3)
    self.filters = np.zeros(self.seekerimshape,np.uint8)
    self.filteryOrigin=None
    self.showFilters = False

    self.player = player
    self.font = cv2.FONT_HERSHEY_SIMPLEX
    self.seekResolution=1.5
    self.seekInc=1/self.seekResolution
    self.clipDuration=30.0
    self.scrubPercent=0.5
    self.tickIncrement=30

    self.colors = colortheme.ColorProvider()
    self.pixelsNeededForIncrement=None

    self.draggingSeek=False
    self.draggingScrub=False
    self.draggingPointSeek=False
    self.scrubOffset=0.0
    self.timeCentre=None

    self.draggingStart = False
    self.draggingEnd   = False

    cv2.namedWindow("seeker")
    cv2.setMouseCallback("seeker", self._handleCV2SeekerClick)


    self.buttons = [
      {'key':'q','text':'Queue Current Clip [Q]',  'help':'Add the currently selected clip section to the processing queue and restart this video to add more.'  },
      {'key':'e','text':'Next File [E]',           'help':'Skip to the next file in the input queue, discarding the current clip selection.'  },
      {'key':'r','text':'Exit and Process [R]',    'help':'Exit the clip extraction ui and start conversion.'  },
      {'key':'t','text':'Toggle Logo [T]',         'help':'Toggle the upper left logo on or off, edit the file logo.png to change the image.'  },
      {'key':'u','text':'Filters [U]',             'help':'Open the filters panel.'  },
      {'key':'c','text':'Crop [C]',                'help':'Start cropping the video frame, click in the player window to set crop extents.'  },
    ]


    self.filterStack = []
    self.selectableFilters = [
      {
        "name":"IOverlay",
        "filter":"null[vin{fn}],movie='{source}'[pwm{fn}],[vin{fn}][pwm{fn}]overlay=x={x}:y={y}",
        "params":[
          {"n":"source", "d":'footer.png',"type":"file"},
          {"n":"x",      "d":100,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
          {"n":"y",      "d":100,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
        ]
      },
      {
        "name":"VOverlay",
        "filter":"null[vin{fn}],movie='{source}',loop=-1:size={frames},setpts=N/FRAME_RATE/TB[pwm{fn}],[vin{fn}][pwm{fn}]overlay=shortest=0:x={x}:y={y}",
        "params":[
          {"n":"source", "d":'footer.png',"type":"file"},
          {"n":"x",      "d":100,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
          {"n":"y",      "d":100,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
          {"n":"frames", "d":100,  "type":"float","range":[0,999]},
        ]
      },





      {
        "name":"tonemap",
        "filter":"zscale=transfer=linear,tonemap={mapping},zscale=transfer=bt709,format=yuv420p",
        "params":[
            {"n":"mapping", "d":"none","type":"cycle","cycle":[
              "none",
              "clip",
              "linear",
              "gamma",
              "reinhard",
              "hable",
              "mobius",
              ]
            },
          ]
      },


      {
        "name":"curves",
        "filter":"curves",
        "params":[
          {"n":"preset", "d":"none","type":"cycle","cycle":[
            "none",
            "color_negative",
            "cross_process",
            "darker",
            "increase_contrast",
            "lighter",
            "linear_contrast",
            "medium_contrast",
            "negative",
            "strong_contrast",
            "vintage",
            ]
          }
        ]
      },

      {
        "name":"colorkey",
        "filter":"colorkey",
        "params":[
          {"n":"color", "d":"Black","type":"cycle","cycle":[
              "Black",
              "Gray",
              "White",
              "Red",
              "Green",
              "Blue",
              "Pink",
              "Thistle",
              "invert"
            ]
          },
          {"n":"similarity",  "d":0.01, "type":"float", "range":None,     'inc':0.01},
          {"n":"blend",           "d":0.0,  "type":"float", "range":None, 'inc':0.01},
        ]
      },



      {
        "name":"chromashift",
        "filter":"chromashift",
        "params":[

          {"n":"cbh",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},
          {"n":"cbv",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},
          {"n":"crh",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},
          {"n":"crv",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},

        ]
      },


      {
        "name":"addroi",
        "filter":"addroi",
        "params":[
          {"n":"x",      "d":0,  "type":"int","range":None, 'inc':1},
          {"n":"y",      "d":0,  "type":"int","range":None, 'inc':1},
          {"n":"w",      "d":100,    "type":"int","range":None, 'inc':1},
          {"n":"h",      "d":100,    "type":"int","range":None, 'inc':1},
          {"n":"qoffset",  "d":0.01, "type":"float", "range":None,     'inc':0.01},
        ]
      },


      {
        "name":"v360",
        "filter":"v360={in_proj}:{out_proj}:in_stereo={in_stereo}:out_stereo={out_stereo}:id_fov={id_fov}:yaw={yaw}:pitch={pitch}:roll={roll}:d_fov={d_fov}:interp={interp}",
        "params":[
          {"n":"in_proj", "d":"sg","type":"cycle","cycle":[
              "sg",
              "fisheye",
              "dfisheye",
              "ball",
              "equirect",
              "gnomonic",
              "rectilinear",
              "pannini",
              "cylindrical",
              "flat",
            ]
          },
          {"n":"out_proj", "d":"rectilinear","type":"cycle","cycle":[
              "sg",
              "fisheye",
              "dfisheye",
              "ball",
              "equirect",
              "gnomonic",
              "rectilinear",
              "pannini",
              "cylindrical",
              "hequirect",
              "flat",
              "perspective",
            ]
          },
          {"n":"in_stereo", "d":"sbs","type":"cycle","cycle":[
              "sbs",
              "2d",
            ]
          },
          {"n":"out_stereo", "d":"2d","type":"cycle","cycle":[
              "sbs",
              "2d",
            ]
          },
          {"n":"yaw",      "d":0.5,  "type":"float","range":None, 'inc':5},
          {"n":"pitch",      "d":0.5,  "type":"float","range":None, 'inc':5},
          {"n":"roll",      "d":0.5,  "type":"float","range":None, 'inc':5},
          {"n":"d_fov",      "d":90.0,  "type":"float","range":None, 'inc':5},
          {"n":"id_fov",      "d":180.0,  "type":"float","range":None, 'inc':5},
          {"n":"interp", "d":"linear","type":"cycle","cycle":[
              "linear",
              "lagrange9",
              "cubic",
              "spline16",
              "gaussian",
            ]
          },
        ]
      },



      {
        "name":"lenscorrection",
        "filter":"format=gbrp,lenscorrection=cx={cx}:cy={cy}:k1={k1}:k2={k2},format=yuv420p",
        "params":[
          {"n":"cx",      "d":0.5,  "type":"float","range":None, 'inc':0.01},
          {"n":"cy",      "d":0.5,  "type":"float","range":None, 'inc':0.01},
          {"n":"k1",      "d":0,    "type":"float","range":None, 'inc':0.01},
          {"n":"k2",      "d":0,    "type":"float","range":None, 'inc':0.01},
        ]
      },



      {
        "name":"colorbalance",
        "filter":"colorbalance",
        "params":[
          {"n":"rs",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"gs",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"bs",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"rm",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"gm",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"bm",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"rh",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"gh",      "d":0,  "type":"float","range":None, 'inc':0.01},
          {"n":"bh",      "d":0,  "type":"float","range":None, 'inc':0.01},
        ]
      },

      {
        "name":"unsharp",
        "filter":"unsharp",
        "params":[
          {"n":"lx",      "d":5,  "type":"int","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
          {"n":"ly",      "d":5,  "type":"int","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
        ]
      },

      {
        "name":"delogo",
        "filter":"delogo",
        "params":[
          {"n":"x",      "d":0,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
          {"n":"y",      "d":0,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
          {"n":"w",      "d":100,"type":"float","range":None, 'controlGroup':'Size',     'controlGroupAxis':'x','inc':1},
          {"n":"h",      "d":100,"type":"float","range":None, 'controlGroup':'Size',     'controlGroupAxis':'y','inc':1}
        ]
      },
      {
        "name":"drawbox",
        "filter":"drawbox",
        "params":[
          {"n":"x",      "d":0,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
          {"n":"y",      "d":0,  "type":"float","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
          {"n":"w",      "d":100,"type":"float","range":None, 'controlGroup':'Size',     'controlGroupAxis':'x','inc':1},
          {"n":"h",      "d":100,"type":"float","range":None, 'controlGroup':'Size',     'controlGroupAxis':'y','inc':1},
          {"n":"t", "d":"fill","type":"cycle","cycle":[
              "fill",
              "1",
              "2",
              "5",
              "w/3"
              "w/5"
              "w/10"
            ]
          },
          {"n":"color", "d":"Black","type":"cycle","cycle":[
              "Black",
              "Gray",
              "White",
              "Red",
              "Green",
              "Blue",
              "Pink",
              "Thistle",
              "invert"
            ]
          }
        ]
      },
      {
        "name":"greyedge",
        "filter":"greyedge",
        "params":[
          {"n":"difford", "d":1,"type":"float","range":[0,2],'inc':0.1},
          {"n":"minknorm","d":5,"type":"float","range":[0,20],'inc':0.1},
          {"n":"sigma",   "d":2,"type":"float","range":[0,1024.0],'inc':5}
        ]
      },

      {"name":"rainbow","filter":"hue='H=2*PI*t*{speed}:s=2'",
        "params":[
          {"n":"speed", "d":1,"type":"float","range":[0,180],'inc':0.1},
        ]
      },
      {
        "name":"rotate","filter":"rotate",
        "params":[
          {"n":"a", "d":0.785398,"type":"float","range":[0,6.28319],'inc':0.0174533},
        ]
      },

      {
        "name":"xbr","filter":"xbr",
        "params":[
          {"n":"n", "d":"2","type":"cycle","cycle":[2,3,4]}
        ]
      },

      {
        "name":"Spin","filter":"rotate=a=t*{speed}",
        "params":[
          {"n":"speed", "d":1,"type":"float","range":[0,180],'inc':0.1},
        ]
      },
      {
        "name":"hue","filter":"hue",
        "params":[
          {"n":"h", "d":0,"type":"float","range":[0,360],'inc':0.0174533},
          {"n":"s", "d":2,"type":"float","range":[-10,10],'inc':0.2},
          {"n":"b", "d":0,"type":"float","range":[-10,10],'inc':0.2},
        ]
      }, 

      {"name":"hflip","filter":"hflip"},
      {"name":"vflip","filter":"vflip"},

     
      {
        "name":"transpose","filter":"transpose",
        "params":[
          {"n":"dir", "d":"cclock","type":"cycle","cycle":[
              "cclock_flip",
              "clock",
              "cclock",
              "clock_flip"
            ]
          }
        ]
      }, 
      {
        "name":"yadif","filter":"yadif",
        "params":[
          {"n":"mode",  "d":"send_frame","type":"cycle","cycle":[
            'send_frame',
            'send_field',
            'send_frame_nospatial',
            'send_field_nospatial'
            ]
          },
          {"n":"parity","d":"auto","type":"cycle","cycle":[
            'tff',
            'bff',
            'auto'
            ]
          },
          {"n":"deint","d":"all","type":"cycle","cycle":[
            'all',
            'interlaced'
            ]
          }
        ]
      },

      {"name":"deblock","filter":"deblock",
        "params":[
          {"n":"filter","d":"strong","type":"cycle","cycle":[
            'weak ',
            'strong',
            ]
          },
          {"n":"block",      "d":8,  "type":"int","range":None,'inc':1},
          {"n":"alpha", "d":0.098,"type":"float","range":[0,1],'inc':0.01},
          {"n":"beta",  "d":0.05,"type":"float","range":[0,1],'inc':0.01},
          {"n":"gamma", "d":0.05,"type":"float","range":[0,1],'inc':0.01},
          {"n":"delta", "d":0.05,"type":"float","range":[0,1],'inc':0.01},
        ]
      },

      {"name":"deshake","filter":"deshake",
       "params":[
          {"n":"x",      "d":-1,  "type":"int","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
          {"n":"y",      "d":-1,  "type":"int","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
          {"n":"w",      "d":-1,  "type":"int","range":None, 'controlGroup':'Size',     'controlGroupAxis':'x','inc':1},
          {"n":"h",      "d":-1,  "type":"int","range":None, 'controlGroup':'Size',     'controlGroupAxis':'y','inc':1},

          {"n":"rx",      "d":16,  "type":"int","range":None, 'controlGroup':'Size',     'controlGroupAxis':'x','inc':1},
          {"n":"ry",      "d":16,  "type":"int","range":None, 'controlGroup':'Size',     'controlGroupAxis':'y','inc':1},

          {"n":"edge","d":"mirror","type":"cycle","cycle":[
            'blank',
            'original',
            'clamp',
            'mirror',
            ]
          },

          {"n":"blocksize",      "d":8,  "type":"int","range":None,'inc':1},
          {"n":"contrast",       "d":125,  "type":"int","range":None,'inc':1},
          {"n":"search","d":"exhaustive","type":"cycle","cycle":[
            'exhaustive',
            'less'
            ]
          }



        ]
      },


      


    ]

    xorigin=5
    for button in self.buttons:
      (bw,bh),baseline = cv2.getTextSize(button['text'],self.font, 0.4, 1)
      button['position'] = (xorigin,15,bw,bh)
      xorigin = xorigin+bw+15
    self.infoXorigin = xorigin
    self.infoFormat = "Start:{:01.2f}s End:{:01.2f}s Dur:{:01.2f}s"

    self.recauclateButtons()

  def recauclateButtons(self):
    xorigin=5
    self.colors = colortheme.ColorProvider()
    for cycle in self.player.sessionProperties.cycles:
      if not hasattr(self.player.sessionProperties, cycle['prop']):
        setattr(self.player.sessionProperties, cycle['prop'], cycle['default'])
      (bw,bh),baseline = cv2.getTextSize( cycle['text'].format( getattr(self.player.sessionProperties, cycle['prop'] ) ) ,self.font, 0.4, 1)
      cycle['position'] = (xorigin,115,bw,bh)
      xorigin = xorigin+bw+15


  def destroy(self):  
    cv2.destroyAllWindows()

  def timeTox(self,time):
    if self.pixelScrubRatio>=1.0:
      return (time/self.player.totalDuration)*self.seekerimshape[1]
    ScrubSecconds = ((self.pixelScrubWidth)*self.pixelScrubRatio)
    scrubStart = (self.scrubPercent* (self.player.totalDuration - (ScrubSecconds) ))
    xpos = ((time-scrubStart)/(ScrubSecconds))*self.seekerimshape[1]
    return xpos

  def xToTime(self,x):
    if self.pixelScrubRatio>=1.0:
      return (x/self.seekerimshape[1])*self.player.totalDuration
    xPercent = x/self.seekerimshape[1]
    ScrubSecconds = (self.pixelScrubWidth*self.pixelScrubRatio)
    scrubStart = (self.scrubPercent* (self.player.totalDuration - (ScrubSecconds) ))
    return xPercent*(ScrubSecconds)+scrubStart



  def _handleCV2SeekerClick(self,event, x, y, flags, param):

    if self.draggingSeek:
      percentInc=0.0
      if x > self.seekerimshape[1] - 10:
        percentInc = 0.01
      elif x<10:
        percentInc = -0.01
      if percentInc!=0.0:
        self.scrubPercent = min(1,max(0,percentInc+self.scrubPercent))

    if event == cv2.EVENT_RBUTTONDOWN or event == cv2.EVENT_RBUTTONDBLCLK:
      self.draggingPointSeek=True
    if event == cv2.EVENT_RBUTTONUP:
      self.draggingPointSeek=False
      if self.timeCentre is not None:
        self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2),'End')

    if self.draggingPointSeek==True:
        self.player.seek(self.xToTime(x))



    if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_LBUTTONDBLCLK:
      if y<26:
        for button in self.buttons:
          bx,_,bw,_ = button['position']
          if bx-5 < x < bx+bw+5:
            self._handleCV2Keypress(ord(button['key']))
            break
      elif 26<y<46:
        self.draggingScrub=True
      elif 46<y<100:
      
        if self.timeCentre is not None and y<60:
          seekstart  = int(self.timeTox(self.timeCentre-(self.clipDuration/2)))
          seekend    = int(self.timeTox(self.timeCentre+(self.clipDuration/2)))

          if seekstart-10<x<seekstart+10:
            self.draggingStart=True
          elif seekend-10<x<seekend+10:
            self.draggingEnd=True
          else:
            self.draggingSeek=True

        else:
          self.draggingSeek=True
      elif 100<y<125:
        for cycle in self.player.sessionProperties.cycles:
          bx,_,bw,_ = cycle['position']
          if bx-5 < x < bx+bw+5:
            current = getattr(self.player.sessionProperties,cycle['prop'])
            ind = (cycle['cycle'].index(current)+1)%len(cycle['cycle'])
            setattr(self.player.sessionProperties,cycle['prop'],cycle['cycle'][ind])
            self.recauclateButtons()

    elif event == cv2.EVENT_LBUTTONUP:
      self.draggingSeek=False
      self.draggingScrub=False

      self.draggingStart=False
      self.draggingEnd=False

    elif event==cv2.EVENT_MOUSEWHEEL:
      increment = 0
      if flags>0:
        increment = 0.2
      else:
        increment = -0.2

      if y>46:
        self.clipDuration+=increment
        if self.timeCentre is not None:
          self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2))
      else:
        if self.pixelScrubRatio<1:
          pass
          """self.pixelScrubWidth = min(self.seekerimshape[1],int(self.pixelScrubWidth+(increment*10)))""" 


    if self.draggingScrub:
      if self.pixelScrubRatio<1:
        self.scrubPercent = min(1.0,max(0.0,( x-(self.pixelScrubWidth//2) )/(self.seekerimshape[1]-(self.pixelScrubWidth))))
      else:
        self.scrubPercent=0.5
    elif self.draggingSeek:
      tempTime = self.xToTime(x)
      if tempTime != self.timeCentre:
        self.timeCentre = tempTime
        self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2))
    elif self.draggingEnd or self.draggingStart:
      tempTime = self.xToTime(x)

      otherTime = self.timeCentre+(self.clipDuration/2)
      jumpLocation='Start'
      if self.draggingEnd:
        otherTime = self.timeCentre-(self.clipDuration/2)
        jumpLocation='End'
      self.clipDuration = abs(tempTime-otherTime)
      self.timeCentre   = (tempTime+otherTime)/2
      self.player.setABLoopRange(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2),jumpLocation)


  def _handleCV2Keypress(self,key):
    if key in [ord(x['key']) for x in self.buttons]:
      self.player._handleMpvKeypress('d-',chr(key),bubble=False)

      if key == ord('u'):
        self.showFilters = not self.showFilters
        if self.showFilters:
          cv2.namedWindow("filters")
          cv2.setMouseCallback("filters", self._handleCV2FilterClick)  
        else:
          cv2.destroyWindow('filters')


  def drawButtons(self):
    self.seeker[0:26,:,:]=self.colors.color_buttonBarBg
    for button in self.buttons:
      x,y,w,h = button['position']
      cv2.putText(self.seeker, button['text'], (x,y), self.font, 0.4, self.colors.color_button_text, 1, cv2.LINE_AA) 
      cv2.rectangle(self.seeker, (x-5,0),(x+w+5,y+h), self.colors.color_button, 1)

    if self.timeCentre is not None:
      cv2.putText(self.seeker, self.infoFormat.format(self.timeCentre-(self.clipDuration//2),self.timeCentre+(self.clipDuration//2),self.clipDuration) , 
                  (self.infoXorigin,y), 
                  self.font, 0.4, self.colors.color_button_text, 1, cv2.LINE_AA) 
    else:
      cv2.putText(self.seeker, self.infoFormat.format(0,0,0) , (self.infoXorigin,y), self.font, 0.4, self.colors.color_button_text, 1, cv2.LINE_AA) 

  def drawScrubBar(self):
    self.seeker[26:46,:,:]=self.colors.color_scrbBg

    if self.pixelsNeededForIncrement is None: 
      self.pixelsNeededForIncrement = int(self.player.totalDuration*(1/self.seekResolution))
      self.pixelScrubRatio = self.seekerimshape[1]/self.pixelsNeededForIncrement

      if self.pixelScrubRatio>1:
        self.pixelScrubRatio=1.0
        self.pixelScrubWidth = self.seekerimshape[1]
      else:
        self.pixelScrubWidth = int(self.seekerimshape[1]*self.pixelScrubRatio)

    scrubCentre = (self.seekerimshape[1]-self.pixelScrubWidth) *self.scrubPercent
    scrubStart = self.pixelScrubWidth//2 + int(  scrubCentre-(self.pixelScrubWidth//2) )
    scrubEnd   = self.pixelScrubWidth//2 + int(  scrubCentre+(self.pixelScrubWidth//2) )

    self.seeker[26:46,scrubStart:scrubEnd,:]=self.colors.color_scrubcurentRange

    if self.pixelsNeededForIncrement is not None: 
      x = int((self.player.currentTime/self.player.totalDuration)* (self.seekerimshape[1]-self.pixelScrubWidth) )+(self.pixelScrubWidth//2)
      x = int(max(min(x,self.seekerimshape[1]-1),0))
      self.seeker[26:46,x:x,:]=self.colors.color_scrubcurrentTime

      if self.timeCentre is not None:
        x = int((self.timeCentre/self.player.totalDuration)* (self.seekerimshape[1]-self.pixelScrubWidth) )+(self.pixelScrubWidth//2)
        x = int(max(min(x,self.seekerimshape[1]-1),0))
        w = max(4,int(self.clipDuration*self.pixelScrubRatio/4))
        self.seeker[26:46,x-w:x+w,:]=self.colors.color_scrubSelectedRange


  def drawSeeKBar(self):

    tickStart = self.xToTime(0)
    tickStart = int((self.tickIncrement * round(tickStart/self.tickIncrement))-5)

    while 1:
      tickStart+=self.tickIncrement
      tx = int(self.timeTox(tickStart))
      if tx<0:
        pass
      elif tx>=self.seekerimshape[1]:
        break
      else:
        self.seeker[80:85,tx,:] = self.colors.color_timelineTick
        (bw,bh),baseline = cv2.getTextSize(str(tickStart),self.font, 0.3, 1)
        cv2.putText(self.seeker, str(tickStart), (tx-(bw//2),96), self.font, 0.3, self.colors.color_timelineText, 1, cv2.LINE_AA)

    if self.pixelsNeededForIncrement is not None: 
      x = self.timeTox(self.player.currentTime)
      x = max(min(x,self.seekerimshape[1]-1),0)
      self.seeker[46:,int(x),:]= self.colors.color_seekercurrentTime
    
    if self.timeCentre is not None:
      seekstart  = int(self.timeTox(self.timeCentre-(self.clipDuration/2)))
      seekcentre = int(self.timeTox(self.timeCentre))
      seekend    = int(self.timeTox(self.timeCentre+(self.clipDuration/2)))

      seekstart  = max(min(seekstart,self.seekerimshape[1]-1),0)
      seekcentre = max(min(seekcentre,self.seekerimshape[1]-1),0)
      seekend    = max(min(seekend,self.seekerimshape[1]-1),0)

      self.seeker[46:56,seekstart:seekend,:] = self.colors.color_seekerHeader

      self.seeker[46:100,seekstart,:]  = self.colors.color_seekEdge
      self.seeker[46:60,seekstart-10:seekstart+10,:]=self.colors.color_seekStartTab

      self.seeker[46:100,seekcentre,:] = self.colors.color_seekCentre
      
      self.seeker[46:100,seekend,:]    = self.colors.color_seekEdge
      self.seeker[46:60,seekend-10:seekend+10,:]= self.colors.color_seekEndTab
  

  def drawCycleBar(self):
    self.seeker[100:126,:,:]=self.colors.color_cycleBarBg
    for cycle in self.player.sessionProperties.cycles:
      x,y,w,h = cycle['position']
      cv2.putText(self.seeker, cycle['text'].format( getattr(self.player.sessionProperties, cycle['prop'] ) ), 
                  (x,y), self.font, 0.4, self.colors.color_button_text , 1, cv2.LINE_AA) 
      cv2.rectangle(self.seeker, (x-5,100),(x+w+5,y+h), self.colors.color_button, 1)

  def recaulcateFilters(self):
    self.player.recaulcateFilters(self.filterStack)

  def _handleCV2FilterClick(self,event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_LBUTTONDBLCLK:
      for ffilter in self.selectableFilters:
          bx,by,bw,bh = ffilter['position']
          if bx-5 < x < bx+bw+5 and by-5 < y < by+bh-2:
            print(ffilter['name'])
            self.filterStack.append(VideoFilter(ffilter,self.filtersimshape[1],self))
            self.recaulcateFilters()

    yorigin=self.filteryOrigin
    remove = False
    for ffilter in self.filterStack:
      if yorigin < y < yorigin + ffilter.height:
        remove = ffilter.handleClick(event, x, y-yorigin, flags, param)
      yorigin+=ffilter.height+15
    if remove:
      self.filterStack = [x for x in self.filterStack if x.remove==False]
      self.recaulcateFilters()


  def updateFilters(self):
    self.filters = np.zeros(self.filtersimshape,np.uint8)
    self.filters[:,:,:] = self.colors.color_bg

    xorigin=15
    yorigin=15
    for ffilter in self.selectableFilters:
      if 'position' not in ffilter:
        (bw,bh),baseline = cv2.getTextSize( ffilter['name'] ,self.font, 0.4, 1)

        if xorigin+bw+17 > self.filtersimshape[1]:
          xorigin=15
          yorigin=yorigin+bh+13
        ffilter['position'] = (xorigin,yorigin,bw,bh)
        xorigin = xorigin+bw+17
      x,y,w,h = ffilter['position']

      cv2.putText(self.filters, ffilter['name'], 
            (x,y), self.font, 0.4, self.colors.color_button_text , 1, cv2.LINE_AA) 
      cv2.rectangle(self.filters, (x-5,y-h-2),(x+w+5,y+h-4), self.colors.color_button, 1)

    if self.filteryOrigin is None:
      self.filteryOrigin=y+15
    
    yorigin=self.filteryOrigin

    for filter in self.filterStack:
      filterImage = filter.getRenderedImage()
      fy,fx,_ = filterImage.shape
      self.filters[yorigin:yorigin+fy,0:fx] = filterImage
      yorigin+=fy+15
    cv2.imshow("filters",self.filters)


  def updateSeeeker(self):
    self.seeker = np.zeros(self.seekerimshape,np.uint8)
    self.seeker[:,:,:] = self.colors.color_bg
    if self.player.totalDuration is not None and self.player.totalDuration > 0:
      if self.clipDuration > self.player.totalDuration:
        self.clipDuration=self.player.totalDuration
      self.drawButtons()
      self.drawScrubBar()
      self.drawSeeKBar()
      self.drawCycleBar()

    cv2.imshow("seeker",self.seeker)
    self._handleCV2Keypress(cv2.waitKey(1))

  def update(self):
    self.updateSeeeker()
    if self.showFilters:
      self.updateFilters()


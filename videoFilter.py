
import cv2
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import cv2
import numpy as np
import os

class VideoFilter():

  def __init__(self,config,allowedWidth,parent):
    self.config=config
    self.name = self.config.get("name","Unamed Filter")
    self.filter = self.config.get("filter",'null')
    
    self.isPostScaleFilter = self.config.get("postScale",False)

    self.previewFilter = self.config.get("filterPreview",self.filter)
    self.params = self.config.get("params",[])

    self.enabled=True
    self.allowedWidth=allowedWidth
    self.parent = parent
    self.remove = False
    self.persist = False

    self.values={}
    self.ranges={}
    for param in self.params:
      self.ranges[param['n']] = param.get("range")
      if self.ranges[param['n']] is None:
        self.ranges[param['n']] = [float('-inf'),float('inf')]


      if param['type'] == 'file':
        Tk().withdraw()
        filename = askopenfilename()
        filename = os.path.relpath(filename, os.getcwd()).replace('\\','\\\\')
        print(filename) 
        self.values[param['n']] = filename
      else:
        self.values[param['n']] = param['d']

    paramStart=38
    if len(self.params)>0:
      for param in self.params:
        (bw,bh),baseline = cv2.getTextSize( '{}:{}'.format(param['n'],self.values[param['n']]) ,self.parent.font, 0.4, 1)
        param['top']=paramStart-(bh/2)
        paramStart = paramStart+bh+9
        param['bottom']=paramStart-(bh/2)
      self.height = paramStart-bh
    else:
      self.height = paramStart

  def getRenderedImage(self):
    image = np.zeros((self.height,self.allowedWidth,3),np.uint8)
    image[:,:,:] = self.parent.colors.color_bg
    image[0,:,:] = self.parent.colors.color_button_text
    
    paramStart=38
    for param in self.params:
      text= '{}'.format(self.values[param['n']])
      if param['type'] == 'float':
        text= '{:01.5f}'.format(self.values[param['n']])
      if param['type'] == 'int':
        text= '{}'.format(self.values[param['n']])

      (bw,bh),baseline = cv2.getTextSize( text ,self.parent.font, 0.4, 1)
      cv2.putText(image, param['n'], (5,paramStart), self.parent.font, 0.4, self.parent.colors.color_button_text, 1, cv2.LINE_AA) 
      cv2.putText(image, text , ( image.shape[1]-(bw)-20 ,paramStart), self.parent.font, 0.4, self.parent.colors.color_button_text, 1, cv2.LINE_AA) 

      paramStart = paramStart+bh+9


    cv2.putText(image, self.name, (5,15), self.parent.font, 0.4, self.parent.colors.color_button_text, 1, cv2.LINE_AA) 
    cv2.putText(image, '[{}] [X]'.format('Enabled' if self.enabled else 'Disabled'), (self.allowedWidth-95,15), self.parent.font, 0.4, self.parent.colors.color_button_text, 1, cv2.LINE_AA) 
    return image

  def handleClick(self,event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_LBUTTONDBLCLK:
      if y<20:
        if x>self.allowedWidth-20:
          self.remove=True
        else:
          self.enabled = not self.enabled
          self.parent.recaulcateFilters()

    for param in self.params:
      rangeLim = self.ranges[param['n']]
      if param['top']<y<param['bottom']:
        if event==cv2.EVENT_MOUSEWHEEL:
          
          increment = 0
          increment = (flags/7864320)*param.get('inc',1.0)

          if param['type'] == 'cycle':
            
            inc=0
            if flags>0:
              inc = 1
            else:
              inc = -1
            
            self.values[param['n']] = param['cycle'][(param['cycle'].index(self.values[param['n']])+inc)%len(param['cycle'])]
            self.parent.recaulcateFilters()
          elif param['type'] == 'int':
            
            increment= int((flags/7864320)*param.get('inc',1.0))
            
            self.values[param['n']] =  min(max( self.values[param['n']]+inc ,rangeLim[0]),rangeLim[1])
            self.parent.recaulcateFilters()
          elif param['type'] == 'float':
            self.values[param['n']] = min(max( self.values[param['n']]+increment ,rangeLim[0]),rangeLim[1])
            self.parent.recaulcateFilters()

    return self.remove

  def getFilterExpression(self,preview=False):
    if not self.enabled:
      return 'null'
    
    if preview:
      filterExp=self.previewFilter
    else:
      filterExp=self.filter

    filerExprams=[]
    i=id(self)

    formatDict={}

    for param in self.params:
      if '{'+param['n']+'}' in filterExp:
        formatDict.update({'fn':i,param['n']:self.values[param['n']]},)
      else:
        if param['type'] == 'float':
          filerExprams.append(':{}={:01.2f}'.format(param['n'],self.values[param['n']]) )
        elif param['type'] == 'int':
          filerExprams.append(':{}={}'.format(param['n'],int(self.values[param['n']])))
        else:
          filerExprams.append(':{}={}'.format(param['n'],self.values[param['n']]) )

    if len(formatDict)>0:
      filterExp = filterExp.format( **formatDict )

    for i,e in enumerate(filerExprams):
      if i==0:
        filterExp+= '='+e[1:]
      else:
        filterExp+= e

    print(filterExp)


    return filterExp
import logging

class VideoManager:

  def __init__(self,globalOptions={}):
    self.subclips = {}
    self.labels = {}
    self.interestMarks = {}
    self.subClipCounter=0
    self.globalOptions=globalOptions
    self.subclipChangeCallbacks=[]

  def updateLabelForClip(self,filename,rid,label):
    self.labels[rid] = label
    print(self.labels)

  def getLabelForClip(self,filename,rid):
    print(self.labels)
    return self.labels.get(rid,'')


  def addSubclipChangeCallback(self,callback):
    if callback not in self.subclipChangeCallbacks:
      self.subclipChangeCallbacks.append(callback)

  def updateCallbacks(self,rid=None,pos=None,action='UPDATE'):
    for callback in self.subclipChangeCallbacks:
      callback(rid=rid,pos=pos,action=action)

  def getStateForSave(self):
    return {'subclips':self.subclips.copy(),
            'interestMarks':{},
            'subClipCounter':self.subClipCounter,
            'labels':self.labels,
            }

  def loadStateFromSave(self,data):
    self.subclips       = data.get('subclips',{})
    self.interestMarks.clear()
    self.subClipCounter = data['subClipCounter']
    self.labels         = data.get('labels',{})

  def reset(self):
    for filename,clips in self.subclips.items():
      for rid,(s,e) in clips.items():
        self.updateCallbacks(rid=rid,pos='s',action='REMOVE')
    self.subclips.clear()
    self.interestMarks.clear()
    self.labels.clear()
    
  def addNewInterestMark(self,filename,point,kind='manual'):
    self.interestMarks.setdefault(filename,set()).add((point,kind))

  def getInterestMarks(self,filename):
    return list(self.interestMarks.get(filename,[]))

  def clearallSubclipsOnFile(self,filename):
    if filename in self.subclips:
      for rid,(s,e) in self.subclips.get(filename,{}).items():
        self.updateCallbacks(rid=rid,pos='s',action='REMOVE')
      self.subclips[filename].clear()

  def clearallInterestMarksOnFile(self,filename):
    if filename in self.subclips:
      self.interestMarks[filename]=set()

  def clearallSubclips(self):
    for filename,clips in self.subclips.items():
      for rid,(s,e) in clips.items():
        self.updateCallbacks(rid=rid,pos='s',action='REMOVE')
    self.subclips.clear()
    
  def getAllClips(self):
    result=[]
    for filename,clips in self.subclips.items():
      for rid,(s,e) in clips.items():
        result.append( (filename,rid,s,e) )
    return result

  def removeVideo(self,filename):
    if filename in self.subclips:
      for rid,(s,e) in self.subclips.get(filename,{}).items():
        self.updateCallbacks(rid=rid,pos='s',action='REMOVE')
      del self.subclips[filename]

  def registerNewSubclip(self,filename,start,end):
    self.subClipCounter+=1
    start,end = sorted([start,end])
    self.subclips.setdefault(filename,{})[self.subClipCounter]=[start,end]
    self.updateCallbacks(rid=self.subClipCounter,pos='s',action='NEW')
    return self.subClipCounter

  def getSurroundingInterestMarks(self,filename,point):
    s,e = point,point

    try:
      s = max([x[0] for x in self.interestMarks.get(filename) if x[0]<=s])
    except Exception as ex:
      logging.error("expandSublcipToInterestMarks",exc_info=ex)
    
    try:
      e   = min([x[0] for x in self.interestMarks.get(filename) if x[0]>=e])
    except Exception as ex:
      logging.error("expandSublcipToInterestMarks",exc_info=ex)

    return s,e

  def expandSublcipToInterestMarks(self,filename,point):
    targetRid = None
    newStart  = None
    newEnd    = None
    print('expand to interestMarks')
    for rid,(s,e) in self.subclips.get(filename,{}).items():
      if s<point<e:
        targetRid = rid
        newStart = s
        newEnd   = e
        try:
          newStart = max([x[0] for x in self.interestMarks.get(filename) if x[0]<=s])
          print(newStart)
        except Exception as e:
          logging.error("expandSublcipToInterestMarks",exc_info=e)
        try:
          newEnd   = min([x[0] for x in self.interestMarks.get(filename) if x[0]>=e])
          print(newEnd)
        except Exception as e:
          logging.error("expandSublcipToInterestMarks",exc_info=e)
        break

    print(filename,targetRid,newStart,newEnd)

    if targetRid is not None:
      self.updateDetailsForRangeId(filename,targetRid,newStart,newEnd)

  def cloneSubclip(self,filename,point):
    clipsToClone=set()
    for rid,(s,e) in self.subclips.get(filename,{}).items():
      if s<point<e:
        clipsToClone.add(rid)
        break
    
    for rid in clipsToClone:
      start,end = self.subclips.get(filename,{})[rid]
      self.registerNewSubclip(filename,start,end)

  def removeSubclip(self,filename,point):
    clipsToRemove=set()
    for rid,(s,e) in self.subclips.get(filename,{}).items():
      if s<=point<=e:
        clipsToRemove.add(rid)
    for rid in clipsToRemove:
      del self.subclips.get(filename,{})[rid]
      self.updateCallbacks(rid=rid,pos='s',action='REMOVE')

  def getRangeDetailsForClip(self,filename,rid):
    return self.subclips.get(filename,{}).get(rid)

  def getRangesForClip(self,filename):
    return self.subclips.get(filename,{}).items()

  def updateDetailsForRangeId(self,filename,rid,start,end):
    start,end = sorted([start,end])
    self.subclips.get(filename,{}).get(rid,[0,0])[0]=start
    self.subclips.get(filename,{}).get(rid,[0,0])[1]=end

  def getDetailsForRangeId(self,searchrid):
    for filename,clips in self.subclips.items():
      for rid,(s,e) in clips.items():
        if rid == searchrid:
          return filename,s,e

  def updatePointForClip(self,filename,rid,pos,ts):
    print('updatePointForClip',filename,rid,pos,ts)
    if pos == 's':
      self.subclips.get(filename,{}).get(rid,[0,0])[0]=ts
    elif pos == 'e':
      self.subclips.get(filename,{}).get(rid,[0,0])[1]=ts
    elif pos == 'm':
      st=self.subclips.get(filename,{}).get(rid,[0,0])[0]
      en=self.subclips.get(filename,{}).get(rid,[0,0])[1]
      dur=(en-st)/2
      self.subclips.get(filename,{}).get(rid,[0,0])[0]=ts-dur
      self.subclips.get(filename,{}).get(rid,[0,0])[1]=ts+dur

    s,e = sorted(self.subclips.get(filename,{}).get(rid,[0,0]))
    self.subclips.get(filename,{}).get(rid,[0,0])[0]=s
    self.subclips.get(filename,{}).get(rid,[0,0])[1]=e

    print(self.subclips)

    self.updateCallbacks(rid=rid,pos=pos,action='UPDATE')


if __name__ == '__main__':
  import webmGenerator

class VideoManager:

  def __init__(self):
    self.subclips = {}
    self.interestMarks = {}
    self.subClipCounter=0


  def getStateForSave(self):
    return {'subclips':self.subclips.copy(),'interestMarks':{},'subClipCounter':self.subClipCounter}

  def loadStateFromSave(self,data):
    self.subclips       = data['subclips']
    self.interestMarks  = {}
    self.subClipCounter = data['subClipCounter']

  def reset(self):
    self.subclips = {}
    self.interestMarks = {}
    self.subClipCounter=0
    
  def addNewInterestMark(self,filename,point,kind='manual'):
    self.interestMarks.setdefault(filename,set()).add((point,kind))

  def getInterestMarks(self,filename):
    return list(self.interestMarks.get(filename,[]))

  def clearallSubclipsOnFile(self,filename):
    if filename in self.subclips:
      self.subclips[filename] = {}

  def clearallSubclips(self):
    self.subclips = {}
    
  def getAllClips(self):
    result=[]
    for filename,clips in self.subclips.items():
      for rid,(s,e) in clips.items():
        result.append( (filename,rid,s,e) )
    return result

  def removeVideo(self,filename):
    if filename in self.subclips:
      del self.subclips[filename]

  def registerNewSubclip(self,filename,start,end):
    self.subClipCounter+=1
    start,end = sorted([start,end])
    self.subclips.setdefault(filename,{})[self.subClipCounter]=[start,end]
    return self.subClipCounter

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
    for rid in clipsToClone:
      start,end = self.subclips.get(filename,{})[rid]
      self.registerNewSubclip(filename,start,end)

  def removeSubclip(self,filename,point):
    clipsToRemove=set()
    for rid,(s,e) in self.subclips.get(filename,{}).items():
      if s<point<e:
        clipsToRemove.add(rid)
    for rid in clipsToRemove:
      del self.subclips.get(filename,{})[rid]

  def getRangesForClip(self,filename):
    return self.subclips.get(filename,{}).items()

  def updateDetailsForRangeId(self,filename,rid,start,end):
    start,end = sorted([start,end])
    print('updateDetailsForRangeId',filename,rid,start,end)
    self.subclips.get(filename,{}).get(rid,[0,0])[0]=start
    self.subclips.get(filename,{}).get(rid,[0,0])[1]=end


  def getDetailsForRangeId(self,rid):
    for filename,clips in self.subclips.items():
      for rid,(s,e) in clips.items():
        return filename,s,e

  def updatePointForClip(self,filename,rid,pos,ts):
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

if __name__ == '__main__':
  import webmGenerator
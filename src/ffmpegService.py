
from datetime import datetime
from queue import Queue
import copy
import hashlib
import itertools
import logging
import math
import os
import shutil
import statistics
import string
import subprocess as sp
import threading
import time

import numpy as np

from .encoders.gifEncoder     import encoder as gifEncoder
from .encoders.mp4x264Encoder import encoder as mp4x264Encoder
from .encoders.webmvp8Encoder import encoder as webmvp8Encoder
from .encoders.webmvp9Encoder import encoder as webmvp9Encoder

from .encodingUtils import cleanFilenameForFfmpeg
from .encodingUtils import getFreeNameForFileAndLog
from .encodingUtils import isRquestCancelled
from .encodingUtils import cancelCurrentEncodeRequest

from .ffmpegInfoParser import getVideoInfo
from .masonry import Brick,Stack



encoderMap = {
   'webm:VP8':webmvp8Encoder
  ,'webm:VP9':webmvp9Encoder
  ,'mp4:x264':mp4x264Encoder
  ,'gif':gifEncoder
}

class FFmpegService():

  def __init__(self,globalStatusCallback=print,imageWorkerCount=2,encodeWorkerCount=1,statsWorkerCount=1):
    

    self.cache={}
    self.imageRequestQueue = Queue()
    self.responseRouting = {}
    self.globalStatusCallback=globalStatusCallback

    def imageWorker():
      while 1:
        try:
          requestKey = self.imageRequestQueue.get()
          requestId,filename,timestamp,filters,size = requestKey
          if filters == '':
            filters='null'
          w,h=size
          if type(timestamp) != float and type(timestamp) != np.float64 and '%' in timestamp:
            pc = float(timestamp.replace('%',''))/100.0
            videoInfo = getVideoInfo(cleanFilenameForFfmpeg(filename))
            timestamp = videoInfo.duration*pc
          cmd=['ffmpeg','-y',"-loglevel", "quiet","-noaccurate_seek",'-ss',str(timestamp),'-i',cleanFilenameForFfmpeg(filename), '-filter_complex',filters+',scale={w}:{h}:flags=bicubic'.format(w=w,h=h),"-pix_fmt", "rgb24",'-vframes', '1', '-an', '-c:v', 'ppm', '-f', 'rawvideo', '-']
          logging.debug("Ffmpeg command: {}".format(' '.join(cmd)))
          proc = sp.Popen(cmd,stdout=sp.PIPE)
          outs,errs = proc.communicate()
          self.postCompletedImageFrame(requestKey,outs)
        except Exception as e:
          logging.error("Image worker Exception",exc_info=e)


    self.imageWorkers=[]
    for _ in range(imageWorkerCount):
      imageWorkerThread = threading.Thread(target=imageWorker,daemon=True)
      imageWorkerThread.start()
      self.imageWorkers.append(imageWorkerThread)

    self.encodeRequestQueue = Queue()

    def encodeStreamCopy(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback):
      
      assert(len(seqClips)==1)

      totalExpectedEncodedSeconds = 0
      for rid,clipfilename,s,e,filterexp,filterexpEnc in seqClips:
        totalExpectedEncodedSeconds += e-s

      totalEncodedSeconds=0

      for i,(rid,clipfilename,s,e,filterexp,filterexpEnc) in enumerate(seqClips):

        etime = e-s
        basename = os.path.basename(clipfilename)
        ext = basename.split('.')[-1]
        
        videoFileName,_,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(basename,ext)

        comvcmd = ['ffmpeg', '-i', cleanFilenameForFfmpeg(clipfilename), '-ss', str(s), '-c', 'copy', '-t', str(etime), tempVideoFilePath]
        print(' '.join(comvcmd))
        proc = sp.Popen(comvcmd,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
        
        currentEncodedTotal=0

        statusCallback('Stream copying started', 0.1)
        self.globalStatusCallback('Stream copying started', 0.1)

        ln=b''
        while 1:
          c = proc.stderr.read(1)
          if isRquestCancelled(requestId):
            proc.kill()
            outs, errs = proc.communicate()
            try:
              os.remove(outname)
            except:
              pass
            return
          if len(c)==0:
            break
          if c == b'\r':
            print(ln)
            for p in ln.split(b' '):
              if b'time=' in p:
                try:
                  pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
                  currentEncodedTotal = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
                  if currentEncodedTotal>0:
                    statusCallback('Stream copying clip {}'.format(i+1), (currentEncodedTotal+totalEncodedSeconds)/totalExpectedEncodedSeconds)
                    self.globalStatusCallback('Stream copying clip {}'.format(i+1), (currentEncodedTotal+totalEncodedSeconds)/totalExpectedEncodedSeconds)
                except Exception as e:
                  logging.error("Clip Stream copy exception",exc_info =e)
            ln=b''
          ln+=c
        proc.communicate()
        totalEncodedSeconds+=etime
        shutil.copy(tempVideoFilePath,videoFilePath)
        statusCallback('Stream copy complete',1,finalFilename=videoFilePath)
        self.globalStatusCallback('Stream copy complete',1)


    def encodeGrid(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback):
      
      tempStack = Stack([],'horizontal')
      brickClips = {}
      brickVideoInfo = {}

      brickn=0

      cutLengths = 0
      minLength = float('inf')
      maxLength = 0

      processed = {}
      
      bricksInSelectedColumn = set()

      maximumSideLength = options.get('maximumWidth',1280)
      inputMaxWidth  = 0
      inputMaxHeight = 0

      for icol,column in enumerate(seqClips):
        col = []

        maxColWidth  = 0
        sumcolHeight = 0
        for i,(rid,clipfilename,s,e,filterexp,filterexpEnc) in enumerate(column):
          
          videoInfo = getVideoInfo(cleanFilenameForFfmpeg(clipfilename),filters=filterexp)
          brick = Brick(brickn,videoInfo.width,videoInfo.height)
          
          maxColWidth = max(maxColWidth, videoInfo.width)
          sumcolHeight += videoInfo.height

          if e-s < minLength:
            minLength = e-s
          cutLengths += e-s

          if e-s > maxLength:
            maxLength = e-s

          brickClips[brickn] = (i,(rid,clipfilename,s,e,filterexp,filterexpEnc))
          brickVideoInfo[brickn] = videoInfo

          if options.get('selectedColumn',0) == icol:
            bricksInSelectedColumn.add(brickn)

          brickn += 1
          col.append(brick)
        inputMaxWidth  += maxColWidth
        inputMaxHeight = max(inputMaxHeight, sumcolHeight)
        colstack = Stack(col,'vertical')
        tempStack.append(colstack)

      largestInputDim = max(inputMaxWidth,inputMaxHeight)
      if largestInputDim < maximumSideLength or maximumSideLength == 0:
        maximumSideLength = largestInputDim

      speedAdjustment = 1.0
      try:
        speedAdjustment= float(options.get('speedAdjustment',1.0))
        speedAdjustment = max(min(speedAdjustment, 100),0.5)
      except Exception as e:
        logging.error('invalid speed Adjustment',exc_info=e)

      gridLoopMergeOption = options.get('gridLoopMergeOption','')
      if 'Loop shorter' in gridLoopMergeOption:
        minLength = maxLength

      totalExpectedEncodedSeconds = cutLengths+(minLength*(1/speedAdjustment))
      totalEncodedSeconds = 0

      brickTofileLookup = {}


      audioMergeMode = options.get('audioMerge','Merge Normalize All')

      for brickn in brickClips.keys():
        (i,(rid,clipfilename,s,e,filterexp,filterexpEnc)) = brickClips[brickn]
        videoInfo = brickVideoInfo[brickn]
        etime = e-s
        if filterexp=='':
          filterexp='null'  

        filterexp+=",scale='if(gte(iw,ih),max(0,min({maxDim},iw)),-2):if(gte(iw,ih),-2,max(0,min({maxDim},ih)))':flags=bicubic".format(maxDim=options.get('maximumWidth',1280))
        filterexp += ',pad=ceil(iw/2)*2:ceil(ih/2)*2'

        key = (rid,clipfilename,s,e,filterexp,filterexpEnc)

        basename = os.path.basename(clipfilename)

        try:
          os.path.exists(tempPathname) or os.mkdir(tempPathname)
        except Exception as e:
          logging.error(msg)

        m = hashlib.md5()
        m.update(filterexp.encode('utf8'))
        filterHash = m.hexdigest()[:10]

        basename = ''.join([x for x in basename if x in string.digits+string.ascii_letters+' -_'])[:10]

        loopCount = 1

        outname = '{}_{}_{}_{}_{}_{}.mp4'.format(i,basename,s,e,filterHash,runNumber)
        outname = os.path.join( tempPathname,outname )

        if os.path.exists(outname):
          processed[key]=outname
          brickTofileLookup[brickn] = outname
          totalEncodedSeconds+=etime
          statusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )
          self.globalStatusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )

        elif key not in processed:
          statusCallback('Cutting clip {}'.format(i+1), totalEncodedSeconds/totalExpectedEncodedSeconds)
          self.globalStatusCallback('Cutting clip {}'.format(i+1), totalEncodedSeconds/totalExpectedEncodedSeconds)
          


          if (not brickVideoInfo[brickn].hasaudio) or options.get('audioChannels','No audio') == 'No audio':
            comvcmd = ['ffmpeg','-y'
                      ,'-f', 'lavfi', '-i', 'anullsrc'                                
                      ,'-ss', str(s)

                      ,'-i', cleanFilenameForFfmpeg(clipfilename)
                      ,'-t', str(e-s)
                      
                      ,'-filter_complex', filterexp
                      ,'-c:v', 'libx264'
                      ,'-crf', '0'
                      ,'-map', '0:a', '-map', '1:v' 
                      ,'-shortest'
                      ,'-ac', '1',outname]
          else:
            comvcmd = ['ffmpeg','-y'                                
                      ,'-ss', str(s)

                      ,'-i', cleanFilenameForFfmpeg(clipfilename)
                      ,'-t', str(e-s)
                      
                      ,'-filter_complex', filterexp
                      ,'-c:v', 'libx264'
                      ,'-crf', '0'
                      ,'-ac', '1',outname]


          proc = sp.Popen(comvcmd,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
          
          currentEncodedTotal=0
          ln=b''
          while 1:
              c = proc.stderr.read(1)
              if isRquestCancelled(requestId):
                proc.kill()
                outs, errs = proc.communicate()
                try:
                  os.remove(outname)
                except:
                  pass
                return
              if len(c)==0:
                break
              if c == b'\r':
                print(ln)
                for p in ln.split(b' '):
                  if b'time=' in p:
                    try:
                      pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
                      currentEncodedTotal = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
                      if currentEncodedTotal>0:
                        statusCallback('Cutting clip {}'.format(i+1), (currentEncodedTotal+totalEncodedSeconds)/totalExpectedEncodedSeconds)
                        self.globalStatusCallback('Cutting clip {}'.format(i+1), (currentEncodedTotal+totalEncodedSeconds)/totalExpectedEncodedSeconds)
                    except Exception as e:
                      logging.error('Clip cutting exception',exc_info=e)
                ln=b''
              ln+=c
          proc.communicate()
          totalEncodedSeconds+=etime
          statusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds)
          self.globalStatusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds)
          processed[key]=outname
          brickTofileLookup[brickn] = outname
        else:
          brickTofileLookup[brickn] = processed[key]
          totalEncodedSeconds+=etime
          statusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )
          self.globalStatusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )

      #PRE CUT END

      
      logger={}
      vow,voh = tempStack.getSizeWithContstraint('width',maximumSideLength,logger,0,0)

      if vow>maximumSideLength or voh>maximumSideLength:
        logger={}
        vow,voh = tempStack.getSizeWithContstraint('height',maximumSideLength,logger,0,0)

      logging.debug("Grid final size {}x{}".format(vow,voh))      
      logging.debug("Grid calculated {}".format(logger))      
      
      #audio calcs
      streropos = {}
      inputAudio  = []
      outputsAudio = []

      largestBrickInd = 0
      largestBrickArea=0

      for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
        streropos[k] = (((xo+w/2)/vow)-0.5)
        vi,(vrid,vclipfilename,vs,ve,vfilterexp,vfilterexpEnc) = brickClips[k]
        if w*h > largestBrickArea:
          largestBrickArea=w*h
          largestBrickInd=k


      if audioMergeMode == 'Selected Column Only':
        for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          videoInfo = brickVideoInfo[k]
          if videoInfo.hasaudio and k in bricksInSelectedColumn:
            inputAudio.append('[{k}:a]loudnorm=I=-16:TP=-1.5:LRA=11,atrim=duration={mindur},volume=1.0:eval=frame,pan=stereo|c0=c0|c1=c0,stereotools=balance_out={panpos}[aud{k}]'.format(k=snum,mindur=minLength,panpos=streropos.get(k,0)))
            outputsAudio.append('[aud{k}]'.format(k=snum))
      elif audioMergeMode == 'Largest Cell by Area':
        for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          videoInfo = brickVideoInfo[k]
          if videoInfo.hasaudio and k == largestBrickInd:
            inputAudio.append('[{k}:a]loudnorm=I=-16:TP=-1.5:LRA=11,atrim=duration={mindur},volume=1.0:eval=frame,pan=stereo|c0=c0|c1=c0,stereotools=balance_out={panpos}[aud{k}]'.format(k=snum,mindur=minLength,panpos=streropos.get(k,0)))
            outputsAudio.append('[aud{k}]'.format(k=snum))
      elif audioMergeMode == 'Adaptive Loudest Cell':
        vols={}
        klookup={}
        for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          videoInfo = brickVideoInfo[k]
          vi,(vrid,vclipfilename,vs,ve,vfilterexp,vfilterexpEnc) = brickClips[k]
          klookup[k]=snum
          file = brickTofileLookup[k]

          proc = sp.Popen(['ffprobe', '-f', 'lavfi'
                          ,'-i','amovie=\'{}\',astats=metadata=1:reset=1'.format(file.replace('\\','/').replace(':','\\:').replace('\'','\\\\\''))
                          ,'-show_entries', 'frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.1.RMS_level,lavfi.astats.2.RMS_level'
                          ,'-of', 'csv=p=0'],stdout=sp.PIPE,stderr=sp.DEVNULL)
          outs,errs = proc.communicate()
          minvol=float('inf')
          maxvol=float('-inf')
          for line in outs.decode('utf8').split('\n'):
            if line.strip() != '':
              parts = line.strip().split(',')
              ts,vol1,vol2 = parts[0],parts[1],parts[2]
              vol= -((float(vol1)+float(vol2))/2)
              minvol = min(minvol,vol)
              maxvol = max(maxvol,vol)
          for line in outs.decode('utf8').split('\n'):
            if line.strip() != '':
              parts = line.strip().split(',')
              ts,vol1,vol2 = parts[0],parts[1],parts[2]
              vol= -((float(vol1)+float(vol2))/2)
              vol = (vol-minvol)/(maxvol-minvol)
              vols.setdefault(round(float(ts),1),{}).setdefault(k,[]).append(vol)

        loudSeq=[]

        for k,v in sorted(vols.items()):

          loudest=None
          loudLevel=None

          for fn,vl in v.items():
            mv = statistics.mean(vl)
            if loudLevel is None or loudLevel<mv:
              loudest = fn
              loudLevel = mv

          loudSeq.append( (k,klookup[loudest],loudLevel) )

        from collections import deque

        selection=None
        hist=deque([],20)

        selectedSections=[]

        for second,index,_ in loudSeq:
          if selection is None:
            selection = index
          hist.append(index)
          try:
            selection=statistics.mode(list(hist)+[selection] )
          except:
            pass
          selectedSections.append( (second,selection) )

        volcommands = {}
        for i,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          onSections = []
          for keybool,group in itertools.groupby(selectedSections,key=lambda x:x[1]==i):
            if keybool:
              gl = [x[0] for x in group]
              onSections.append( (min(gl),max(gl)) )
          if len(onSections)>0:
            volcommands[k] = '+'.join([ '(between(t,{s},{e}) + ( between(t,{s}-1,{s}+1)*cos(t-{s}) ) + ( between(t,{e}-1,{e}+1)*cos(t-{e}) ))'.format(s=x[0],e=x[1]) for x in onSections])

        for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          videoInfo = brickVideoInfo[k]
          if videoInfo.hasaudio:
            inputAudio.append('[{k}:a]loudnorm=I=-16:TP=-1.5:LRA=11,atrim=duration={mindur},volume=\'1.0*min(1,{vol})\':eval=frame,pan=stereo|c0=c0|c1=c0,stereotools=balance_out={panpos}[aud{k}]'.format(k=snum,mindur=minLength,panpos=streropos.get(k,0),vol=volcommands.get(k,'0.0')))
            outputsAudio.append('[aud{k}]'.format(k=snum))
      elif audioMergeMode == 'Merge Original Volume':
        for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          videoInfo = brickVideoInfo[k]
          if videoInfo.hasaudio:
            inputAudio.append('[{k}:a]atrim=duration={mindur},volume=1.0:eval=frame,pan=stereo|c0=c0|c1=c0,stereotools=balance_out={panpos}[aud{k}]'.format(k=snum,mindur=minLength,panpos=streropos.get(k,0)))
            outputsAudio.append('[aud{k}]'.format(k=snum))
      else:
        for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
          videoInfo = brickVideoInfo[k]
          if videoInfo.hasaudio:
            inputAudio.append('[{k}:a]loudnorm=I=-16:TP=-1.5:LRA=11,atrim=duration={mindur},volume=1.0:eval=frame,pan=stereo|c0=c0|c1=c0,stereotools=balance_out={panpos}[aud{k}]'.format(k=snum,mindur=minLength,panpos=streropos.get(k,0)))
            outputsAudio.append('[aud{k}]'.format(k=snum))


      #audio calcs


      ffmpegFilterCommand = "color=s={w}x{h}:c=black[base],".format(w=int(vow),h=int(voh))
      
      inputsList = []
      inputScales = []
      overlays = []

      for snum,(k,(xo,yo,w,h,ar,ow,oh)) in enumerate(sorted(logger.items(),key=lambda x:int(x[0]))):
        vi,(vrid,vclipfilename,vs,ve,vfilterexp,vfilterexpEnc) = brickClips[k]

        vetime = ve-vs
        loopCount=0
        if 'Loop shorter' in gridLoopMergeOption:
          print('loop',vclipfilename,maxLength,vetime,maxLength/vetime,math.ceil(maxLength/vetime))
          loopCount =  math.ceil(maxLength/vetime)


        inputsList.extend(['-stream_loop', str(loopCount),'-i',brickTofileLookup[k]])
        inputScales.append('[{k}:v]setpts=PTS-STARTPTS+{st},trim=duration={maxlen},scale={w}:{h}:flags=bicubic[vid{k}]'.format(k=snum,w=int(w),h=int(h),st=0,maxlen=maxLength))

        srcLayer='[tmp{k}]'.format(k=snum)
        if snum==0:
          srcLayer='[base]'
        destLayer='[tmp{k}]'.format(k=int(snum)+1)
        overlay = '[vid{k}]overlay=shortest=1:x={x}:y={y}'.format(k=snum,x=int(xo),y=int(yo))

        overlays.append(srcLayer+overlay+destLayer )

      if len(inputAudio)>0:
        ffmpegFilterCommand += ','.join(inputAudio) + ','

      ffmpegFilterCommand += ','.join(inputScales)
      ffmpegFilterCommand += ',' + ','.join(overlays)
      ffmpegFilterCommand += ',[tmp{k}]null,pad=ceil(iw/2)*2:ceil(ih/2)*2[outvpre]'.format(k=snum+1)

      if len(inputAudio)>1:
        ffmpegFilterCommand +=  ',{}amix=inputs={}:duration=shortest[outapre]'.format(''.join(outputsAudio),len(outputsAudio))
      elif len(inputAudio)==1:
        ffmpegFilterCommand +=  ',{}anull[outapre]'.format(''.join(outputsAudio),len(outputsAudio))
      else:
        ffmpegFilterCommand +=  ',anullsrc[outapre]'

    
      audioOverride      = options.get('audioOverride',None)
      audioOverrideDelay = options.get('audiOverrideDelay',0)
      audioOverrideBias  = options.get('audioOverrideBias',1)

      try:
        audioOverrideDelay = float(audioOverrideDelay)
      except Exception as e:
        logging.error("Audio delay exception",exc_info =e)
        audioOverrideDelay = 0


      if audioOverride is not None:
        inputsLen = len(inputsList)//4
        inputsList.extend(['-i',audioOverride])
        finalAudoTS = audioOverrideDelay+minLength
        weightDub    = audioOverrideBias
        weightSource = 1-audioOverrideBias

        ffmpegFilterCommand += ',[{soundind}:a]atrim={startaTS}:{endaTS}[adub],[adub]asetpts=PTS-STARTPTS[dubclipped],[outapre][dubclipped]amix=inputs=2:duration=first:weights=\'{srcw} {dubw}\'[outa]'.format(soundind=inputsLen,startaTS=audioOverrideDelay,endaTS=finalAudoTS,srcw=weightSource,dubw=weightDub)
      else:
        ffmpegFilterCommand += ',[outapre]anull[outa]'

      print(ffmpegFilterCommand)

      postProcessingPath = os.path.join( 'postFilters', options.get('postProcessingFilter','') )
      if os.path.exists( postProcessingPath ) and os.path.isfile( postProcessingPath ):
        ffmpegFilterCommand += open( postProcessingPath ,'r').read()
      else:
        ffmpegFilterCommand += ',[outvpre]null[outv]'



      filtercommand = ffmpegFilterCommand

      outputFormat  = options.get('outputFormat','webm:VP8')
      finalEncoder  = encoderMap.get(outputFormat,encoderMap.get('webm:VP8'))
      finalEncoder(inputsList, 
                   outputPathName,
                   filenamePrefix, 
                   filtercommand, 
                   options, 
                   totalEncodedSeconds,   
                   totalExpectedEncodedSeconds, 
                   statusCallback, requestId=requestId)

    def encodeConcat(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback):

      expectedTimes = []
      processed={}
      fileSequence=[]
      clipDimensions = []
      infoOut={}

      fadeStartToEnd = options.get('fadeStartToEnd',True)

      encodeStageFilterList = []

      for i,(rid,clipfilename,s,e,filterexp,filterexpEnc) in enumerate(seqClips):
        if filterexpEnc is not None and len(filterexpEnc)>0 and filterexpEnc != 'null':
          encodeStageFilterList.append(filterexpEnc)

        expectedTimes.append(e-s)
        videoInfo = getVideoInfo(cleanFilenameForFfmpeg(clipfilename))
        infoOut[rid] = videoInfo

        videoh=videoInfo.height
        videow=videoInfo.width

        clipDimensions.append((videow,videoh))

      speedAdjustment = 1.0
      try:
        speedAdjustment= float(options.get('speedAdjustment',1.0))
        speedAdjustment = max(min(speedAdjustment, 100),0.5)
      except Exception as e:
        logging.error("invalid speed Adjustment",exc_info =e)

      totalExpectedFinalLength=sum(expectedTimes)

      expectedTimes.append(sum(expectedTimes)*(1/speedAdjustment))
      totalExpectedEncodedSeconds = sum(expectedTimes)
      totalEncodedSeconds = 0
      shortestClipLength = float('inf')



      for i,(etime,(videow,videoh),(rid,clipfilename,start,end,filterexp,filterexpEnc)) in enumerate(zip(expectedTimes,clipDimensions,seqClips)):
        shortestClipLength = min(shortestClipLength, etime)
        if filterexp=='':
          filterexp='null'  

        basename = os.path.basename(clipfilename)
        basename = ''.join([x for x in basename if x in string.digits+string.ascii_letters+' -_'])[:10]

        if 'subtitles=filename=' in  filterexp:

          m = hashlib.md5()
          m.update(filterexp.encode('utf8'))
          filterHash = m.hexdigest()[:10]

          subfilename = filterexp.split('subtitles=filename=')[1].split(':force_style=')[0]
          subfilenameStrip = subfilename.replace("'",'')
          subOutname = os.path.join( tempPathname,'{}_{}_{}_{}_{}_{}.srt'.format(i,basename,start,end,filterHash,runNumber) )

          subcmd  = ['ffmpeg','-y','-ss' , str(start), '-itsoffset', str(0-start), '-i', subfilenameStrip.replace('\\:',':'), '-c', 'copy', subOutname]
          print(' '.join(subcmd))
          subProc = sp.Popen(subcmd)
          subProc.communicate()
          
          cleanSubPath = os.path.abspath(subOutname).replace('\\','/').replace(':','\\:')
          filterexp = filterexp.replace(subfilenameStrip,cleanSubPath)

          print(subfilenameStrip)
          print(subOutname)
          print(filterexp)

        #scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720

        filterexp+=",scale='if(gte(iw,ih),max(0,min({maxDim},iw)),-2):if(gte(iw,ih),-2,max(0,min({maxDim},ih)))':flags=bicubic".format(maxDim=options.get('maximumWidth',1280))
        filterexp += ',pad=ceil(iw/2)*2:ceil(ih/2)*2'



        try:
          os.path.exists(tempPathname) or os.mkdir(tempPathname)
        except Exception as e:
          logging.error(msg)

        m = hashlib.md5()
        m.update(filterexp.encode('utf8'))
        filterHash = m.hexdigest()[:10]

        key = (rid,clipfilename,start,end,filterexp,filterexpEnc)
        basename = os.path.basename(clipfilename)
        basename = ''.join([x for x in basename if x in string.digits+string.ascii_letters+' -_'])[:10]

        outname = '{}_{}_{}_{}_{}_{}.mp4'.format(i,basename,start,end,filterHash,runNumber)
        outname = os.path.join( tempPathname,outname )

        if os.path.exists(outname):
          processed[key]=outname
          fileSequence.append(processed[key])
          totalEncodedSeconds+=etime
          statusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )
          self.globalStatusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )

        elif key not in processed:
          statusCallback('Cutting clip {}'.format(i+1), totalEncodedSeconds/totalExpectedEncodedSeconds)
          self.globalStatusCallback('Cutting clip {}'.format(i+1), totalEncodedSeconds/totalExpectedEncodedSeconds)
          
          if infoOut[rid].hasaudio:
            comvcmd = ['ffmpeg','-y'                                
                      ,'-ss', str(start)
                      ,'-i', cleanFilenameForFfmpeg(clipfilename)
                      ,'-t', str(end-start)
                      ,'-filter_complex', filterexp
                      ,'-c:v', 'libx264'
                      ,'-crf', '0'
                      ,'-ac', '1',outname]
          else:
            comvcmd = ['ffmpeg','-y'
                      ,'-f', 'lavfi', '-i', 'anullsrc'                                
                      ,'-ss', str(start)
                      ,'-i', cleanFilenameForFfmpeg(clipfilename)
                      ,'-t', str(end-start)
                      ,'-filter_complex', filterexp
                      ,'-c:v', 'libx264'
                      ,'-crf', '0'
                      ,'-map', '0:a', '-map', '1:v' 
                      ,'-shortest'
                      ,'-ac', '1',outname]

          proc = sp.Popen(comvcmd,stderr=sp.PIPE,stdin=sp.DEVNULL,stdout=sp.DEVNULL)
          
          currentEncodedTotal=0
          ln=b''
          while 1:
              c = proc.stderr.read(1)
              if isRquestCancelled(requestId):
                proc.kill()
                outs, errs = proc.communicate()
                try:
                  os.remove(outname)
                except:
                  pass
                return
              if len(c)==0:
                break
              if c == b'\r':
                for p in ln.split(b' '):
                  if b'time=' in p:
                    try:
                      pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
                      currentEncodedTotal = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
                      if currentEncodedTotal>0:
                        statusCallback('Cutting clip {}'.format(i+1), (currentEncodedTotal+totalEncodedSeconds)/totalExpectedEncodedSeconds)
                        self.globalStatusCallback('Cutting clip {}'.format(i+1), (currentEncodedTotal+totalEncodedSeconds)/totalExpectedEncodedSeconds)
                    except Exception as e:
                      logging.error("Clip cutting exception",exc_info =e)
                ln=b''
              ln+=c
          proc.communicate()
          totalEncodedSeconds+=etime
          statusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds)
          self.globalStatusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds)

          processed[key]=outname
          fileSequence.append(outname)
        else:
          fileSequence.append(processed[key])
          totalEncodedSeconds+=etime
          statusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )
          self.globalStatusCallback('Cutting clip {}'.format(i+1),(totalEncodedSeconds)/totalExpectedEncodedSeconds )

      fadeDuration=0.25
      try:
        fadeDuration= float(options.get('transDuration',0.5))
      except Exception as e:
        logging.error("invalid fade duration",exc_info =e)

      sizeMatchMode = 'PAD'
      if 'center crop' in options.get('frameSizeStrategy',''):
        sizeMatchMode = 'CROP'

      dimensionsSet = set()
      fpsSet        = set()
      tbnSet        = set()
      
      in_maxWidth  = 0
      in_minWidth  = float('inf')
      in_maxHeight = 0
      in_minHeight = float('inf')

      for clipfilename in fileSequence:

        videoInfo = getVideoInfo(cleanFilenameForFfmpeg(clipfilename))
        videoh=videoInfo.height
        in_maxHeight = max(in_maxHeight, videoh)
        in_minHeight = min(in_minHeight, videoh)
        
        videow=videoInfo.width
        in_maxWidth  = max(in_maxWidth, videow)
        in_minWidth  = min(in_minWidth, videow)
        fpsSet.add(videoInfo.tbr)
        dimensionsSet.add( (videow,videoh) )
        tbnSet.add(videoInfo.tbn)
        if isRquestCancelled(requestId):
          return

      fpsCmd = 'null'

      if len(fpsSet)>1 or len(tbnSet)>1:
        count=0
        targetfps = 0
        for fpse in fpsSet:
          if fpse is not None:
            count+=1
            targetfps+=fpse
        fpse = targetfps/count
        if fpse != 0:
          fpsCmd = 'fps={},settb=AVTB'.format(targetfps)

      if fadeDuration > 0.0:
        inputsList = []

        for vi,v in enumerate(fileSequence):
          inputsList.extend(['-i',v])

        transition = options.get('transStyle','smoothleft')
        offset=fadeDuration*2
        expectedFadeDurations = expectedTimes[:-1]

        videoSplits=[]
        transitionFilters=[]
        audioSplits=[]
        crossfades=[]
        crossfadeOut=''

        splitTemplate     = '[{i}:v]{splitexp},split[vid{i}a][vid{i}b];'
        xFadeTemplate     = '[vid{i}a][vid{n}b]xfade=transition={trans}:duration={fdur}:offset={o}[fade{i}];'
        fadeTrimTemplate  = '[fade{i}]trim={preo}:{dur},setpts=PTS-STARTPTS[fadet{i}];'
        asplitTemplate    = '[{i}:a]asplit[ata{i}][atb{i}];[ata{i}]atrim={preo}:{dur}[atat{i}];'
        crossfadeTemplate = '[atat{i}][atb{n}]acrossfade=d={preo},atrim=0:{o}[audf{i}];'

        for i,dur in enumerate(expectedFadeDurations):
          n=0 if i==len(expectedFadeDurations)-1 else i+1
          o=dur-offset
          preo=offset          
          totalExpectedFinalLength-= (fadeDuration*2)

          splitexp = 'null'
          if mode == 'CONCAT' and len(dimensionsSet) > 1:
            splitexp = "scale={in_maxWidth}:{in_maxHeight}:force_original_aspect_ratio=decrease:flags=bicubic,pad={in_maxWidth}:{in_maxHeight}:(ow-iw)/2:(oh-ih)/2,setsar=1:1,{fpsCmd}".format(in_maxWidth=in_maxWidth,in_maxHeight=in_maxHeight,fpsCmd=fpsCmd)

          videoSplits.append(splitTemplate.format(i=i,splitexp=splitexp))
          transitionFilters.append(xFadeTemplate.format(i=i,n=n,o=o,fdur=fadeDuration,trans=transition))
          audioSplits.append(fadeTrimTemplate.format(i=i,preo=preo,dur=dur))
          audioSplits.append(asplitTemplate.format(i=i,preo=preo,dur=dur))
          crossfades.append(crossfadeTemplate.format(i=i,preo=preo,dur=dur,n=n,o=o))
          crossfadeOut+='[fadet{i}][audf{i}]'.format(i=i)
        crossfadeOut+='concat=n={}:v=1:a=1[concatOutV][concatOutA]'.format(len(expectedFadeDurations))

        if speedAdjustment==1.0:
          crossfadeOut += ',[concatOutV]null[outvpre],[concatOutA]anull[outapre]'
        else:
          try:
            vfactor=1/speedAdjustment
            afactor=speedAdjustment
            crossfadeOut += ',[concatOutV]setpts={vfactor}*PTS,minterpolate=\'mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1:fps=30\'[outvpre],[concatOutA]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
          except Exception as e:
            logging.error("Crossfade exception",exc_info =e)
            crossfadeOut += ',[concatOutV]null[outvpre],[concatOutA]anull[outapre]'

        filtercommand = ''.join(videoSplits+transitionFilters+audioSplits+crossfades+[crossfadeOut])
      else:
        inputsList   = []
        filterInputs = ''
        filterPeProcess = ''
        for vi,v in enumerate(fileSequence):
          inputsList.extend(['-i',v])
          if mode == 'CONCAT' and len(dimensionsSet) > 1:
            filterPeProcess += "[{i}:v]scale={in_maxWidth}:{in_maxHeight}:force_original_aspect_ratio=decrease:flags=bicubic,pad={in_maxWidth}:{in_maxHeight}:(ow-iw)/2:(oh-ih)/2,setsar=1:1,{fpsCmd}[{i}vsc],".format(in_maxWidth=in_maxWidth,in_maxHeight=in_maxHeight,i=vi,fpsCmd=fpsCmd)
          else:
            filterPeProcess += '[{i}:v]null[{i}vsc],'.format(i=vi)

          filterInputs += '[{i}vsc][{i}:a]'.format(i=vi)

        filtercommand = filterPeProcess + filterInputs + 'concat=n={}:v=1:a=1[outvconcat][outaconcat]'.format(len(inputsList)//2)


        if speedAdjustment==1.0:
          filtercommand += ',[outvconcat]null[outvpre],[outaconcat]anull[outapre]'
        else:
          try:
            vfactor=1/speedAdjustment
            afactor=speedAdjustment
            filtercommand += ',[outvconcat]setpts={vfactor}*PTS,minterpolate=\'mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1:fps=30\'[outvpre],[outaconcat]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
          except Exception as e:
            logging.error("Concat progress Exception",exc_info=e)
            filtercommand += ',[outvconcat]null[outvpre],[outaconcat]anull[outapre]'

      postProcessingPath = os.path.join( 'postFilters', options.get('postProcessingFilter','') )
      if os.path.exists( postProcessingPath ) and os.path.isfile( postProcessingPath ):
        filtercommand += open( postProcessingPath ,'r').read()
      else:
        filtercommand += ',[outvpre]null[outv]'

      logging.debug("Filter command: {}".format(filtercommand))

      try:
        os.path.exists(outputPathName) or os.mkdir(outputPathName)
      except Exception as e:
          logging.error(msg)

      audioOverride      = options.get('audioOverride',None)
      audioOverrideDelay = options.get('audiOverrideDelay',0)

      try:
        audioOverrideDelay = float(audioOverrideDelay)
      except Exception as e:
        logging.error("audioOverrideDelay exception",exc_info =e)
        audioOverrideDelay = 0

      audioOverrideBias  = options.get('audioOverrideBias',1)


      if audioOverride is not None:
        inputsLen = len(inputsList)//2
        inputsList.extend(['-i',audioOverride])
        finalAudoTS = audioOverrideDelay+totalExpectedFinalLength
        if mode == 'GRID':
          finalAudoTS = audioOverrideDelay+shortestClipLength 

        weightDub    = audioOverrideBias
        weightSource = 1-audioOverrideBias

        filtercommand += ',[{soundind}:a]atrim={startaTS}:{endaTS}[adub],[adub]asetpts=PTS-STARTPTS[dubclipped],[outapre][dubclipped]amix=inputs=2:duration=first:weights=\'{srcw} {dubw}\'[outa]'.format(soundind=inputsLen,startaTS=audioOverrideDelay,endaTS=finalAudoTS,srcw=weightSource,dubw=weightDub)
      else:
        filtercommand += ',[outapre]anull[outa]'

      outputFormat  = options.get('outputFormat','webm:VP8')
      finalEncoder  = encoderMap.get(outputFormat,encoderMap.get('webm:VP8'))

      if len(encodeStageFilterList)>0:
        encodeStageFilter = ','.join(encodeStageFilterList)
      else:
        encodeStageFilter = 'null'


      finalEncoder(inputsList, 
                   outputPathName,
                   filenamePrefix, 
                   filtercommand, 
                   options, 
                   totalEncodedSeconds, 
                   totalExpectedEncodedSeconds, 
                   statusCallback, requestId=requestId, encodeStageFilter=encodeStageFilter)


    def encodeWorker():
      tempPathname='tempVideoFiles'
      outputPathName='finalVideos'
      
      try:
        os.path.exists(tempPathname) or os.mkdir(tempPathname)
      except Exception as e:
        logging.error("tempPathname exception",exc_info =e)

      try:
        os.path.exists(outputPathName) or os.mkdir(outputPathName)
      except Exception as e:
        logging.error("outputPathName exception",exc_info =e)

      runNumber=int(time.time())

      while 1:
        try:
          requestId,mode,seqClips,options,filenamePrefix,statusCallback = self.encodeRequestQueue.get()

          if mode == 'CONCAT':
            encodeConcat(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback)
          elif mode == 'GRID':
            encodeGrid(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback)
          elif mode == 'STREAMCOPY':
            encodeStreamCopy(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback)

        except Exception as e:
          logging.error("unhandled {} exception".format(mode),exc_info =e)


    self.encodeWorkers=[]
    for _ in range(encodeWorkerCount):
      encodeWorkerThread = threading.Thread(target=encodeWorker,daemon=True)
      encodeWorkerThread.start()
      self.encodeWorkers.append(encodeWorkerThread)

    self.statsRequestQueue = Queue()
    def statsWorker():
      while 1:
        try:
          filename,requestType,options,callback = self.statsRequestQueue.get()
          if requestType == 'GetAutoCropCoords':

            start = options.get('start')
            audocropcmd = ["ffmpeg", "-ss", str(start), "-i", filename, "-t", "1", "-filter_complex", "cropdetect", "-f", "null", "NUL"]
            popen_params = {
              "bufsize": 10 ** 5,
              "stdout": sp.PIPE,
              #"stderr": sp.DEVNULL,
            }
            
            x,y,w,h = None,None,None,None

            proc = sp.Popen(audocropcmd,stderr=sp.PIPE)
            ln=b''
            while 1:
              c=proc.stderr.read(1)
              if len(c)==0:
                break
              if c in b'\r\n':
                if b'Parsed_cropdetect_0' in ln:
                  for e in ln.split(b' '):
                    if b'w:' in e:
                      w = float(e.split(b':')[-1])
                    elif b'h:' in e:
                      h = float(e.split(b':')[-1])
                    elif b'x:' in e:
                      x = float(e.split(b':')[-1])
                    elif b'y:' in e:
                      y = float(e.split(b':')[-1])
                ln=b''
              else:
                ln+=c
            proc.communicate()
            callback(x,y,w,h)

          elif requestType == 'MSESearch':
            logging.debug('new loop error seatch start')
            filename = options.get('filename')
            secondsCenter = options.get('secondsCenter')
            minSeconds   = options.get('minSeconds')
            maxSeconds   = options.get('maxSeconds')

            cropRect = options.get('cropRect')

            startTs = secondsCenter-(maxSeconds*1.5)

            od=224
            nbytes = 3 * od * od
            frameDistance=0.01

            if cropRect is None:
              videofilter = "scale={}:{}:flags=bicubic".format(od,od)
            else:
              x,y,w,h = cropRect
              videofilter = "crop={}:{}:{}:{},scale={}:{}:flags=bicubic".format(x,y,w,h,od,od)



            popen_params = {
              "bufsize": 10 ** 5,
              "stdout": sp.PIPE,
              #"stderr": sp.DEVNULL,
            }

            framesCmd = ["ffmpeg"
                      ,'-ss',str(startTs)
                      ,"-i", cleanFilenameForFfmpeg(filename)  
                      ,'-s', '{}x{}'.format(od,od)
                      ,'-ss',str(startTs)
                      ,'-t', str((maxSeconds*1.5)*2)
                      ,"-filter_complex", videofilter
                      ,"-copyts"
                      ,"-f","image2pipe"
                      ,"-an"
                      ,"-pix_fmt","bgr24"
                      ,"-vcodec","rawvideo"
                      ,"-vsync", "vfr"
                      ,"-"]

            searchFrames = np.frombuffer(sp.Popen(framesCmd,**popen_params).stdout.read(), dtype="uint8")
            searchFrames.shape = (-1,od,od,3)

            frameDistance = (((maxSeconds*1.5)*2)/searchFrames.shape[0])

            print(searchFrames.shape)

            distances = []
            minMse    = float('inf')

            for si,frame in enumerate(searchFrames):

              mse = ((searchFrames[si] - searchFrames)**2).mean(axis=(1,2,3))

              for ei,fmse in enumerate(mse):
                matchStart = (startTs)+(si*frameDistance)
                matchEnd   = (startTs)+(ei*frameDistance)

                if fmse <= minMse and maxSeconds >= (matchEnd-matchStart) >= minSeconds:
                  print( fmse,matchStart,matchEnd )
                  distances.append( (fmse,matchStart,matchEnd) )
                  minMse=fmse
            
              self.globalStatusCallback('Finding closest frame match',si/searchFrames.shape[0])



            finalmse,finals,finale = sorted(distances)[0]

            logging.debug("Frame search finalmse:{} finalstart:{} finalend:{}".format(finalmse,finals,finale))

            self.globalStatusCallback('Found closest matches, updating',1)
            callback(filename,mse,finals,finale)



          elif requestType == 'MSESearchImprove':
            logging.debug('error seatch start')
            filename = options.get('filename')
            start = options.get('start')
            end   = options.get('end')
            searchDistance=options.get('secondsChange')

            halfclipDur = (end-start)/2

            if searchDistance>halfclipDur:
              searchDistance=halfclipDur

            cropRect = options.get('cropRect')
            rid = options.get('rid')
            


            od=224
            nbytes = 3 * od * od
            frameDistance=0.01

            if cropRect is None:
              videofilter = "scale={}:{}:flags=bicubic".format(od,od)
            else:
              x,y,w,h = cropRect
              videofilter = "crop={}:{}:{}:{},scale={}:{}:flags=bicubic".format(x,y,w,h,od,od)

            popen_params = {
              "bufsize": 10 ** 5,
              "stdout": sp.PIPE,
              #"stderr": sp.DEVNULL,
            }

            startCmd = ["ffmpeg"
                      ,'-ss',str(start-searchDistance)
                      ,"-i", cleanFilenameForFfmpeg(filename)  
                      ,'-s', '{}x{}'.format(od,od)
                      ,'-ss',str(start-searchDistance)
                      ,'-t', str(searchDistance*2)
                      ,"-filter_complex", videofilter
                      ,"-copyts"
                      ,"-f","image2pipe"
                      ,"-an"
                      ,"-pix_fmt","bgr24"
                      ,"-vcodec","rawvideo"
                      ,"-vsync", "vfr"
                      ,"-"]
            endCmd = ["ffmpeg"
                      ,'-ss',str(end-searchDistance)
                      ,"-i", cleanFilenameForFfmpeg(filename) 
                      ,'-s', '{}x{}'.format(od,od)
                      ,'-ss',str(end-searchDistance)
                      ,'-t', str(searchDistance*2)
                      ,"-filter_complex", videofilter
                      ,"-copyts"
                      ,"-f","image2pipe"
                      ,"-an"
                      ,"-pix_fmt","bgr24"
                      ,"-vcodec","rawvideo"
                      ,"-vsync", "vfr"
                      ,"-"]

            startFrames = np.frombuffer(sp.Popen(startCmd,**popen_params).stdout.read(), dtype="uint8")
            endFrames   = np.frombuffer(sp.Popen(endCmd,**popen_params).stdout.read(), dtype="uint8")

            startFrames.shape = (-1,od,od,3)
            endFrames.shape = (-1,od,od,3)

            distances = []
            sframeDistance = ((searchDistance*2)/startFrames.shape[0])
            eframeDistance = ((searchDistance*2)/endFrames.shape[0])

            for si,frame in enumerate(startFrames):
              
              self.globalStatusCallback('Finding closest frame match',si/startFrames.shape[0])

              mse = ((startFrames[si] - endFrames)**2).mean(axis=(1,2,3))
              argmin = np.argmin(mse)  
              matchStart = (start-searchDistance)+(si*sframeDistance)
              matchEnd   = (end-searchDistance)+(argmin*eframeDistance)
              distances.append( (mse[argmin],matchStart,matchEnd) )
              logging.debug("Frame search mse:{} matchstart:{} matchend:{}".format(mse[argmin],matchStart,matchEnd))

            finalmse,finals,finale = sorted(distances)[0]
            logging.debug("Frame search finalmse:{} finalstart:{} finalend:{}".format(finalmse,finals,finale))

            self.globalStatusCallback('Found closest matches, updating',1)
            callback(filename,rid,mse,finals,finale)

          elif requestType == 'SceneChangeSearch':
            expectedLength = options.get('duration',0)
            self.globalStatusCallback('Starting scene change detection ',0/expectedLength)
            proc = sp.Popen(
              ['ffmpeg','-i',cleanFilenameForFfmpeg(filename),'-filter_complex', 'select=gt(scene\\,0.3),showinfo', '-f', 'null', 'NUL']
              ,stderr=sp.PIPE)
            ln=b''
            while 1:
              c=proc.stderr.read(1)
              if len(c)==0:
                break
              if c in b'\r\n':
                if b'pts_time' in ln:
                  for e in ln.split(b' '):
                    if b'pts_time' in e:
                      ts = float(e.split(b':')[-1])
                      self.globalStatusCallback('Scene change detection ',ts/expectedLength)
                      callback(filename,ts)
                ln=b''
              else:
                ln+=c
            proc.communicate()
        except Exception as e:
          logging.error("Scene Change Search progress Exception",exc_info=e)

    self.statsWorkers=[]
    for _ in range(statsWorkerCount):
      statsWorkerThread = threading.Thread(target=statsWorker,daemon=True)
      statsWorkerThread.start()
      self.statsWorkers.append(statsWorkerThread)

    self.loadImageAsVideoRequestQueue = Queue()

    def loadImageAsVideoWorker():
      imageasVideoID=0
      while 1:
        filename,duration,completioncallback = self.loadImageAsVideoRequestQueue.get()
        vidInfo = getVideoInfo(filename)
        logging.debug(str(vidInfo))
        imageasVideoID+=1
        
        try:
          os.path.exists('tempVideoFiles') or os.mkdir('tempVideoFiles')
        except Exception as e:
          logging.error("outputPathName exception",exc_info =e)

        outfileName = os.path.join('tempVideoFiles','loadImageAsVideo_{}.mp4'.format(imageasVideoID))
        proc = sp.Popen(['ffmpeg','-y','-loop','1','-i',filename,'-c:v','libx264','-t',str(duration),'-pix_fmt','yuv420p','-tune', 'stillimage','-vf', 'scale={}:{}:flags=bicubic,pad=ceil(iw/2)*2:ceil(ih/2)*2'.format(vidInfo.width,vidInfo.height),outfileName],stderr=sp.PIPE)
        ln=b''
        while 1:
          c=proc.stderr.read(1)
          if len(c)==0:
            break
          if c in b'\r\n':
            for p in ln.split(b' '):
              if b'time=' in p:
                try:
                  pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
                  currentEncodedTotal = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
                  if currentEncodedTotal>0:
                    self.globalStatusCallback('Loading image {}'.format(filename),currentEncodedTotal/duration)
                except Exception as e:
                  logging.error("loadImageAsVideo Exception",exc_info=e)
            ln=b''
          else:
            ln+=c
            
        proc.communicate()
        completioncallback(outfileName)

    self.loadImageAsVideoWorkers=[]
    loadImageAsVideoWorkerThread = threading.Thread(target=loadImageAsVideoWorker,daemon=True)
    loadImageAsVideoWorkerThread.start()
    self.loadImageAsVideoWorkers.append(loadImageAsVideoWorkerThread)

    self.timelinePreviewFrameWorkerRequestQueue = Queue()
    self.lastTimelinePreviewFilenameRequested = None

    def timelinePreviewFrameWorker():
      while 1:
        filename,startTime,Endtime,frameWidth,timelineWidth,callback = self.timelinePreviewFrameWorkerRequestQueue.get()
        if filename is None or filename != self.lastTimelinePreviewFilenameRequested:
          continue


        videoInfo = getVideoInfo(cleanFilenameForFfmpeg(filename),filters="scale={}:45:force_original_aspect_ratio=decrease:flags=neighbor".format(frameWidth))
        outputWidth = videoInfo.width

        numberOfFrames = math.floor( (timelineWidth)/frameWidth )

        framePercentage = frameWidth/(timelineWidth)
        totalDuration = Endtime-startTime
        frameGap = totalDuration/numberOfFrames
        midpoint = (startTime+Endtime)/2

        popen_params = {
          "bufsize": 10 ** 5,
          "stdout": sp.PIPE,
          #"stderr": sp.DEVNULL,
        }

        ts = startTime+(frameGap/2)
        tsl=[]
        while ts <= Endtime:
          tsl.append(ts)

          previewData = "P5\n{} 45\n255\n".format(outputWidth) + ("0" * outputWidth * 45)
          callback(filename,ts,outputWidth,previewData)

          ts+=frameGap

        tsl = sorted(tsl,key=lambda x: min(abs(x-midpoint),x,totalDuration-x)    )

        maxActiveInstances = 3
        procQueue = []

        while len(tsl)>0 or len(procQueue)>0:
          while len(procQueue)<maxActiveInstances and len(tsl)>0:
            ts = tsl.pop(0)
            frameCommand = ["ffmpeg"
                          ,"-loglevel", "quiet"
                          ,"-noaccurate_seek"
                          ,"-ss",str(ts)
                          ,"-i", cleanFilenameForFfmpeg(filename)  
                          ,'-frames:v', '1'
                          ,"-an"
                          ,"-filter_complex", "scale={}:45:force_original_aspect_ratio=decrease:flags=fast_bilinear".format(frameWidth)
                          ,'-f', 'rawvideo'
                          ,"-pix_fmt", "rgb24"
                          ,'-c:v', 'ppm' 
                          ,'-y'
                          ,"-"]
            procQueue.append((ts,sp.Popen(frameCommand,**popen_params)))

          if len(procQueue)>0:
            ts,proc = procQueue.pop(0)
            currentFrame = proc.stdout.read()
            if filename == self.lastTimelinePreviewFilenameRequested:
              callback(filename,ts,frameWidth,currentFrame)
            else:
              break
              procQueue.append((ts,sp.Popen(frameCommand,**popen_params)))
          if filename != self.lastTimelinePreviewFilenameRequested:
            break 
        while len(procQueue)>0:
          procQueue.pop(0)[1].communicate()

    self.timelinePreviewFrameWorkerThread = threading.Thread(target=timelinePreviewFrameWorker,daemon=True)
    self.timelinePreviewFrameWorkerThread.start()

  def encode(self,requestId,mode,seq,options,filenamePrefix,statusCallback):
    self.encodeRequestQueue.put((requestId,mode,seq,options,filenamePrefix,statusCallback))

  def requestTimelinePreviewFrames(self,filename,startTime,Endtime,frameWidth,timelineWidth,callback):
    self.lastTimelinePreviewFilenameRequested = filename
    self.timelinePreviewFrameWorkerRequestQueue.put( (filename,startTime,Endtime,frameWidth,timelineWidth,callback) )

  def requestPreviewFrame(self,requestId,filename,timestamp,filters,size,callback):
    requestKey = (requestId,filename,timestamp,filters,size)
    self.responseRouting[requestKey]=callback
    if requestKey in self.cache:
      callback(requestId,timestamp,size,self.cache[requestKey])
    self.imageRequestQueue.put( requestKey )

  def postCompletedImageFrame(self,requestKey,responseImage):
    self.cache[requestKey] = responseImage
    requestId,filename,timestamp,filters,size = requestKey
    self.responseRouting[requestKey](requestId,timestamp,size,responseImage)

  def requestAutocrop(self,rid,mid,filename,callback):
   self.statsRequestQueue.put( (filename,'GetAutoCropCoords',dict(filename=filename,
                                                                  rid=rid,
                                                                  start=mid),callback) )

  def runSceneChangeDetection(self,filename,duration,callback):
    self.statsRequestQueue.put( (filename,'SceneChangeSearch',dict(filename=filename,
                                                                   duration=duration),callback) )

  def findLowerErrorRangeforLoop(self,filename,start,end,rid,secondsChange,cropRect,callback):
    self.statsRequestQueue.put( (filename,'MSESearchImprove',dict(filename=filename,
                                                                  start=start,
                                                                  end=end,
                                                                  rid=rid,
                                                                  cropRect=cropRect,
                                                                  secondsChange=secondsChange),callback) )


  def findRangeforLoop(self,filename,secondsCenter,minSeconds,maxSeconds,cropRect,callback):
    self.statsRequestQueue.put( (filename,'MSESearch',dict(filename=filename,
                                                           secondsCenter=secondsCenter,
                                                           minSeconds=minSeconds,
                                                           maxSeconds=maxSeconds,
                                                           cropRect=cropRect),callback) )


  def cancelEncodeRequest(self,requestId):
    cancelCurrentEncodeRequest(requestId)

  def loadImageFile(self,filename,duration,callback):
    self.loadImageAsVideoRequestQueue.put((filename,duration,callback))

if __name__ == '__main__':
  import webmGenerator
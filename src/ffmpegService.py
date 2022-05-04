
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
from .encoders.apngEncoder    import encoder as apngEncoder
from .encoders.mp4x264Encoder import encoder as mp4x264Encoder
from .encoders.webmvp8Encoder import encoder as webmvp8Encoder
from .encoders.webmvp9Encoder import encoder as webmvp9Encoder
from .encoders.mp4x264NvencEncoder import encoder as mp4x264NvencEncoder
from .encoders.mp4H265NvencEncoder import encoder as mp4H265NvencEncoder
from .encoders.mp4AV1Encoder       import encoder as mp4AV1Encoder

from .encodingUtils import cleanFilenameForFfmpeg
from .encodingUtils import getFreeNameForFileAndLog
from .encodingUtils import isRquestCancelled
from .encodingUtils import cancelCurrentEncodeRequest

from .subtitleCutter import trimSRTfile

from .ffmpegInfoParser import getVideoInfo
from .masonry import Brick,Stack


import subprocess as sp
import numpy as np
from collections import defaultdict, deque

def rgb2gray(rgb):
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray

def lucas_kanade_np(im1, im2, win=2):
    im1 = rgb2gray(im1)
    im2 = rgb2gray(im2)

    assert im1.shape == im2.shape
    I_x = np.zeros(im1.shape)
    I_y = np.zeros(im1.shape)
    I_t = np.zeros(im1.shape)
    I_x[1:-1, 1:-1] = (im1[1:-1, 2:] - im1[1:-1, :-2]) / 2
    I_y[1:-1, 1:-1] = (im1[2:, 1:-1] - im1[:-2, 1:-1]) / 2
    I_t[1:-1, 1:-1] = im1[1:-1, 1:-1] - im2[1:-1, 1:-1]
    params = np.zeros(im1.shape + (5,)) #Ix2, Iy2, Ixy, Ixt, Iyt
    params[..., 0] = I_x * I_x # I_x2
    params[..., 1] = I_y * I_y # I_y2
    params[..., 2] = I_x * I_y # I_xy
    params[..., 3] = I_x * I_t # I_xt
    params[..., 4] = I_y * I_t # I_yt
    del I_x, I_y, I_t
    cum_params = np.cumsum(np.cumsum(params, axis=0), axis=1)
    del params
    win_params = (cum_params[2 * win + 1:, 2 * win + 1:] -
                  cum_params[2 * win + 1:, :-1 - 2 * win] -
                  cum_params[:-1 - 2 * win, 2 * win + 1:] +
                  cum_params[:-1 - 2 * win, :-1 - 2 * win])
    del cum_params
    op_flow = np.zeros(im1.shape + (2,))
    det = win_params[...,0] * win_params[..., 1] - win_params[..., 2] **2
    op_flow_x = np.where(det != 0,
                         (win_params[..., 1] * win_params[..., 3] -
                          win_params[..., 2] * win_params[..., 4]) / det,
                         0)
    op_flow_y = np.where(det != 0,
                         (win_params[..., 0] * win_params[..., 4] -
                          win_params[..., 2] * win_params[..., 3]) / det,
                         0)
    op_flow[win + 1: -1 - win, win + 1: -1 - win, 0] = op_flow_x[:-1, :-1]
    op_flow[win + 1: -1 - win, win + 1: -1 - win, 1] = op_flow_y[:-1, :-1]

    mag = np.hypot(op_flow[:,:,0], op_flow[:,:,1])

    return mag.max()-mag.mean()

encoderMap = {
   'webm:VP8':webmvp8Encoder
  ,'webm:VP9':webmvp9Encoder
  ,'mp4:x264':mp4x264Encoder
  ,'mp4:x264_Nvenc':mp4x264NvencEncoder
  ,'mp4:H265_Nvenc':mp4H265NvencEncoder
  ,'mp4:AV1':mp4AV1Encoder
  ,'gif':gifEncoder
  ,'apng':apngEncoder
}

class FFmpegService():

  def __init__(self,globalStatusCallback=print,imageWorkerCount=2,encodeWorkerCount=1,statsWorkerCount=1,globalOptions={}):

    self.globalOptions=globalOptions
    self.cache={}
    self.imageRequestQueue = Queue()
    self.responseRouting = {}
    self.globalStatusCallback=globalStatusCallback
    self.abortflag=False
    self.scanabortflag=False

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
          
          cmd=['ffmpeg','-y',"-loglevel", "quiet","-noaccurate_seek",'-ss',str(timestamp),'-i',cleanFilenameForFfmpeg(filename), '-filter_complex',filters+',scale={w}:{h}:flags=area,thumbnail'.format(w=w,h=h),"-pix_fmt", "rgb24",'-vframes', '1', '-an', '-c:v', 'ppm', '-f', 'rawvideo', '-']
          
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
        
        videoFileName,_,tempVideoFilePath,videoFilePath = getFreeNameForFileAndLog(basename,ext,i)

        comvcmd = ['ffmpeg', '-i', cleanFilenameForFfmpeg(clipfilename), '-c', 'copy', '-copyinkf', '-ss', str(s), '-t', str(etime), tempVideoFilePath]
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

        basename = ''.join([x for x in basename if x in string.digits+string.ascii_letters+' -_'])[:50]

        loopCount = 1

        outname = '{}_{}_{}_{}_{}_{}.mp4'.format(i,basename,s,e,filterHash,runNumber)
        outname = os.path.join( tempPathname,outname )

        print('BRICKN',brickn,(i,(rid,clipfilename,s,e,filterexp,filterexpEnc)))
        print('key',key,outname)


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

      gridPaddingWidth =0
      try:
        gridPaddingWidth = int(options.get('gridPaddingWidth',0))
      except:
        pass
      
      logger={}
      vow,voh = tempStack.getSizeWithContstraint('width',maximumSideLength,logger,0,0,gridPaddingWidth)

      if vow>maximumSideLength or voh>maximumSideLength:
        logger={}
        vow,voh = tempStack.getSizeWithContstraint('height',maximumSideLength,logger,0,0,gridPaddingWidth)

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
              try:
                ts,vol1,vol2 = parts[0],parts[1],parts[2]
              except:
                ts,vol1,vol2 = parts[0],parts[1],parts[1]

              vol= -((float(vol1)+float(vol2))/2)
              minvol = min(minvol,vol)
              maxvol = max(maxvol,vol)

          for line in outs.decode('utf8').split('\n'):
            if line.strip() != '':
              parts = line.strip().split(',')
              try:
                ts,vol1,vol2 = parts[0],parts[1],parts[2]
              except:
                ts,vol1,vol2 = parts[0],parts[1],parts[1]
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


      ffmpegFilterCommand = "color=s={w}x{h}:c={colour}[base],".format(w=int(vow),h=int(voh),colour=options.get('gridPadColour','Black'))
      
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


      print('\nprocessed\n')
      print(processed)

      print('\nbrickTofileLookup\n')
      print(brickTofileLookup)
      print('\ninputsList\n')
      print(inputsList)
      print('\nbrickClips\n')
      print(brickClips)
      print('\nsorted(logger.items(),key=lambda x:int(x[0]))\n')
      print(sorted(logger.items(),key=lambda x:int(x[0])))
      print('\nfiltercommand\n')
      print(filtercommand)
      print('\n')


      outputFormat  = options.get('outputFormat','webm:VP8')
      finalEncoder  = encoderMap.get(outputFormat,encoderMap.get('webm:VP8'))
      finalEncoder(inputsList, 
                   outputPathName,
                   filenamePrefix, 
                   filtercommand, 
                   options, 
                   totalEncodedSeconds,   
                   totalExpectedEncodedSeconds, 
                   statusCallback, requestId=requestId, globalOptions=self.globalOptions)

    def encodeConcat(tempPathname,outputPathName,runNumber,requestId,mode,seqClips,options,filenamePrefix,statusCallback):

      expectedTimes = []
      processed={}
      fileSequence=[]
      clipDimensions = []
      infoOut={}

      usNVHWenc = '_Nvenc' in options.get('outputFormat','mp4:x264') 

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

      interpolateSpeedAdjustment = True
      try:
        interpolateSpeedAdjustment = bool(options.get('speedAdjustmentInterploate',True))
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
        basename = ''.join([x for x in basename if x in string.digits+string.ascii_letters+' -_'])[:50]

        if 'subtitles=filename=' in  filterexp:

          m = hashlib.md5()
          m.update(filterexp.encode('utf8'))
          filterHash = m.hexdigest()[:10]

          subfilename = filterexp.split('subtitles=filename=')[1].split(':force_style=')[0]
          subfilenameStrip = subfilename.replace("'",'')
          subOutname = os.path.join( tempPathname,'{}_{}_{}_{}_{}_{}.srt'.format(i,basename,start,end,filterHash,runNumber) )

          trimSRTfile(subfilenameStrip.replace('\\:',':'),subOutname,start,end)
                    
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
        basename = ''.join([x for x in basename if x in string.digits+string.ascii_letters+' -_'])[:50]

        outname = '{}_{}_{}_{}_{}_{}_{}.mp4'.format(i,basename,start,end,filterHash,runNumber,int(usNVHWenc))
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
          
          cuda_flags = []

          if usNVHWenc:
            if self.globalOptions.get('passCudaFlags',False):
              cuda_flags = ['-hwaccel', 'cuda']
            slice_encoder_preset = ['-c:v', 'h264_nvenc' , '-preset', 'losslesshp','-pix_fmt','yuv420p']
          else:  
            slice_encoder_preset = ['-c:v', 'libx264' , '-preset', 'veryfast']

          if infoOut[rid].hasaudio:
            comvcmd = ['ffmpeg','-y' ]+cuda_flags+[                                
                       '-ss', str(start)
                      ,'-i', cleanFilenameForFfmpeg(clipfilename)
                      ,'-t', str(end-start)
                      ,'-filter_complex', filterexp ] + slice_encoder_preset + [
                       '-crf', '0'
                      ,'-ac', '1',outname]
          else:
            comvcmd = ['ffmpeg','-y'  ]+cuda_flags+[
                       '-f', 'lavfi', '-i', 'anullsrc'                                
                      ,'-ss', str(start)
                      ,'-i', cleanFilenameForFfmpeg(clipfilename)
                      ,'-t', str(end-start)
                      ,'-filter_complex', filterexp ] + slice_encoder_preset + [
                       '-crf', '0'
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
                logging.debug(ln)
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

      useNewCrossfade=self.globalOptions.get('useNewCrossfade',True)
      loopStartAndEnd=options.get('loopStartAndEnd',False)

      transition = options.get('transStyle','smoothleft,smoothright').split(',')
      transition = itertools.cycle([x.strip() for x in transition if len(x.strip())>0])

      if useNewCrossfade and fadeDuration > 0.0 and len(fileSequence)>1:
        inputsList = []

        splitInitTemplate = '[0:v]{splitexp},null[vidsz0];'
        splitTemplate     = '[{i}:v]{splitexp},null[vidsz{i}];'

        audioSplitInitTemplate = '[0:a]anull[audsz0];'
        audioSplitTemplate     = '[{i}:a]anull[audsz{i}];'


        xFadeInitTemplate = '[vidsz0][vidsz1]xfade=transition={transition}:duration={fadeDuration:0.4f}s:offset={fadeOffset:0.4f}s[fade1];'
        xFadeTemplate     = '[fade{i}][vidsz{nexti}]xfade=transition={transition}:duration={fadeDuration:0.4f}s:offset={fadeOffset:0.4f}s[fade{nexti}];'

        crossfadeInitTemplate = '[audsz0][audsz1]acrossfade=d={fadeDuration}s[afade1];'
        crossfadeTemplate     = '[afade{i}]asetpts=PTS-STARTPTS,adelay=delays={delays}s:all=1,asetpts=PTS-STARTPTS[afade{i}ad],[afade{i}ad][audsz{nexti}]acrossfade=d={fadeDuration:0.4f}s,atrim={delays}s,asetpts=PTS-STARTPTS[afade{nexti}];'

  
        if loopStartAndEnd:
          audioSplitInitTemplate = '[0:a]asplit[tsa0][tsa1];[tsa0]atrim={fadedur:0.4f}:{dur},asetpts=PTS-STARTPTS[audsz0a];[tsa1]atrim=0:{fadedur:0.4f},asetpts=PTS-STARTPTS[audsz0];'        
          splitInitTemplate      = '[0:v]{splitexp},split[tsv0][tsv1];[tsv0]trim={fadedur}:{dur},setpts=PTS-STARTPTS[vidsz0a];[tsv1]trim=0:{fadedur:0.4f},setpts=PTS-STARTPTS[vidsz0];'
          
          crossfadeInitTemplate = '[audsz0a]asetpts=PTS-STARTPTS,adelay=delays={delays}s:all=1,asetpts=PTS-STARTPTS[audsz0ad],[audsz0ad][audsz1]acrossfade=d={fadeDuration:0.4f}s,atrim={delays}s,asetpts=PTS-STARTPTS[afade1];'
          xFadeInitTemplate     = '[vidsz0a][vidsz1]xfade=transition={transition}:duration={fadeDuration:0.4f}s:offset={fadeOffset:0.4f}s[fade1];'


        for vi,v in enumerate(fileSequence):
          inputsList.extend(['-i',v])

        
        offset=fadeDuration*2
        expectedFadeDurations = expectedTimes[:-1]

        audioSplits=[]
        videoSplits=[]
        xfades=[]
        crossfades=[]
        crossfadeOut=''
        
        previousXfadeOffset = 0
        for i,dur in enumerate(expectedFadeDurations):
          nexti= 0 if i==(len(expectedFadeDurations)-1) else i+1

          fadeoffset = (dur+previousXfadeOffset)-(fadeDuration)

          if loopStartAndEnd and i==0:
            fadeoffset -= fadeDuration

          totalExpectedFinalLength-=offset

          splitexp = fpsCmd
          if mode == 'CONCAT' and len(dimensionsSet) > 1:
            splitexp = "scale={in_maxWidth}:{in_maxHeight}:force_original_aspect_ratio=decrease:flags=bicubic,pad={in_maxWidth}:{in_maxHeight}:(ow-iw)/2:(oh-ih)/2,setsar=1:1,{fpsCmd}".format(in_maxWidth=in_maxWidth,in_maxHeight=in_maxHeight,fpsCmd=fpsCmd)

          if i == 0:
            videoSplits.append(splitInitTemplate.format(i=i,splitexp=splitexp,dur=dur,fadedur=fadeDuration,fadedurend=dur-fadeDuration))
            xfades.append(xFadeInitTemplate.format(i=i,nexti=nexti,fadeDuration=fadeDuration,fadeOffset=fadeoffset,transition=next(transition)))
            audioSplits.append(audioSplitInitTemplate.format(i=i,dur=dur,fadedur=fadeDuration,fadedurend=dur-fadeDuration))
            crossfades.append(crossfadeInitTemplate.format(i=i,nexti=nexti,fadeDuration=fadeDuration,fadeOffset=fadeoffset,delays=int(dur+1)))
          else:
            videoSplits.append(splitTemplate.format(i=i,splitexp=splitexp))
            xfades.append(xFadeTemplate.format(i=i,nexti=nexti,fadeDuration=fadeDuration,fadeOffset=fadeoffset,transition=next(transition)))
            
            audioSplits.append(audioSplitTemplate.format(i=i))
            crossfades.append(crossfadeTemplate.format(i=i,nexti=nexti,fadeDuration=fadeDuration,fadeOffset=fadeoffset,delays=int(dur+1)))



          print('------------------------')  
          print(i,dur)
          print(videoSplits[-1])
          print(xfades[-1])
          print(crossfades[-1])

          previousXfadeOffset = fadeoffset

        if loopStartAndEnd:
          crossfadeOut='[fade{i}]null[concatOutV],[afade{i}]anull[concatOutA]'.format(i=0)
        else:
          xfades=xfades[:-1]
          crossfades=crossfades[:-1]
          crossfadeOut='[fade{i}]null[concatOutV],[afade{i}]anull[concatOutA]'.format(i=i)


        if speedAdjustment==1.0:
          crossfadeOut += ',[concatOutV]null[outvpre],[concatOutA]anull[outapre]'
        else:
          try:
            vfactor=1/speedAdjustment
            afactor=speedAdjustment
            if interpolateSpeedAdjustment:
              crossfadeOut += ',[concatOutV]setpts={vfactor}*PTS,minterpolate=\'mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1:fps=30\'[outvpre],[concatOutA]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
            else:
              crossfadeOut += ',[concatOutV]setpts={vfactor}*PTS[outvpre],[concatOutA]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
          except Exception as e:
            logging.error("Crossfade exception",exc_info =e)
            crossfadeOut += ',[concatOutV]null[outvpre],[concatOutA]anull[outapre]'

        filtercommand = ''.join(videoSplits+xfades+audioSplits+crossfades+[crossfadeOut])
        print(filtercommand)

      elif fadeDuration > 0.0 and len(fileSequence)>1:

        inputsList = []

        splitTemplate     = '[{i}:v]{splitexp},split[vid{i}a][vid{i}b];'
        xFadeTemplate     = '[vid{i}a][vid{n}b]xfade=transition={trans}:duration={fdur}:offset={o}[fade{i}];'
        fadeTrimTemplate  = '[fade{i}]trim={preo}:{dur},setpts=PTS-STARTPTS[fadet{i}];'
        asplitTemplate    = '[{i}:a]asplit[ata{i}][atb{i}];[ata{i}]atrim={preo}:{dur}[atat{i}];'
        crossfadeTemplate = '[atat{i}][atb{n}]acrossfade=d={preo},atrim=0:{o}[audf{i}];'

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


        for i,dur in enumerate(expectedFadeDurations):
          n=0 if i==len(expectedFadeDurations)-1 else i+1
          o=dur-offset
          preo=offset          
          totalExpectedFinalLength-=offset

          splitexp = fpsCmd
          if mode == 'CONCAT' and len(dimensionsSet) > 1:
            splitexp = "scale={in_maxWidth}:{in_maxHeight}:force_original_aspect_ratio=decrease:flags=bicubic,pad={in_maxWidth}:{in_maxHeight}:(ow-iw)/2:(oh-ih)/2,setsar=1:1,{fpsCmd}".format(in_maxWidth=in_maxWidth,in_maxHeight=in_maxHeight,fpsCmd=fpsCmd)

          videoSplits.append(splitTemplate.format(i=i,splitexp=splitexp))
          transitionFilters.append(xFadeTemplate.format(i=i,n=n,o=o,fdur=fadeDuration,trans=next(transition)))
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
            if interpolateSpeedAdjustment:
              crossfadeOut += ',[concatOutV]setpts={vfactor}*PTS,minterpolate=\'mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1:fps=30\'[outvpre],[concatOutA]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
            else:
              crossfadeOut += ',[concatOutV]setpts={vfactor}*PTS[outvpre],[concatOutA]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
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
            if interpolateSpeedAdjustment:
              filtercommand += ',[outvconcat]setpts={vfactor}*PTS,minterpolate=\'mi_mode=mci:mc_mode=aobmc:me_mode=bidir:me=epzs:vsbmc=1:fps=30\'[outvpre],[outaconcat]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
            else:
              filtercommand += ',[outvconcat]setpts={vfactor}*PTS[outvpre],[outaconcat]atempo={afactor}[outapre]'.format(vfactor=vfactor,afactor=afactor)
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
                   statusCallback, requestId=requestId, encodeStageFilter=encodeStageFilter, globalOptions=self.globalOptions)


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
          print(requestType,options)
          

          if requestType =='MaxInterFrameMove':


            logging.debug('inter frame move start')
            filename = options.get('filename')
            start = options.get('start')
            end   = options.get('end')
            position= options.get('pos','mid')
            clipDur = (end-start)

            cropRect = options.get('cropRect')
            rid = options.get('rid')
            
            od=256
            nbytes = 3 * od * od

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

            self.globalStatusCallback('Finding greatest motion',0)
            
            famesCmd = ["ffmpeg"
                      ,'-ss',str(start)
                      ,"-i", cleanFilenameForFfmpeg(filename)  
                      ,'-s', '{}x{}'.format(od,od)
                      ,'-ss',str(start)
                      ,'-t', str(clipDur)
                      ,"-filter_complex", videofilter
                      ,"-copyts"
                      ,"-f","image2pipe"
                      ,"-an"
                      ,"-pix_fmt","bgr24"
                      ,"-vcodec","rawvideo"
                      ,"-vsync", "vfr"
                      ,"-"]

            frames = np.frombuffer(sp.Popen(famesCmd,**popen_params).stdout.read(), dtype="uint8")
            frames.shape = (-1,od,od,3)

            lastFrame=None
            maxInterFrame=0
            maxFrameInd=None

            for si,frame in enumerate(frames):
              
              self.globalStatusCallback('Finding greatest motion',si/frames.shape[0])

              if lastFrame is not None:
                #mse = ((frames[si] - lastFrame)**2).mean()
                mse = lucas_kanade_np(frames[si],lastFrame)
                print(si,mse)

                if mse > maxInterFrame:
                  maxInterFrame = mse
                  maxFrameInd = si

              lastFrame = frames[si]

            if maxFrameInd is not None:
              pc = maxFrameInd/frames.shape[0]
              pcSeconds = (clipDur*pc)
              secondsAdjust = pcSeconds-(clipDur/2)

              self.globalStatusCallback('Finding greatest motion, updating',1)
              if position == 'start':
                callback(filename,rid,mse,start+pcSeconds,end+pcSeconds)
              elif position == 'end':
                callback(filename,rid,mse,start-pcSeconds,end-pcSeconds)
              else:
                callback(filename,rid,mse,start+secondsAdjust,end+secondsAdjust)
            else:
              self.globalStatusCallback('No maximum found, closing',1)
              

          elif requestType == 'FullLoopSearch':
            addCuts        = bool(options.get('addCuts',True))
            
            totalDuration  = float(options.get('duration'))
            minSeconds     = float(options.get('minSeconds',1))
            maxSeconds     = float(options.get('maxSeconds',5))

            addCuts     = bool(options.get('addCuts',False))
            useRange    = bool(options.get('useRange',False))
            rangeStart  = options.get('rangeStart',0)
            rangeEnd    = options.get('rangeEnd',0)
            threshold   = options.get('threshold',30)                                                                
            cropRect    = options.get('cropRect',(0,0,0,0))

            midThreshold    = float(options.get('midThreshold',30))
            minLength       = float(options.get('minLength',1))
            maxLength       = float(options.get('maxLength',3))
            timeSkip        = float(options.get('timeSkip',1))
            ifdmode         = bool(options.get('ifdmode',False))
            scaleWidth      = int(float(options.get('scaleWidth',450)))
                       
            finalScanMode = options.get('selectionMode','bestFirst')

            scaleFilter = "scale={}:-1:force_original_aspect_ratio=decrease:flags=neighbor".format(scaleWidth)

            videoInfo = getVideoInfo(cleanFilenameForFfmpeg(filename),filters=scaleFilter)

            startTs = 0
            endTs   = totalDuration

            if useRange:
              startTs = rangeStart
              endTs   = rangeEnd


            length = endTs-startTs

            odw=videoInfo.width
            odh=videoInfo.height

            min_duration=minLength
            max_duration=maxLength

            match_threshold   = threshold
            nomatch_threshold = midThreshold

            time_distance=timeSkip

            if nomatch_threshold is None:
                nomatch_threshold = match_threshold

            nomatchAndMatchAreEqual = nomatch_threshold == match_threshold

            N_pixels = odw*odh*3

            def dot_product(F1, F2):
              return (F1 * F2).sum() / N_pixels



            def distance(t1, t2):
                uv = dot_product(frame_dict[t1]["frame"], frame_dict[t2]["frame"])
                u, v = frame_dict[t1]["|F|sq"], frame_dict[t2]["|F|sq"]
                return np.sqrt(u + v - 2 * uv)

            cmd = ["ffmpeg"
                      ,'-ss',str(startTs)
                      ,"-i", cleanFilenameForFfmpeg(filename) 
                      ,'-ss',str(startTs)
                      ,'-t', str(length)
                      ,'-vf','scale={}:{},setsar=1/1'.format(odw,odh)
                      ,"-copyts"
                      ,"-f","image2pipe"
                      ,"-an"
                      ,"-pix_fmt","bgr24"
                      ,"-vcodec","rawvideo"
                      ,"-vsync", "vfr"
                      ,"-"]

            proc = sp.Popen(cmd,stdout=sp.PIPE,stderr=sp.DEVNULL,bufsize=10 ** 5)

            fps=23.98
            t=startTs-(1/fps)

            frame_dict = {}
            matching_frames = []
            framen=0
            distances = deque([0],int(fps*2*max_duration))
            totalRawMatches=0
            goodMatches=[]

            self.globalStatusCallback('Starting loop scan',0)

            self.scanabortflag=False

            while 1:

              if self.scanabortflag:
                break

              frame = proc.stdout.read(N_pixels)
              if len(frame)==N_pixels:
                frame = np.frombuffer(frame,dtype="uint8")
                t = t+(1/fps)

                framen+=1
                if framen%10==0:
                  meanDist = float(np.mean(distances))
                  self.globalStatusCallback('Running loop scan, pendingMatches:{urm} rawMatches:{trm} meanFrameDist:{ifd:0.3f}'.format(urm=len(matching_frames),trm=totalRawMatches,ifd=meanDist),(t-startTs)/length)
                  if ifdmode:
                    match_threshold=meanDist+threshold
                    nomatch_threshold=meanDist+midThreshold



                flat_frame = 1.0 * frame.flatten()
                F_norm_sq = dot_product(flat_frame, flat_frame)
                F_norm = np.sqrt(F_norm_sq)

                for t2 in list(frame_dict.keys()):
                  # forget old frames, add 't' to the others frames
                  # check for early rejections based on differing norms
                  if (t - t2) > max_duration:
                    frame_dict.pop(t2)
                  else:
                    frame_dict[t2][t] = {
                        "min": abs(frame_dict[t2]["|F|"] - F_norm),
                        "max": frame_dict[t2]["|F|"] + F_norm,
                    }
                    frame_dict[t2][t]["rejected"] = (
                        frame_dict[t2][t]["min"] > match_threshold
                    )

                t_F = sorted(frame_dict.keys())
                frame_dict[t] = {"frame": flat_frame, "|F|sq": F_norm_sq, "|F|": F_norm}

                for i, t2 in enumerate(t_F):
                  # Compare F(t) to all the previous frames

                  if frame_dict[t2][t]["rejected"]:
                      continue

                  

                  dist = distance(t, t2)

                  if i==len(t_F)-1:
                    distances.append(dist)
                  
                  frame_dict[t2][t]["min"] = frame_dict[t2][t]["max"] = dist
                  frame_dict[t2][t]["rejected"] = dist >= match_threshold

                  for t3 in t_F[i + 1 :]:
                    t3t, t2t3 = frame_dict[t3][t], frame_dict[t2][t3]
                    t3t["max"] = min(t3t["max"], dist + t2t3["max"])
                    t3t["min"] = max(t3t["min"], dist - t2t3["max"], t2t3["min"] - dist)
                    if t3t["min"] > match_threshold:
                        t3t["rejected"] = True

                # Store all the good matches (end_time,t)
                new_matching_frames =  [
                  (t1, t, frame_dict[t1][t]["min"], frame_dict[t1][t]["max"])
                  for t1 in frame_dict
                  if (t1 != t) and not frame_dict[t1][t]["rejected"]
                ]
                totalRawMatches += len(new_matching_frames)
                matching_frames += new_matching_frames

              if len(matching_frames)>0:
                olderFrames=[]
                while 1:
                  frameAdded=False
                  if len(matching_frames)>0 and ( ( matching_frames[0][0]<(t-(max_duration*4)) or   ( len(olderFrames)>0 and  matching_frames[0][0]<(t-(max_duration*2))))  or len(frame)<N_pixels):
                    olderFrames.append(matching_frames.pop(0))
                    frameAdded=True
                  if not frameAdded:
                    break      
                if len(olderFrames)>0:

                  print('------ Frame Scan------')
                  print('finalScanMode == '+finalScanMode)

                  if finalScanMode == 'bestFirst':
                    pushedFrames = set()

                    for start,end,min_distance,max_distance in sorted(olderFrames, key=lambda x:x[3]):
                      if (end - start) > min_duration:
                        hasOverlap = False
                        for eStart,eEnd in pushedFrames:
                          latest_start = max(start, eStart - time_distance)
                          earliest_end = min(end,   eEnd   + time_distance)
                          overlap = (earliest_end-latest_start)+1
                          overlap = max(0, overlap)
                          if overlap > 0:
                            hasOverlap=True
                            break
                        if not hasOverlap:
                          callback(filename,start,end,kind='Cut')
                          pushedFrames.add((start,end))

                  else:

                    dict_starts = defaultdict(lambda: [])
                    for (start, end, min_distance, max_distance) in olderFrames:
                        dict_starts[start].append([end, min_distance, max_distance])
                    starts_ends = sorted(dict_starts.items(), key=lambda k: k[0])

                    min_start = 0
                    for start, ends_distances in starts_ends:

                      if start < min_start:
                          print('start < min_start')
                          continue
                      ends = [end for (end, min_distance, max_distance) in ends_distances]
                      great_matches = [
                          (end, min_distance, max_distance)
                          for (end, min_distance, max_distance) in ends_distances
                          if max_distance < match_threshold
                      ]
                      print('great_matches',start,great_matches)
                      great_long_matches = [
                          (end, min_distance, max_distance)
                          for (end, min_distance, max_distance) in great_matches
                          if (end - start) > min_duration
                      ]

                      print('great_long_matches',start,great_long_matches)
                      if not great_long_matches:
                          print('not great_long_matches')
                          continue  # No GIF can be made starting at this time

                      
                      poor_matches = {
                          end
                          for (end, min_distance, max_distance) in ends_distances
                          if min_distance > nomatch_threshold
                      }
                      short_matches = {end for end in ends if (end - start) <= 0.6}

                      print('poor_matches',start,poor_matches)
                      print('short_matches',start,short_matches)

                      
                      if not poor_matches.intersection(short_matches):
                          print(start,'not poor_matches.intersection(short_matches)')
                          continue
                      
                      end = max(end for (end, min_distance, max_distance) in great_long_matches)
                      end, min_distance, max_distance = next(
                          e for e in great_long_matches if e[0] == end
                      )

                      print('\n\nMATCH!')

                      callback(filename,start,end,kind='Cut')
                      print('\n')
                      goodMatches.append( (start, end, min_distance, max_distance) )
                      min_start = end + time_distance
                  print('------------')

              if len(frame)<N_pixels:
                break

            self.globalStatusCallback('Loop scan complete',1)

          elif requestType == 'RepresentativeSections':
            addCuts        = bool(options.get('addCuts',True))
            clipLength     = float(options.get('clipLength'))
            halfclipLength = clipLength/2
            totalDuration  = float(options.get('duration'))
            videoInfo = getVideoInfo(filename)

            sectionLength = int(videoInfo.fps*clipLength*3)
            proc = sp.Popen(["ffmpeg","-i",cleanFilenameForFfmpeg(filename) ,"-vf","scale=400:400,thumbnail=n={sectionLength}".format(sectionLength=sectionLength),"-f","null","-"],stderr=sp.PIPE,stdout=sp.DEVNULL)
            l=b''
            pair=[]
            self.globalStatusCallback('Detecting scene centres',0)

            while 1:
              c = proc.stderr.read(1)
              if len(c)==0:
                break

              if c in b'\n\r':
                if b' (pts_time=' in l:
                  ts = float(l.split(b' (pts_time=')[1].split(b')')[0])

                  if options.get('addCuts',False):
                    callback(filename,ts-halfclipLength,ts+halfclipLength,kind='Cut')
                  else:
                    callback(filename,ts,kind='Mark')
                  self.globalStatusCallback('Detecting scene centres',ts/totalDuration)

                l=b''
              else:
                l += c 

            self.globalStatusCallback('Detecting scene centres complete',1)


          elif requestType == 'AddLoudSections':
            threshold = options.get('threshold',90)
            totalDuration=float(options.get('duration',1))
            mergeDistance = options.get('mergeDistance',3)
            timetampOffset=0
            rangeClause = []

            if options.get('useRange',False):
              a = float(options.get('rangeStart',0))
              b = float(options.get('rangeEnd',totalDuration))
              totalDuration=(b-a)
              rangeClause=['-ss',str(a),'-to',str(b)]             
              timetampOffset=a


            proc = sp.Popen(["ffmpeg"]+rangeClause+["-i",cleanFilenameForFfmpeg(filename) ,"-af","silencedetect=n=-{threshold}dB:d=10".format(threshold=threshold),"-f","null","-"],stderr=sp.PIPE,stdout=sp.DEVNULL)

            l=b''
            pair=[]
            self.globalStatusCallback('Detecting loud sections',0)

            while 1:
              c = proc.stderr.read(1)
              if len(c)==0:
                break

              if c in b'\n\r':
                t=None
                if b'silence_start:' in l:
                  t=float(l.split(b' ')[4])
                elif b'silence_end:' in l:
                  t=float(l.split(b' ')[4])
                elif b'time=' in l:
                  try:
                    tstamp = l.split(b'time=')[1].split(b' ')[0].strip()
                    pt = datetime.strptime(tstamp.decode('utf8'),'%H:%M:%S.%f')
                    tstamp = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
                    self.globalStatusCallback('Detecting loud sections',tstamp/totalDuration)
                  except Exception as e:
                    print(e)
                if t is not None and t>0:
                  pair.append(t)
                  if len(pair)==2:
                    callback(filename,pair[0]+timetampOffset,pair[1]+timetampOffset)
                    pair=[]
                l=b''
              else:
                l += c 

            self.globalStatusCallback('Loud section detection complete',1)

          elif requestType == 'GetAutoCropCoords':

            start = options.get('start',0)
            audocropcmd = ["ffmpeg", "-ss", str(start), "-i", cleanFilenameForFfmpeg(filename) , "-t", "1", "-filter_complex", "cropdetect", "-f", "null", "NUL"]
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
            
            self.globalStatusCallback('Finding closest frame match',0)

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
            searchDistance = (end-start)*(searchDistance/100)            

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

            self.globalStatusCallback('Finding closest frame match',0)
            
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
            threshold = float(options.get('threshold',0.3))
            self.globalStatusCallback('Starting scene change detection ',0/expectedLength)
            
            rangeClause=[]
            rangeStart=0
            lastTimestamp=0
            timetampOffset=0
            ts=0
            if options.get('useRange',False):
              a = float(options.get('rangeStart',0))
              b = float(options.get('rangeEnd',expectedLength))
              expectedLength=(b-a)
              rangeStart=a
              rangeClause=['-ss',str(a),'-to',str(b)]          
              lastTimestamp=a    
              timetampOffset=a

            cmd = ['ffmpeg']+rangeClause+['-i',cleanFilenameForFfmpeg(filename),'-filter_complex','select=gt(scene\\,{threshold}),showinfo'.format(threshold=threshold), '-f', 'null', 'NUL']
            print(' '.join(cmd))
            proc = sp.Popen(
              cmd  
              ,stderr=sp.PIPE)

            ln=b''
            
            while 1:
              c=proc.stderr.read(1)
              if len(c)==0:
                break
              try:
                if c in b'\r\n':
                  if b'pts_time' in ln:
                    for e in ln.split(b' '):
                      if b'pts_time' in e:
                        ts = float(e.split(b':')[-1])
                        self.globalStatusCallback('Scene change detection ',ts/expectedLength)
                        if options.get('addCuts',False):
                          callback(filename,lastTimestamp,ts+timetampOffset,kind='Cut')
                          lastTimestamp=ts+timetampOffset
                        else:
                          callback(filename,ts+timetampOffset,kind='Mark')
                  ln=b''
                else:
                  ln+=c
              except Exception as e:
                print(e)
            if lastTimestamp != rangeStart:
              if options.get('addCuts',False):
                callback(filename,lastTimestamp,ts+timetampOffset,kind='Cut')
                lastTimestamp=ts+timetampOffset
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

  def runSceneChangeDetection(self,filename,duration,callback,threshold=0.3,addCuts=False,useRange=False,rangeStart=None,rangeEnd=None):
    self.statsRequestQueue.put( (filename,'SceneChangeSearch',dict(filename=filename,
                                                                   addCuts=addCuts,
                                                                   useRange=useRange,
                                                                   rangeStart=rangeStart,
                                                                   rangeEnd=rangeEnd,
                                                                   threshold=threshold,
                                                                   duration=duration),callback) )


  def runRepresentativeCentresDetection(self,filename,duration,callback,clipLength=30,addCuts=False,useRange=False,rangeStart=None,rangeEnd=None):
    self.statsRequestQueue.put( (filename,'RepresentativeSections',dict(filename=filename,
                                                                        addCuts=addCuts,
                                                                        useRange=useRange,
                                                                        rangeStart=rangeStart,
                                                                        rangeEnd=rangeEnd,
                                                                        clipLength=clipLength,
                                                                        duration=duration),callback) )



  def scanAndAddLoudSections(self,filename,totalDuration,threshold,callback,useRange=False,rangeStart=None,rangeEnd=None):
    self.statsRequestQueue.put( (filename,'AddLoudSections',dict(filename=filename, 
                                                                 duration=totalDuration,
                                                                 useRange=useRange,
                                                                 rangeStart=rangeStart,
                                                                 rangeEnd=rangeEnd,                                                                 
                                                                 threshold=threshold),callback) )    


  def moveToMaximumInterFrameDistance(self, filename,start,end,pos,rid,callback):
    self.statsRequestQueue.put( (filename,'MaxInterFrameMove',dict(filename=filename,
                                                              start=start,
                                                              end=end,
                                                              pos=pos,
                                                              rid=rid),callback) )

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
    
  def fullLoopSearch(self,filename,duration,callback,midThreshold=30,minLength=1,maxLength=5,timeSkip=1,threshold=30,addCuts=True,useRange=False,rangeStart=None,rangeEnd=None,ifdmode=False,selectionMode='bestFirst'):
    self.statsRequestQueue.put( (filename,'FullLoopSearch',dict(filename=filename,
                                                                duration=duration,
                                                                midThreshold=midThreshold,
                                                                minLength=minLength,
                                                                maxLength=maxLength,
                                                                timeSkip=timeSkip,
                                                                threshold=threshold,
                                                                addCuts=addCuts,
                                                                useRange=useRange,
                                                                rangeStart=rangeStart,
                                                                rangeEnd=rangeEnd,
                                                                ifdmode=ifdmode,  
                                                                selectionMode=selectionMode,                                                              
                                                                cropRect=None),callback) )

  def cancelEncodeRequest(self,requestId):
    cancelCurrentEncodeRequest(requestId)

  def cancelAllEncodeRequests(self):
    self.abortflag=True
    cancelCurrentEncodeRequest(-1)

  def cancelCurrentScans(self):
    self.scanabortflag=True



  def loadImageFile(self,filename,duration,callback):
    self.loadImageAsVideoRequestQueue.put((filename,duration,callback))

if __name__ == '__main__':
  import webmGenerator
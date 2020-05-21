
import subprocess as sp
import os
from datetime import datetime


maxWidth = 1280

targetSizeAllowance = 0.98
audio_mp = 8
video_mp = 1024*1024
crf=4
threads = 2
logo='logo.png'
footer='footer.png'
maxTriesBeforeAcceptingSmaller=10
maxTries=15
printFFmpegVerbose=True

import json
try:
  config         = json.loads(open('config.json','r').read())
  maxWidth       = config.get('maxWidth',maxWidth) 
  crf            = config.get('crf',crf) 
  threads        = config.get('threads',threads)  
  maxTries       = config.get('maxTries',maxTries)  
  maxTriesBeforeAcceptingSmaller = config.get('maxTriesBeforeAcceptingSmaller',maxTriesBeforeAcceptingSmaller)
  printFFmpegVerbose             = bool(config.get('printFFmpegVerbose',printFFmpegVerbose))
except Exception as e:
  print(e)


def monitorFFMPEGProgress(proc,desc,a,b,filename):
  print('Encoding (Starting)',end='\r')
  ln=b''
  percents = []
  sizes    = []
  percentComplete=0
  while 1:
    c = proc.stderr.read(1)
    if len(c)==0:
      break
    if c == b'\r':
      if printFFmpegVerbose:
        print(ln)
      for p in ln.split(b' '):
        if b'time=' in p:
          try:
            pt = datetime.strptime(p.split(b'=')[-1].decode('utf8'),'%H:%M:%S.%f')
            total_seconds = pt.microsecond/1000000 + pt.second + pt.minute*60 + pt.hour*3600
            if total_seconds>0:
              percentComplete = (total_seconds/abs(a-b))
              print('Encoding (Actual) {:01.2f}%'.format(percentComplete*100) ,end='\r')
          except Exception as e:
            print(e)
      ln=b''
    ln+=c
  print('Encoding (Complete) {:01.2f}%'.format(percentComplete*100) ,end='\r')
  return percentComplete

def buildFilterString(incudelogo,extraFiltersPre,extraFiltersPost,cw,ch,cx,cy,fpsLimit,maxVWidth,minVWidth):

  if fpsLimit is None or fpsLimit == 'None':
    fpsLimit=None
  else:
    fpsLimit=float(fpsLimit)+0.1

  if maxVWidth is None or maxVWidth == 'None':
    maxVWidth=9999999
  else:
    maxVWidth = int(float(maxVWidth))

  if minVWidth is None or minVWidth == 'None':
    minVWidth=0
  else:
    minVWidth = int(float(minVWidth))


  filterString = "movie='logo.png'[logo]"

  if extraFiltersPre is not None:
    filterString += ',[0:v]'+extraFiltersPre+'[inFilters]'
  else:
    filterString += ',[0:v]null[inFilters]'


  if cx!=0 and cy !=0 and cw!=0 and ch!=0:
    filterString += ",[inFilters]crop={}:{}:{}:{}[cropped]".format(cw,ch,cx,cy)
  else:
    filterString += ",[inFilters]null[cropped]"

  filterString += ",[cropped] scale='max({}\\,min({}\\,iw)):-1'[scaled]".format(minVWidth,maxVWidth)

  if incudelogo:
    filterString += ",[scaled][logo]overlay='5:5'"
  else:
    filterString += ",[logo]nullsink,[scaled]null"

  if fpsLimit is not None:
    filterString += ",select='eq(n,0)+if(gt(t-prev_selected_t,1/{}),1,0)'[fpscap]".format(fpsLimit)
  else:
    filterString += ',null[fpscap]'

  if extraFiltersPost is not None:
    filterString += ',[fpscap]'+extraFiltersPost+',sidedata=mode=delete'
  else:
    filterString += ',[fpscap]null,sidedata=mode=delete'

  return filterString



def buildFFmpegCommand(passNumber,filename,logName,start,duration,bitrate,threads,crf,filterString,outputFilename,audioBR,requiresTransparency):
  command = [
    "ffmpeg"
   ,"-y" 
   ,"-ss", "{:01.2f}".format(start) 
   ,"-i", filename 
   ,"-map_metadata", "-1"
   ,"-ss", "{:01.2f}".format(start) 
   ,"-t", "{:01.2f}".format(duration)
   ,"-c:v","libvpx" 
   ,"-stats"
   ,"-bufsize", "3000k"
   ,"-threads", str(threads)
   ,"-quality", "best"] 
   
  if requiresTransparency:
    command.extend([
      "-auto-alt-ref", "0"  
    ])
  else:
    command.extend([
      "-auto-alt-ref", "1"  
    ])

  command.extend([
    "-lag-in-frames", "16" 
   ,"-slices", "8"
   ,"-passlogfile", logName
   ,"-cpu-used", "0"
   ,"-copyts"
   ,"-crf"  ,str(crf)
   ,"-b:v",str(bitrate)
   ,"-ac"   ,"1"
   ,"-sn"
  ])

  if passNumber == 1 or audioBR == 'No Audio':
    command.extend(["-an"])
  else:
    command.extend([
      "-c:a"  ,"libvorbis"
     ,"-b:a"  , audioBR
    ])

  command.extend([
     "-sn"
    ,"-sws_flags", "bicubic+full_chroma_inp+accurate_rnd+full_chroma_inp"
    ,"-filter_complex", filterString
  ])

  if requiresTransparency:
    command.extend(["-pix_fmt","yuva420p"])
  else:
    command.extend(["-pix_fmt","yuv420p"])


  command.extend([
     "-movflags",       "faststart"
    ,"-pass"            ,str(passNumber)
    ,"-f"               ,"webm" 

    ,"-map_metadata", "-1"
    ,outputFilename
  ])

  return command

def processClips(clipsQueue):

  t=clipsQueue.qsize()
  
  outFolder = datetime.now().strftime('Batch_%Y%m%d_%H%M%S')
  i=-1
  while 1:
    job = clipsQueue.get()
    if job is None:
      clipsQueue.task_done()
      return
    ((cat,src,s,e),(incudelogo,(extraFiltersPre,extraFiltersPost)),(cw,ch,cx,cy),properties) = job
    i=i+1

    requiresTransparency=False
    if extraFiltersPre is not None and 'colorkey' in extraFiltersPre:
      requiresTransparency=True

    fpsLimit,sizeLimit,audioBR,videoBrMax,maxVWidth,minVWidth = properties

    if videoBrMax is None or sizeLimit == 'None':
      videoBrMax = None
    else:
      videoBrMax = sizeLimit.replace('M','')
      videoBrMax = float(videoBrMax*video_mp)

    desc = """
Job: {i}/{t}
Source file:{src}
Category:{cat}
Range: {s}s - {e}s
Include Logo:{incudelogo}
ExtraFiltersPre:{extraFiltersPre}
extraFiltersPost:{extraFiltersPost}
Crop: w={cw} h={ch} x={cx} y={cy}
    """.format(i=i+1,t=t,cat=cat,src=src,
               s=s,e=e,
               incudelogo=incudelogo,
               extraFiltersPre=extraFiltersPre,
               extraFiltersPost=extraFiltersPost,
               cw=cw,ch=ch,cx=cx,cy=cy)

    print(desc)
    cw,ch,cx,cy  = int(cw),int(ch),int(cx),int(cy)

    s = max(0,s)
    dur = abs(s-e)

    targetSize_max   = 4194304
    if sizeLimit is None or sizeLimit == 'None':
      targetSize_max=9999999999999999
      targetSize_min=0
      br = 544000000
      targetSize_guide = (targetSize_max+targetSize_min)/2
    else:
      targetSize_max = int(sizeLimit.replace('M',''))
      targetSize_max = float(targetSize_max*video_mp)
      targetSize_min   = targetSize_max*targetSizeAllowance
      targetSize_guide = (targetSize_max+targetSize_min)/2
      br = ( ((targetSize_guide)/dur) - ((64 / audio_mp)/dur) )*8

    

    outFilename=os.path.join('out',outFolder,os.path.splitext(os.path.basename(src))[0]+'.'+str(int(s))+'.'+str(int(e))+".webm")
    tempname = os.path.join('temp',os.path.splitext(os.path.basename(src))[0]+'.'+str(int(s))+'.'+str(int(e))+".webm")

    attempt=0
    filterString = buildFilterString(incudelogo,extraFiltersPre,extraFiltersPost,cw,ch,cx,cy,fpsLimit,maxVWidth,minVWidth)

    smallestFailedBr=float('inf')

    largestFailedUnderMinimum=None
    smallestFailedOverMaximum=None


    cmd = buildFFmpegCommand(passNumber=2,
                             filename=src,
                             logName=tempname+'.log',
                             start=s,
                             duration=dur,
                             bitrate=br,
                             threads=threads,
                             crf=crf,
                             filterString=filterString,
                             outputFilename=tempname,
                             audioBR=audioBR,
                             requiresTransparency=requiresTransparency)
    
    print('Ffmpeg command')
    print(' '.join(cmd))
    print('')

    while 1:
      attempt+=1
      
      cmd = buildFFmpegCommand(passNumber=1,
                               filename=src,
                               logName=tempname+'.log',
                               start=s,
                               duration=dur,
                               bitrate=br,
                               threads=threads,
                               crf=crf,
                               filterString=filterString,
                               outputFilename='nul',
                               audioBR=audioBR,
                               requiresTransparency=requiresTransparency)

      print('Starting Pass 1 attempt {} @ bitrate {}'.format(attempt,br))

      if printFFmpegVerbose:
        print('\nFFmpeg Phase 1 Cmd\n',' '.join(cmd))

      os.path.exists('temp') or os.mkdir('temp')

      proc = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)
      proc.communicate()

      cmd = buildFFmpegCommand(passNumber=2,
                               filename=src,
                               logName=tempname+'.log',
                               start=s,
                               duration=dur,
                               bitrate=br,
                               threads=threads,
                               crf=crf,
                               filterString=filterString,
                               outputFilename=tempname,
                               audioBR=audioBR,
                               requiresTransparency=requiresTransparency)

      print('Starting Pass 2 attempt {} @ bitrate {}'.format(attempt,br))
      
      

      if printFFmpegVerbose:
        print('\nFFmpeg Phase 2 Cmd\n',' '.join(cmd))
      proc = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)
      monitorFFMPEGProgress(proc,'Encoding:',s,e,tempname)
      
      proc.communicate()

      finalSize = os.stat(tempname).st_size

      if targetSize_min<finalSize<targetSize_max or (br==videoBrMax) or (finalSize<targetSize_max and attempt>10):
        print("Encoding Complete.")
        os.path.exists('out') or os.mkdir('out')
        os.path.exists(os.path.join('out',outFolder)) or os.mkdir(os.path.join('out',outFolder))
        os.rename(tempname,outFilename)
        try:
          sp.Popen(['mkvpropedit',outFilename,'--edit','track:1','--delete','projection-type'])#,'--delete','stereo-mode'
        except Exception as e:
          print('mkvpropedit not installed skipping projection removal',e)
        clipsQueue.task_done()
        break
      else:
        if finalSize>targetSize_max:

          if smallestFailedOverMaximum is None or br<smallestFailedOverMaximum:
            smallestFailedOverMaximum=br

          if br<smallestFailedBr:
            smallestFailedBr = br

          print('Encoding complete {:01.2f}%  [ {}B @ {} : {:01.2f}MB {:01.2f}% of size maximum]'.format( 
              100, 
              finalSize,
              br,
              finalSize/1048576 , 
              ( finalSize / targetSize_max )*100 
            ))
        if finalSize<targetSize_min:

          if largestFailedUnderMinimum is None or br>largestFailedUnderMinimum:
            largestFailedUnderMinimum=br

          print('Encoding complete {:01.2f}%  [ {}B @ {} : {:01.2f}MB {:01.2f}% of size minimum]'.format( 
              100, 
              finalSize,
              br,
              finalSize/1048576 , 
              ( finalSize / targetSize_min )*100 
            ))

        lastbr=br


        br =  br * (1/(finalSize/targetSize_guide))
        br =  min(min(videoBrMax,br),smallestFailedBr-1)
        
        if largestFailedUnderMinimum is not None and smallestFailedOverMaximum is not None:
          br = (largestFailedUnderMinimum+smallestFailedOverMaximum)/2

        print("Setting new bitrate {} ({:+f})".format(br,br-lastbr))
  

import subprocess as sp
import os
import threading
from queue import Queue
import traceback

class YTDLService():

  def __init__(self,globalStatusCallback=print()):
    self.globalStatusCallback = globalStatusCallback
    self.downloadRequestQueue = Queue()

    def downloadFunc():
      while 1:
        try:
          url,callback = self.downloadRequestQueue.get()

          if url == 'UPDATE':
            self.globalStatusCallback('youtube-dl upgrade',0.0)
            print(url)
            proc = sp.Popen(['youtube-dl','--update'],stdout=sp.PIPE)
            l = b''
            while 1:
              c=proc.stdout.read(1)
              l+=c
              if len(c)==0:
                break
              if c in (b'\n',b'\r'):
                self.globalStatusCallback('youtube-dl upgrade {}'.format(l.decode('utf8',errors='ignore').strip()),0.0)
            self.globalStatusCallback('youtube-dl upgrade {}'.format(l.decode('utf8',errors='ignore').strip()),1.0)
            continue

          tempPathname='tempDownloadedVideoFiles'
          os.path.exists(tempPathname) or os.mkdir(tempPathname)
          outfolder = os.path.join(tempPathname,'%(id)s-%(title)s.%(ext)s')
          proc = sp.Popen(['youtube-dl','--ignore-errors','--restrict-filenames','-f','best',url,'-o',outfolder,'--merge-output-format','mp4'],stdout=sp.PIPE)
          l = b''
          self.globalStatusCallback('Downloading {}'.format(url),0)
          finalName = b''
          
          seenFiles = set()
          emittedFiles = set()

          while 1:
            c=proc.stdout.read(1)
            l+=c
            if len(c)==0:
              print(c,l)
              break
            if c in (b'\n',b'\r'):
              print(l)
              
              if b'[download] Destination:' in l:
                finalName = l.replace(b'[download] Destination: ',b'').strip()
                seenFiles.add(finalName)
                print(finalName)
              if b'[ffmpeg] Merging formats into' in l:
                finalName = l.split(b'"')[-2].strip()
                seenFiles.add(finalName)
                self.globalStatusCallback('Download complete {}'.format(finalName),1.0)
                print('Done',finalName)
              if b'[download]' in l and b' has already been downloaded and merged' in l:
                finalName = l.replace(b' has already been downloaded and merged',b'').replace(b'[download] ',b'').strip()
                seenFiles.add(finalName)
                self.globalStatusCallback('Download already complete {}'.format(finalName),1.0)

              if b'[download]' in l and b'%' in l:
                try:
                  pc = b'0'
                  for tc in l.split(b' '):
                    if b'%' in tc:
                      pc = tc.replace(b'%',b'')
                  desc = l.replace(b'[download]',b'').strip().decode('utf8',errors='ignore')
                  self.globalStatusCallback('Downloading {} {}'.format(url,desc),float(pc)/100)

                  print(finalName,int(float(pc)) == 100)
                  if int(float(pc)) == 100 and len(finalName)>0:
                    self.globalStatusCallback('Download complete {}'.format(finalName),1.0)
                except Exception as e:
                  print(e)
                  traceback.print_exc()

              if finalName is not None:
                for seenfilename in seenFiles:
                  if seenfilename not in emittedFiles and len(seenfilename)>0 and seenfilename != finalName:
                    emitName = seenfilename.decode('utf8')
                    callback(emitName)
                    emittedFiles.add(seenfilename)
              l=b''
          if len(seenFiles)>0:
            for seenfilename in seenFiles:
              if seenfilename not in emittedFiles and len(seenfilename)>0:
                emitName = seenfilename.decode('utf8')
                callback(emitName)
                emittedFiles.add(seenfilename)
          else:
            self.globalStatusCallback('Download failed {}'.format(url),1.0)
        except Exception as e:
          print(e)
          traceback.print_exc()
          self.globalStatusCallback('Download failed {}'.format(url),1.0)


    
    self.downloadWorkerThread = threading.Thread(target=downloadFunc,daemon=True)
    self.downloadWorkerThread.start()


  def loadUrl(self,url,callback):
    self.downloadRequestQueue.put((url,callback))

  def update(self):
    self.downloadRequestQueue.put(('UPDATE',None))



if __name__ == '__main__':
  import webmGenerator
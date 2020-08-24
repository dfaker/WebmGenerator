
import subprocess as sp
import os
import threading
from queue import Queue

class YTDLService():

  def __init__(self,globalStatusCallback=print()):
    self.globalStatusCallback = globalStatusCallback
    self.downloadRequestQueue = Queue()

    def downloadFunc():
      while 1:
        url,callback = self.downloadRequestQueue.get()
        tempPathname='tempVideoFiles'
        os.path.exists(tempPathname) or os.mkdir(tempPathname)
        outfolder = os.path.join(tempPathname,'%(title)s.%(ext)s')
        proc = sp.Popen(['youtube-dl',url,'-o',outfolder,'--merge-output-format','mp4'],stdout=sp.PIPE)
        l = b''
        self.globalStatusCallback('Downloading {}'.format(url),0)
        finalName = b''
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
              print(finalName)
            if b'[ffmpeg] Merging formats into' in l:
              finalName = l.split(b'"')[-2].strip()
              self.globalStatusCallback('Download complete {}'.format(finalName),1.0)
              callback(finalName)
              print('Done',finalName)
            if b'[download]' in l and b'%' in l:
              pc = b'0'
              for tc in l.split(b' '):
                if b'%' in tc:
                  pc = tc.replace(b'%',b'')
              self.globalStatusCallback('Downloading {}'.format(url),float(pc)/100)

              print(finalName,int(float(pc)) == 100)
              if int(float(pc)) == 100 and len(finalName)>0:
                self.globalStatusCallback('Download complete {}'.format(finalName),1.0)
                callback(finalName)

            l=b''

    
    self.downloadWorkerThread = threading.Thread(target=downloadFunc,daemon=True)
    self.downloadWorkerThread.start()


  def loadUrl(self,url,callback):
    self.downloadRequestQueue.put((url,callback))


if __name__ == '__main__':
  import webmGenerator

from itertools import groupby
from datetime import datetime

def trimSRTfile(infilename,outfilename,sliceStart,sliceEnd):

  n=0
  tszero = datetime.strptime('00:00:00,000', '%H:%M:%S,%f')

  with open(outfilename,'w') as outfile:
    for key,grp in groupby(open(infilename,'r').readlines(),key=lambda x:x.strip()!=''):
      if key:
        lstgrp = list(grp) 
        print(lstgrp)
        number,timestamp,*lines = lstgrp 
        tsstart,tsend =  timestamp.split(' --> ')
        
        tsstart = tsstart.strip()
        tsend = tsend.strip()

        tsstart = datetime.strptime(tsstart, '%H:%M:%S,%f')
        tsend   = datetime.strptime(tsend, '%H:%M:%S,%f')


        tsstart = (tsstart-tszero).total_seconds()
        tsend   = (tsend-tszero).total_seconds()

        if not (tsend<sliceStart or tsstart>sliceEnd):
          n+=1
          tsstart = max(tsstart,sliceStart)-sliceStart
          tsend   = min(tsend,sliceEnd)-sliceStart

          tsstart_str = datetime.strftime(datetime.utcfromtimestamp(tsstart),'%H:%M:%S,%f')          
          startP1,startP2 = tsstart_str.split(',')
          tsstart_str = startP1 + ',' + str(int(int(startP2)/1000))

          tsend_str   = datetime.strftime(datetime.utcfromtimestamp(tsend),'%H:%M:%S,%f')
          startP2,endP2 = tsstart_str.split(',')
          tsend_str = startP2 + ',' + str(int(int(endP2)/1000))

          timeString = "{}\n{} --> {}\n{}\n".format(n,
            tsstart_str,
            tsend_str,
            '\n'.join(lines)
          )

          outfile.write(timeString)

        

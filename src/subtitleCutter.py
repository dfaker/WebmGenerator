
from itertools import groupby
from datetime import datetime

def trimSRTfile(infilename,outfilename,sliceStart,sliceEnd):

  n=0
  tszero = datetime.strptime('00:00:00,000', '%H:%M:%S,%f')

  with open(outfilename,'w') as outfile:
    for key,grp in groupby(open(infilename,'r').readlines(),key=lambda x:x.strip()!=''):
      if key:
        
        number,timestamp,*lines = list(grp) 
        tsstart,tsend =  timestamp.split(' --> ')
        tsstart = datetime.strptime(tsstart, '%H:%M:%S,%f')
        tsend   = datetime.strptime(tsend, '%H:%M:%S,%f')
        tsstart = (tsstart-tszero).total_seconds()
        tsend   = (tsend-tszero).total_seconds()

        if not (tsend<sliceStart or tsstart>sliceEnd):
          n+=1
          tsstart = max(tsstart,sliceStart)-sliceStart
          tsend   = min(tsend,sliceEnd)-sliceStart

          timeString = "{}\n{} --> {}\n{}\n".format(n,
            datetime.strftime(datetime.utcfromtimestamp(tsstart),'%H:%M:%S,%f'),
            datetime.strftime(datetime.utcfromtimestamp(tsend),'%H:%M:%S,%f'),
            '\n'.join(lines)
          )

          outfile.write(timeString)

        

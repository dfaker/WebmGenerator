
import logging
import mimetypes
import os

def _isVideoFile(filename):
  g = mimetypes.guess_type(filename)
  return g is not None and g[0] is not None and 'video' in g[0]

def gatherArgs(arglist):
  print(arglist)
  
  filters = set()
  files   = []

  for arg in arglist:
    if os.path.isfile(arg):
      if _isVideoFile(arg):
        files.append((None,arg))
    elif os.path.isdir(arg):
      for r,dl,fl in os.walk(arg):
        for f in fl:
          p = os.path.join(r,f)
          if _isVideoFile(p):
            if len(filters)==0:
              files.append((None,p))
            else:
              for f in filters:
                if f.upper() in p.upper():
                  files.append((f,p))
                  break
    else:
      filters.add(arg.upper())

  return files

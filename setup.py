from cx_Freeze import setup, Executable
import os

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))

os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

# Dependencies are automatically detected, but it might need
# fine tuning.

buildVersion = None

for line in open(os.path.join('src','webmGeneratorUi.py') ).readlines():
  if 'RELEASE_NUMVER = ' in line:
     buildVersion = line.split("'")[1]
if buildVersion is not None and 'v' in buildVersion:
  print('buildVersion=',buildVersion)
else:
  print('buildVersion invalid=',buildVersion)

buildOptions = dict(packages = ["os"], 
                    include_files = [
                     ('resources\\QRCode.gif','resources\\QRCode.gif')
                    ,('resources\\quicksand.otf','resources\\quicksand.otf')
                    ,('resources\\playerbg.png','resources\\playerbg.png')
                      
                    ,('filterTemplates\\4 Second Header Text.json','filterTemplates\\4 Second Header Text.json')
                      
                    ,('resources\\RankImages\\Rank-0-cell.png','resources\\RankImages\\Rank-0-cell.png')
                    ,('resources\\RankImages\\Rank-A.png','resources\\RankImages\\Rank-A.png')
                    ,('resources\\RankImages\\Rank-B.png','resources\\RankImages\\Rank-B.png')
                    ,('resources\\RankImages\\Rank-C.png','resources\\RankImages\\Rank-C.png')
                    ,('resources\\RankImages\\Rank-D.png','resources\\RankImages\\Rank-D.png')
                    ,('resources\\RankImages\\Rank-E.png','resources\\RankImages\\Rank-E.png')
                    ,('resources\\RankImages\\Rank-F.png','resources\\RankImages\\Rank-F.png')
                      
                    ,('resources\\cutPreview.png','resources\\cutPreview.png')
                    ,('resources\\loadingPreview.png','resources\\loadingPreview.png')
                     
                    ,('resources\\cascade\\','resources\\cascade\\')
                    ,('resources\\speechModel\\','resources\\speechModel\\')
                    ,('resources\\voiceModel\\','resources\\voiceModel\\')
                      
                    ,('postFilters\\','postFilters\\')
                    
                    ,('customEncodeprofiles\\','customEncodeprofiles\\')
                    
                    ,('src\\screenspacetools.lua','src\\screenspacetools.lua')
                    ,('src\\vrscript.lua','src\\vrscript.lua')
                      
                      
                    ,('src\\filterSpecs.json','src\\filterSpecs.json')
                    
                    ,'yt-dlp.exe'
                    ,'ffmpeg.exe'
                    ,'ffprobe.exe'  
                    ,'mpv-1.dll'
                    ,os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll')
                    ,os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll')  
                    ],
                    includes= ["tkinter","email","http","tkinter.ttk"],
                    excludes = [
                    'PIL',  
                    'distutils',  
                    'future', 
                    'pydoc_data',
                    'setuptools', 
                    'test', 
                    'tests', 
                    'test', 
                    "colorama",
                    "curses",
                    "email",
                    "jinja2",
                    "markupsafe",
                    "scipy",
                    "numba",
                    "numpy.core._dotblas",
                    "PIL",
                    "pycparser",
                    "PyQt4.QtNetwork",
                    "PyQt4.QtScript",
                    "PyQt4.QtSql",
                    "PyQt5",
                    "pytz",
                    "scipy.lib.lapack.flapack",
                    "sqlite3",
                    "test",
                    'dbm',
                    'http',
                    'llvmlite',
                    'matplotlib',
                    'sklearn',
                    'multiprocessing',
                    'test',
                    'unittest',
                    'xmlrpc',
                    ])


base = "console"

executables = [
Executable('webmGenerator.py', base=base, icon = 'resources\\icon.ico')
]

setup(name='WebmGenerator',
      version = '1.1',
      description = 'UI and Automation to generate high quality VP8 webms',
      options = dict(build_exe = buildOptions),
      executables = executables)

# The Uppercase name is detected first in a failed Queue import and
# doesn't get lowercased again (possibly only with case insensitive paths)
# this renames Tkinter->tkinter.
import os
import glob
for tkinterfolder in glob.glob(os.path.join('build','*','lib','Tkinter')):
  os.rename(tkinterfolder,tkinterfolder.replace('Tkinter','tkinter'))


for existingArch in glob.glob(os.path.join('build','*','*.zip')):
  os.remove(existingArch)

for buildPath in glob.glob(os.path.join('build','*')):
  os.chdir(buildPath)
  finalZipLocation = os.path.join('.','WebmGenerator-win64-{}.zip'.format(buildVersion))
  print(finalZipLocation)
  print(buildPath)
  z7cmd = '"C:\\Program Files\\7-Zip\\7z" a -mm=Deflate -mfb=258 -mpass=15 -r {} {}'.format(finalZipLocation,'.')
  print(z7cmd)
  os.system(z7cmd)
  break

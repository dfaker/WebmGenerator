from cx_Freeze import setup, Executable
import os

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))

os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')


# Dependencies are automatically detected, but it might need
# fine tuning.


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
                      
                    ,('postFilters\\PostFilter-addQRCode.txt','postFilters\\PostFilter-addQRCode.txt')
                    ,('postFilters\\PostFilter-chromaShift.txt','postFilters\\PostFilter-chromaShift.txt')
                    ,('postFilters\\PostFilter-rainbow.txt','postFilters\\PostFilter-rainbow.txt')
                    ,('postFilters\\PostFilter-vhsishclean.txt','postFilters\\PostFilter-vhsishclean.txt')
                    
                    ,('customEncodeprofiles\\4Chan 4Meg Webm with no Sound.json','customEncodeprofiles\\4Chan 4Meg Webm with no Sound.json')
                    ,('customEncodeprofiles\\4Chan 4Meg Webm with sound.json','customEncodeprofiles\\4Chan 4Meg Webm with sound.json')
                    ,('customEncodeprofiles\\Discord 8M limit mp4.json','customEncodeprofiles\\Discord 8M limit mp4.json')
                    
                    ,('src\\screenspacetools.lua','src\\screenspacetools.lua')
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

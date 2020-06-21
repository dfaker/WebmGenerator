from cx_Freeze import setup, Executable
import os

os.environ['TCL_LIBRARY'] = os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\Python\Python37\tcl\tcl8.6')
os.environ['TK_LIBRARY'] =  os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\Python\Python37\tcl\tk8.6')

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = ["os"], 
                    include_files = [
                    'ffmpeg.exe'
                    ,'screenspacetools.lua'
                    ,'mpv-1.dll'
                    ,os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\Python\Python37\DLLs\tcl86t.dll')
                    ,os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\Python\Python37\DLLs\tk86t.dll')
                    ],
                    includes= ["tkinter","tkinter.ttk"],
                    excludes = [
                    'PIL',
                    'distutils', 
                    'email', 
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
Executable('webmGenerator.py', base=base)
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
for tkinterfolder in os.path.join('build','*','lib','Tkinter'):
  os.rename(tkinterfolder,tkinterfolder.replace('Tkinter','tkinter'))
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], 
                    include_files = [
                    'ffmpeg.exe'
                    ,'footer.png'
                    ,('2logo.png','logo.png')
                    ,'colortheme.txt'
                    ,'easycrop.lua'
                    ,'mpv-1.dll'
                    ],
                    excludes = [
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
                    "tkinter.tzdata",
                    'dbm',
                    'http',
                    'llvmlite',
                    'matplotlib',
                    'multiprocessing',
                    'tcl',
                    'test',
                    'tk',
                    'unittest',
                    'xml',
                    'xmlrpc',
                    ])

base = 'Console'

executables = [
Executable('webmGenerator.py', base=base)
]

setup(name='WebmGenerator',
      version = '1.1',
      description = 'UI and Automation to generate high quality VP8 webms',
      options = dict(build_exe = buildOptions),
      executables = executables)

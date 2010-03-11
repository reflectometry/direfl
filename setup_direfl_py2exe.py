#!/usr/bin/env python

"""
Create direfl.exe using py2exe where the output is in the \dist directory tree.
This is a self contained Win32 distribution of the DiRefl application built
from the Reflectometry repository.
"""

import os
import sys
import glob
from distutils.core import setup

import matplotlib
import py2exe
import reflectometry

if len(sys.argv) == 1:
    sys.argv.append('py2exe')

# Retrieve version information.
local_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, local_path)
from version import version as version

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the version info resources
        self.version = version
        self.company_name = "University of Maryland"
        self.copyright = "BSD style copyright"
        self.name = "DIREFL"

data_files = []
# Add matplotlib data files from the mpl-data folder and its subfolders.
# The compiled program will look for these files in the \mpl-data ...
# Note that the location of these data files varies dependnig on the version of
# MatPlotLib that is being used.
# Note that glob will not find files without an extension such as matplotlibrc.
#
# The technique for obtaining MatPlotLib auxliliary files was adapted from the
# examples and discussion on http://www.py2exe.org/index.cgi/MatPlotLib.
matplotlibdatadir = matplotlib.get_data_path()
mplData = ('mpl-data', glob.glob(os.path.join(matplotlibdatadir,'*.*')))
data_files.append(mplData)
mplData = ('mpl-data', [os.path.join(matplotlibdatadir,'matplotlibrc')])
data_files.append(mplData)
mplData = (r'mpl-data\images',glob.glob(os.path.join(matplotlibdatadir,r'images\*.*')))
data_files.append(mplData)
mplData = (r'mpl-data\fonts\afm',glob.glob(os.path.join(matplotlibdatadir,r'fonts\afm\*.*')))
data_files.append(mplData)
mplData = (r'mpl-data\fonts\pdfcorefonts',glob.glob(os.path.join(matplotlibdatadir,r'fonts\pdfcorefonts\*.*')))
data_files.append(mplData)
mplData = (r'mpl-data\fonts\ttf',glob.glob(os.path.join(matplotlibdatadir,r'fonts\ttf\*.*')))
data_files.append(mplData)

'''
# Add images for the toolbar.
images = []
imageDir = os.path.join('.', 'images')
for fname in os.listdir(imageDir):
    fullFname = os.path.join(imageDir, fname)
    if os.path.isfile(fullFname):
        images.append(fullFname)
imagesData = ('images', images)
data_files.append(imagesData)
'''

# Add data files that need to reside in the same directory as the image.
data_files.append( ('.', [os.path.join('.','demo_model_1.dat')]) )
data_files.append( ('.', [os.path.join('.','demo_model_2.dat')]) )
data_files.append( ('.', [os.path.join('.','direfl.ico')]) )
data_files.append( ('.', [os.path.join('.','LICENSE-direfl.txt')]) )
data_files.append( ('.', [os.path.join('.','qrd1.refl')]) )
data_files.append( ('.', [os.path.join('.','qrd2.refl')]) )
data_files.append( ('.', [os.path.join('.','surround_air_4.refl')]) )
data_files.append( ('.', [os.path.join('.','surround_d2o_4.refl')]) )
data_files.append( ('.', [os.path.join('.','README-direfl.txt')]) )
data_files.append( ('.', [os.path.join('.','splash.png')]) )

# Add required packages.
packages = ['numpy', 'scipy', 'matplotlib', 'pytz']

# Specify include and exclude files.
includes = []

excludes = ['Tkinter', 'PyQt4']

dll_excludes = ['MSVCR71.dll',
                'w9xpopen.exe',
                'libgdk_pixbuf-2.0-0.dll',
                'libgobject-2.0-0.dll',
                'libgdk-win32-2.0-0.dll',
                'cygwin1.dll',
                'tcl84.dll',
                'tk84.dll',
                'QtGui4.dll',
                'QtCore4.dll']

# This will create a console window on starup in which the DiRefl application
# is run that will create a separate GUI application window.
target_console_direfl = Target(
      description = 'DiRefl: Direct Inversion and Phase Reconstruction',
      script = './direfl.py',
      dest_base = "direfl"
      )

# Now do the work to create a standalone distribution using py2exe.
setup(console=[target_console_direfl],
      options={'py2exe': {
                    'dll_excludes': dll_excludes,
                    'packages': packages,
                    'includes': includes,
                    'excludes': excludes,
                    'compressed': 1,
                    'optimize': 0,
                    'bundle_files': 1} # bundle python25.dll in executable file
              },
      zipfile=None,                    # bundle library.zip in executable file
      data_files=data_files
     )

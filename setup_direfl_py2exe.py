#!/usr/bin/env python

# Copyright (C) 2006-2010, University of Maryland
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/ or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Author: James Krycka

"""
Create direfl.exe in the inversion\dist directory tree using py2exe.  This
executable contains the python runtime environment, required python packages,
and the DiRefl application.  Additional resource files needed to run DiRefl are
placed in the dist directory tree.  On completion, the contents of the dist
directory tree can be used by the Inno Setup Compiler to build a Windows
installer/uninstaller for the DiRefl application.
"""

import os
import sys
import glob

from distutils.core import setup
import py2exe  # augment setup interface with the py2exe command

if len(sys.argv) == 1:
    sys.argv.append('py2exe')

import matplotlib

'''
print "*** Python path is:"
for i, p in enumerate(sys.path):
    print "%5d  %s" %(i, p)
'''

# Retrieve version information.
from version import version as version

# Create a manifest for use with Python 2.5 on Windows XP.  This manifest is
# required to be included in a py2exe image (or accessible as a file in the
# image directory) when wxPython is included so that the Windows XP theme is
# used when rendering wx widgets.  The manifest below is adapted from the
# Python manifest file (C:\Python25\pythonw.exe.manifest).

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>DiRefl</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""

class Target():
    def __init__(self, **kw):
        # Metadata about the distribution
        self.__dict__.update(kw)
        self.version = version
        self.company_name = "University of Maryland"
        self.copyright = "BSD style copyright"
        self.name = "DiRefl"

# Create a list of all files to include with the executable being built in the
# dist directory tree.
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
mplData = (r'mpl-data\images',
           glob.glob(os.path.join(matplotlibdatadir,r'images\*.*')))
data_files.append(mplData)
mplData = (r'mpl-data\fonts\afm',
           glob.glob(os.path.join(matplotlibdatadir,r'fonts\afm\*.*')))
data_files.append(mplData)
mplData = (r'mpl-data\fonts\pdfcorefonts',
           glob.glob(os.path.join(matplotlibdatadir,r'fonts\pdfcorefonts\*.*')))
data_files.append(mplData)
mplData = (r'mpl-data\fonts\ttf',
           glob.glob(os.path.join(matplotlibdatadir,r'fonts\ttf\*.*')))
data_files.append(mplData)

# Add data files that need to reside in the same directory as the image.
data_files.append( ('.', [os.path.join('.','demo_model_1.dat')]) )
data_files.append( ('.', [os.path.join('.','demo_model_2.dat')]) )
data_files.append( ('.', [os.path.join('.','demo_model_3.dat')]) )
data_files.append( ('.', [os.path.join('.','direfl.ico')]) )
data_files.append( ('.', [os.path.join('.','LICENSE-direfl.txt')]) )
data_files.append( ('.', [os.path.join('.','qrd1.refl')]) )
data_files.append( ('.', [os.path.join('.','qrd2.refl')]) )
data_files.append( ('.', [os.path.join('.','surround_air_4.refl')]) )
data_files.append( ('.', [os.path.join('.','surround_d2o_4.refl')]) )
data_files.append( ('.', [os.path.join('.','README-direfl.txt')]) )
data_files.append( ('.', [os.path.join('.','splash.png')]) )

# Specify required packages.
packages = ['numpy', 'scipy', 'matplotlib', 'pytz']

# Specify files to include and exclude.
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

# This will create a console window when the DiRefl application is run.  The
# application will then create a separate GUI application window.
target_console_client = Target(
    description = 'DiRefl: Direct Inversion and Phase Reconstruction',
    script = './direfl.py',
    dest_base = "direfl",
    other_resources = [(24, 1, manifest)])

# Now do the work to create a standalone distribution using py2exe.
setup(windows=[],
      console=[target_console_client],
      options={'py2exe': {
                          'dll_excludes': dll_excludes,
                          'packages': packages,
                          'includes': includes,
                          'excludes': excludes,
                          'compressed': 1,
                          'optimize': 0,
                          'bundle_files': 1 # bundle python25.dll in executable
                         }
              },
      zipfile=None,                         # bundle library.zip in executable
      data_files=data_files
     )

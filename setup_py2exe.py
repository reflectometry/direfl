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
This script uses py2exe to create inversion\dist\direfl.exe for Windows.

The resulting executable bundles the DiRefl application, the python runtime
environment, and other required python packages into a single file.  Additional
resource files that are needed when DiRefl is run are placed in the dist
directory tree.  On completion, the contents of the dist directory tree can be
used by the Inno Setup Compiler (via a separate script) to build a Windows
installer/uninstaller for deployment of the DiRefl application.  For testing
purposes, direfl.exe can be run from the dist directory.
"""

import os
import sys

'''
print "*** Python path is:"
for i, p in enumerate(sys.path):
    print "%5d  %s" %(i, p)
'''

from distutils.core import setup

# Augment the setup interface with the py2exe command and make sure the py2exe
# option is passed to setup.
import py2exe

if len(sys.argv) == 1:
    sys.argv.append('py2exe')

import matplotlib

# Retrieve the application version string.
from version import version

# A manifest is required to be included in a py2exe image (or accessible as a
# file in the image directory) when wxPython is included so that the Windows XP
# theme is used when rendering wx widgets.  The manifest must be matched to the
# version of Python that is being used.
#
# Create a manifest for use with Python 2.5 on Windows XP or Vista.  It is
# adapted from the Python manifest file (C:\Python25\pythonw.exe.manifest).

manifest_for_python25 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s</description>
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

# Create a manifest for use with Python 2.6 or 2.7 on Windows XP or Vista.

manifest_for_python26 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32">
  </assemblyIdentity>
  <description>%(prog)s</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
          level="asInvoker"
          uiAccess="false">
        </requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.VC90.CRT"
        version="9.0.21022.8"
        processorArchitecture="x86"
        publicKeyToken="1fc8b3b9a1e18e3b">
      </assemblyIdentity>
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="x86"
        publicKeyToken="6595b64144ccf1df"
        language="*">
      </assemblyIdentity>
    </dependentAssembly>
  </dependency>
</assembly>
"""

# Select the appropriate manifest to use.
if sys.version_info >= (3, 0) or sys.version_info < (2, 5):
    print "*** This script only works with Python 2.5, 2.6, or 2.7."
    sys.exit()
elif sys.version_info >= (2, 6):
    manifest = manifest_for_python26
elif sys.version_info >= (2, 5):
    manifest = manifest_for_python25

# Create a list of all files to include along side the executable being built
# in the dist directory tree.  Each element of the data_files list is a tuple
# consisting of a path (relative to dist\) and a list of files in that path.
data_files = []

# Add data files from the matplotlib\mpl-data folder and its subfolders.
# For matploblib prior to version 0.99 see the examples at the end of the file.
data_files = matplotlib.get_py2exe_datafiles()

# Add resource files that need to reside in the same directory as the image.
data_files.append( ('.', [os.path.join('.', 'direfl.ico')]) )
data_files.append( ('.', [os.path.join('.', 'direfl_splash.png')]) )
data_files.append( ('.', [os.path.join('.', 'LICENSE.txt')]) )
data_files.append( ('.', [os.path.join('.', 'README.txt')]) )
data_files.append( ('examples', [os.path.join('examples', 'demo_model_1.dat')]) )
data_files.append( ('examples', [os.path.join('examples', 'demo_model_2.dat')]) )
data_files.append( ('examples', [os.path.join('examples', 'demo_model_3.dat')]) )
data_files.append( ('examples', [os.path.join('examples', 'qrd1.refl')]) )
data_files.append( ('examples', [os.path.join('examples', 'qrd2.refl')]) )
data_files.append( ('examples', [os.path.join('examples', 'surround_air_4.refl')]) )
data_files.append( ('examples', [os.path.join('examples', 'surround_d2o_4.refl')]) )

# Add the Microsoft Visual C++ 2008 redistributable kit if we are building with
# Python 2.6 or 2.7.  This kit will be installed on the target system as part
# of the installation process for the frozen image.  Note that the Python 2.5
# interpreter requires msvcr71.dll which is included in the Python25 package,
# however, Python 2.6 and 2.7 require the msvcr90.dll but they do not bundle it
# with the Python26 or Python27 package.  Thus, for Python 2.6 and later, the
# appropriate dll must be present on the target system at runtime.
if sys.version_info >= (2, 6):
    pypath = os.path.dirname(sys.executable)
    data_files.append( ('.', [os.path.join(pypath, 'vcredist_x86.exe')]) )

# Specify required packages to bundle in the executable image.
packages = ['matplotlib', 'numpy', 'scipy', 'pytz']

# Specify files to include in the executable image.
includes = []

# Specify files to exclude from the executable image.
# - We can safely exclude Tk/Tcl and Qt modules because our app uses wxPython.
# - We do not use ssl services so they are omitted.
# - We can safely exclude the TkAgg matplotlib backend because our app uses
#   "matplotlib.use('WXAgg')" to override the default matplotlib configuration.
# - On the web it is widely recommended to exclude certain lib*.dll modules
#   but this does not seem necessary any more (but adding them does not hurt).
# - Python25 requires mscvr71.dll, however, Win XP includes this file.
# - Since we do not support Win 9x systems, w9xpopen.dll is not needed.
# - For some reason cygwin1.dll gets included by default, but it is not needed.

excludes = ['Tkinter', 'PyQt4', '_ssl', '_tkagg']

dll_excludes = ['libgdk_pixbuf-2.0-0.dll',
                'libgobject-2.0-0.dll',
                'libgdk-win32-2.0-0.dll',
                'tcl84.dll',
                'tk84.dll',
                'QtGui4.dll',
                'QtCore4.dll',
                'msvcr71.dll',
                'msvcp90.dll',
                'w9xpopen.exe',
                'cygwin1.dll']

class Target():
    """This class stores metadata about the distribution in a dictionary."""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.version = version

client = Target(
    name = 'DiRefl',
    description = 'Direct Inversion Reflectometry (DiRefl) application',
    script = 'bin/direfl.py',  # module to run on application start
    dest_base = 'direfl',  # file name part of the exe file to create
    icon_resources = [(1, 'direfl.ico')],  # also need to specify in data_files
    bitmap_resources = [],
    other_resources = [(24, 1, manifest % dict(prog='DiRefl'))] )

# Now we do the work to create a standalone distribution using py2exe.
#
# When the application is run in console mode, a console window will be created
# to receive any logging or error messages and the application will then create
# a separate GUI application window.
#
# When the application is run in windows mode, it will create a GUI application
# window and no console window will be provided.  Output to stderr will be
# written to <app-image-name>.log.
setup(
      #console=[client],
      windows=[client],
      options={'py2exe': {
                   'packages': packages,
                   'includes': includes,
                   'excludes': excludes,
                   'dll_excludes': dll_excludes,
                   'compressed': 1,   # standard compression
                   'optimize': 0,     # no byte-code optimization
                   'dist_dir': "dist",# where to put py2exe results
                   'xref': False,     # display cross reference (as html doc)
                   'bundle_files': 1  # bundle python25.dll in library.zip
                         }
              },
      #zipfile=None,                  # None means bundle library.zip in exe
      data_files=data_files           # list of files to copy to dist directory
     )

#==============================================================================
# This section is for reference only when using older versions of matplotlib.

# The location of mpl-data files has changed across releases of matplotlib.
# Furthermore, matplotlib.get_py2exe_datafiles() had problems prior to version
# 0.99 (see link below for details), so alternative ways had to be used.
# The various techniques shown below for obtaining matplotlib auxiliary files
# (and previously used by this project) was adapted from the examples and
# discussion on http://www.py2exe.org/index.cgi/MatPlotLib.
#
# The following technique worked for matplotlib 0.91.2.
# Note that glob '*.*' will not find files that have no file extension.
'''
import glob

data_files = []
matplotlibdatadir = matplotlib.get_data_path()
mpl_lst = ('mpl-data', glob.glob(os.path.join(matplotlibdatadir, '*.*')))
data_files.append(mpl_lst)
mpl_lst = ('mpl-data', [os.path.join(matplotlibdatadir, 'matplotlibrc')])
data_files.append(mpl_lst)  # pickup file missed by glob
mpl_lst = (r'mpl-data\fonts',
           glob.glob(os.path.join(matplotlibdatadir, r'fonts\*.*')))
data_files.append(mpl_lst)
mpl_lst = (r'mpl-data\images',
           glob.glob(os.path.join(matplotlibdatadir, r'images\*.*')))
data_files.append(mpl_lst)
'''

# The following technique worked for matplotlib 0.98.5.
# Note that glob '*.*' will not find files that have no file extension.
'''
import glob

data_files = []
matplotlibdatadir = matplotlib.get_data_path()
mpl_lst = ('mpl-data', glob.glob(os.path.join(matplotlibdatadir, '*.*')))
data_files.append(mpl_lst)
mpl_lst = ('mpl-data', [os.path.join(matplotlibdatadir, 'matplotlibrc')])
data_files.append(mpl_lst)  # pickup file missed by glob
mpl_lst = (r'mpl-data\fonts\afm',
           glob.glob(os.path.join(matplotlibdatadir, r'fonts\afm\*.*')))
data_files.append(mpl_lst)
mpl_lst = (r'mpl-data\fonts\pdfcorefonts',
           glob.glob(os.path.join(matplotlibdatadir, r'fonts\pdfcorefonts\*.*')))
data_files.append(mpl_lst)
mpl_lst = (r'mpl-data\fonts\ttf',
           glob.glob(os.path.join(matplotlibdatadir, r'fonts\ttf\*.*')))
data_files.append(mpl_lst)
mpl_lst = (r'mpl-data\images',
           glob.glob(os.path.join(matplotlibdatadir, r'images\*.*')))
data_files.append(mpl_lst)
'''

# The following technique worked for matplotlib 0.98 and 0.99.
'''
from distutils.filelist import findall

data_files = []
matplotlibdatadir = matplotlib.get_data_path()
matplotlibdata = findall(matplotlibdatadir)

for f in matplotlibdata:
    dirname = os.path.join('mpl-data', f[len(matplotlibdatadir)+1:])
    data_files.append((os.path.split(dirname)[0], [f]))
'''

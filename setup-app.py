# This program is in the public domain.

from distutils.core import setup
import py2app

## \file
#  \brief Setup file for constructing OS X applications.  Run using:
#
#   % python setup-app.py py2app
   
#Should be combined with setup.py which understands py2exe so that
#it is easier to keep names and versions consistent.
#

from distutils.core import setup
import py2app

NAME = 'Invert'
SCRIPT = 'invert.py'
VERSION = '0.0.1'
ICON = '' #'ks.icns'
ID = 'Invert'
COPYRIGHT = 'This program is public domain'
DATA_FILES = []

plist = dict(
    CFBundleIconFile            = ICON,
    CFBundleName                = NAME,
    CFBundleShortVersionString  = ' '.join([NAME, VERSION]),
    CFBundleGetInfoString       = NAME,
    CFBundleExecutable          = NAME,
    CFBundleIdentifier          = 'gov.nist.ncnr.%s' % ID,
    NSHumanReadableCopyright    = COPYRIGHT
)


EXCLUDES=[]
#EXCLUDES=['matplotlib','pylab']
app_data = dict(script=SCRIPT, plist=plist)
py2app_opt = dict(excludes=[], optimize=2)
options = dict(py2app=py2app_opt,)

setup(
  data_files = DATA_FILES,
  app = [app_data],
  options = options,
)

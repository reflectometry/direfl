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

# Authors: Nikunj Patel and James Krycka

"""
This script builds the DiRefl application and documentation from source and runs
unit tests and doc tests.
"""

import os
import sys
import zipfile
import shutil
import subprocess

# Windows commands to run utilities
SVN    = "svn"
PYTHON = "python"
INNO   = r'"C:\Program Files\Inno Setup 5\ISCC"'  # command line Inno compiler

# URL of the Subversion repository where the source code lives
SVN_REPO_URL = "svn://svn@danse.us/reflectometry/trunk/reflectometry/inversion"
# Name of the package
PKG_NAME = "inversion"
# Local installation root directory (in place of C:\PythonNN\Lib\site-packages
LOCAL_INSTALL = "local-site-packages"
# Name of the application we're building
APP_NAME = "direfl"

# Normally this script is downloaded into a top-level directory.  When run it
# downloads the files from the application repository into a subdirectory.  For
# example if test1 is the top-level directory, we might have:
#   E:/work/test1/this-script.py
#                /inversion/this-script.py
#                /inversion/...
#
# Alternatively, the repository can be downloaded by the user and this script
# can be run from the application subdirectory:
#   E:/work/test1/inversion/this-script.py
#                /inversion/...
#
# In this case, the top-level directory is defined as one-level-up and the
# repository is not downloaded (as it is assumed to be fully present).
#
# Determine the full directory paths of the top-level, source, and installation
# directories based on the directory where the script is running.
RUN_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
head, tail = os.path.split(RUN_DIR)
if tail == PKG_NAME:
    TOP_DIR = head
else:
    TOP_DIR = RUN_DIR
SRC_DIR = os.path.join(TOP_DIR, PKG_NAME)
INS_DIR = os.path.join(TOP_DIR, LOCAL_INSTALL)
print "RUN_DIR =", RUN_DIR
print "TOP_DIR =", TOP_DIR
print "SRC_DIR =", SRC_DIR
print "INS_DIR =", INS_DIR

def checkout():
    # Check the system for all required dependent packages.
    check_packages()

    #--------------------------------------------------------------------------

    # Checkout the application code from the repository into a directory tree
    # under the top level directory.
    print "\nStep 1 - Checking out application code from the repository ...\n"
    os.chdir(TOP_DIR)

    if RUN_DIR == TOP_DIR:
        subprocess.call("%s checkout %s %s" % (SVN, SVN_REPO_URL, PKG_NAME))
    else:
        print "*** Skipping checkout of repository because the executing script"
        print "*** is within the repository, not in the top-level directory."

    #--------------------------------------------------------------------------

    # Create a zip file to archive the source code.
    print "\nStep 2 - Creating a zip archive of the application repository ...\n"
    os.chdir(SRC_DIR)

    # Get the version string for the application.
    # This has to be done after we have checked out the repository.
    if RUN_DIR == TOP_DIR:
        from inversion.version import version as version
    else:
        from version import version as version
    # Delete the .pyc files created as a result of the import.
    if os.path.isfile("__init__.pyc"):
        os.remove(os.path.join(SRC_DIR, "__init__.pyc"))
    if os.path.isfile("version.pyc"):
        os.remove(os.path.join(SRC_DIR, "version.pyc"))

    arch_dir = dir_archive(".", "True")
    zfile = os.path.join(TOP_DIR, APP_NAME+"-"+str(version)+"-source.zip")
    try:
        a = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_DEFLATED)
        for f in arch_dir:
            a.write(f)
        a.close()
    except:
        print "*** Failed to create zip file ***"
    else:
        print "Zip file created"

    #--------------------------------------------------------------------------

    # Install the application package in a private directory tree.
    # If the INS_DIR directory already exists, warn the user.
    # Intermediate work files are stored in the <SRC_DIR>/build directory tree.
    print "\nStep 3 - Installing the %s package in %s...\n" %(PKG_NAME, INS_DIR)
    os.chdir(SRC_DIR)

    if os.path.isdir(INS_DIR):
        print "\n WARNING!\n"
        print "In order to build "+APP_NAME+" cleanly, the local build directory"
        print INS_DIR+" needs to be deleted."
        print "Do you want to delete this directory and continue (Y)"
        print "            or continue with a dirty installation (N)"
        print "            or exit the build script (E)"
        answer = raw_input("Please choose either (Y|N|E)? [E]: ")
        if answer.upper() == "Y":
            # Workaround: symbolic link to Inversion.pdf may be set to read-only.
            #shutil.rmtree(INS_DIR)
            shutil.rmtree(INS_DIR, ignore_errors=True)
        elif answer.upper() == "N":
            pass
        else:
            sys.exit()

    # Perform the installation to a private directory tree and create the
    # PYTHONPATH environment variable to pass this info to the py2exe build
    # script later on.
    subprocess.call("%s setup.py -q install --install-lib=%s" %(PYTHON, INS_DIR))
    os.environ["PYTHONPATH"] = INS_DIR

    #--------------------------------------------------------------------------

    # Use py2exe to create a Win32 executable along with auxiliary files in the
    # <SRC_DIR>/dist directory tree.
    print "\nStep 4 - Using py2exe to create a Win32 executable ...\n"
    os.chdir(SRC_DIR)

    subprocess.call("%s setup_%s_py2exe.py" %(PYTHON, APP_NAME))

    #--------------------------------------------------------------------------

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller for
    # the application.
    print "\nStep 5 - Running Inno Setup Compiler to create Win32 "\
          "installer/uninstaller ...\n"
    os.chdir(SRC_DIR)

    # First create an include file to convey the application's version
    # information to the Inno Setup compiler.  If the include file exists, then
    # append the directive at the end.
    f = open("%s.iss-include" % APP_NAME, "a")
    f.write('#define MyAppVersion "%s"\n' % version)  # version must be quoted
    f.close()

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller.
    # Override the output specification in <APP_NAME>.iss to put the executable
    # and the manifest file in the top-level directory.
    subprocess.call("%s /Q /O%s %s.iss" % (INNO, TOP_DIR, APP_NAME))

    #--------------------------------------------------------------------------

    # Run the Sphinx utility to build the application's documentation.
    print "\nStep 6 - Running the Sphinx utility to build documentation ...\n"
    os.chdir(os.path.join(INS_DIR, PKG_NAME, "doc", "sphinx"))

    # Delete any left over files from a previous build.
    subprocess.call("make clean")
    # Create documentation in HTML format.
    subprocess.call("make html")
    # Create documentation in PDF format.
    subprocess.call("make pdf")
    # Copy PDF file to the top-level directory.
    os.chdir(os.path.join("_build", "latex"))
    if os.path.isfile("DirectInversion.pdf"):
        shutil.copy("DirectInversion.pdf", TOP_DIR)

    #--------------------------------------------------------------------------

    # Run Nose unittests and doctests.
    print "\nStep 7 - Running Nose unittests and doctests ...\n"
    os.chdir(INS_DIR)

    subprocess.call("nosetests -v %s" % PKG_NAME)

def check_packages():
    """
    Checks that the system has the necessary Python packages installed.
    """

    # Python appears to write directly to the console, not to stdout, so the
    # following code does not work as expected:
    # p = subprocess.Popen("%s -V" % PYTHON, stdout=subprocess.PIPE)
    # print "Using ", p.stdout.read().strip()
    print "Using ",
    subprocess.call("%s -V" % PYTHON)  # displays python name and version string

    req_pack = {}

    try:
        import matplotlib
    except:
        print "matplotlib not found"

    if not matplotlib.__version__ == "0.99.0":
        req_pack["matplotlib"]= ("0.99.0", matplotlib.__version__)

    try:
        import numpy
    except:
        print "numpy not found"

    if not numpy.__version__ == "1.2.1":
        req_pack["numpy"]= ("1.2.1", numpy.__version__)

    try:
        import scipy
    except:
        print "scipy not found"

    if not scipy.__version__ == "0.7.0":
        req_pack["scipy"]= ("0.7.0", scipy.__version__)

    try:
        import wx
    except:
        print "wx not found"

    if not wx.__version__ == "2.8.11.0":
        req_pack["wx"]= ("2.8.11.0", wx.__version__)

    try:
        import setuptools
    except:
        print "setuptools not found"

    if not setuptools.__version__ == "0.6c11":
        req_pack["setuptools"]= ("0.6c11", setuptools.__version__)

    try:
        import sphinx
    except:
        print "sphinx not found"

    if not sphinx.__version__ == "1.0":
        req_pack["sphinx"]= ("1.0", sphinx.__version__)

    try:
        p = subprocess.Popen("gcc -dumpversion", stdout=subprocess.PIPE)
        gcc_version = p.stdout.read().strip()
        if not gcc_version == "3.4.5":
            req_pack["gcc"]= ("3.4.5", gcc_version)
    except:
        print "gcc compiler not found"

    if not req_pack == {}:
        print "\n WARNING!\n"
        for key, values in req_pack.items():
            print key, ("required version is %s and your system version is %s"
                        % (req_pack[key][0], req_pack[key][1]))
        ans = raw_input("\nDo you want to continue (Y|N)? [N]: ")
        if ans.upper() != "Y":
            sys.exit()

def dir_archive(dir_name, subdir):
    """
    Return a list of file names found in directory 'dir_name'.
    If 'subdir' is True, recursively access subdirectories under 'dir_name'.
    Example usage: file_list = dir_archive(r'E:\testbuild', True)
    All files and all the files in subdirectories under E:\testbuild will be
    added to the list except for cetain subdirectories and types of file that
    are excluded.
    """

    file_list = []
    for file in os.listdir(dir_name):
        name = os.path.join(dir_name, file)
        # Exclude files with certain extensions that indicate compiled modules
        # or temporary files generated by this script.
        if os.path.isfile(name):
            base, ext = os.path.splitext(name)
            if ext not in (".pyc", ".pyo", ".pyd", ".so", ".iss-include"):
                file_list.append(name)
        # Recursively access file names in subdirectories.
        elif os.path.isdir(name) and subdir:
            # Exclude certain directories.
            if name.count('svn') > 0:
                pass
            elif name.count('build') > 0:
                pass
            elif name.count('dist') > 0:
                pass
            elif name.count(LOCAL_INSTALL) > 0:
                pass
            else:
                file_list.extend(dir_archive(name, subdir))
    return file_list

if __name__ == "__main__":
    print "Build script for "+APP_NAME
    if len(sys.argv)==1:
        # If there is no argument, build the installer
        sys.argv.append("-i")

    if len(sys.argv)>1:
        # Help
        if sys.argv[1]=="-h":
            print "Usage:"
            print "    python build_%s.py [command]\n" % APP_NAME
            print "[command] can be any of the following:"
            print "    -h: Lists the command line options"
            print "    -t: Builds application from the trunk"

        else:
            # Check the command line argument
            if sys.argv[1]=="-t":
                print("Building from reflectometry/trunk")
                checkout()
            elif sys.argv[1]=="-i":
                print("Building from reflectometry/trunk")
                checkout()


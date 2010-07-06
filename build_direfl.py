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

import os
import sys
import zipfile
import shutil

# Windows commands to run utilities
SVN    = "svn"
PYTHON = "python"
INNO   = r'"c:\Program Files\Inno Setup 5\ISCC"'

# URL for SVN repository
INVERSION_URL = "svn://svn@danse.us/reflectometry/trunk/reflectometry/inversion"


def checkout():
    # Check the system for all required dependent packages.
    check_packages()

    # Checkout the code from the repository into a directory tree named
    # <build>/inversion.
    print "\nPart 1 - Checking out code from the inversion repository ...\n"

    os.system("%s checkout -q %s" % (SVN, INVERSION_URL))

    # Get the version string for DiRefl.
    # This has to be done after we have checked out the repository.
    from inversion.version import version as version

    # Create a zip file to archive the source code.
    print "\nPart 2 - Creating a zip archive of the inversion repository ...\n"

    os.chdir("inversion")
    curr_dir = os.getcwd()
    for file in os.listdir(curr_dir):
        (shortname, extension) = os.path.splitext(file)
        if extension == ".zip":
            os.remove(shortname+extension)
    arch_dir = dir_archive(".", "True")
    a = zipfile.ZipFile("direfl-"+str(version)+"-source.zip", 'w',
                        zipfile.ZIP_DEFLATED)
    for f in arch_dir:
        a.write(f)
    a.close()

    # Install the inversion package in a private directory tree named
    # <build>/inversion/build-install.
    # If the build-install folder already exists, warn the user.
    print "\nPart 3 - Installing the inversion package in a private directory ...\n"

    if os.path.isdir("build-install"):
        print "\n WARNING!\n"
        print "In order to build a clean version of Direfl, the local"
        print "build-install directory needs to be deleted."
        print "Do you want to delete this directory and continue [Y]"
        print "            or continue with a dirty installation [N]"
        print "            or exit the build script [E]"
        answer = raw_input("Please choose either [Y|N|E]? (E): ")
        if answer.upper() == "Y":
            shutil.rmtree("build-install")
        elif answer.upper() == "N":
            pass
        else:
            sys.exit()
    os.system("%s setup.py -q install --install-lib=build-install" % PYTHON)

    # Use py2exe to create a Win32 executable along with auxiliary files in the
    # <build-dir>/inversion/dist directory tree.
    print "\nPart 4 - Using py2exe to create a Win32 executable ...\n"

    os.system("%s setup_direfl_py2exe.py" % PYTHON)

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller for
    # DiRefl.
    print "\nPart 5 - Running Inno Setup Compiler to create a Win32 installer/uninstaller ...\n"

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller.
    sts = os.system("%s /Q direfl.iss" % INNO)
    if sts == 0:
        print "Inno Setup was successful"
    else:
        print "*** Inno Setup failed ***"

    # Run the Sphinx utility to build DiRefl documentation.
    print "\nPart 6 - Running the Sphinx utility to build DiRefl documentation ...\n"

    os.chdir("doc\sphinx")
    os.system("make html")
    os.system("make pdf")

def check_packages():
    """
    Checks that the system has the necessary modules.
    """
    temp = "_temp.txt"

    print "Using ",
    os.system("%s -V > %s" % (PYTHON, temp))
    print ""

    try:
        import matplotlib
        if not matplotlib.__version__ == "0.99.0":
            req_pack["matplotlib"]= ("0.99.0", matplotlib.__version__)
    except:
        print "matplotlib missing"

    try:
        import numpy
        if not numpy.__version__ == "1.2.1":
            req_pack["numpy"]= ("1.2.1", numpy.__version__)
    except:
        print "numpy missing"

    try:
        import scipy
        if not scipy.__version__ == "0.7.0":
            req_pack["scipy"]= ("0.7.0", scipy.__version__)
    except:
        print "scipy missing"

    req_pack = {}
    try:
        import wx
        if not wx.__version__ == "2.8.11.0":
            req_pack["wx"]= ("2.8.11.0", wx.__version__)
    except:
        print "wxpython missing"

    try:
        os.system("gcc -dumpversion > %s" % temp)
        f = open(temp, "r")
        gcc_version = f.readline().strip()
        f.close()
        os.remove(temp)
        if not gcc_version == "3.4.5":
            req_pack["gcc"]= ("3.4.5", gcc_version)
    except:
        print "gcc compiler missing"

    if not req_pack == {}:
        print "\n WARNING!\n"
        for key, values in req_pack.items():
            print key, ("required version is %s actual version is %s"
                        % (req_pack[key][0], req_pack[key][1]))
        ans = raw_input("\nDo you want to continue [Y|N]? (N): ")
        if ans.upper() != "Y":
            sys.exit()

def dir_archive(dir_name, subdir):
    """
    Return a list of file names found in directory 'dir_name'.
    If 'subdir' is True, recursively access subdirectories under 'dir_name'.
    Example usage: file_list = dir_archive(r'H:\TEMP', True)
    All files and all the files in subdirectories under H:\TEMP will be added
    to the list.
    """

    file_list = []
    for file in os.listdir(dir_name):
        dirfile = os.path.join(dir_name, file)
        if os.path.isfile(dirfile):
            file_list.append(dirfile)
        # recursively access file names in subdirectories
        elif os.path.isdir(dirfile) and subdir:
            # exclude svn directories
            if dirfile.count('svn') >0:
                pass
            elif dirfile.count('build')>0:
                pass
            elif dirfile.count('build-install') >0:
                pass
            elif dirfile.count('dist') >0:
                pass
            else:
                file_list.extend(dir_archive(dirfile, subdir))
    return file_list

if __name__ == "__main__":
    print "Build script for DiRefl"
    if len(sys.argv)==1:
        # If there is no argument, build the installer
        sys.argv.append("-i")

    if len(sys.argv)>1:
        # Help
        if sys.argv[1]=="-h":
            print "Usage:"
            print "    python build_direfl.py [command]\n"
            print "[command] can be any of the following:"
            print "    -h: lists the command line options"
            print "    -t: Builds DiRefl from the trunk"

        else:
            # Check the command line argument
            if sys.argv[1]=="-t":
                print("Building from reflectometry/trunk")
                checkout()
            elif sys.argv[1]=="-i":
                print("Building from reflectometry/trunk")
                checkout()

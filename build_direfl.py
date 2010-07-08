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
import subprocess

# Windows commands to run utilities
SVN    = "svn"
PYTHON = "python"
INNO   = r'"c:\Program Files\Inno Setup 5\ISCC"'

# URL for SVN repository
INVERSION_URL = "svn://svn@danse.us/reflectometry/trunk/reflectometry/inversion"


def checkout():
    # Check the system for all required dependent packages.
    check_packages()

    # Checkout the code from the repository into a directory tree under the
    # current directory, i.e., <build>/inversion.
    print "\nPart 1 - Checking out code from the inversion repository ...\n"

    subprocess.call("%s checkout %s" % (SVN, INVERSION_URL))

    # Get the version string for DiRefl.
    # This has to be done after we have checked out the repository.
    from inversion.version import version as version

    # Create a zip file to archive the source code.
    print "\nPart 2 - Creating a zip archive of the inversion repository ...\n"

    top_dir = os.getcwd()
    os.chdir("inversion")
    curr_dir = os.getcwd()
    for file in os.listdir(curr_dir):
        (shortname, extension) = os.path.splitext(file)
        if extension == ".zip":
            os.remove(shortname+extension)
    arch_dir = dir_archive(".", "True")
    zfile = os.path.join(top_dir, "direfl-"+str(version)+"-source.zip")
    try:
        a = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_DEFLATED)
        for f in arch_dir:
            a.write(f)
        a.close()
    except:
        print "*** Failed to create zip file ***"
    else:
        print "Zip file created"

    # Install the inversion package in a private directory tree named
    # <build>/inversion/build-install.
    # If the build-install folder already exists, warn the user.
    print "\nPart 3 - Installing the inversion package in subdirectory build-install ...\n"

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

    # Perform the install to a private directory tree and create the
    # PYTHONPATH environment variable to pass this info to the py2exe build
    # script later on.
    subprocess.call("%s setup.py -q install --install-lib=build-install" % PYTHON)
    os.environ["PYTHONPATH"] = os.path.join(curr_dir, "build-install")

    # Use py2exe to create a Win32 executable along with auxiliary files in the
    # <build>/inversion/dist directory tree.
    print "\nPart 4 - Using py2exe to create a Win32 executable in subdirectory dist ...\n"

    subprocess.call("%s setup_direfl_py2exe.py" % PYTHON)

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller for
    # DiRefl.
    print "\nPart 5 - Running Inno Setup Compiler to create a Win32 installer/uninstaller ...\n"

    # First append Direfl's version information to the Inno Setup include file.
    f = open("direfl_include.iss", "a")
    f.write('#define MyAppVersion "%s"\n' % version)  # version must be quoted
    f.close()

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller.
    # Override the output specification in direfl.iss to put the executable and
    # the manifest file in the top-level directory.
    try:
        subprocess.call("%s /Q /O%s direfl.iss" % (INNO, top_dir))
    except:
        print "*** Failed to create installer executable ***"
    else:
        print "Installer executable created"

    # Run the Sphinx utility to build DiRefl documentation.
    print "\nPart 6 - Running the Sphinx utility to build DiRefl documentation ...\n"

    os.chdir("doc\sphinx")
    # Delete any left over files from a previous build.
    subprocess.call("make clean")
    # Create documentation in HTML format.
    subprocess.call("make html")
    # Create documentation in PDF format.
    subprocess.call("make pdf")
    # Copy PDF file to the top-level directory.
    os.chdir("_build\latex")
    if os.path.isfile("DirectInversion.pdf"):
        shutil.copy("DirectInversion.pdf", top_dir)


def check_packages():
    """
    Checks that the system has the necessary modules.
    """

    # Python appears to write directly to the console, not to stdout, so the
    # following code does not work as expected:
    # p = subprocess.Popen("%s -V" % PYTHON, stdout=subprocess.PIPE)
    # print "Using ", p.stdout.read().strip()
    print "Using ",
    subprocess.call("%s -V" % PYTHON)  # displays python name and version string

    try:
        import matplotlib
        if not matplotlib.__version__ == "0.99.0":
            req_pack["matplotlib"]= ("0.99.0", matplotlib.__version__)
    except:
        print "matplotlib not found"

    try:
        import numpy
        if not numpy.__version__ == "1.2.1":
            req_pack["numpy"]= ("1.2.1", numpy.__version__)
    except:
        print "numpy not found"

    try:
        import scipy
        if not scipy.__version__ == "0.7.0":
            req_pack["scipy"]= ("0.7.0", scipy.__version__)
    except:
        print "scipy not found"

    req_pack = {}
    try:
        import wx
        if not wx.__version__ == "2.8.11.0":
            req_pack["wx"]= ("2.8.11.0", wx.__version__)
    except:
        print "wxpython not found"

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
        # Recursively access file names in subdirectories.
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

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

# Authors: James Krycka and Nikunj Patel

"""
This script builds the DiRefl application and documentation from source and
runs unit tests and doc tests.  It supports building on Windows and Linux.

Usually, you downloaded this script into a top-level directory (the root)
and run it from there which downloads the files from the application
repository into a subdirectory (the package directory).  For example if
test1 is the root directory, we might have:
  E:/work/test1/this-script.py
               /inversion/this-script.py
               /inversion/...

Alternatively, you can download the whole application repository and run
this script from the application's package directory where it is stored.
The script determines whether it is executing from the root or the package
directory and makes the necessary adjustments.  In this case, the root
directory is defined as one-level-up and the repository is not downloaded
(as it is assumed to be fully present).  In the example below test1 is the
implicit root (i.e. top-level) directory.
  E:/work/test1/inversion/this-script.py
               /inversion/...
"""
from __future__ import print_function

import os
import sys
import shutil
import subprocess

# Windows commands to run utilities
SVN    = "svn"
PYTHON = "python"
INNO   = r"C:\Program Files\Inno Setup 5\ISCC.exe"  # command line operation

# URL of the Subversion repository where the source code lives
SVN_REPO_URL = "svn://svn@danse.us/reflectometry/trunk/reflectometry/inversion"
# Name of the package
PKG_NAME = "inversion"
# Name of the application we're building
APP_NAME = "direfl"
# Relative path for local install (by default the installation path on Windows
# is C:\PythonNN\Lib\site-packages)
LOCAL_INSTALL = "local-site-packages"

# Required Python packages and utilities and their minimum versions
MIN_PYTHON = "2.5"
MAX_PYTHON = "3.0"
MIN_MATPLOTLIB = "0.99.0"
MIN_NUMPY = "1.2.1"
MIN_SCIPY = "0.7.0"
MIN_WXPYTHON = "2.8.10.0"
MIN_SETUPTOOLS = "0.6c9"
MIN_SPHINX = "1.0"
MIN_DOCUTILS = "0.5"
MIN_PYGMENTS = "1.0"
MIN_JINJA2 = "2.2"
MIN_NOSE = "0.11"
MIN_GCC = "3.4.4"
MIN_PY2EXE = "0.6.9"
MIN_INNO = "5.3.10"

# Create a line separator string for printing
SEPARATOR = "\n" + "/"*79

# Determine the full directory paths of the top-level, source, and installation
# directories based on the directory where the script is running.  Here the
# top-level directory refers to the parent directory of the package.
RUN_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
head, tail = os.path.split(RUN_DIR)
if tail == PKG_NAME:
    TOP_DIR = head
else:
    TOP_DIR = RUN_DIR
SRC_DIR = os.path.join(TOP_DIR, PKG_NAME)
INS_DIR = os.path.join(TOP_DIR, LOCAL_INSTALL)

#==============================================================================

def build_it():
    # Check the system for all required dependent packages.
    if not (len(sys.argv) > 1 and '-s' in sys.argv[1:]):
        check_dependencies()

    # Checkout code from repository.
    checkout_code()

    # Get the version string for the application to use later.
    # This has to be done after we have checked out the repository.
    if RUN_DIR == TOP_DIR:
        from inversion.version import version
    else:
        from version import version

    # Create an archive of the source code.
    if not (len(sys.argv) > 1 and '-a' in sys.argv[1:]):
        create_archive(version)

    # Install the application in a local directory tree.
    install_package()

    # Create a Windows executable file using py2exe.
    if not (len(sys.argv) > 1 and '-w' in sys.argv[1:]):
        if os.name == 'nt':
            create_windows_exe()

    # Create a Windows installer/uninstaller exe using the Inno Setup Compiler.
    if not (len(sys.argv) > 1 and '-w' in sys.argv[1:]):
        if os.name == 'nt':
            create_windows_installer(version)

    # Build HTML and PDF documentaton using sphinx.
    if not (len(sys.argv) > 1 and '-b' in sys.argv[1:]):
        build_documentation()

    # Run unittests using nose.
    if not (len(sys.argv) > 1 and ('-t' in sys.argv[1:] or
                                   '-u' in sys.argv[1:])):
        run_unittests()

    # Run doctests using nose.
    if not (len(sys.argv) > 1 and ('-t' in sys.argv[1:] or
                                   '-d' in sys.argv[1:])):
        run_doctests()


def checkout_code():
    # Checkout the application code from the repository into a directory tree
    # under the top level directory.
    print(SEPARATOR)
    print("\nStep 1 - Checking out application code from the repository ...\n")
    os.chdir(TOP_DIR)

    if RUN_DIR == TOP_DIR:
        exec_cmd("%s checkout %s %s" %(SVN, SVN_REPO_URL, PKG_NAME))
    else:
        print("*** Skipping checkout of repository because the executing script")
        print("*** is within the repository, not in the top-level directory.")


def create_archive(version=None):
    # Create zip and tar archives of the source code and a manifest file
    # containing the names of all files.
    print(SEPARATOR)
    print("\nStep 2 - Creating an archive of the source code ...\n")
    os.chdir(SRC_DIR)

    try:
        # Create zip and tar archives in the dist subdirectory.
        exec_cmd("%s setup.py sdist --formats=zip,gztar" %(PYTHON))
    except:
        print("*** Failed to create source archive ***")
    else:
        # Copy the archives and its manifest to the top-level directory.
        shutil.move(os.path.join("dist", PKG_NAME+"-"+str(version)+".zip"),
                    os.path.join(TOP_DIR, APP_NAME+"-"+str(version)+"-source.zip"))
        shutil.move(os.path.join("dist", PKG_NAME+"-"+str(version)+".tar.gz"),
                    os.path.join(TOP_DIR, APP_NAME+"-"+str(version)+"-source.tar.gz"))
        shutil.copy(os.path.join(SRC_DIR, "MANIFEST"),
                    os.path.join(TOP_DIR, APP_NAME+"-"+str(version)+"-source-manifest.txt"))


def install_package():
    # Install the application package in a private directory tree.
    # If the INS_DIR directory already exists, warn the user.
    # Intermediate work files are stored in the <SRC_DIR>/build directory tree.
    print(SEPARATOR)
    print("\nStep 3 - Installing the %s package in %s...\n" %(PKG_NAME, INS_DIR))
    os.chdir(SRC_DIR)

    if os.path.isdir(INS_DIR):
        print("WARNING: In order to build", APP_NAME, "cleanly, the local build")
        print("directory", INS_DIR, "needs to be deleted.")
        print("Do you want to delete this directory and continue (D)")
        print("            or leave contents intact and continue (C)")
        print("            or exit the build script (E)")
        answer = raw_input("Please choose either (D|C|E)? [E]: ")
        if answer.upper() == "D":
            shutil.rmtree(INS_DIR, ignore_errors=True)
        elif answer.upper() == "C":
            pass
        else:
            sys.exit()

    # Perform the installation to a private directory tree and create the
    # PYTHONPATH environment variable to pass this info to the py2exe build
    # script later on.
    exec_cmd("%s setup.py -q install --install-lib=%s" %(PYTHON, INS_DIR))
    os.environ["PYTHONPATH"] = INS_DIR


def create_windows_exe():
    # Use py2exe to create a Win32 executable along with auxiliary files in the
    # <SRC_DIR>/dist directory tree.
    print(SEPARATOR)
    print("\nStep 4 - Using py2exe to create a Win32 executable ...\n")
    os.chdir(SRC_DIR)

    exec_cmd("%s setup_py2exe.py" %PYTHON)


def create_windows_installer(version=None):
    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller for
    # the application.
    print(SEPARATOR)
    print("\nStep 5 - Running Inno Setup Compiler to create Win32 "
          "installer/uninstaller ...\n")
    os.chdir(SRC_DIR)

    # First create an include file to convey the application's version
    # information to the Inno Setup compiler.  If the include file exists, then
    # append the directive at the end.
    f = open("%s.iss-include" %APP_NAME, "a")
    f.write('#define MyAppVersion "%s"\n' %version)  # version must be quoted
    f.close()

    # Run the Inno Setup Compiler to create a Win32 installer/uninstaller.
    # Override the output specification in <APP_NAME>.iss to put the executable
    # and the manifest file in the top-level directory.
    exec_cmd("%s /Q /O%s %s.iss" %(INNO, TOP_DIR, APP_NAME))


def build_documentation():
    # Run the Sphinx utility to build the application's documentation.
    print(SEPARATOR)
    print("\nStep 6 - Running the Sphinx utility to build documentation ...\n")
    os.chdir(os.path.join(INS_DIR, PKG_NAME, "doc", "sphinx"))

    # Delete any left over files from a previous build.
    exec_cmd("make clean")
    # Create documentation in HTML format.
    exec_cmd("make html")
    # Create documentation in PDF format.
    exec_cmd("make pdf")
    # Copy PDF file to the top-level directory.
    os.chdir(os.path.join("_build", "latex"))
    if os.path.isfile("DirectInversion.pdf"):
        shutil.copy("DirectInversion.pdf", TOP_DIR)


def run_unittests():
    # Run Nose unittests.
    print(SEPARATOR)
    print("\nStep 7 - Running Nose unittests ...\n")
    os.chdir(INS_DIR)

    exec_cmd("nosetests -v %s" %PKG_NAME)


def run_doctests():
    # Run Nose doctests.
    print(SEPARATOR)
    print("\nStep 8 - Running Nose doctests ...\n")
    os.chdir(INS_DIR)

    exec_cmd("nosetests -v --with-doctest %s"
                 %os.path.join(PKG_NAME, "api/invert.py"))
    #exec_cmd("nosetests -v --with-doctest %s"
    #             %os.path.join(PKG_NAME, "api/resolution.py"))
    #exec_cmd("nosetests -v --with-doctest %s"
    #             %os.path.join(PKG_NAME, "api/simulate.py"))


def check_dependencies():
    """
    Checks that the system has the necessary Python packages installed.
    """

    import platform
    from pkg_resources import parse_version as PV

    python_ver = platform.python_version()
    print("Using Python", python_ver)
    print("")
    if PV(python_ver) < PV(MIN_PYTHON) or PV(python_ver) >= PV(MAX_PYTHON):
        print("ERROR - build requires Python >= %s, but < %s" %(MIN_PYTHON,
                                                                MAX_PYTHON))
        sys.exit()


    req_pkg = {}

    try:
        from matplotlib import __version__ as mpl_ver
    except:
        mpl_ver = "0"
    finally:
        req_pkg["matplotlib"] = (mpl_ver, MIN_MATPLOTLIB)

    try:
        from numpy import __version__ as numpy_ver
    except:
        numpy_ver = "0"
    finally:
        req_pkg["numpy"] = (numpy_ver, MIN_NUMPY)

    try:
        from scipy import __version__ as scipy_ver
    except:
        scipy_ver = "0"
    finally:
        req_pkg["scipy"] = (scipy_ver, MIN_SCIPY)

    try:
        from wx import __version__ as wx_ver
    except:
        wx_ver = "0"
    finally:
        req_pkg["wxpython"] = (wx_ver, MIN_WXPYTHON)

    try:
        from setuptools import __version__ as setup_ver
    except:
        setup_ver = "0"
    finally:
        req_pkg["setuptools"] = (setup_ver, MIN_SETUPTOOLS)

    try:
        from sphinx import __version__ as sphinx_ver
    except:
        sphinx_ver = "0"
    finally:
        req_pkg["sphinx"] = (sphinx_ver, MIN_SPHINX)

    try:
        from docutils import __version__ as docutils_ver
    except:
        docutils_ver = "0"
    finally:
        req_pkg["docutils"] = (docutils_ver, MIN_DOCUTILS)

    try:
        from pygments import __version__ as pygments_ver
    except:
        pygments_ver = "0"
    finally:
        req_pkg["pygments"] = (pygments_ver, MIN_PYGMENTS)

    try:
        from jinja2 import __version__ as jinja2_ver
    except:
        jinja2_ver = "0"
    finally:
        req_pkg["jinja2"] = (jinja2_ver, MIN_JINJA2)

    try:
        from nose import __version__ as nose_ver
    except:
        nose_ver = "0"
    finally:
        req_pkg["nose"] = (nose_ver, MIN_NOSE)

    try:
        if os.name == 'nt': flag = False
        else:               flag = True
        p = subprocess.Popen("gcc -dumpversion", stdout=subprocess.PIPE,
                             shell=flag)
        gcc_ver = p.stdout.read().strip()
    except:
        gcc_ver = "0"
    finally:
        req_pkg["gcc"] = (gcc_ver, MIN_GCC)

    if os.name == 'nt':
        try:
            from py2exe import __version__ as py2exe_ver
        except:
            py2exe_ver = "0"
        finally:
            req_pkg["py2exe"] = (py2exe_ver, MIN_PY2EXE)

        if os.path.isfile(INNO):
            req_pkg["Inno Setup Compiler"] = ("?", MIN_INNO)
        else:
            req_pkg["Inno Setup Compiler"] = ("0", MIN_INNO)


    error = False
    for key, values in req_pkg.items():
        if req_pkg[key][0] == "0":
            print("====> %s not found; version %s or later is required - ERROR"
                %(key, req_pkg[key][1]))
            error = True
        elif req_pkg[key][0] == "?":
            print("Found %s" %(key))  # version is unknown
        elif PV(req_pkg[key][0]) >= PV(req_pkg[key][1]):
            print("Found %s %s" %(key, req_pkg[key][0]))
        else:
            print("Found %s %s but minimum tested version is %s - WARNING"
                %(key, req_pkg[key][0], req_pkg[key][1]))
            error = True

    if error:
        ans = raw_input("\nDo you want to continue (Y|N)? [N]: ")
        if ans.upper() != "Y":
            sys.exit()
    else:
        print("\nSoftware dependencies have been satisfied")


def exec_cmd(command):
    """Runs the specified command in a subprocess."""

    if os.name == 'nt': flag = False
    else:               flag = True

    subprocess.call(command, shell=flag)


if __name__ == "__main__":
    if len(sys.argv)>1:
        # Display help if requested.
        if len(sys.argv) > 1 and '-h' in sys.argv[1:]:
            print("\nUsage: python master_builder.py [options]\n")
            print("Options:")
            print("  -a  Skip build of source archive")
            print("  -b  Skip build of books (documentation)")
            print("  -d  Skip doctests")
            print("  -h  Show this help text")
            print("  -s  Skip software dependency checks")
            print("  -t  Skip all tests (unittests and doctests); same as -u -d")
            print("  -u  Skip unittests")
            print("  -w  Skip build of Windows executable and installer")
            sys.exit()

    print("\nBuilding the %s application from the %s repository ...\n"
        %(APP_NAME, PKG_NAME))
    print("Current working directory  =", RUN_DIR)
    print("Top-level (root) directory =", TOP_DIR)
    print("Package (source) directory =", SRC_DIR)
    print("Installation directory     =", INS_DIR)
    print("")

    build_it()

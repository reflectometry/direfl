# ==============================================================================
# File: build_direfl_msw.sh
# ==============================================================================
# This shell script builds a Windows installer/uninstaller for DiRefl named
# direfl-x.y.z-win32.exe.  It obtains the source code from the inversion
# repository, uses setup.py to build the application in a local directory, then
# uses py2exe to create a self contained executable named direfl.exe, and
# finally invokes the Inno Setup Tool to create the installer executable.
# This script has been tested using Bash under Cygwin on Windows XP with the
# following software installed:
# (1) Python 2.5.4
# (2) Cygwin 2.573.2.3 (including Bash, SVN, SSH, ZIP)
# (3) gcc 3.4.4 from Cygwin and also gcc 3.4.5 from MinGW 5.1.4
#     (with the addition of distutils.cfg to specify mingw32 as compiler)
# (4) Numpy 1.2.1
# (5) Scipy 0.7.0 (with fixup to polyint.py to correct an import statement)
# (6) Matplotlib 0.98.5.2 (with fixup to mathtext.py to add a call to str())
# (7) wxPython 2.8.10.1
# (8) py2exe 0.6.9 (with fixup to build_exe.py needed to process numpy)
# (9) Inno Setup 5.3.7 including the Preprocessor add-on
#
# This script performs the following actions:
# (1) A root directory <build-dir> is created with a name specified by the user.
# (2) The contents of the reflectometry/trunk/reflectometry/inversion repository
#     is checked out in the directory tree named <build-dir>/inversion.
# (3) These source files are archived in <build-dir>/direfl-x.y.z-source.zip.
# (4) The inversion package is built and installed in a work directory tree
#     named <build-dir>/site-packages/inversion.
# (5) py2exe is used to create direfl.exe and associated files in the directory
#     tree <build-dir>/inversion/dist.
# (6) Inno Setup is used to create an installer/uninstaller for DiRefl as a
#     single executable file named <build-dir>/direfl-x.y.z-win32.exe.  Also a
#     manifest file named <build-dir>/direfl-x.y.z-manifest.txt is created.
#
# Usage:
#   $ ./build_direfl_msw.sh <version> <ex|co> <build-dir>
#   where all parameters are optional:
#     <version> is a string of the form x.y or x.y.z; default is "0.0.0"
#     <ex|co> determines whether an SVN EXPORT or SVN CHECKOUT operation is
#       performed; default is "ex"; export produces a smaller source zip file
#       because no .svn directories are included; see comments in the code
#       below for other differences between export and checkout
#     <build-dir> is the top level build directory that will be created,
#       including any embedded version info; it can be a absolute path name or
#       a relative path name; default is ./direfl-<version>
#
# Examples from a Cygwin session on Windows XP:
#    $ cd e:/work
#    $ svn export svn://danse.us/reflectometry/trunk/reflectometry/inversion/build_direfl_msw.sh
#    $ ./build-direfl-msw.sh 1.0.0
#    $ ####### -> e:/work/direfl-1.0.0/direfl-a.b.c-win32.exe
#    $ ####### -> e:/work/direfl-1.0.0/direfl-a.b.c-manifest.txt
#    $ ####### -> e:/work/direfl-1.0.0/direfl-1.0.0-source.zip
#    $
# or $ ./build-direfl-msw.sh 1.2.3 co f:/dev/test
#    Enter passphrase for key '/cygdrive/z/.ssh/id_rsa':
#    Enter passphrase for key '/cygdrive/z/.ssh/id_rsa':
#    $ ####### -> f:/dev/test/direfl-a.b.c-win32.exe
#    $ ####### -> f:/dev/test/direfl-a.b.c-manifest.txt
#    $ ####### -> f:/dev/test/direfl-1.2.3-source.zip
#    $
# or $ <some-path>/build-direfl-msw.sh
#    $ ####### -> e:/work/direfl-0.0.0/direfl-a.b.c-win32.exe
#    $ ####### -> e:/work/direfl-0.0.0/direfl-a.b.c-manifest.txt
#    $ ####### -> e:/work/direfl-0.0.0/direfl-0.0.0-source.zip
#
# NOTE: The contents of <build-dir>/inversion/direfl.iss will determine the
#       version of the DiRefl app that is built and displayed when the app is
#       installed (indicated by a.b.c in the examples above).  Therefore, it is
#       advised (but not required) that you specify the same version number to
#       this script as parameter 1 so that the name of the install image and the
#       zip source file contain the same version string.
# ==============================================================================

### (0) Process the command line parameters.
SAVE_PWD=$PWD

if [ "$1" = "" ]
then
    VER="0.0.0"
else
    VER="$1"
fi

if [ "$2" = "co" ]
then
    CHECKOUT=1
else
    CHECKOUT=0
fi

if [ "$3" = "" ]
then
    MYROOT="direfl-$VER"
else
    MYROOT="$3"
fi

### (1) Create the top-level directory.
###     The user can specify either a relative path or a fully qualified path.
###     The user is asked to confirm the version and path before proceeding.

if [ -d $MYROOT ]
then
    cd $MYROOT
    echo "***"
    echo "*** Directory $MYROOT already exists"
    echo "*** Delete the directory or choose another directory and try again"
    echo "***"
    cd $SAVE_PWD
    exit
else
    mkdir $MYROOT
    cd $MYROOT
    echo
    echo "*** DiRefl $VER will be built in the following directory tree:"
    echo "***     $PWD"
    echo "***"
    #read -p "*** Enter C to continue or Q to quit: " ans
    #if [[ $ans != "C" && $ans != "c" ]] # test for positive confirmation
    read -p "*** Press <enter> to continue or Q to quit: " ans
    if [ "$ans" != "" ]   # exit on any response other than <enter>
    then
        cd ..
        rmdir $MYROOT
        cd $SAVE_PWD
        exit
    fi
fi

### (2) Fetch the source code.
###     Export preserves file date and time and does not include .svn
###     directories.  Checkout creates file copies with current date and time
###     and includes .svn directories.  In addition, this script will use
###     secure access when the checkout option is used, but not for export.

if [ $CHECKOUT -eq 1 ]
then
    svn checkout svn+ssh://svn@danse.us/reflectometry/trunk/reflectometry/inversion inversion
else
    svn export svn://danse.us/reflectometry/trunk/reflectometry/inversion inversion
fi

### (3) Save the source code in an archive in the top-level directory.
zip -r -v -9 direfl-$VER-source.zip .

### (4) Install the inversion package in a private subdirectory.
cd inversion
python setup.py install --install-lib=../site-packages

### (5) Use py2exe to create a Win32 executable and auxiliary files in the
###     <build-dir>/inversion/dist directory tree.  The .exe file (as the py2exe
###     setup script is currently written) bundles the library.zip and the
###     python25.dll files in the .exe along with the necessary compiled
###     byte-code from the inversion repository.  The environment variable
###     PYTHONPATH is used to find our privately installed inversion package.
PYTHONPATH=../site-packages python setup_direfl_py2exe.py
ls -lAp --group-directories-first dist/

### (6) Run the Inno Setup Compiler to create a Win32 installer/uninstaller for
###     DiRefl and move the image and manifest files to the top-level directory.
"C:/Program Files/Inno Setup 5/ISCC.exe" direfl.iss
cd ..
mv -v inversion/*win32.exe .
mv -v inversion/*manifest.txt .
echo
ls -l
cd $SAVE_PWD
echo
echo "*** Now you can install DiRefl by executing:"
echo -n "***     "
ls $MYROOT/*.exe
echo "***"
echo "*** Or you can run DiRefl by executing:"
echo -n "***     "
ls $MYROOT/inversion/dist/*.exe
echo "***"
echo "*** Or you can even run DiRefl from the command line by executing:"
echo "***     python $MYROOT/site-packages/inversion/direfl.py"
echo
cd $SAVE_PWD
exit

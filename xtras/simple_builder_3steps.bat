@ECHO OFF
REM This script downloads DiRefl from the repository, builds and installs it
REM under the current directory, and then builds the HTML and PDF documentation.
REM This is a temporary script until master_builder.py is fully developed.

if exist inversion (
    rmdir /S /Q inversion
)
if exist local-site-packages (
    rmdir /S /Q local-site-packages
)

REM Step 1 - get code from the repository.

svn export svn://danse.us/reflectometry/trunk/reflectometry/inversion

REM Step 2 - build and install inversion in a local directory tree.

pushd inversion
python setup.py install --install-lib=../local-site-packages
popd

REM Setp 3 - create the html and pdf documentation and copy pdf to root dir.

pushd local-site-packages\inversion\doc\sphinx
REM Due to an unresolved problem in trying to run c:\cygwin\bin\pdflatex
REM (shortcut) rename make.bat to hide it so that MAKEFILE is used instead.
mv make.bat make.bat-hide
make html
make pdf
copy _build\latex\DirectInversion.pdf ..\..\..\..\
popd

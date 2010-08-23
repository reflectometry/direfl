### This script downloads DiRefl from the repository, builds and installs it
### under the current directory, and then builds the HTML and PDF documentation.
### This is a temporary script until master_builder.py is fully developed.

if [ -d inversion ]
then
    echo "*** WARNING - subdirectory inversion exists and will be deleted"
    read -p "*** Do you want to continue or quit? (Y|N) [N]:" ans
    if [ "$ans" != "Y" -a "$ans" != "y" ]
    then
        exit
    else
        rm -rf inversion
    fi
fi
if [ -d local-site-packages ]
then
    echo "*** WARNING - subdirectory local-site-packages exists and will be deleted"
    read -p "*** Do you want to continue or quit? (Y|N) [N]:" ans
    if [ "$ans" != "Y" -a "$ans" != "y" ]
    then
        exit
    else
        rm -rf local-site-packages
    fi
fi

### Step 1 - get code from the repository.

svn export svn://danse.us/reflectometry/trunk/reflectometry/inversion

### Step 2 - build and install inversion in a local directory tree.

cd inversion
python setup.py install --install-lib=../local-site-packages

### Setp 3 - create the html and pdf documentation and copy pdf to root dir.

cd ../local-site-packages/inversion/doc/sphinx
make html
make pdf
cp _build/latex/DirectInversion.pdf ../../../../

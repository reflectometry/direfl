#!/usr/bin/env python

import os
import sys
import numpy
from numpy.distutils.core import setup
from numpy.distutils.misc_util import Configuration


def configuration(parent_package='', top_path=None):
    config = Configuration('inversion', parent_package, top_path)

    config.add_subpackage('core')
    #config.add_subpackage('data')
    config.add_subpackage('gui')

    #config.add_data_dir('config')
    config.add_data_dir('doc')
    #config.add_data_dir('examples')
    config.add_data_dir('tests')

    config.add_data_files('direfl.ico')
    config.add_data_files('direfl.iss')
    config.add_data_files('splash.png')
    config.add_data_files('*.dat')
    config.add_data_files('*.refl')
    config.add_data_files('*.txt')

    config.get_version(os.path.join('version.py'))   # sets config.version

    return config


if __name__ == '__main__':
    if len(sys.argv) == 1: sys.argv.append('install')

    # When this file is run as a script, Inversion will be installed as its
    # own package and an .egg-info file will be created.
    # Note that the name parameter is given as a null string which will be
    # concatenated with the name parameter from Configuration.  This allows
    # Inversion to be installed as a standalone package when this setup is run
    # as a script, or installed as a subpackage of Reflectometry when its setup
    # is run.
    setup(name='',  # set to null so that name from Configuration prevails
          maintainer='DANSE Reflectometry Group',
          maintainer_email='UNKNOWN',
          description='DiRefl - Direct Inversion Reflectometry',
          url='http://www.reflectometry.org/danse',
          license='BSD',
          configuration=configuration)

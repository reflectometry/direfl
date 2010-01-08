#!/usr/bin/env python

import sys
import numpy
from numpy.distutils.core import setup
from numpy.distutils.misc_util import Configuration


def configuration(parent_package='', top_path=None):
    config = Configuration('inversion', parent_package, top_path)

    #config.add_subpackage('core')
    #config.add_subpackage('utils')

    #config.add_data_dir('config')
    #config.add_data_dir('doc')
    #config.add_data_dir('examples')
    #config.add_data_dir('tests')

    config.add_data_files('direfl.ico')
    config.add_data_files('direfl.iss')
    config.add_data_files('splash.png')
    config.add_data_files('*.dat')
    config.add_data_files('*.refl')
    config.add_data_files('*.txt')

    return config


if __name__ == '__main__':
    if len(sys.argv) == 1: sys.argv.append('install')
    setup(**configuration(top_path='').todict() )

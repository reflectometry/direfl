#!/usr/bin/env python

import os.path

from numpy.distutils.misc_util import Configuration


def configuration(parent_package='', top_path=None):
    config = Configuration('core', parent_package, top_path)

    # Form list of reflectometry library sources.
    srcpath = os.path.join(config.package_path, 'lib')
    sources = [os.path.join(srcpath, 'src', pattern)
               for pattern in ['*.c', '*.cc']]
    sources += [os.path.join(srcpath, 'reflmodule.cc'),
                os.path.join(srcpath, 'methods.cc')]

    config.add_extension('reflmodule', sources=sources)

    return config

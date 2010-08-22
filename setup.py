#!/usr/bin/env python

import os
import sys
from numpy.distutils.core import setup
from numpy.distutils.misc_util import Configuration


def configuration(parent_package='', top_path=None):
    config = Configuration('inversion', parent_package, top_path)

    config.add_subpackage('api')
    config.add_subpackage('common')
    config.add_subpackage('gui')

    config.add_data_dir('data')
    config.add_data_dir('doc')
    config.add_data_dir('tests')
    #config.add_data_dir('xtras')

    config.add_data_files('direfl.ico')
    config.add_data_files('direfl.iss')
    config.add_data_files('splash.png')
    config.add_data_files('*.txt')

    config.get_version(os.path.join('version.py'))  # sets config.version

    return config


if __name__ == '__main__':
    """
    When run as a script ($ python .../inversion/setup.py), the DiRefl
    application will be installed as a package named inversion and an .egg-info
    file will be created (e.g. in c:\Python25\Lib\site-packages\ for Windows).

    When run indirectly as part of installing the Reflectometry package
    ($ python .../reflectometry/setup.py), the DiRefl application will be
    installed as a subpackage of Reflectometry and a separate .egg-info file
    will not be created.

    Note that the name parameter in the call below is given as a null string
    which will be concatenated with the name parameter from Configuration.
    This allows Inversion to be installed as a standalone package when this
    setup is run as a script, or installed as a subpackage of Reflectometry.
    """

    short_desc = "DiRefl (Direct Inversion Reflectometry) GUI application"
    long_desc = """\
The Direct Inversion Reflectometry GUI application generates a
scattering length density (SLD) profile of a thin film or free form
sample using two neutron scattering datasets without the need to
perform a fit of the data.  It also has a simulation capability for
creating datasets from a simple model description of the sample."""

    if len(sys.argv) == 1: sys.argv.append('install')

    # These parameters will appear in the .egg-info file created.
    setup(name='',  # set to null so that name from Configuration prevails
          description=short_desc,
          long_description=long_desc,
          author='University of Maryland, DANSE Reflectometry Group',
          author_email='UNKNOWN',
          url='http://reflectometry.org/danse',
          license='BSD style license',
          platforms='Windows, Linux, MacOSX',
          configuration=configuration)

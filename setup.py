#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages, Extension

import direfl

packages = ['direfl']


if len(sys.argv) == 1:
    sys.argv.append('install')

# reflmodule extension
def reflmodule_config():
    sources = [os.path.join('direfl','api','lib',f)
               for f in ("reflmodule.cc","methods.cc",
                         "src/reflectivity.cc","src/magnetic.cc",
                         "src/reflrough.cc","src/resolution.c")]
    module = Extension('direfl.api.reflmodule', sources=sources)
    return module


short_desc = "DiRefl (Direct Inversion Reflectometry) GUI application"
long_desc = """\
The Direct Inversion Reflectometry GUI application generates a
scattering length density (SLD) profile of a thin film or free form
sample using two neutron scattering datasets without the need to
perform a fit of the data.  DiRefl also has a simulation capability
for creating datasets from a simple model description of the sample."""


setup(name='direfl',
      description=short_desc,
      version = direfl.__version__,
      long_description=long_desc,
      author='University of Maryland, DANSE Reflectometry Group',
      author_email='pkienzle@nist.gov',
      url='http://reflectometry.org/danse',
      license='BSD style license',
      platforms='Windows, Linux, MacOSX',
      classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Science/Research',
            'License :: Public Domain',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering :: Chemistry',
            'Topic :: Scientific/Engineering :: Physics',
            ],
      packages = find_packages(),
      package_data = direfl.package_data(),
      scripts = ['bin/direfl'],
      ext_modules = [reflmodule_config()],
      )


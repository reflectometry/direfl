"""Initialization for the direct inversion package."""

__version__ = "1.1.2"

def package_data():
    import os.path
    from glob import glob
    from .gui.utilities import resource_dir, APPNAME
    return { APPNAME.lower()+'-data': glob(os.path.join(resource_dir(),'*')) }

#!/usr/bin/env python

# Copyright (C) 2006-2011, University of Maryland
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
#
# Author: James Krycka

"""
This script starts the DiRefl Direct Inversion Reflectometry application.
"""

#==============================================================================

import os
import sys
import time

# Normally the inversion package will be installed, but if it is not installed,
# augment sys.path to include the parent directory of the package.  This
# assures that the module search path will include the package namespace and
# allows the application to be run directly from the source tree, even if the
# package has not been installed.
try:
    import direfl
except:
    this_dir_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(this_dir_path) == 'inversion':
        sys.path.insert(1, (os.path.dirname(this_dir_path)))
    else:
        print """\
        *** To run this script, either install the inversion package or
        *** place this module in the top-level directory of the package."""

#==============================================================================

if __name__ == "__main__":
    import direfl.gui.gui_app
    direfl.gui.gui_app.main()

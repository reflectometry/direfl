# Copyright (C) 2006-2010, University of Maryland
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

# Author: James Krycka

from version import version as APP_VERSION

APP_NAME = "DiRefl"

APP_COPYRIGHT = "(C) 2010 University of Maryland"

APP_DESCRIPTION = """\
The Direct Inversion Reflectometry (DiRefl) application generates a scattering \
length density (SLD) profile of a thin film or free form sample using two \
neutron scattering datasets without the need to perform a fit of the data.  \
DiRefl also has a simulation capability for creating datasets from a simple \
model description of the sample material.\
\n\n\
DiRefl applies phase reconstruction and direct inversion techniques to analyze \
the reflectivity datasets produced by the two neutron scattering experiments \
performed on a single or multi-layer sample sandwiched between incident and \
substrate layers whose characteristics are known.  The only setup difference \
between the runs is that the user changes the material of one of the \
surrounding layers.  Output from DiRefl is in the form of a SLD profile graph \
and other supporting plots that can be saved or printed.  In addition, the user \
can load, edit, and save model information, load reflectometry datasets, and \
adjust several parameters that affect the qualitative results of the analysis.\
"""

APP_LICENSE = """\
Permission is hereby granted, free of charge, to any person obtaining a copy \
of this software and associated documentation files (the "Software"), to deal \
in the Software without restriction, including without limitation the rights \
to use, copy, modify, merge, publish, distribute, sublicense, and/ or sell \
copies of the Software, and to permit persons to whom the Software is \
furnished to do so, subject to the following conditions:\
\n\n\
The above copyright notice and this permission notice shall be included in \
all copies or substantial portions of the Software.\
\n\n\
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR \
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, \
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE \
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER \
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, \
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN \
THE SOFTWARE."""

APP_PROJECT_URL = "http://reflectometry.org/danse"
APP_PROJECT_TAG = "DANSE/Reflectometry home page"

APP_TUTORIAL_URL = """http://www.reflectometry.org/danse/packages.html"""
APP_TUTORIAL_TXT = \
"""For a tutorial and other documentation on DiRefl, please visit:"""

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
#
# Author: James Krycka

import wx
import os
import sys

# Text string used to compare the string width in pixels for different fonts.
# This benchmark string has 236 characters, containing 92 distinct characters
# consisting of the lowercase alpha chars in the ratio used in an English
# Scrabble(TM) set, the uppercase alpha chars, digits, special chars with
# multiples of commonly used ones, and many spaces to approximate spacing
# between words in sentences and labels.
BENCHMARK_TEXT =\
"eeeeeeeeeeee aaaaaaaaa iiiiiiiii oooooooo nnnnnn rrrrrr tttttt "\
"llll ssss uuuu dddd ggg bb cc mm pp ff hh vv ww yy k j x q z "\
"ABCDEF GHIJKLM NOPQRST UVWXYZ 0123456789 "\
"...... :::: ()()() \"\",,'' ++--**//== {}[]<> ;|~\\_ ?!@#$%^&"

# The width and height in pixels of the test string using MS Windows default
# font and a dpi of 96.
BENCHMARK_WIDTH = 1279
BENCHMARK_HEIGHT = 14


def choose_fontsize(fontname=None):
    """
    Determine the largest font size (in points) to use for a given font such
    that the rendered width of a benchmark string is less than or equal to the
    rendered width of the string using the Windows default font at 96 dpi.

    The width in pixels of a rendered string is affected by the choice of font,
    the point size of the font, and the resolution of the installed font as
    measured in dots-per-inch (aka points-per inch).
    """

    test = wx.Frame(parent=None, id=wx.ID_ANY, title="")
    if fontname is None:
        fontname = test.GetFont().GetFaceName()

    for fontsize in xrange(12, 5, -1):
        test.SetFont(wx.Font(fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL, False,
                             fontname))
        benchmark = wx.StaticText(test, wx.ID_ANY, label="")
        w, h = benchmark.GetTextExtent(BENCHMARK_TEXT)
        benchmark.Destroy()
        if w <= BENCHMARK_WIDTH: break

    test.Destroy()
    return fontsize


def display_fontsize(fontname=None, benchmark_text=BENCHMARK_TEXT,
                                    benchmark_width=BENCHMARK_WIDTH,
                                    benchmark_height=BENCHMARK_HEIGHT):
    """
    Display the width in pixels of a benchmark text string for a given font
    at various point sizes when rendered on the application's output device
    (which implicitly takes into account the resolution (in dpi) of the font
    faces at the various point sizes).
    """

    test = wx.Frame(parent=None, id=wx.ID_ANY, title="")

    # Set the fontname if one is given, otherwise use the system default font.
    # Get the font name even if we just set it in case the specified font is
    # not installed and the system chooses another one.
    if fontname is not None:
        test.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, False,
                             fontname))
    fontname = test.GetFont().GetFaceName()

    x, y = wx.ClientDC(test).GetPPI()
    print "Benchmark text width and height in pixels = %4d %2d"\
          %(benchmark_width, benchmark_height)
    print "Compare against %s font with dpi resolution of %d:" %(fontname, x)

    for fontsize in xrange(12, 5, -1):
        test.SetFont(wx.Font(fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL, False,
                             fontname))
        benchmark = wx.StaticText(test, wx.ID_ANY, label="")
        w, h = benchmark.GetTextExtent(benchmark_text)
        benchmark.Destroy()
        print "  For point size %2d, benchmark text w, h = %4d  %2d"\
              %(fontsize, w, h)

    test.Destroy()


def get_appdir():
    """
    Return the directory path of the main module of the application, i.e, the
    root directory from which the application was started.  Note that this may
    be different than the current working directory.
    """

    if hasattr(sys, "frozen"):  # check for py2exe image
        path = sys.executable
    else:
        path = sys.argv[0]
    return os.path.dirname(os.path.abspath(path))


def write_to_statusbar(text, index):
    """Write a message to the status bar in the specified slot."""

    frame = wx.FindWindowByName("AppFrame", parent=None)
    frame.statusbar.SetStatusText(text, index)


def display_error_message(parent, caption, message):
    """Display an error message in a pop-up dialog box with an OK button."""

    msg = wx.MessageDialog(parent, message, caption, style=wx.ICON_ERROR|wx.OK)
    msg.ShowModal()
    msg.Destroy()


def display_warning_message(parent, caption, message):
    """Display a warning message in a pop-up dialog box with an OK button."""

    msg = wx.MessageDialog(parent, message, caption,
                           style=wx.ICON_WARNING|wx.OK)
    msg.ShowModal()
    msg.Destroy()


def display_information_message(parent, caption, message):
    """Display an informational message in a pop-up with an OK button."""

    msg = wx.MessageDialog(parent, message, caption,
                           style=wx.ICON_INFORMATION|wx.OK)
    msg.ShowModal()
    msg.Destroy()


def display_question(parent, caption, message):
    """Display a question in a pop-up dialog box with YES and NO buttons."""

    msg = wx.MessageDialog(parent, message, caption,
                           style=wx.ICON_QUESTION|wx.YES_NO)
    msg.ShowModal()
    msg.Destroy()

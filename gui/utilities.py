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

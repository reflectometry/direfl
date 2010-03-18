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
import sys

from gui.app_frame import AppFrame
from gui.about import APP_TITLE

# Desired initial window size (if physical screen size permits).
DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 900

#==============================================================================

class InversionApp(wx.App):
    """This class implements the main application window."""

    def OnInit(self):
        # Compute the size of the application frame such that it fits on the
        # user's screen without obstructing (or being obstructed by) the
        # Windows task bar.  The maximum initial size in pixels is bounded by
        # DISPLAY_WIDTH x DISPLAY_HEIGHT.
        #
        # Note that when running Linux and using an Xming (X11) server on a PC
        # with a dual  monitor configuration, the reported display size of the
        # PC may be that of both monitors combined with an incorrect display
        # count of 1.  To avoid displaying this app across both monitors, we
        # check if screen is 'too big'.  If so, the frame is not centered.
        xpos = ypos = 0

        # x, y = wx.DisplaySize()  # includes task bar area, if any
        j, k, x, y = wx.Display().GetClientArea() # rectangle less task bar area
        if x > 1920: x = 1280  # display on left side, not centered on screen

        if x > DISPLAY_WIDTH:  xpos = (x - DISPLAY_WIDTH)/2
        if y > DISPLAY_HEIGHT: ypos = (y - DISPLAY_HEIGHT)/2

        frame = AppFrame(parent=None, title=APP_TITLE, pos=(xpos, ypos),
                         size=(min(x, DISPLAY_WIDTH), min(y, DISPLAY_HEIGHT)))
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

#==============================================================================

if __name__ == '__main__':
    # Instantiate the application class and give control to wxPython.
    app = InversionApp(redirect=False, filename=None)

    # For wx debugging, load the wxPython Widget Inspection Tool if requested.
    # It will cause a separate interactive debugger window to be displayed.
    if len(sys.argv) > 1 and '-inspect' in sys.argv[1:]:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()

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

"""
This module is used to start the GUI for the Direct Inversion Reflectometry
application.  It creates the initial wxPython frame, presents a splash screen
to the user, and then constructs the rest of the GUI using other modules.

From the command line, the application can be run as follows:

$ python direfl.py [<optional parameters>]

The following is a list of command line parameters for development and
debugging purposes.  None are documented and they may change at any time.

Options for showing diagnostic info:
    -platform       Display platform specific info, especially about fonts
    -tracep         Display values from user input fields
    -debug          Display info for debugging purposes (changes frequently)
    -time           Display diagnostic timing information

Options for overriding the default font and point size attributes where
parameters within each set are mutually exclusive (last one takes precedence):
    -tahoma, -arial, -verdana
    -6pt, -7pt, -8pt, -9pt, -10pt, -11pt, -12pt

Options for controlling the development and testing environment:
    -xtabs          Add extra notebook pages for test purposes
        -test1      Execute test1() in a test page
        -test2      Execute test2() in a test page
    -inspect        Run the wxPython Widget Inspection Tool in a debug window
"""

#==============================================================================

import os
import sys
import time

import wx
from wx.lib.wordwrap import wordwrap

# Add a path to sys.path that is the parent directory of the directory from
# which the application (i.e. this file) is being run.  This allows the app to
# run even if the inversion package is not installed and the current working
# directory is in a diffferent location.  Do this before importing (directly or
# indirectly) from sibling directories (e.g. 'from inversion/...'.  Note that
# 'from ..core.module' cannot be used as it traverses outside of the package.
# Note also that this technique works when running the py2exe image of the app.

from gui.utilities import get_appdir
# print "*** path added to sys.path is", os.path.dirname(get_appdir())
# print "*** app root directory is", get_appdir(), "and __file__ is" , __file__
sys.path.append(os.path.dirname(get_appdir()))

from gui.app_frame import AppPanel
from gui.images import getOpenBitmap
from gui.about import (APP_NAME, APP_TITLE, APP_VERSION,
                       APP_COPYRIGHT, APP_DESCRIPTION, APP_LICENSE,
                       APP_PROJECT_URL, APP_PROJECT_TAG,
                       APP_TUTORIAL_URL, APP_TUTORIAL_TXT)
from gui.utilities import (choose_fontsize, display_fontsize, log_time)

# Desired initial window size (if physical screen size permits).
DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 900

# Resource files.
PROG_SPLASH_SCREEN = "splash.png"
PROG_ICON = "direfl.ico"

# Other constants
NEWLINE = "\n"
NEWLINES_2 = "\n\n"

#==============================================================================

class DiReflApp(wx.App):
    """
    This class implements the wxPyton based GUI for the Direct Inversion
    Reflectometry application.
    """

    # Design note: The basic frame and splash window are created in this module
    # and the frame is then populated by code in another module.  This is done
    # so that the splash screen is displayed before the more time consuming,
    # application specific packages are imported.

    def OnInit(self):
        # Determine the position and size of the application frame and likewise
        # for the splash window that will cover it.
        pos, size = self.window_placement()

        # Create a basic application frame without any child panels.
        frame = AppFrame(parent=None, title=APP_TITLE, pos=pos, size=size)

        # Display a splash screen on top of the frame.
        if len(sys.argv) > 1 and '-time' in sys.argv[1:]:
            log_time("Starting to display the splash screen")
        self.display_splash_screen(frame)

        # Create the graphical user interface for the application on the frame.
        if len(sys.argv) > 1 and '-time' in sys.argv[1:]:
            log_time("Starting to build the GUI on the frame")
        frame.init_GUI()

        frame.Show(True)
        self.SetTopWindow(frame)

        # The splash screen can be dismissed by the user (or the splash screen
        # exits due to its timeout mechanism) as soon as the wxPython event
        # loop is entered (i.e. when the caller executes app.MainLoop()).
        return True


    def window_placement(self):
        """
        Determines the position and size of the application frame such that it
        fits on the user's screen without obstructing (or being obstructed by)
        the Windows task bar.  The maximum initial size in pixels is bounded by
        DISPLAY_WIDTH x DISPLAY_HEIGHT.
        """

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

        # Return the suggested position and size for the application frame.
        return (xpos, ypos), (min(x, DISPLAY_WIDTH), min(y, DISPLAY_HEIGHT))


    def display_splash_screen(self, parent):
        """Displays the splash screen.  It will exactly cover the main frame."""

        # Prepare the picture.  On a 2GHz intel cpu, this takes about a second.
        x, y = parent.GetSizeTuple()
        image = wx.Image(os.path.join(get_appdir(), PROG_SPLASH_SCREEN),
                         wx.BITMAP_TYPE_PNG)
        image.Rescale(x, y, wx.IMAGE_QUALITY_HIGH)
        bm = image.ConvertToBitmap()

        # Create and show the splash screen.  It will disappear only when the
        # program has entered the event loop AND either the timeout has expired
        # or the user has left clicked on the screen.  Thus any processing
        # performed in this routine (including sleeping) or processing in the
        # calling routine (including doing imports) will prevent the splash
        # screen from disappearing.
        #
        # Note that on Linux, the timeout appears to occur immediately in which
        # case the splash screen disappears upon entering the event loop.
        wx.SplashScreen(bitmap=bm,
                        splashStyle=(wx.SPLASH_CENTRE_ON_PARENT|
                                     wx.SPLASH_TIMEOUT|wx.STAY_ON_TOP),
                        milliseconds=4000,
                        parent=parent,
                        id=wx.ID_ANY)

        # Keep the splash screen up a minimum amount of time for non-Windows
        # systems.  This is a workaround for Linux and possibly MacOS that
        # appear to ignore the splash screen timeout option.
        if '__WXMSW__' not in wx.PlatformInfo:
            if len(sys.argv) > 1 and '-time' in sys.argv[1:]:
                log_time("Starting sleep of 2 secs")
            time.sleep(2)

        # A call to wx.Yield does not appear to be required.  If used on
        # Windows, the cursor changes from 'busy' to 'ready' before the event
        # loop is reached which is not desirable.  On Linux it seems to have
        # no effect.
        #wx.Yield()

#==============================================================================

class AppFrame(wx.Frame):
    """
    This class creates the top-level frame for the application and populates it
    with application specific panels and widgets.
    """

    def __init__(self, parent=None, id=wx.ID_ANY, title=APP_TITLE,
                 pos=wx.DefaultPosition, size=(800, 600), name="AppFrame"
                ):
        wx.Frame.__init__(self, parent, id, title, pos, size, name=name)

        # Display the application's icon in the title bar.
        icon = wx.Icon(os.path.join(get_appdir(), PROG_ICON),
                       wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Set the default font family and font size for the application.
        self.set_default_font()

        # Initialize the menu bar with common items.
        self.add_menubar()

        # Initialize the tool bar.
        self.add_toolbar()

        # Initialize the status bar.
        self.add_statusbar()

        # Comment out the call to Fit() to keep the frame at its initial size,
        # otherwise it will be reduced to its minimum size.
        #self.Fit()


    def init_GUI(self):
        """
        Constructs the GUI for the application on top of the basic frame
        already created.  The GUI should be built after the splash screen
        (if used) is displayed so that this work is done while the user is
        viewing the splash screen.
        """
        AppPanel(frame=self)


    def set_default_font(self):
        """
        Sets the default font family and font size for the frame which will be
        inherited by all child windows subsequently created.
        """

        # Save the system default font information before we make any changes.
        fontname = default_fontname = self.GetFont().GetFaceName()
        fontsize = default_fontsize = self.GetFont().GetPointSize()

        # If requested, override the font name to use.  Note that:
        # - the MS Windows default font appears to be the same as Tahoma
        # - Arial tends to be narrower and taller than Tahoma.
        # - Verdana tends to be wider and shorter than Tahoma.
        if len(sys.argv) > 1:
            if '-tahoma' in sys.argv[1:]: fontname = "Tahoma"
            if '-arial' in sys.argv[1:]: fontname = "Arial"
            if '-verdana' in sys.argv[1:]: fontname = "Verdana"

        fontsize = choose_fontsize(fontname=fontname)

        # If requested, override the font point size to use.
        if len(sys.argv) > 1:
            if '-12pt' in sys.argv[1:]: fontsize = 12
            if '-11pt' in sys.argv[1:]: fontsize = 11
            if '-10pt' in sys.argv[1:]: fontsize = 10
            if '-9pt' in sys.argv[1:]: fontsize = 9
            if '-8pt' in sys.argv[1:]: fontsize = 8
            if '-7pt' in sys.argv[1:]: fontsize = 7
            if '-6pt' in sys.argv[1:]: fontsize = 6

        # Set the default font for this and all child windows.  The font of the
        # frame's title bar is not affected (which is a good thing).  However,
        # this setting does not affect the font used in the frame's menu bar or
        # menu items (which is not such a good thing as the menu text may be
        # larger or smaller than the normal text used in the widgets used by
        # the application).  Menu text font cannot be changed by wxPython.
        self.SetFont(wx.Font(fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL, False,
                             fontname))

        # If requested, display font and miscellaneous platform information.
        if len(sys.argv) > 1 and '-platform' in sys.argv[1:]:
            print ">>> Platform =", wx.PlatformInfo
            print ">>> Default font is %s  Chosen font is %s"\
                  %(default_fontname, self.GetFont().GetFaceName())
            print ">>> Default point size = %d  Chosen point size = %d"\
                  %(default_fontsize, self.GetFont().GetPointSize())
            display_fontsize(fontname=fontname)


    def add_menubar(self):
        """Creates a default menu bar, menus, and menu options."""

        # Create the menu bar.
        mb = wx.MenuBar()

        # Add a 'File' menu to the menu bar and define its options.
        file_menu = wx.Menu()

        _item = file_menu.Append(wx.ID_ANY, "&Exit")
        self.Bind(wx.EVT_MENU, self.OnExit, _item)

        mb.Append(file_menu, "&File")

        # Add a 'Help' menu to the menu bar and define its options.
        help_menu = wx.Menu()

        _item = help_menu.Append(wx.ID_ANY, "&Tutorial")
        self.Bind(wx.EVT_MENU, self.OnTutorial, _item)
        _item = help_menu.Append(wx.ID_ANY, "&License")
        self.Bind(wx.EVT_MENU, self.OnLicense, _item)
        _item = help_menu.Append(wx.ID_ANY, "&About")
        self.Bind(wx.EVT_MENU, self.OnAbout, _item)

        mb.Append(help_menu, "&Help")

        # Attach the menu bar to the frame.
        self.SetMenuBar(mb)


    def add_toolbar(self):
        """Creates a default tool bar."""

        #tb = self.CreateToolBar()
        tb = wx.ToolBar(parent=self, style=wx.TB_HORIZONTAL|wx.NO_BORDER)

        #tb.AddSimpleTool(wx.ID_OPEN, getOpenBitmap(),
        #                 wx.GetTranslation("Open Data Files"),
        #                 wx.GetTranslation("Open reflectometry data files"))
        tb.Realize()
        self.SetToolBar(tb)


    def add_statusbar(self):
        """Creates a default status bar."""
        sb = self.statusbar = self.CreateStatusBar()


    def OnAbout(self, evt):
        """Shows the About dialog box."""

        # Note that use of Website or License information causes wx to default
        # to the generic About Box implementation instead of the native one.
        # In addition, the generic form centers each line of the license text
        # which is undesirable (and there is no way to disable centering).  The
        # workaround is to use About Box only with parameters that result in
        # the native mode being used, and to display the other info as separate
        # menu items (this is the wx recommended approach to handle the
        # shortcoming).

        info = wx.AboutDialogInfo()
        info.Name = APP_NAME
        info.Version = APP_VERSION + NEWLINE
        info.Copyright = APP_COPYRIGHT + NEWLINE
        info.Description = wordwrap(APP_DESCRIPTION, 500, wx.ClientDC(self))
        #info.WebSite = (APP_PROJECT_URL, APP_PROJECT_TAG)
        wx.AboutBox(info)


    def OnExit(self, event):
        """Terminates the program."""
        self.Close()


    def OnLicense(self, evt):
        """Shows the License dialog box."""

        # See the comments in OnAbout for explanation why this is not part of
        # the About dialog box as 'info.License' item.

        info = wx.AboutDialogInfo()
        info.Name = APP_NAME
        info.Version = APP_VERSION + NEWLINE
        info.Copyright = APP_COPYRIGHT + NEWLINE
        info.Description = wordwrap(APP_LICENSE, 500, wx.ClientDC(self))
        wx.AboutBox(info)


    def OnTutorial(self, event):
        """Shows the Tutorial dialog box."""

        dlg =wx.MessageDialog(self,
                              message = wordwrap(APP_TUTORIAL_TXT +
                                                 NEWLINES_2 +
                                                 APP_TUTORIAL_URL,
                                                 500, wx.ClientDC(self)),
                              caption = 'Tutorial',
                              style=wx.OK|wx.CENTRE)
        dlg.ShowModal()
        dlg.Destroy()

#==============================================================================

if __name__ == '__main__':
    if len(sys.argv) > 1 and '-time' in sys.argv[1:]:
        log_time("Starting DiRefl")

    # Instantiate the application class and give control to wxPython.
    app = DiReflApp(redirect=False, filename=None)

    # For wx debugging, load the wxPython Widget Inspection Tool if requested.
    # It will cause a separate interactive debugger window to be displayed.
    if len(sys.argv) > 1 and '-inspect' in sys.argv[1:]:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()

    if len(sys.argv) > 1 and '-time' in sys.argv[1:]:
        log_time("Done initializing - entering the event loop")

    app.MainLoop()

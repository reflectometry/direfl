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
This module consstructs the GUI for the Direct Inversion Reflectometry
application.
"""

#==============================================================================

import os
import sys

import wx
from wx.lib.wordwrap import wordwrap

from .app_panel import AppPanel
from .about import (APP_NAME, APP_TITLE, APP_VERSION,
                    APP_COPYRIGHT, APP_DESCRIPTION, APP_LICENSE,
                    APP_PROJECT_URL, APP_PROJECT_TAG,
                    APP_TUTORIAL_URL, APP_TUTORIAL_TXT)
from .utilities import (get_appdir, choose_fontsize, display_fontsize)

# Resource files.
PROG_ICON = "direfl.ico"

# Other constants
NEWLINE = "\n"
NEWLINES_2 = "\n\n"

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
        tb.Realize()
        self.SetToolBar(tb)


    def add_statusbar(self):
        """Creates a default status bar."""

        sb = self.statusbar = self.CreateStatusBar()
        sb.SetFieldsCount(1)


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

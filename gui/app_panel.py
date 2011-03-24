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
This module implements the AppPanel class which creates the main panel on top
of the frame of the GUI for the Direct Inversion Reflectometry application.  It
updates the menu, tool bar, and status bar, and also builds notebook pages on
the panel.
"""

#==============================================================================

import os
import sys

import wx

import matplotlib

# Disable interactive mode so that plots are only updated on show() or draw().
# Note that the interactive function must be called before selecting a backend
# or importing pyplot, otherwise it will have no effect.
matplotlib.interactive(False)

# Specify the backend to use for plotting and import backend dependent classes.
# Note that this must be done before importing pyplot to have an effect.
matplotlib.use('WXAgg')

from .images import getOpenBitmap
from .simulation_page import SimulationPage
from .inversion_page import InversionPage
from .auxiliary_page import AuxiliaryPage

# Custom colors.
PALE_GREEN = "#C8FFC8"
PALE_BLUE  = "#E8E8FF"

#==============================================================================

class AppPanel(wx.Panel):
    """
    This class creates the main panel of the frame and builds the GUI for the
    application on it.
    """

    def __init__(self, frame, id=wx.ID_ANY, style=wx.RAISED_BORDER,
                 name="AppPanel"
                ):
        # Create a panel on the frame.  This will be the only child panel of
        # the frame and it inherits its size from the frame which is useful
        # during resize operations (as it provides a minimal size to sizers).
        wx.Panel.__init__(self, parent=frame, id=id, style=style, name=name)

        self.SetBackgroundColour("WHITE")
        self.frame = frame

        # Modify the menu bar.
        self.modify_menubar()

        # Modify the tool bar.
        self.modify_toolbar()

        # Reconfigure the status bar.
        self.modify_statusbar([-34, -50, -16])

        # Initialize the notebook bar.
        self.add_notebookbar()


    def modify_menubar(self):
        """Adds items to the menu bar, menus, and menu options."""

        frame = self.frame
        mb = frame.GetMenuBar()

        # Add items to the "File" menu (prepending them in reverse order).
        file_menu = mb.GetMenu(0)
        file_menu.PrependSeparator()
        _item = file_menu.Prepend(wx.ID_ANY, "&Save Model ...",
                                             "Save model parameters to a file")
        frame.Bind(wx.EVT_MENU, self.OnSaveModel, _item)
        _item = file_menu.Prepend(wx.ID_ANY, "&Load Model ...",
                                             "Load model parameters from a file")
        frame.Bind(wx.EVT_MENU, self.OnLoadModel, _item)

        # Add a 'Demo' menu to the menu bar and define its options.
        demo_menu = wx.Menu()

        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Model 1",
                                            "Load description of sample model 1")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoModel1, _item)
        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Model 2",
                                            "Load description of sample model 2")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoModel2, _item)
        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Model 3",
                                            "Load description of sample model 3")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoModel3, _item)

        demo_menu.AppendSeparator()

        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Dataset 1",
                                            "Load reflectivity data files for example 1")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoDataset1, _item)
        frame.load_demo_dataset_1_item = _item  # handle for hide/show
        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Dataset 2",
                                            "Load reflectivity data files for example 2")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoDataset2, _item)
        frame.load_demo_dataset_2_item = _item  # handle for hide/show

        mb.Insert(1, demo_menu, "&Demo")


    def modify_toolbar(self):
        """Populates the tool bar."""
        tb = self.frame.GetToolBar()

        '''
        tb.AddSimpleTool(wx.ID_OPEN, getOpenBitmap(),
                         "Open Data Files", "Open reflectivity data files")
        icon_size = (16,16)
        icon_bitmap = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR,
                                               icon_size)
        tb.AddSimpleTool(wx.ID_OPEN, icon_bitmap,
                         "Open Data Files", "Open reflectivity data files")
        '''

        tb.Realize()
        self.frame.SetToolBar(tb)


    def modify_statusbar(self, subbars):
        """Divides the status bar into multiple segments."""

        sb = self.frame.GetStatusBar()
        sb.SetFieldsCount(len(subbars))
        sb.SetStatusWidths(subbars)


    def add_notebookbar(self):
        """Creates a notebook bar and a set of tabs, one for each page."""

        nb = self.notebook = wx.Notebook(self, wx.ID_ANY,
                             style=wx.NB_TOP|wx.NB_FIXEDWIDTH|wx.NB_NOPAGETHEME)
        nb.SetTabSize((100,20))  # works on Windows but not on Linux

        # Create page windows as children of the notebook.
        self.page0 = SimulationPage(nb, colour=PALE_GREEN, fignum=0)
        self.page1 = InversionPage(nb, colour=PALE_BLUE, fignum=1)

        # Add the pages to the notebook with a label to show on the tab.
        nb.AddPage(self.page0, "Simulation")
        nb.AddPage(self.page1, "Inversion")

        # Create test page windows and add them to notebook if requested.
        if len(sys.argv) > 1 and '--xtabs' in sys.argv[1:]:
            self.page10 = AuxiliaryPage(nb, colour="FIREBRICK", fignum=10)
            self.page11 = AuxiliaryPage(nb, colour="BLUE", fignum=11)
            self.page12 = AuxiliaryPage(nb, colour="GREEN", fignum=12)
            self.page13 = AuxiliaryPage(nb, colour="WHITE", fignum=13)

            nb.AddPage(self.page10, "Test 1")
            nb.AddPage(self.page11, "Test 2")
            nb.AddPage(self.page12, "Test 3")
            nb.AddPage(self.page13, "Test 4")

        # Put the notebook in a sizer attached to the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)

        '''
        # Sample code to switch windows in notebook tabs
        nb.RemovePage(self.page0)
        nb.RemovePage(self.page1)
        nb.InsertPage(0, self.page1, "Replace 1")
        nb.InsertPage(1, self.page0, "Replace 0")
        '''

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

        # Make sure the first page is the active one.
        # Note that SetSelection generates a page change event only if the
        # page changes and ChangeSelection does not generate an event.  Thus
        # we force a page change event so that the status bar is properly set
        # on startup.
        nb.ChangeSelection(0)
        nb.SendPageChangedEvent(0, 0)


    def OnPageChanged(self, event):
        """
        Performs page specific save, restore, or update operations when the
        user clicks on a notebook tab to change pages or when the program calls
        SetSelection.  (Note that ChangeSelection does not generate an event.)
        """

        ### prev_page = self.notebook.GetPage(event.GetOldSelection())
        ### print "*** OnPageChanged:", event.GetOldSelection(),\
        ###                             event.GetSelection()
        curr_page = self.notebook.GetPage(event.GetSelection())
        curr_page.OnActivePage()
        event.Skip()


    def OnLoadDemoModel1(self, event):
        """Loads Demo Model 1 from a resource file."""

        self.page0.OnLoadDemoModel1(event)
        self.notebook.SetSelection(0)


    def OnLoadDemoModel2(self, event):
        """Loads Demo Model 2 from a resource file."""

        self.page0.OnLoadDemoModel2(event)
        self.notebook.SetSelection(0)


    def OnLoadDemoModel3(self, event):
        """Loads Demo Model 3 from a resource file."""

        self.page0.OnLoadDemoModel3(event)
        self.notebook.SetSelection(0)


    def OnLoadModel(self, event):
        """Loads the Model from a user specified file."""

        self.page0.OnLoadModel(event)
        self.notebook.SetSelection(0)


    def OnSaveModel(self, event):
        """Saves the Model to a user specified file."""

        self.page0.OnSaveModel(event)
        self.notebook.SetSelection(0)


    def OnLoadDemoDataset1(self, event):
        """Loads demo 1 reflectometry data from resource files."""

        self.page1.OnLoadDemoDataset1(event)
        self.notebook.SetSelection(1)


    def OnLoadDemoDataset2(self, event):
        """Loads demo 2 reflectometry data from resource files."""

        self.page1.OnLoadDemoDataset2(event)
        self.notebook.SetSelection(1)

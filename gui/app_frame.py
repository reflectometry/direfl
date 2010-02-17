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

import matplotlib

# Disable interactive mode so that plots are only updated on show() or draw().
# Note that the interactive function must be called before selecting a backend
# or importing pyplot, otherwise it will have no effect.
matplotlib.interactive(False)

# Specify the backend to use for plotting and import backend dependent classes.
# Note that this must be done before importing pyplot to have an effect.
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar

# The Figure object is used to create backend-independent plot representations.
from matplotlib.figure import Figure

from matplotlib import pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons

# Wx-Pylab magic ...
from matplotlib import _pylab_helpers
from matplotlib.backend_bases import FigureManagerBase

import numpy as np

from wx.lib.wordwrap import wordwrap


from .utilities import (get_appdir, write_to_statusbar,
                        display_error_message, display_warning_message)
# Add a path one level above 'inversion...' to sys.path so that this app can be
# run even if the inversion package is not installed and the current working
# directory is in a diffferent location.  Do this before importing (directly or
# indirectly) from sibling directories (e.g. 'from inversion/...'.  Note that
# 'from ..core.module' cannot be used as it traverses outside of the package.
#print "path added to sys.path:", os.path.dirname(get_appdir())
#print "app root directory:", get_appdir(), " and __file__:", __file__
sys.path.append(os.path.dirname(get_appdir()))

from .about import (APP_NAME, APP_TITLE, APP_VERSION,
                    APP_COPYRIGHT, APP_DESCRIPTION, APP_LICENSE,
                    APP_PROJECT_URL, APP_PROJECT_TAG,
                    APP_TUTORIAL_URL, APP_TUTORIAL_TXT)
from .images import getOpenBitmap
from .input_list import ItemListDialog, ItemListInput

from inversion.core.ncnrdata import ANDR, NG1, NG7, XRay, NCNRLoader
from inversion.core.snsdata import Liquids, Magnetic

# Text strings for use in file selection dialog boxes.
REFL_FILES = "Refl files (*.refl)|*.refl"
DATA_FILES = "Data files (*.dat)|*.dat"
TEXT_FILES = "Text files (*.txt)|*.txt"
ALL_FILES = "All files (*.*)|*.*"

# Resource files.
PROG_ICON = "direfl.ico"
PROG_SPLASH_SCREEN = "splash.png"
DEMO_MODEL_DESC = "demo_model_1.dat"
DEMO_REFLDATA_1 = "qrd1.refl"
DEMO_REFLDATA_2 = "qrd2.refl"

NEWLINE = "\n"
NEWLINES_2 = "\n\n"

BKGD_COLOUR_WINDOW = "#ECE9D8"
PALE_YELLOW = "#FFFFB0"
PALE_GREEN = "#B0FFB0"

#==============================================================================

class AppFrame(wx.Frame):
    """This class implements the top-level frame for the application."""

    def __init__(self, parent=None, id=wx.ID_ANY, title=APP_TITLE,
                 pos=wx.DefaultPosition, size=(800, 600), name="AppFrame"
                ):
        wx.Frame.__init__(self, parent, id, title, pos, size, name=name)

        # Create a panel for the frame.  This will be the only child panel of
        # the frame and it inherits its size from the frame which is useful
        # during resize operations (as it provides a minimal size to sizers).
        self.panel = wx.Panel(self, wx.ID_ANY, style=wx.RAISED_BORDER)
        #self.panel = wx.Panel(self, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.panel.SetBackgroundColour("WHITE")

        # Display the DiRefl icon in the title bar.
        icon = wx.Icon(os.path.join(get_appdir(), PROG_ICON),
                       wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Display a splash screen.
        self.display_splash_screen()

        # Initialize the menu bar.
        self.add_menubar()

        # Initialize the tool bar.
        self.add_toolbar()

        # Initialize the status bar.
        self.add_statusbar([-5, -1, -1, -1])

        # Initialize the notebook bar.
        self.add_notebookbar()

        # Comment out the call to Fit() to keep the frame at its initial size.
        # Uncomment the call to reduce the frame to its minimum required size.
        #self.Fit()


    def display_splash_screen(self):
        """Display the splash screen.  It will exactly cover the main frame."""

        x, y = self.GetSizeTuple()
        image = wx.Image(os.path.join(get_appdir(), PROG_SPLASH_SCREEN),
                         wx.BITMAP_TYPE_PNG)
        image.Rescale(x, y, wx.IMAGE_QUALITY_HIGH)
        bm = image.ConvertToBitmap()
        # bug? - wx.SPLASH_NO_CENTRE seems to ignore pos parameter; uses (0, 0)
        wx.SplashScreen(bitmap=bm,
                        #splashStyle=wx.SPLASH_NO_CENTRE|wx.SPLASH_TIMEOUT,
                        splashStyle=wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT,
                        milliseconds=3000,
                        pos=self.GetPosition(),
                        parent=None, id=wx.ID_ANY)
        wx.Yield()


    def add_menubar(self):
        """Create a menu bar, menus, and menu options."""

        # Create the menubar.
        mb = wx.MenuBar()

        # Add a 'File' menu to the menu bar and define its options.
        file_menu = wx.Menu()

        ret_id = file_menu.Append(wx.ID_ANY, "Load &Data Files ...")
        self.Bind(wx.EVT_MENU, self.OnLoadData, ret_id)

        # For debug - jak
        if len(sys.argv) > 1 and '-rtabs' in sys.argv[1:]:
            ret_id = file_menu.Append(wx.ID_ANY, "Load &Data Files (res)...")
            self.Bind(wx.EVT_MENU, self.OnLoadData_res, ret_id)

        file_menu.AppendSeparator()

        ret_id = file_menu.Append(wx.ID_ANY, "&Load Model ...")
        self.Bind(wx.EVT_MENU, self.OnLoadModel, ret_id)
        ret_id = file_menu.Append(wx.ID_ANY, "&Save Model ...")
        self.Bind(wx.EVT_MENU, self.OnSaveModel, ret_id)

        file_menu.AppendSeparator()

        ret_id = file_menu.Append(wx.ID_ANY, "&Exit")
        self.Bind(wx.EVT_MENU, self.OnExit, ret_id)

        mb.Append(file_menu, "&File")

        # Add an 'Edit' menu to the menu bar and define its options.
        edit_menu = wx.Menu()

        ret_id = edit_menu.Append(wx.ID_ANY, "&Instrument ...")
        self.Bind(wx.EVT_MENU, self.OnInstrument, ret_id)

        mb.Append(edit_menu, "&Edit")

        # Add a 'Help' menu to the menu bar and define its options.
        help_menu = wx.Menu()

        ret_id = help_menu.Append(wx.ID_ANY, "&Tutorial")
        self.Bind(wx.EVT_MENU, self.OnTutorial, ret_id)
        ret_id = help_menu.Append(wx.ID_ANY, "&License")
        self.Bind(wx.EVT_MENU, self.OnLicense, ret_id)
        ret_id = help_menu.Append(wx.ID_ANY, "&About")
        self.Bind(wx.EVT_MENU, self.OnAbout, ret_id)

        mb.Append(help_menu, "&Help")

        # Attach the menubar to the frame.
        self.SetMenuBar(mb)


    def add_toolbar(self):
        """Create a tool bar and populate it."""

        #tb = self.CreateToolBar()
        tb = wx.ToolBar(parent=self, style=wx.TB_HORIZONTAL|wx.NO_BORDER)

        tb.AddSimpleTool(wx.ID_OPEN, getOpenBitmap(),
                         wx.GetTranslation("Open Data Files"),
                         wx.GetTranslation("Open reflectometry data files"))
        tb.Realize()
        self.SetToolBar(tb)


    def add_statusbar(self, subbars):
        """Create a status bar."""

        sb = self.statusbar = self.CreateStatusBar()
        sb.SetFieldsCount(len(subbars))
        sb.SetStatusWidths(subbars)


    def add_notebookbar(self):
        """Create a notebook bar and a set of tabs, one for each page."""

        nb = self.notebook = wx.Notebook(self.panel, wx.ID_ANY,
                                         style=wx.NB_TOP|wx.NB_FIXEDWIDTH)

        # Create page windows as children of the notebook.
        self.page0 = SimulatedDataPage(nb, colour=PALE_YELLOW, fignum=0)
        self.page1 = CollectedDataPage(nb, colour=PALE_GREEN, fignum=1)

        # Add the pages to the notebook with a label to show on the tab.
        nb.AddPage(self.page0, "Simulated Data")
        nb.AddPage(self.page1, "Collected Data")

        # For debug - jak
        # Create test page windows and add them to notebook if requested.
        if len(sys.argv) > 1 and '-rtabs' in sys.argv[1:]:
            self.page2 = SimulatedDataPage(nb, colour="YELLOW", fignum=2)
            self.page3 = CollectedDataPage(nb, colour="GREEN", fignum=3)

            nb.AddPage(self.page2, "Simulation Test")
            nb.AddPage(self.page3, "Analysis Test")

        if len(sys.argv) > 1 and '-xtabs' in sys.argv[1:]:
            self.page2 = TestPlotPage(nb, colour="GREEN", fignum=2)
            self.page3 = TestPlotPage(nb, colour="BLUE", fignum=3)
            self.page4 = TestPlotPage(nb, colour="YELLOW", fignum=4)
            self.page5 = TestPlotPage(nb, colour="RED", fignum=5)

            nb.AddPage(self.page2, "Test 1")
            nb.AddPage(self.page3, "Test 2")
            nb.AddPage(self.page4, "Test 3")
            nb.AddPage(self.page5, "Test 4")

        # Put the notebook in a sizer attached to the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nb, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)
        sizer.Fit(self.panel)

        '''
        # Sample code to switch windows in notebook tabs
        nb.RemovePage(self.page0)
        nb.RemovePage(self.page1)
        nb.InsertPage(0, self.page1, "Replace 1")
        nb.InsertPage(1, self.page0, "Replace 0")
        '''

        self.page0.active_page()

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)


    def OnPageChanged(self, event):
        """
        Perform any save, restore, or update operations when the user switches
        notebook pages (via clicking on the notebook tab).
        """

        #prev_page = self.notebook.GetPage(event.GetOldSelection())
        #print "*** OnPageChanged:", event.GetOldSelection(), event.GetSelection()
        curr_page = self.notebook.GetPage(event.GetSelection())
        curr_page.active_page()
        event.Skip()


    def OnAbout(self, evt):
        """
        Show the About dialog box.

        Note that use of Website or License information causes wx to default
        to the generic About Box implementation instead of the native one.
        In addition, the generic form centers each line of the license text
        which is undesirable (and there is no way to disable centering).  The
        workaround is to use About Box only with parameters that result in the
        native mode being used, and to display the other info as separate menu
        items (this is the wx recommended approach to handle the shortcoming).
        """

        info = wx.AboutDialogInfo()
        info.Name = APP_NAME
        info.Version = APP_VERSION + NEWLINE
        info.Copyright = APP_COPYRIGHT + NEWLINE
        info.Description = wordwrap(APP_DESCRIPTION, 500, wx.ClientDC(self))
        #info.WebSite = (APP_PROJECT_URL, APP_PROJECT_TAG)
        wx.AboutBox(info)


    def OnExit(self, event):
        """Terminate the program."""
        self.Close()


    def OnInstrument(self, event):
        """Edit instrument metadata."""

        self.page0.OnEdit(event)


    def OnLicense(self, evt):
        """
        Show the License dialog box.

        See the comments in OnAbout for explanation why this is not part of the
        About dialog box as 'info.License' item.
        """

        info = wx.AboutDialogInfo()
        info.Name = APP_NAME
        info.Version = APP_VERSION + NEWLINE
        info.Copyright = APP_COPYRIGHT + NEWLINE
        info.Description = wordwrap(APP_LICENSE, 500, wx.ClientDC(self))
        wx.AboutBox(info)


    def OnLoadData(self, event):
        """Load reflectometry data files for measurements 1 and 2."""

        self.page1.col_tab_OnLoadData(event)  # TODO: create menu in dest class


    # For debug - jak
    def OnLoadData_res(self, event):
        """Load reflectometry data files for measurements 1 and 2."""

        self.page3.col_tab_OnLoadData(event)  # TODO: create menu in dest class


    def OnLoadModel(self, event):
        """Load Model from a file."""

        self.page0.sim_tab_OnLoadModel(event)  # TODO: create menu in dest class


    def OnSaveModel(self, event):
        """Save Model to a file."""

        self.page0.sim_tab_OnSaveModel(event)  # TODO: create menu in dest class


    def OnTutorial(self, event):
        """Show the Tutorial dialog box."""

        dlg =wx.MessageDialog(self,
                              message = wordwrap(APP_TUTORIAL_TXT +
                                                 NEWLINES_2 +
                                                 APP_TUTORIAL_URL,
                                                 500, wx.ClientDC(self)),
                              caption = 'Tutorial',
                              style=wx.OK | wx.CENTRE)
        dlg.ShowModal()
        dlg.Destroy()

#==============================================================================

class SimulatedDataPage(wx.Panel):
    """
    This class implements phase reconstruction and direct inversion analysis
    of two simulated surround variation data sets (generated from a model)
    to produce a scattering length density profile of the sample.
    """

    def __init__(self, parent, id=wx.ID_ANY, colour="", fignum=0, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.fignum=fignum
        self.SetBackgroundColour(colour)

        # Split the panel to separate the input fields from the plots.
        # wx.SP_LIVE_UPDATE can be omitted to disable repaint as sash is moved.
        sp = wx.SplitterWindow(self, style=wx.SP_3D|wx.SP_LIVE_UPDATE)
        sp.SetMinimumPaneSize(290)

        # Create display panels as children of the splitter.
        self.pan1 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan1.SetBackgroundColour(colour)
        self.pan2 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan2.SetBackgroundColour("WHITE")

        self.init_param_panel()
        self.init_plot_panel()

        # Attach the child panels to the splitter.
        sp.SplitVertically(self.pan1, self.pan2, sashPosition=300)
        sp.SetSashGravity(0.2)  # on resize grow mostly on right side

        # Put the splitter in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_param_panel(self):
        """Initialize the parameter input panel of the SimulatedDataPage."""

        self.instmeta = InstrumentMetadata()

        # Create instructions for using the model description input box.
        line1 = wx.StaticText(self.pan1, wx.ID_ANY,
                    label="Define the Surface, Sample Layers, and Substrate")
        line2 = wx.StaticText(self.pan1, wx.ID_ANY,
                    label="components of your model (one layer per line):")
        #line3 = wx.StaticText(self.pan1, wx.ID_ANY,
        #           label="    as shown below (roughness defaults to 0):")

        # Read in demo model parameters.
        # Note that the number of lines determines the height of the box.
        # TODO: create a model edit box with a min-max height.
        filespec = os.path.join(get_appdir(), DEMO_MODEL_DESC)

        try:
            fd = open(filespec, 'rU')
            demo_model_params = fd.read()
            fd.close()
        except:
            display_warning_message(self, "Load Model Error",
                "Error loading demo model from file "+DEMO_MODEL_DESC)
            demo_model_params = \
                "# SLDensity  Thickness  Roughness  comments" + \
                NEWLINES_2 + NEWLINES_2 + NEWLINES_2 + NEWLINE

        # Create an input box to enter and edit the model description and
        # populate it with the contents of the demo file.
        self.model = wx.TextCtrl(self.pan1, wx.ID_ANY,
                                 value=demo_model_params,
                                 style=wx.TE_MULTILINE|wx.TE_WORDWRAP)
        self.model.SetBackgroundColour(BKGD_COLOUR_WINDOW)
        #self.model.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Group model parameter widgets into a labelled section and
        # manage them with a static box sizer.
        sbox1 = wx.StaticBox(self.pan1, wx.ID_ANY, "Model Parameters")
        sbox1_sizer = wx.StaticBoxSizer(sbox1, wx.VERTICAL)
        sbox1_sizer.Add(line1, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sbox1_sizer.Add(line2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        #sbox1_sizer.Add(line3, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sbox1_sizer.Add(self.model, 1,
                        wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=10)

        #----------------------------------------------------------------------

        # Create a panel for gathering instrument metadata.
        self.pan11 = wx.Panel(self.pan1, wx.ID_ANY, style=wx.RAISED_BORDER)
        self.pan11.SetBackgroundColour(BKGD_COLOUR_WINDOW)

        # Present a combobox with instrument choices.
        cb_label = wx.StaticText(self.pan11, wx.ID_ANY, "Choose Instrument:")
        inst_names = self.instmeta.get_inst_names()
        cb = wx.ComboBox(self.pan11, wx.ID_ANY,
                         value=inst_names[self.instmeta.get_inst_idx()],
                         choices=inst_names,
                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, cb)

        # Create a horizontal box sizer for the combo box and its label.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(cb_label, 0,
            wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT,
            border=10)
        hbox1_sizer.Add(cb, 1, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Associate the sizer with its container.
        self.pan11.SetSizer(hbox1_sizer)
        hbox1_sizer.Fit(self.pan11)

        # Create button controls.
        btn_edit = wx.Button(self.pan1, wx.ID_ANY, "Edit")
        self.Bind(wx.EVT_BUTTON, self.OnEdit, btn_edit)
        btn_reset = wx.Button(self.pan1, wx.ID_ANY, "Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)

        # Create a horizontal box sizer for the buttons.
        hbox2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox2_sizer.Add((10,20), 1)  # stretchable whitespace
        hbox2_sizer.Add(btn_edit, 0)
        hbox2_sizer.Add((10,20), 0)  # non-stretchable whitespace
        hbox2_sizer.Add(btn_reset, 0)

        # Group instrument metadata widgets into a labelled section and
        # manage them with a static box sizer.
        sbox2 = wx.StaticBox(self.pan1, wx.ID_ANY, "Instrument Metadata")
        sbox2_sizer = wx.StaticBoxSizer(sbox2, wx.VERTICAL)
        sbox2_sizer.Add(self.pan11, 0,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sbox2_sizer.Add(hbox2_sizer, 0, wx.EXPAND|wx.ALL, border=10)

        #----------------------------------------------------------------------

        fields = [
                ###["SLD of Substrate:", 2.07, "float", None, True],
                   ["SLD of Surface 1:", 0.0, "float", None, True],
                   ["SLD of Surface 2:", 4.5, "float", None, True],
                ###["Sample Thickness:", 1000, "float", None, True],
                   ["Qmin:", 0.0, "float", None, True],
                   ["Qmax:", 0.4, "float", None, True],
                   ["# Profile Steps:", 128, "int", None, True],
                   ["Over Sampling Factor:", 4, "int", None, True],
                   ["# Inversion Iterations:", 6, "int", None, True],
                   ["# Monte Carlo Trials:", 10, "int", None, True],
                ###["Cosine Transform Smoothing:", 0.0, "float", None, True],
                ###["Back Reflectivity:", "True", "str", ("True", "False"), True],
                ###["Inversion Noise Factor:", 1, "int", None, True],
                   ["Simulated Noise (as %):", 8.0, "float", None, True],
                   ["Bound State Energy:", 0.0, "float", None, True],
                   ["Perfect Reconstruction:", "False", "str", ("True", "False"), True],
                ###["Show Iterations:", "False", "str", ("True", "False"), True]
                ###["Monitor:", "None", "str", None, False]
                 ]

        self.inv_params = ItemListInput(parent=self.pan1, itemlist=fields)

        # Group inversion parameter widgets into a labelled section and
        # manage them with a static box sizer.
        sbox3 = wx.StaticBox(self.pan1, wx.ID_ANY, "Inversion Parameters")
        sbox3_sizer = wx.StaticBoxSizer(sbox3, wx.VERTICAL)
        sbox3_sizer.Add(self.inv_params, 1,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)

        #----------------------------------------------------------------------

        # Create button controls.
        btn_compute = wx.Button(self.pan1, wx.ID_ANY, "Compute")
        self.Bind(wx.EVT_BUTTON, self.OnCompute, btn_compute)

        # Create a horizontal box sizer for the buttons.
        hbox3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox3_sizer.Add((10,20), 1)  # stretchable whitespace
        hbox3_sizer.Add(btn_compute, 0)

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbox1_sizer, 2, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox2_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox3_sizer, 3, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(hbox3_sizer, 0, wx.EXPAND|wx.BOTTOM|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan1.SetSizer(sizer)
        sizer.Fit(self.pan1)


    def init_plot_panel(self):
        """Initialize the plotting panel of the SimulatedDataPage."""

        INTRO_TEXT = """\
Results from phase reconstruction and inversion of simulated data files \
generated from model parameters:"""

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the FigureCanvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(self.pan2, wx.ID_ANY, figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for Pylab so that when
        # pylab plotting statements are executed they will operate on our
        # canvas and not create a new frame and canvas for display purposes.
        # This technique allows this application to execute code that uses
        # pylab stataments to generate plots and embed these plots in our
        # application window(s).
        self.fm = FigureManagerBase(canvas, self.fignum)
        _pylab_helpers.Gcf.set_active(self.fm)

        # Instantiate the matplotlib navigation toolbar and explicitly show it.
        mpl_toolbar = Toolbar(canvas)
        mpl_toolbar.Realize()

        # Create a placeholder for text displayed above the plots.
        intro = wx.StaticText(self.pan2, wx.ID_ANY, label=INTRO_TEXT)
        intro.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(intro, 0, wx.EXPAND|wx.ALL, border=10)
        sizer.Add(canvas, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(mpl_toolbar, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan2.SetSizer(sizer)
        sizer.Fit(self.pan2)


    def active_page(self):
        """This method is called when user selects (makes current) the page."""

        WHAT_TODO_NEXT = """\
Edit parameters then press the Compute button to generate a density profile \
from your model."""
        write_to_statusbar(WHAT_TODO_NEXT, 0)
        write_to_statusbar("", 1)
        write_to_statusbar("", 2)


    def OnComboBoxSelect(self, event):
        """Process the user's choice of instrument."""

        sel = event.GetEventObject().GetSelection()
        self.instmeta.set_inst_idx(sel)


    def OnCompute(self, event):
        """Perform the operation."""

        import pylab
        import time

        # Explicitly validate all input parameters before proceeding.  The
        # panel's Validate method will invoke all validators associated with
        # its top-level input objects and transfer data from them.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the Compute button without
        # making the corrections, so a full validation pass must be done now.
        if not self.inv_params.Validate():
            display_error_message(self, "Data Entry Error",
                "Please correct the highlighted fields in error.")
            return

        # Get the validated parameters.
        self.params = self.inv_params.GetResults()

        # Validate and convert the model description into a list of layers.
        lines = self.model.GetValue().splitlines()
        layers = []
        for line in lines:
            lin = line.strip()
            if lin.startswith('#'): continue  # skip over comment line
            if len(lin) == 0: continue  # discard blank line
            keep = lin.split('#')
            lin = keep[0]  # discard trailing comment
            ln = lin.split(None, 4)  # we'll break into a max of 4 items
            if len(ln) == 1: ln.append('100')  # default thickness to 100
            if len(ln) == 2: ln.append('0')  # default roughness to 0.0

            try:
                temp = [ float(ln[0]), float(ln[1]), float(ln[2]) ]
            except:
                display_error_message(self, "Syntax Error",
                    "Please correct syntax error in model description.")
                return

            layers.append(temp)

        if len(layers) < 3:
            display_error_message(self, "Less Than 3 Layers Defined",
                ("You must specify at least one Surface, Sample, and " +
                 "Substrate layer for your model."))
            return

        sample = layers[1:-1]
        #print "=== layers", layers
        #print "=== sample", sample
        self.params.append(layers[-1][0])  # add SLD of substrate to list
        self.params.append(layers[-1][2])  # add roughness of substrate to list

        # Get resolution parameters.
        i = self.instmeta.get_inst_idx()
        if i <= 3:
            self.wavelength = self.instmeta.get_wavelength()
            self.dLoL = self.instmeta.get_dLoL()
            self.d_s1 = self.instmeta.get_d_s1()
            self.d_s2 = self.instmeta.get_d_s2()
            self.Tlo = self.instmeta.get_Tlo()
            self.Thi = self.instmeta.get_Thi()
            self.slit1_at_Tlo = self.instmeta.get_slit1_at_Tlo()
            self.slit2_at_Tlo = self.instmeta.get_slit2_at_Tlo()
            self.slit1_below = self.instmeta.get_slit1_below()
            self.slit2_below = self.instmeta.get_slit2_below()
            self.slit1_above = self.instmeta.get_slit1_above()
            self.slit2_above = self.instmeta.get_slit2_above()
            self.sample_width = self.instmeta.get_sample_width()
            self.sample_broadening = self.instmeta.get_sample_broadening()
        else:
            self.wavelength_lo = self.instmeta.get_wavelength_lo()
            self.wavelength_hi = self.instmeta.get_wavelength_hi()
            self.dLoL = self.instmeta.get_dLoL()
            self.slit1_size = self.instmeta.get_slit1_size()
            self.slit2_size = self.instmeta.get_slit2_size()
            self.d_s1 = self.instmeta.get_d_s1()
            self.d_s2 = self.instmeta.get_d_s2()
            self.theta = self.instmeta.get_theta()
            self.sample_width = self.instmeta.get_sample_width()
            self.sample_broadening = self.instmeta.get_sample_broadening()

        # Inform the user that we're entering a period of high computation.
        write_to_statusbar("Generating new plots ...", 1)
        write_to_statusbar("", 2)

        # Set the plotting figure manager for this class as the active one and
        # erase the current figure.
        _pylab_helpers.Gcf.set_active(self.fm)
        pylab.clf()
        pylab.draw()

        # Apply phase reconstruction and direct inversion techniques on the
        # simulated reflectivity datasets.
        t0 = time.time()
        if self.fignum == 0:
            perform_simulation(sample, self.params)
        # For debug - jak
        if len(sys.argv) > 1 and '-rtabs' in sys.argv[1:] and self.fignum == 2:
            perform_simulation_res(sample, self.params)
        pylab.draw()
        secs = time.time() - t0

        # Write the total execution and plotting time to the status bar.
        write_to_statusbar("Plots updated", 1)
        write_to_statusbar("%g secs" %(secs), 2)


    def OnEdit(self, event):
        self.instmeta.edit_metadata()


    def OnReset(self, event):
        self.instmeta.init_metadata()


    def sim_tab_OnLoadModel(self, event):
    #def OnLoadModel(self, event):  # TODO: reorganize menu to call directly
        """Load Model from a file."""

        dlg = wx.FileDialog(self,
                            message="Load Model from File ...",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=DATA_FILES+"|"+TEXT_FILES+"|"+ALL_FILES,
                            style=wx.OPEN)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            pathname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            filespec = os.path.join(pathname, filename)
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        # Read the entire input file into a buffer.
        try:
            fd = open(filespec, 'rU')
            model_params = fd.read()
            fd.close()
        except:
            display_error_message(self, "Load Model Error",
                                  "Error loading model from file "+filename)
            return

        # Replace the contents of the model parameter text control box with
        # the data from the file.
        self.model.Clear()
        self.model.SetValue(model_params)


    def sim_tab_OnSaveModel(self, event):
    #def OnSaveModel(self, event):  # TODO: reorganize menu to call directly
        """Save Model to a file."""

        dlg = wx.FileDialog(self,
                            message="Save Model to File ...",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=DATA_FILES+"|"+TEXT_FILES+"|"+ALL_FILES,
                            style=wx.SAVE|wx.OVERWRITE_PROMPT)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            pathname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            filespec = os.path.join(pathname, filename)
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        # Put the contents of the model parameter text control box into a
        # buffer.
        model_params = self.model.GetValue()

        # Write the entire buffer to the output file.
        try:
            fd = open(filespec, 'w')
            fd.write(model_params)
            fd.close()
        except:
            display_error_message(self, "Save Model Error",
                                  "Error saving model to file "+filename)
            return

#==============================================================================

class CollectedDataPage(wx.Panel):
    """
    This class implements phase reconstruction and direct inversion analysis
    of two surround variation data sets (i.e., experimentally collected data)
    to produce a scattering length density profile of the sample.
    """

    def __init__(self, parent, id=wx.ID_ANY, colour="", fignum=0, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.parent=parent
        self.fignum=fignum
        self.SetBackgroundColour(colour)

        # Split the panel to separate the input fields from the plots.
        # wx.SP_LIVE_UPDATE can be omitted to disable repaint as sash is moved.
        sp = wx.SplitterWindow(self, style=wx.SP_3D|wx.SP_LIVE_UPDATE)
        sp.SetMinimumPaneSize(290)

        # Create display panels as children of the splitter.
        self.pan1 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan1.SetBackgroundColour(colour)
        self.pan2 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan2.SetBackgroundColour("WHITE")

        self.init_param_panel()
        self.init_plot_panel()

        # Attach the panels to the splitter.
        sp.SplitVertically(self.pan1, self.pan2, sashPosition=300)
        sp.SetSashGravity(0.2)  # on resize grow mostly on right side

        # Put the splitter in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_param_panel(self):
        """Initialize the parameter input panel of the CollectedDataPage."""

        self.instmeta = InstrumentMetadata()

        # Create a panel for gathering instrument metadata.
        self.pan11 = wx.Panel(self.pan1, wx.ID_ANY, style=wx.RAISED_BORDER)
        self.pan11.SetBackgroundColour(BKGD_COLOUR_WINDOW)

        # Present a combobox with instrument choices.
        cb_label = wx.StaticText(self.pan11, wx.ID_ANY, "Choose Instrument:")
        inst_names = self.instmeta.get_inst_names()
        cb = wx.ComboBox(self.pan11, wx.ID_ANY,
                         value=inst_names[self.instmeta.get_inst_idx()],
                         choices=inst_names,
                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, cb)

        # Create a horizontal box sizer for the combo box and its label.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(cb_label, 0,
            wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT,
            border=10)
        hbox1_sizer.Add(cb, 1, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Associate the sizer with its container.
        self.pan11.SetSizer(hbox1_sizer)
        hbox1_sizer.Fit(self.pan11)

        # Create button controls.
        btn_edit = wx.Button(self.pan1, wx.ID_ANY, "Edit")
        self.Bind(wx.EVT_BUTTON, self.OnEdit, btn_edit)
        btn_reset = wx.Button(self.pan1, wx.ID_ANY, "Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)

        # Create a horizontal box sizer for the buttons.
        hbox2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox2_sizer.Add((10,20), 1)  # stretchable whitespace
        hbox2_sizer.Add(btn_edit, 0)
        hbox2_sizer.Add((10,20), 0)  # non-stretchable whitespace
        hbox2_sizer.Add(btn_reset, 0)

        # Group instrument metadata widgets into a labelled section and
        # manage them with a static box sizer.
        sbox1 = wx.StaticBox(self.pan1, wx.ID_ANY, "Instrument Metadata")
        sbox1_sizer = wx.StaticBoxSizer(sbox1, wx.VERTICAL)
        sbox1_sizer.Add(self.pan11, 0,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sbox1_sizer.Add(hbox2_sizer, 0, wx.EXPAND|wx.ALL, border=10)

        #----------------------------------------------------------------------

        fields = [ ["SLD of Substrate:", 2.07, "float", None, True],
                   ["SLD of Surface 1:", 6.33, "float", None, True],
                   ["SLD of Surface 2:", 0.0, "float", None, True],
                   ["Sample Thickness:", 1000, "float", None, True],
                   ["Qmin:", 0.0, "float", None, True],
                   ["Qmax:", 0.2, "float", None, True],
                   ["# Profile Steps:", 128, "int", None, True],
                   ["Over Sampling Factor:", 4, "int", None, True],
                   ["# Inversion Iterations:", 6, "int", None, True],
                   ["# Monte Carlo Trials:", 10, "int", None, True],
                ###["Cosine Transform Smoothing:", 0.0, "float", None, True],
                ###["Back Reflectivity:", "True", "str", ("True", "False"), False],
                ###["Inversion Noise Factor:", 1, "int", None, True],
                   ["Bound State Energy:", 0.0, "float", None, True],
                ###["Show Iterations:", "False", "str", ("True", "False"), True]
                ###["Monitor:", "None", "str", None, False]
                 ]

        self.inv_params = ItemListInput(parent=self.pan1, itemlist=fields)

        # Group inversion parameter widgets into a labelled section and
        # manage them with a static box sizer.
        sbox2 = wx.StaticBox(self.pan1, wx.ID_ANY, "Inversion Parameters")
        sbox2_sizer = wx.StaticBoxSizer(sbox2, wx.VERTICAL)
        sbox2_sizer.Add(self.inv_params, 1,
                       wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)

        #----------------------------------------------------------------------

        # Create button controls.
        btn_compute = wx.Button(self.pan1, wx.ID_ANY, "Compute")
        self.Bind(wx.EVT_BUTTON, self.OnCompute, btn_compute)

        # Create a horizontal box sizer for the buttons.
        box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        box_sizer.Add((10,20), 1)  # stretchable whitespace
        box_sizer.Add(btn_compute, 0)

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(intro, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox1_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox2_sizer, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan1.SetSizer(sizer)
        sizer.Fit(self.pan1)


    def init_plot_panel(self):
        """Initialize the plotting panel of the CollectedDataPage."""

        INTRO_TEXT = """\
Results from phase reconstruction and inversion of reflectometry data files \
from two surround measurements:"""

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the FigureCanvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(self.pan2, wx.ID_ANY, figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for Pylab so that when
        # pylab plotting statements are executed they will operate on our
        # canvas and not create a new frame and canvas for display purposes.
        # This technique allows this application to execute code that uses
        # pylab stataments to generate plots and embed these plots in our
        # application window(s).
        self.fm = FigureManagerBase(canvas, self.fignum)
        _pylab_helpers.Gcf.set_active(self.fm)

        # Instantiate the matplotlib navigation toolbar and explicitly show it.
        mpl_toolbar = Toolbar(canvas)
        mpl_toolbar.Realize()

        # Create a placeholder for text displayed above the plots.
        intro = wx.StaticText(self.pan2, wx.ID_ANY, label=INTRO_TEXT)
        intro.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(intro, 0, wx.EXPAND|wx.ALL, border=10)
        sizer.Add(canvas, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(mpl_toolbar, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan2.SetSizer(sizer)
        sizer.Fit(self.pan2)

        root = get_appdir()
        self.data_file_1 = os.path.join(root, DEMO_REFLDATA_1)
        self.data_file_2 = os.path.join(root, DEMO_REFLDATA_2)


    def active_page(self):
        """This method is called when user selects (makes current) the page."""

        WHAT_TODO_NEXT = """\
Edit parameters then press the Compute button to generate a density profile \
from the data files."""
        write_to_statusbar(WHAT_TODO_NEXT, 0)
        write_to_statusbar("", 1)
        write_to_statusbar("", 2)


    def OnComboBoxSelect(self, event):
        """Process the user's choice of instrument."""

        sel = event.GetEventObject().GetSelection()
        self.instmeta.set_inst_idx(sel)


    def OnCompute(self, event):
        """Perform the operation."""

        import pylab
        import time

        # Explicitly validate all input parameters before proceeding.  The
        # panel's Validate method will invoke all validators associated with
        # its top-level input objects and transfer data from them.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the Compute button without
        # making the corrections, so a full validation pass must be done now.
        if not self.inv_params.Validate():
            display_error_message(self, "Data Entry Error",
                "Please correct the highlighted fields in error.")
            return

        self.args = [self.data_file_1, self.data_file_2]

        # Get the validated parameters.
        self.params = self.inv_params.GetResults()
        #print "Results from %d input fields:" %(len(self.params))
        #print "  ", self.params

        # Inform the user that we're entering a period of high computation.
        write_to_statusbar("Generating new plots ...", 1)
        write_to_statusbar("", 2)

        # Set the plotting figure manager for this class as the active one and
        # erase the current figure.
        _pylab_helpers.Gcf.set_active(self.fm)
        pylab.clf()
        pylab.draw()

        # Apply phase reconstruction and direct inversion techniques on the
        # experimental reflectivity datasets.
        t0 = time.time()
        if self.fignum == 1:
            perform_recon_inver(self.args, self.params)
        # For debug - jak
        if len(sys.argv) > 1 and '-rtabs' in sys.argv[1:] and self.fignum == 3:
            perform_recon_inver_res(self.args, self.params)
        pylab.draw()
        secs = time.time() - t0

        # Write the total execution and plotting time to the status bar.
        write_to_statusbar("Plots updated", 1)
        write_to_statusbar("%g secs" %(secs), 2)


    def OnEdit(self, event):
        self.instmeta.edit_metadata()


    def OnReset(self, event):
        self.instmeta.init_metadata()


    def col_tab_OnLoadData(self, event):
    #def OnLoadData(self, event):  # TODO: reorganize menu to call directly
        """Load reflectometry data files for measurement 1 and 2."""

        dlg = wx.FileDialog(self,
                            message="Load Data for Measurement 1",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=REFL_FILES+"|"+TEXT_FILES+"|"+ALL_FILES,
                            style=wx.OPEN)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            pathname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            filespec = os.path.join(pathname, filename)
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        self.data_file_1 = filespec

        dlg = wx.FileDialog(self,
                            message="Load Data for Measurement 2",
                            defaultDir=pathname,  # directory of 1st file
                            defaultFile="",
                            wildcard=REFL_FILES+"|"+TEXT_FILES+"|"+ALL_FILES,
                            style=wx.OPEN)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            pathname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            filespec = os.path.join(pathname, filename)
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        self.data_file_2 = filespec

#==============================================================================

class TestPlotPage(wx.Panel):
    """This class implements adds a page to the notebook."""

    def __init__(self, parent, id=wx.ID_ANY, colour="", fignum=0, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.fignum=fignum
        self.SetBackgroundColour(colour)

        self.pan1 = wx.Panel(self, wx.ID_ANY, style=wx.SUNKEN_BORDER)

        self.init_testplot_panel()

        # Put the panel in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.pan1, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_testplot_panel(self):
        """Initialize the main panel of the TestPlotPage."""

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the FigureCanvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(self.pan1, wx.ID_ANY, figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for Pylab so that when
        # pylab plotting statements are executed they will operate on our
        # canvas and not create a new frame and canvas for display purposes.
        # This technique allows this application to execute code that uses
        # pylab stataments to generate plots and embed these plots in our
        # application window(s).
        fm = FigureManagerBase(canvas, self.fignum)
        _pylab_helpers.Gcf.set_active(fm)

        # Instantiate the matplotlib navigation toolbar and explicitly show it.
        mpl_toolbar = Toolbar(canvas)
        mpl_toolbar.Realize()

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(canvas, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(mpl_toolbar, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan1.SetSizer(sizer)
        sizer.Fit(self.pan1)

        # Execute tests associated with the test tabs.
        # For debug - jak
        if len(sys.argv) > 1 and '-rtabs' in sys.argv[1:]:
            if (self.fignum==2 and '-test1' in sys.argv[1:]): test1()
            if (self.fignum==3 and '-test2' in sys.argv[1:]): test2()
        if self.fignum==4: test3()
        if self.fignum==5: test4(figure)


    def active_page(self):
        """This method is called when user selects (makes current) the page."""

        write_to_statusbar("", 0)
        write_to_statusbar("", 1)
        write_to_statusbar("", 2)

#==============================================================================

class InstrumentMetadata():
    """This class is responsible for processing the instrument metadata."""

    def __init__(self):
        self.inst_names = ("NCNR ANDR", "NCNR NG1", "NCNR NG7", "NCNR Xray",
                           "SNS Liquids", "SNS Magnetic")
        self.inst_classes = ("ANDR", "NG1", "NG7", "Xray", "Liquids", "Magnetic")
        self.radiation = ["unknown"] *6
        self.wavelength = [[0.0] * 6, [0.0] * 6]
        self.dLoL = [[0.0] * 6, [0.0] * 6]
        self.d_s1 = [[0.0] * 6, [0.0] * 6]
        self.d_s2 = [[0.0] * 6, [0.0] * 6]
        self.Tlo = [[0.0] * 6, [0.0] * 6]
        self.Thi = [[0.0] * 6, [0.0] * 6]
        self.slit1_at_Tlo = [[0.0] * 6, [0.0] * 6]
        self.slit2_at_Tlo = [[0.0] * 6, [0.0] * 6]
        self.slit1_below = [[0.0] * 6, [0.0] * 6]
        self.slit2_below = [[0.0] * 6, [0.0] * 6]
        self.slit1_above = [[0.0] * 6, [0.0] * 6]
        self.slit2_above = [[0.0] * 6, [0.0] * 6]
        self.sample_width = [[0.0] * 6, [0.0] * 6]
        self.sample_broadening = [[0.0] * 6, [0.0] * 6]

        self.wavelength_lo = [[0.0] * 6, [0.0] * 6]
        self.wavelength_hi = [[0.0] * 6, [0.0] * 6]
        self.slit1_size = [[0.0] * 6, [0.0] * 6]
        self.slit2_size = [[0.0] * 6, [0.0] * 6]
        self.theta = [[0.0] * 6, [0.0] * 6]

        self.set_attr_mono(ANDR, 0)
        self.set_attr_mono(NG1, 1)
        self.set_attr_mono(NG7, 2)
        self.set_attr_mono(XRay, 3)
        self.set_attr_poly(Liquids, 4)
        self.set_attr_poly(Magnetic, 5)
        '''
        for i, name in iter(self.inst_names):
            if i <= 3: self.set_attr_mono(name, i)
            else:      self.set_attr_poly(name, i)
        '''
        self.inst_idx = 0

    def set_attr_mono(self, iclass, idx):
        if hasattr(iclass, 'radiation'):
            self.radiation[idx] = iclass.radiation
        if hasattr(iclass, 'wavelength'):
            self.wavelength[0][idx] = iclass.wavelength
        if hasattr(iclass, 'dLoL'):
            self.dLoL[0][idx] = iclass.dLoL
        if hasattr(iclass, 'd_s1') and iclass.d_s1 is not None:  # temp check
            self.d_s1[0][idx] = iclass.d_s1
        if hasattr(iclass, 'd_s2') and iclass.d_s2 is not None:  # temp check
            self.d_s2[0][idx] = iclass.d_s2
        self.inst_idx = idx
        self.init_metadata()

    def set_attr_poly(self, iclass, idx):
        if hasattr(iclass, 'radiation'):
            self.radiation[idx] = iclass.radiation
        if hasattr(iclass, 'wavelength'):
            self.wavelength_lo[0][idx], \
            self.wavelength_hi[0][idx] = iclass.wavelength
        if hasattr(iclass, 'dLoL'):
            self.dLoL[0][idx] = iclass.dLoL
        if hasattr(iclass, 'd_s1'):
            self.d_s1[0][idx] = iclass.d_s1
        if hasattr(iclass, 'd_s2'):
            self.d_s2[0][idx] = iclass.d_s2
        self.inst_idx = idx
        self.init_metadata()


    def get_inst_names(self):
        return self.inst_classes
    def get_inst_classes(self):
        return self.inst_classes
    def get_radiation(self):
        return self.radiation[self.inst_idx]
    def get_wavelength(self):
        return self.wavelength[1][self.inst_idx]
    def get_dLoL(self):
        return self.dLoL[1][self.inst_idx]
    def get_d_s1(self):
        return self.d_s1[1][self.inst_idx]
    def get_d_s2(self):
        return self.d_s2[1][self.inst_idx]
    def get_Tlo(self):
        return self.Tlo[1][self.inst_idx]
    def get_Thi(self):
        return self.Thi[1][self.inst_idx]
    def get_slit1_at_Tlo(self):
        return self.slit1_at_Tlo[1][self.inst_idx]
    def get_slit2_at_Tlo(self):
        return self.slit2_at_Tlo[1][self.inst_idx]
    def get_slit1_below(self):
        return self.slit1_below[1][self.inst_idx]
    def get_slit2_below(self):
        return self.slit2_below[1][self.inst_idx]
    def get_slit1_above(self):
        return self.slit1_above[1][self.inst_idx]
    def get_slit2_above(self):
        return self.slit2_above[1][self.inst_idx]
    def get_sample_width(self):
        return self.sample_width[1][self.inst_idx]
    def get_sample_broadening(self):
        return self.sample_broadening[1][self.inst_idx]
    def get_wavelength_lo(self):
        return self.wavelength_lo[1][self.inst_idx]
    def get_wavelength_hi(self):
        return self.wavelength_hi[1][self.inst_idx]
    def get_slit1_size(self):
        return self.slit1_size[1][self.inst_idx]
    def get_slit2_size(self):
        return self.slit2_size[1][self.inst_idx]
    def get_theta(self):
        self.theta[1][self.inst_idx]


    def get_inst_idx(self):
        return self.inst_idx


    def set_inst_idx(self, index):
        self.inst_idx = index
        self.init_metadata()


    def init_metadata(self):
        # Set current metadata values for insturment to their default values.
        i = self.inst_idx
        self.wavelength[1][i] = self.wavelength[0][i]
        self.dLoL[1][i] = self.dLoL[0][i]
        self.d_s1[1][i] = self.d_s1[0][i]
        self.d_s2[1][i] = self.d_s2[0][i]
        self.Tlo[1][i] = self.Tlo[0][i]
        self.Thi[1][i] = self.Thi[0][i]
        self.slit1_at_Tlo[1][i] = self.slit1_at_Tlo[0][i]
        self.slit2_at_Tlo[1][i] = self.slit2_at_Tlo[0][i]
        self.slit1_below[1][i] = self.slit1_below[0][i]
        self.slit2_below[1][i] = self.slit2_below[0][i]
        self.slit1_above[1][i] = self.slit1_above[0][i]
        self.slit2_above[1][i] = self.slit2_above[0][i]
        self.sample_width[1][i] = self.sample_width[0][i]
        self.sample_broadening[1][i] = self.sample_broadening[0][i]

        self.wavelength_lo[1][i] = self.wavelength_lo[0][i]
        self.wavelength_hi[1][i] = self.wavelength_hi[0][i]
        self.slit1_size[1][i] = self.slit1_size[0][i]
        self.slit2_size[1][i] = self.slit2_size[0][i]
        self.theta[1][i] = self.Tlo[0][i]


    def edit_metadata(self):
        if self.inst_idx <= 3:
            self.edit_metadata_mono()
        else:
            self.edit_metadata_poly()


    def edit_metadata_mono(self):
        i = self.inst_idx
        fields = [
                   ["Radiation Type:", self.radiation[i], "str", None, False],
                   ["Wavelength (A):", self.wavelength[1][i], "float", None, True],
                   ["Wavelength Dispersion (dLoL):", self.dLoL[1][i], "float", None, True],
                   ["Distance to Slit 1 (mm):", self.d_s1[1][i], "float", None, True],
                   ["Distance to Slit 2 (mm):", self.d_s2[1][i], "float", None, True],
                   ["Theta Lo (degrees):", self.Tlo[1][i], "float", None, True],
                   ["Theta Hi (degrees):", self.Thi[1][i], "float", None, True],
                   ["Slit 1 at Theta Lo (mm):", self.slit1_at_Tlo[1][i], "float", None, True],
                   ["Slit 2 at Theta Lo (mm):", self.slit2_at_Tlo[1][i], "float", None, True],
                   ["Slit 1 below Theta Lo (mm):", self.slit1_below[1][i], "float", None, True],
                   ["Slit 2 below Theta Lo (mm):", self.slit2_below[1][i], "float", None, True],
                   ["Slit 1 above Theta Hi (mm):", self.slit1_above[1][i], "float", None, True],
                   ["Slit 2 above Theta Hi (mm):", self.slit2_above[1][i], "float", None, True],
                   ["Sample Width (mm):", self.sample_width[1][i], "float", None, True],
                   ["Sample Broadening (mm):", self.sample_broadening[1][i], "float", None, True],
                 ]

        title = "Edit " + self.inst_names[self.inst_idx] + " Attribues"
        dlg = ItemListDialog(parent=None,
                             title=title,
                             pos=(500, 100),
                             itemlist=fields)
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetResults()
            #print "Results from all input fields of the dialog box:"
            #print "  ", results

            # Skip results[0], the radiation value that is not editable
            i = self.inst_idx
            self.wavelength[1][i] = results[1]
            self.dLoL[1][i] = results[2]
            self.d_s1[1][i] = results[3]
            self.d_s2[1][i] = results[4]
            self.Tlo[1][i] = results[5]
            self.Thi[1][i] = results[6]
            self.slit1_at_Tlo[1][i] = results[7]
            self.slit2_at_Tlo[1][i] = results[8]
            self.slit1_below[1][i] = results[9]
            self.slit2_below[1][i] = results[10]
            self.slit1_above[1][i] = results[11]
            self.slit2_above[1][i] = results[12]
            self.sample_width[1][i] = results[13]
            self.sample_broadening[1][i] = results[14]
        dlg.Destroy()


    def edit_metadata_poly(self):
        i = self.inst_idx
        fields = [
                   ["Radiation Type:", self.radiation[i], "str", None, False],
                   ["Wavelength Lo (A):", self.wavelength_lo[1][i], "float", None, True],
                   ["Wavelength Hi (A):", self.wavelength_hi[1][i], "float", None, True],
                   ["Wavelength Dispersion (dLoL):", self.dLoL[1][i], "float", None, True],
                   ["Slit 1 Size (mm):", self.slit1_size[1][i], "float", None, True],
                   ["Slit 2 Size (mm):", self.slit2_size[1][i], "float", None, True],
                   ["Distance to Slit 1 (mm):", self.d_s1[1][i], "float", None, True],
                   ["Distance to Slit 2 (mm):", self.d_s2[1][i], "float", None, True],
                   ["Theta (degrees):", self.theta[1][i], "float", None, True],
                   ["Sample Width (mm):", self.sample_width[1][i], "float", None, True],
                   ["Sample Broadening (mm):", self.sample_broadening[1][i], "float", None, True],
                 ]

        title = "Edit " + self.inst_names[self.inst_idx] + " Attribues"
        dlg = ItemListDialog(parent=None,
                             title=title,
                             pos=(500, 100),
                             itemlist=fields)
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetResults()
            print "Results from all input fields of the dialog box:"
            print "  ", results
            # Skip results[0], the radiation value that is not editable
            i = self.inst_idx
            self.wavelength_lo [1][i] = results[1]
            self.wavelength_hi[1][i] = results[2]
            self.dLoL[1][i] = results[3]
            self.slit1_size[1][i] = results[4]
            self.slit2_size[1][i] = results[5]
            self.d_s1[1][i] = results[6]
            self.d_s2[1][i] = results[7]
            self.theta[1][i] = results[8]
            self.sample_width[1][i] = results[9]
            self.sample_broadening[1][i] = results[10]
        dlg.Destroy()

#==============================================================================

def perform_recon_inver(args, params):
    """
    Perform phase reconstruction and direct inversion on two reflectometry data
    sets to generate a scattering length depth profile of the sample.
    """

    from inversion.core.core import refl, SurroundVariation, Inversion
    import pylab

    u = params[0]
    v1 = params[1]
    v2 = params[2]
    phase = SurroundVariation(args[0], args[1], u=u, v1=v1, v2=v2)
    data = phase.Q, phase.RealR, phase.dRealR

    #if dz: rhopoints = ceil(1/dz)
    #_backrefl = True if params[99] == "True" else False
    _backrefl = True
    #_showiters = True if params[99] == "True" else False
    _showiters = False

    res = Inversion(data=data, **dict(substrate=u,
                                      thickness=params[3],
                                      Qmin=params[4],
                                      Qmax=params[5],
                                      #Qmax=None,
                                      rhopoints=params[6],
                                      calcpoints=params[7],
                                      iters=params[8],
                                      stages=params[9],
                                      ctf_window=0, #cosine transform smoothing
                                      backrefl=_backrefl,
                                      noise=1,  # inversion noise factor
                                      bse=params[10],
                                      showiters=_showiters,
                                      monitor=None))
    res.run(showiters=False)
    res.plot(phase=phase)

    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right=0.96,
                          top=0.95, bottom=0.08)


# For debug - jak
def perform_recon_inver_res(args, params):
    """
    Perform phase reconstruction and direct inversion on two reflectometry data
    sets to generate a scattering length depth profile of the sample.
    """

    from inversion.core.core import refl, SurroundVariation, Inversion
    import pylab

    u = params[0]
    v1 = params[1]
    v2 = params[2]
    phase = SurroundVariation(args[0], args[1], u=u, v1=v1, v2=v2)
    data = phase.Q, phase.RealR, phase.dRealR

    #if dz: rhopoints = ceil(1/dz)
    #_backrefl = True if params[99] == "True" else False
    _backrefl = True
    #_showiters = True if params[99] == "True" else False
    _showiters = False

    res = Inversion(data=data, **dict(substrate=u,
                                      thickness=params[3],
                                      Qmin=params[4],
                                      Qmax=params[5],
                                      #Qmax=None,
                                      rhopoints=params[6],
                                      calcpoints=params[7],
                                      iters=params[8],
                                      stages=params[9],
                                      ctf_window=0, #cosine transform smoothing
                                      backrefl=_backrefl,
                                      noise=1,  # inversion noise factor
                                      bse=params[10],
                                      showiters=_showiters,
                                      monitor=None))
    res.run(showiters=False)
    res.plot(phase=phase)

    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right=0.96,
                          top=0.95, bottom=0.08)


def perform_simulation(sample, params):
    """
    Simulate reflectometry data sets from model information then perform
    phase reconstruction and direct inversion on the data to generate a
    scattering length density profile.
    """

    from inversion.core.simulate import Simulation
    from numpy import linspace
    import pylab

    if sample is None:
        # Roughness parameters (surface, sample, substrate)
        sv, s, su = 3, 5, 2
        # Surround parameters
        u, v1, v2 = 2.07, 0, 4.5
        # Default sample
        sample = ([5,100,s], [1,123,s], [3,47,s], [-1,25,s])
        sample[0][2] = sv
    else:
        su = 2

    # Run the simulation
    _perfect_reconstruction = True if params[10] == "True" else False
    #_showiters = True if params[99] == "True" else False
    _showiters = False
    _noise = params[8]
    if _noise < 0.01: _noise = 0.01
    _noise /= 100.0  # convert percent value to hundreths value

    inv = dict(showiters=_showiters,
               monitor=None,
               bse=params[9],
               noise=1,  # inversion noise factor
               iters=params[6],
               stages=params[7],
               rhopoints=params[4],
               calcpoints=params[5])

    t = Simulation(q=linspace(params[2], params[3], 150),
                   sample=sample,
                   u=params[11],
                   urough=params[12],
                   v1=params[0],
                   v2=params[1],
                   noise=_noise,
                   invert_args=inv,
                   phase_args=dict(stages=100),
                   perfect_reconstruction=_perfect_reconstruction)

    t.plot()
    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right = 0.96,
                          top=0.95, bottom=0.08)


# For debug - jak
def perform_simulation_res(sample, params):
    """
    Simulate reflectometry data sets from model information then perform
    phase reconstruction and direct inversion on the data to generate a
    scattering length density profile.
    """

    from inversion.core.simulate import Simulation
    from numpy import linspace
    import pylab

    if sample is None:
        # Roughness parameters (surface, sample, substrate)
        sv, s, su = 3, 5, 2
        # Surround parameters
        u, v1, v2 = 2.07, 0, 4.5
        # Default sample
        sample = ([5,100,s], [1,123,s], [3,47,s], [-1,25,s])
        sample[0][2] = sv
    else:
        su = 2

    # Run the simulation
    _perfect_reconstruction = True if params[10] == "True" else False
    #_showiters = True if params[99] == "True" else False
    _showiters = False
    _noise = params[8]
    if _noise < 0.01: _noise = 0.01
    _noise /= 100.0  # convert percent value to hundreths value

    instrument = NG1(Tlo=0.5, slits_at_Tlo=0.2, slits_below=0.1)
    res = instrument.resolution(Q=np.linspace(params[2], params[3], 150))

    inv = dict(showiters=_showiters,
               monitor=None,
               bse=params[9],
               noise=1,  # inversion noise factor
               iters=params[6],
               stages=params[7],
               rhopoints=params[4],
               calcpoints=params[5])
    t = Simulation(q=linspace(params[2], params[3], 150),
                   dq=res.dQ,
                   sample=sample,
                   u=params[11],
                   urough=params[12],
                   v1=params[0],
                   v2=params[1],
                   noise=_noise,
                   invert_args=inv,
                   phase_args=dict(stages=100),
                   perfect_reconstruction=_perfect_reconstruction)

    t.plot()
    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right = 0.96,
                          top=0.95, bottom=0.08)


def test1():
    """
    Test interface to phase reconstruction and direct inversion routines
    in core.py using two actual reflectometry data files.
    """

    from inversion.core.core import refl, SurroundVariation, Inversion
    import os
    import pylab

    #args = ['wsh02_re.dat']
    local = os.path.dirname(os.path.realpath(__file__))
    args = [os.path.join(local, "qrd1.refl"),
            os.path.join(local, "qrd2.refl")]
    if len(args) == 1:
        phase = None
        data = args[0]
    elif len(args) == 2:
        v1 = 6.33
        v2 = 0.0
        u = 2.07
        phase = SurroundVariation(args[0], args[1], u=u, v1=v1, v2=v2)
        data = phase.Q, phase.RealR, phase.dRealR

    #if dz: rhopoints = ceil(1/dz)
    res = Inversion(data=data, **dict(substrate=2.07,
                                      thickness=1000,
                                      calcpoints=4,
                                      rhopoints=128,
                                      Qmin=0,
                                      Qmax=None,
                                      iters=6,
                                      stages=10,
                                      ctf_window=0,
                                      backrefl=True,
                                      noise=1,
                                      bse=0,
                                      showiters=False,
                                      monitor=None))

    res.run(showiters=False)
    res.plot(phase=phase)
    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right=0.96,
                          top=0.95, bottom=0.08)


def test2():
    """
    Test interface to simulation routine in simulation.py using a reconstructed
    reflectometry data file.
    """

    from inversion.core.simulate import Simulation
    from numpy import linspace
    import pylab

    # Roughness parameters (surface, sample, substrate)
    sv, s, su = 3, 5, 2
    # Surround parameters
    u, v1, v2 = 2.07, 0, 4.5
    # Default sample
    sample = ([5,100,s], [1,123,s], [3,47,s], [-1,25,s])
    sample[0][2] = sv
    bse = 0

    # Run the simulation
    inv = dict(showiters=False, iters=6, monitor=None, bse=bse,
               noise=1, stages=10, calcpoints=4, rhopoints=128)

    t = Simulation(q = linspace(0, 0.4, 150), sample=sample,
                   u=u, urough=su, v1=v1, v2=v2, noise=0.08,
                   invert_args=inv, phase_args=dict(stages=100),
                   perfect_reconstruction=False)

    t.plot()
    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right = 0.96,
                          top=0.95, bottom=0.08)


def test3():
    """
    Test the ability to utilize code that uses the procedural interface
    to pylab to generate subplots.
    """

    import pylab

    pylab.suptitle("Test use of procedural interface to Pylab", fontsize=16)

    pylab.subplot(211)
    x = np.arange(0, 6, .01)
    y = np.sin(x**2)*np.exp(-x)
    pylab.xlabel("x-axis")
    pylab.ylabel("y-axis")
    pylab.title("First Plot")
    pylab.plot(x, y)

    pylab.subplot(212)
    x = np.arange(0, 8, .01)
    y = np.sin(x**2)*np.exp(-x) + 1
    pylab.xlabel("x-axis")
    pylab.ylabel("y-axis")
    pylab.title("Second Plot")
    pylab.plot(x, y)

    #pylab.show()


def test4(figure):
    """
    Test the ability to utilize code that uses the object oriented interface
    to pylab to generate subplots.
    """

    import pylab

    axes = figure.add_subplot(311)
    x = np.arange(0, 6, .01)
    y = np.sin(x**2)*np.exp(-x)
    axes.plot(x, y)

    axes = figure.add_subplot(312)
    x = np.arange(0, 8, .01)
    y = np.sin(x**2)*np.exp(-x) + 1
    axes.plot(x, y)
    axes.set_ylabel("y-axis")

    axes = figure.add_subplot(313)
    x = np.arange(0, 4, .01)
    y = np.sin(x**2)*np.exp(-x) + 2
    axes.plot(x, y)
    axes.set_xlabel("x-axis")

    pylab.suptitle("Test use of object oriented interface to Pylab",
                   fontsize=16)
    pylab.subplots_adjust(hspace=0.35)
    #pylab.show()

#==============================================================================
# The following code fails because AppFrame is run in a non-package context.
# Instead it must be imported from a package because it and its imported
# modules use relative imports which Python does allow from script mode.
'''
if __name__ == '__main__':
    # Instantiate the application class and give control to wxPython.
    app = wx.PySimpleApp()
    frame = AppFrame(title="DiRefl Test")
    frame.Show(True)
    app.SetTopWindow(frame)
    app.MainLoop()
'''
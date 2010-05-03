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
This module builds the GUI for the Direct Inversion Reflectometry application
on top of an wxPython frame previously constructed.
"""

#==============================================================================

import os
import sys
import time

import wx

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
from matplotlib.font_manager import FontProperties

# For use in the matplotlib toolbar.
from matplotlib.widgets import Slider, Button, RadioButtons

# Wx-Pylab magic for displaying plots within an application's window.
from matplotlib import _pylab_helpers
from matplotlib.backend_bases import FigureManagerBase

#from matplotlib import pyplot as plt
import pylab

import numpy
from numpy import linspace, inf

from wx.lib import delayedresult

from .utilities import (get_appdir, write_to_statusbar,
                        display_error_message, display_warning_message,
                        log_time, WorkingIndicator)

from .input_list import InputListDialog, InputListPanel
from .images import getOpenBitmap

from inversion.core.core import SurroundVariation, Inversion
from inversion.core.simulate import Simulation
from inversion.core.ncnrdata import ANDR, NG1, NG7, XRay, NCNRLoader
from inversion.core.snsdata import Liquids, Magnetic, SNSLoader
from inversion.core.resolution import bins, binwidths

# Text strings for use in file selection dialog boxes.
REFL_FILES = "Refl files (*.refl)|*.refl"
DATA_FILES = "Data files (*.dat)|*.dat"
TEXT_FILES = "Text files (*.txt)|*.txt"
ALL_FILES = "All files (*.*)|*.*"

# Resource files.
DEMO_MODEL1_DESC = "demo_model_1.dat"
DEMO_MODEL2_DESC = "demo_model_2.dat"
DEMO_REFLDATA1_1 = "qrd1.refl"
DEMO_REFLDATA1_2 = "qrd2.refl"
DEMO_REFLDATA2_1 = "surround_air_4.refl"
DEMO_REFLDATA2_2 = "surround_d2o_4.refl"

# Custom colors.
WINDOW_BKGD_COLOUR = "#ECE9D8"
PALE_YELLOW = "#FFFFB0"
PALE_GREEN1 = "#C0FFC0"
PALE_GREEN2 = "#D0FFD0"
PALE_BLUE1  = "#E8E8FF"
PALE_BLUE2  = "#F0F0FF"

# Other constants
NEWLINE = "\n"
NEWLINES_2 = "\n\n"

DATA_ENTRY_ERRMSG = """\
Please correct any highlighted field in error,
then retry the operation.\n
Yellow indicates an input value is required.
Red means the input value has incorrect syntax."""

INSTR_PARAM_ERRMSG = """\
Please edit the instrument data to supply missing
required parameters needed to compute resolution for
the simulated datasets."""

INSTR_CALC_RESO_ERRMSG = """\
Please specify an instrument to be used for the calculating
resolution for the simulated datasets, or disable this calculation
by selecting the 'No' button for the 'With Resolution' question
at the bottom of the page."""

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
        self.modify_statusbar([-64, -16, -10, -10])

        # Initialize the notebook bar.
        self.add_notebookbar()


    def modify_menubar(self):
        """Adds items to the menu bar, menus, and menu options."""

        frame = self.frame
        mb = frame.GetMenuBar()

        # Add items to the "File" menu (prepending them in reverse order).
        file_menu = mb.GetMenu(0)
        file_menu.PrependSeparator()
        _item = file_menu.Prepend(wx.ID_ANY, "&Save Model ...")
        frame.Bind(wx.EVT_MENU, self.OnSaveModel, _item)
        _item = file_menu.Prepend(wx.ID_ANY, "&Load Model ...")
        frame.Bind(wx.EVT_MENU, self.OnLoadModel, _item)

        # Add a 'Demo' menu to the menu bar and define its options.
        demo_menu = wx.Menu()

        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Model 1")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoModel1, _item)

        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Model 2")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoModel2, _item)

        demo_menu.AppendSeparator()

        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Dataset 1")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoDataset1, _item)
        frame.load_demo_dataset_1_item = _item  # handle for hide/show
        _item = demo_menu.Append(wx.ID_ANY, "Load &Demo Dataset 2")
        frame.Bind(wx.EVT_MENU, self.OnLoadDemoDataset2, _item)
        frame.load_demo_dataset_2_item = _item  # handle for hide/show

        mb.Insert(1, demo_menu, "&Demo")


    def modify_toolbar(self):
        """Populates the tool bar."""

        tb = self.frame.GetToolBar()

        #tb.AddSimpleTool(wx.ID_OPEN, getOpenBitmap(),
        #                 wx.GetTranslation("Open Data Files"),
        #                 wx.GetTranslation("Open reflectometry data files"))
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
                                         style=wx.NB_TOP|wx.NB_FIXEDWIDTH)

        # Create page windows as children of the notebook.
        self.page0 = SimulateDataPage(nb, colour=PALE_GREEN1, fignum=0)
        self.page1 = AnalyzeDataPage(nb, colour=PALE_BLUE1, fignum=1)

        # Add the pages to the notebook with a label to show on the tab.
        nb.AddPage(self.page0, "Simulation")
        nb.AddPage(self.page1, "Analysis")

        # Create test page windows and add them to notebook if requested.
        if len(sys.argv) > 1 and '-xtabs' in sys.argv[1:]:
            self.page2 = SimulateDataPage(nb, colour=PALE_GREEN2, fignum=2)
            self.page3 = AnalyzeDataPage(nb, colour=PALE_BLUE2, fignum=3)
            self.page4 = TestPlotPage(nb, colour="FIREBRICK", fignum=4)
            self.page5 = TestPlotPage(nb, colour="BLUE", fignum=5)
            self.page6 = TestPlotPage(nb, colour="GREEN", fignum=6)
            self.page7 = TestPlotPage(nb, colour="WHITE", fignum=7)

            nb.AddPage(self.page2, "Simulation Test")
            nb.AddPage(self.page3, "Analysis Test")
            nb.AddPage(self.page4, "Test 1")
            nb.AddPage(self.page5, "Test 2")
            nb.AddPage(self.page6, "Test 3")
            nb.AddPage(self.page7, "Test 4")

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

        self.page0.active_page()

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)


    def OnPageChanged(self, event):
        """
        Performs any save, restore, or update operations when the user switches
        notebook pages (via clicking on the notebook tab).
        """

        ### prev_page = self.notebook.GetPage(event.GetOldSelection())
        ### print "*** OnPageChanged:", event.GetOldSelection(),
        ###                             event.GetSelection()
        curr_page = self.notebook.GetPage(event.GetSelection())
        curr_page.active_page()
        event.Skip()


    def OnLoadDemoModel1(self, event):
        """Loads Demo Model 1 from a resource file."""

        self.page0.OnLoadDemoModel1(event)
        self.notebook.SetSelection(0)


    def OnLoadDemoModel2(self, event):
        """Loads Demo Model 2 from a resource file."""

        self.page0.OnLoadDemoModel2(event)
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

#==============================================================================

class SimulateDataPage(wx.Panel):
    """
    This class implements phase reconstruction and direct inversion analysis
    of two simulated surround variation data sets (generated from a model)
    to produce a scattering length density profile of the sample.
    """

    def __init__(self, parent, id=wx.ID_ANY, colour="", fignum=0, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)

        self.fignum=fignum
        self.SetBackgroundColour(colour)
        self.app_root_dir = get_appdir()

        # Split the panel to separate the input fields from the plots.
        # wx.SP_LIVE_UPDATE can be omitted to disable repaint as sash is moved.
        sp = wx.SplitterWindow(self, style=wx.SP_3D|wx.SP_LIVE_UPDATE)
        sp.SetMinimumPaneSize(100)

        # Create display panels as children of the splitter.
        self.pan1 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan1.SetBackgroundColour(colour)
        self.pan2 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan2.SetBackgroundColour("WHITE")

        self.init_param_panel()
        self.init_plot_panel()

        # Attach the child panels to the splitter.
        sp.SplitVertically(self.pan1, self.pan2, sashPosition=310)
        sp.SetSashGravity(0.2)  # on resize grow mostly on right side

        # Put the splitter in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_param_panel(self):
        """Initializes the parameter input panel of the SimulateDataPage."""

        #----------------------------
        # Section 1: Model Parameters
        #----------------------------

        # Create instructions for using the model description input box.
        line1 = wx.StaticText(self.pan1, wx.ID_ANY,
                    label="Define the Surface, Sample, and Substrate")
        line2 = wx.StaticText(self.pan1, wx.ID_ANY,
                    label="layers of your model (one layer per line):")
        #line3 = wx.StaticText(self.pan1, wx.ID_ANY,
        #           label="    as shown below (roughness defaults to 0):")

        demo_model_params = \
            "# SLDensity  Thickness  Roughness (optional)" + \
            NEWLINES_2 + NEWLINES_2 + NEWLINES_2 + NEWLINE

        # Create an input box to enter and edit the model description and
        # populate it with a header but no layer information.
        # Note that the number of lines determines the height of the box.
        # TODO: create a model edit box with a min-max height.
        self.model = wx.TextCtrl(self.pan1, wx.ID_ANY, value=demo_model_params,
                         style=wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.RAISED_BORDER)
        self.model.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        # Group model parameter widgets into a labelled section and
        # manage them with a static box sizer.
        sbox1 = wx.StaticBox(self.pan1, wx.ID_ANY, "Model Parameters")
        sbox1_sizer = wx.StaticBoxSizer(sbox1, wx.VERTICAL)
        sbox1_sizer.Add(line1, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sbox1_sizer.Add(line2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        #sbox1_sizer.Add(line3, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sbox1_sizer.Add((10,4), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sbox1_sizer.Add(self.model, 1,
                        wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border=10)

        #---------------------------------
        # Section 2: Instrument Parameters
        #---------------------------------

        self.instr_param = InstrumentParameters()

        # Create a panel for gathering instrument metadata.
        self.pan12 = wx.Panel(self.pan1, wx.ID_ANY, style=wx.RAISED_BORDER)
        self.pan12.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        # Present a combobox with instrument choices.
        cb_label = wx.StaticText(self.pan12, wx.ID_ANY, "Choose Instrument:")
        instr_names = self.instr_param.get_instr_names()
        cb = wx.ComboBox(self.pan12, wx.ID_ANY,
                         #value=instr_names[self.instr_param.get_instr_idx()],
                         value="",
                         choices=instr_names,
                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
        cb.SetBackgroundColour(PALE_YELLOW)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, cb)
        self.instr_cb = cb

        # Create a horizontal box sizer for the combo box and its label.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(cb_label, 0,
            wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT,
            border=10)
        hbox1_sizer.Add(cb, 1, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Associate the sizer with its container.
        self.pan12.SetSizer(hbox1_sizer)
        hbox1_sizer.Fit(self.pan12)

        # Create button controls.
        self.btn_edit = wx.Button(self.pan1, wx.ID_ANY, "Edit")
        self.Bind(wx.EVT_BUTTON, self.OnEdit, self.btn_edit)
        self.btn_reset = wx.Button(self.pan1, wx.ID_ANY, "Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, self.btn_reset)

        # Create a horizontal box sizer for the buttons.
        hbox2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox2_sizer.Add((10,20), 1)  # stretchable whitespace
        hbox2_sizer.Add(self.btn_edit, 0)
        hbox2_sizer.Add((10,20), 0)  # non-stretchable whitespace
        hbox2_sizer.Add(self.btn_reset, 0)

        # Group instrument metadata widgets into a labelled section and
        # manage them with a static box sizer.
        sbox2 = wx.StaticBox(self.pan1, wx.ID_ANY, "Resolution Parameters")
        sbox2_sizer = wx.StaticBoxSizer(sbox2, wx.VERTICAL)
        sbox2_sizer.Add(self.pan12, 0,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sbox2_sizer.Add(hbox2_sizer, 0, wx.EXPAND|wx.ALL, border=10)

        #---------------------------------------------------
        # Section 3: Inversion and Reconstruction Parameters
        #---------------------------------------------------

        fields = [
                ###["SLD of Substrate:", 2.07, "float", 'RE', None],
                   ["SLD of Surface for Exp 1:", None, "float", 'RE', None],
                   ["SLD of Surface for Exp 2:", None, "float", 'RE', None],
                ###["Sample Thickness:", 1000, "float", 'RE', None],
                   ["Qmin:", 0.0, "float", 'RE', None],
                   ["Qmax:", 0.4, "float", 'RE', None],
                   ["# Profile Steps:", 128, "int", 'RE', None],
                   ["Over Sampling Factor:", 4, "int", 'REL', None],
                   ["# Inversion Iterations:", 6, "int", 'RE', None],
                   ["# Monte Carlo Trials:", 10, "int", 'RE', None],
                   ["Simulated Noise (as %):", 5.0, "float", 'RE', None],
                   ["Bound State Energy:", 0.0, "float", 'RE', None],
                   ["Perfect Reconstruction:", "False", "str", 'CRE',
                        ("True", "False")],
                ###["Cosine Transform Smoothing:", 0.0, "float", 'RE', None],
                ###["Back Reflectivity:", "True", "str", 'CRE', ("True", "False")],
                ###["Inversion Noise Factor:", 1, "int", 'RE', None],
                ###["Show Iterations:", "False", "str", 'CRE', ("True", "False")]
                ###["Monitor:", "", "str", 'RE', None]
                 ]

        self.inver_param = InputListPanel(parent=self.pan1, itemlist=fields,
                                          align=True)

        # Group inversion parameter widgets into a labelled section and
        # manage them with a static box sizer.
        sbox3 = wx.StaticBox(self.pan1, wx.ID_ANY, "Inversion Parameters")
        sbox3_sizer = wx.StaticBoxSizer(sbox3, wx.VERTICAL)
        sbox3_sizer.Add(self.inver_param, 1,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)

        #---------------------------
        # Section 4: Control Buttons
        #---------------------------

        # Create radio buttons to enable/disable resolution calculation.
        calc_reso = wx.StaticText(self.pan1, wx.ID_ANY,
                                  label="With Resolution:  ")
        calc_reso.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        self.radio1 = wx.RadioButton(self.pan1, wx.ID_ANY, "Yes  ",
                                style=wx.RB_GROUP)
        self.radio2 = wx.RadioButton(self.pan1, wx.ID_ANY, "No")
        self.radio1.SetBackgroundColour(WINDOW_BKGD_COLOUR)
        self.radio2.SetBackgroundColour(WINDOW_BKGD_COLOUR)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnCalcResoSelect, self.radio1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnCalcResoSelect, self.radio2)

        grid1 = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid1.Add(self.radio1, 0, wx.ALIGN_CENTER)
        grid1.Add(self.radio2, 0, wx.ALIGN_CENTER)

        sbox4 = wx.StaticBox(self.pan1, wx.ID_ANY, "")
        sbox4_sizer = wx.StaticBoxSizer(sbox4, wx.HORIZONTAL)
        sbox4_sizer.Add(calc_reso, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sbox4_sizer.Add(grid1, 0, wx.ALIGN_CENTER_VERTICAL)

        # Create the Compute button.
        self.btn_compute = wx.Button(self.pan1, wx.ID_ANY, "Compute")
        self.Bind(wx.EVT_BUTTON, self.OnCompute, self.btn_compute)

        # Create a horizontal box sizer for the buttons.
        hbox3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox3_sizer.Add(sbox4_sizer, 0)
        hbox3_sizer.Add((10,20), 1)  # stretchable whitespace
        hbox3_sizer.Add(self.btn_compute, 0, wx.TOP, border=6)

        #----------------------------------------
        # Manage all of the widgets in the panel.
        #----------------------------------------

        # Put all section sizers in a vertical box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbox1_sizer, 2, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox2_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox3_sizer, 3, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(hbox3_sizer, 0, wx.EXPAND|wx.BOTTOM|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan1.SetSizer(sizer)
        sizer.Fit(self.pan1)

        # Set flag to indicate that resolution will be calculated for a
        # simulation operation.
        self.calc_resolution = True


    def init_plot_panel(self):
        """Initializes the plotting panel of the SimulateDataPage."""

        INTRO_TEXT = "Phase Reconstruction and Inversion of Simulated Data:"

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the FigureCanvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(self.pan2, wx.ID_ANY, figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for pylab so that when
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

        # Display a title above the plots.
        self.pan2_intro_text = INTRO_TEXT
        self.pan2_intro = wx.StaticText(self.pan2, wx.ID_ANY, label=INTRO_TEXT)
        font = self.pan2_intro.GetFont()
        font.SetPointSize(font.GetPointSize() + 1)
        font.SetWeight(wx.BOLD)
        self.pan2_intro.SetFont(font)

        # Create a progress bar to be displayed during a lengthy computation.
        self.pan2_gauge = WorkingIndicator(self.pan2)
        self.pan2_gauge.Show(False)

        # Create a horizontal box sizer to hold the title and progress bar.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(self.pan2_intro, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox1_sizer.Add((10,25), 1)  # stretchable whitespace
        hbox1_sizer.Add(self.pan2_gauge, 0)

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hbox1_sizer, 0, wx.EXPAND|wx.ALL, border=10)
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


    def OnCalcResoSelect(self, event):
        """Process the With Resolution radio button select event."""

        radio_selected = event.GetEventObject()
        if self.radio1 is radio_selected:
            self.radio1.SetValue(True)
            self.radio2.SetValue(False)
            self.pan12.Enable(True)
            self.btn_edit.Enable(True)
            self.btn_reset.Enable(True)
            self.calc_resolution = True
        else:
            self.radio2.SetValue(True)
            self.radio1.SetValue(False)
            self.pan12.Enable(False)
            self.btn_edit.Enable(False)
            self.btn_reset.Enable(False)
            self.calc_resolution = False


    def OnComboBoxSelect(self, event):
        """Processes the user's choice of instrument."""

        sel = event.GetEventObject().GetSelection()
        self.instr_param.set_instr_idx(sel)
        event.GetEventObject().SetBackgroundColour("WHITE")

        # Show the instrument data to the user and allow edits.
        self.instr_param.edit_metadata()


    def OnCompute(self, event):
        """
        Generates a simulated dataset then performs phase reconstruction and
        phase inversion on the data in a separate thread.  OnComputeEnd is
        called when the computation is finished to plot the results.
        """

        #---------------------------------
        # Step 1: Process Model Parameters
        #---------------------------------

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
                temp = [float(ln[0]), float(ln[1]), float(ln[2])]
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

        #-------------------------------------
        # Step 2: Process Inversion Parameters
        #-------------------------------------

        # Explicitly validate all inversion parameters before proceeding.  The
        # panel's Validate method will invoke all validators associated with
        # its top-level input objects and transfer data from them.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the Compute button without
        # making the corrections, so a full validation pass must be done now.
        if not self.inver_param.Validate():
            display_error_message(self, "Data Entry Error", DATA_ENTRY_ERRMSG)
            return

        # Get the validated inversion parameters.
        params = self.inver_param.GetResults()
        if len(sys.argv) > 1 and '-tracep' in sys.argv[1:]:
            print ">>> Simulation parameters:"; print params

        sample = layers[1:-1]
        params.append(layers[-1][0])  # add SLD of substrate to list
        params.append(layers[-1][2])  # add roughness of substrate to list
        if len(sys.argv) > 1 and '-tracep' in sys.argv[1:]:
            print ">>> Model parameters (all layers):"; print layers
            print ">>> Sample layers excluding Surround:"; print sample

        #---------------------------------------------------------------
        # Step 3: Process Instrument Parameters and Calculate Resolution
        #---------------------------------------------------------------

        # Get the instrument parameter class and obtain the class that defines
        # the selected instrument.
        ip = self.instr_param
        classes = ip.get_instr_classes()
        classname = classes[ip.get_instr_idx()]

        # If the user has chosen to disable resolution calculation, then we are
        # done with this step.
        if not self.calc_resolution:
            Q = None
            dQ = None

        # Check to see if an instrument has been specified.
        elif ip.get_instr_idx() < 0:
            display_error_message(self, "Choose an Instrument",
                                        INSTR_CALC_RESO_ERRMSG)
            return

        # For a monochromatic instrument, get its parameters and calculate
        # resolution.
        elif ip.get_instr_idx() <= 3:
            wavelength = ip.get_wavelength()
            dLoL = ip.get_dLoL()
            d_s1 = ip.get_d_s1()
            d_s2 = ip.get_d_s2()
            Tlo = ip.get_Tlo()
            Thi = ip.get_Thi()
            slit1_at_Tlo = ip.get_slit1_at_Tlo()
            slit2_at_Tlo = ip.get_slit2_at_Tlo()
            slit1_below = ip.get_slit1_below()
            slit2_below = ip.get_slit2_below()
            slit1_above = ip.get_slit1_above()
            slit2_above = ip.get_slit2_above()
            sample_width = ip.get_sample_width()
            sample_broadening = ip.get_sample_broadening()

            # Calculate the resolution of the instrument.  Specifically compute
            # the resolution vector dQ for given values of a Q vector based on
            # L, dL, T, and dT.  We do not have all of the input data directly
            # (for instance we know L (wavelength) but not dT), however, the
            # required parameters can be determined by the resolution method
            # from the instrument geometry.  At a minimum, we need to supply
            # L, dLoL, d_s1, d_s2, Tlo, and slits_at_Tlo.

            # First, transform some of the data into the format required by
            # the resolution method and in all cases avoid passing a datatype
            # of None directly or indirectly as part of a tuple.
            slits_at_Tlo = (slit1_at_Tlo, slit2_at_Tlo)
            if slit2_at_Tlo is None: slits_at_Tlo = slit1_at_Tlo
            slits_below = (slit1_below, slit2_below)
            if slit2_below is None: slits_below = slit1_below
            slits_above = (slit1_above, slit2_above)
            if slit2_above is None: slits_above = slit1_above
            if sample_width is None: sample_width = 1e10  # set to a large value
            if sample_broadening is None: sample_broadening = 0.0

            if (wavelength is None or
                dLoL is None or
                d_s1 is None or
                d_s2 is None or
                Tlo is None or
                slits_at_Tlo is None):
                display_error_message(self, "Need Instrument Parameters",
                                      INSTR_PARAM_ERRMSG)
                return

            # Define the reflectometer.
            instrument = classname(wavelength=wavelength,
                                   dLoL=dLoL,
                                   d_s1=d_s1,
                                   d_s2=d_s2,
                                   Tlo=Tlo,
                                   Thi=Thi,
                                   slits_at_Tlo=slits_at_Tlo,
                                   slits_below=slits_below,
                                   slits_above=slits_above,
                                   sample_width=sample_width,
                                   sample_broadening=sample_broadening)

            # Compute the resolution.
            Q = numpy.linspace(params[2], params[3], params[4])
            res = instrument.resolution(Q=Q)
            Q = res.Q
            dQ = res.dQ

        # For a monochromatic instrument, get its parameters and calculate
        # resolution.
        elif ip.get_instr_idx() > 3:
            wavelength_lo = ip.get_wavelength_lo()
            wavelength_hi = ip.get_wavelength_hi()
            dLoL = ip.get_dLoL()
            slit1_size = ip.get_slit1_size()
            slit2_size = ip.get_slit2_size()
            d_s1 = ip.get_d_s1()
            d_s2 = ip.get_d_s2()
            T = ip.get_T()
            sample_width = ip.get_sample_width()
            sample_broadening = ip.get_sample_broadening()

            # Calculate the resolution of the instrument.  Specifically compute
            # the resolution vector dQ for given values of a Q vector.

            # First, transform some of the data into the format required by
            # the resolution method and in all cases avoid passing a datatype
            # of None directly or indirectly as part of a tuple.
            wavelength = (wavelength_lo, wavelength_hi)
            slits = (slit1_size, slit2_size)
            if slit2_size is None: slits = slit1_size
            if sample_width is None: sample_width = 1e10  # set to a large value
            if sample_broadening is None: sample_broadening = 0.0

            if (wavelength is None or
                dLoL is None or
                d_s1 is None or
                d_s2 is None or
                T is None or
                slits is None):
                display_error_message(self, "Need Instrument Parameters",
                                      INSTR_PARAM_ERRMSG)
                return

            # Define the reflectometer.
            instrument = classname(wavelength=wavelength,
                                   dLoL=dLoL,
                                   d_s1=d_s1,
                                   d_s2=d_s2,
                                   T=T,
                                   slits=slits,
                                   sample_width=sample_width,
                                   sample_broadening=sample_broadening)

            # Compute the resolution.
            L = bins(wavelength[0], wavelength[1], dLoL)
            dL = binwidths(L)
            '''
            Q = numpy.linspace(params[2], params[3], params[4])
            res = instrument.resolution(Q=Q, L=L, dL=dL)
            print "*** len of Q, res.Q, res.dQ, L:",
            print len(Q), len(res.Q), len(res.dQ), len(L)
            '''
            res = instrument.resolution(L=L, dL=dL)
            Q = res.Q
            dQ = res.dQ
            # FIXME: perform_simulation fails if either Q or dQ is not None
            Q = None
            dQ = None

        #--------------------------------------------------------------
        # Step 4: Perform the Simulation, Reconstruction, and Inversion
        #--------------------------------------------------------------

        # Hide widgets that can change the active plotting canvas or initiate
        # another compute operation before we're finished with the current one.
        self.btn_compute.Enable(False)
        frame = wx.FindWindowByName("AppFrame")
        frame.load_demo_dataset_1_item.Enable(False)
        frame.load_demo_dataset_2_item.Enable(False)

        # Inform the user that we're starting the computation.
        write_to_statusbar("Generating new plots ...", 1)
        write_to_statusbar("", 2)

        # Display the progress gauge.
        self.pan2_gauge.Start()
        self.pan2_gauge.Show(True)
        self.pan2.Layout()

        # Keep track of the time it takes to do the computation and plotting.
        self.t0 = time.time()

        # Set the plotting figure manager for this class as the active one and
        # erase the current figure.
        _pylab_helpers.Gcf.set_active(self.fm)
        pylab.clf()
        pylab.draw()

        # Apply phase reconstruction and direct inversion techniques on the
        # experimental reflectivity datasets.
        try:
            ExecuteInThread(self.OnComputeEnd, perform_simulation,
                            sample, params, Q=Q, dQ=dQ)
        except Exception, e:
            display_error_message(self, "Operation Failed", str(e))
            return
        else:
            self.pan2_intro.SetLabel(self.pan2_intro_text)
            self.pan2_intro.Refresh()


    def OnComputeEnd(self, delayedResult):
        """
        Callback function that plots the results of a phase reconstruction and
        phase inversion operation.
        """

        # The delayedResult object is not used to get the results because
        # currently no results are passed back; instead plots are generated.

        # Stop and hide the progress gauge.
        self.pan2_gauge.Stop()
        self.pan2_gauge.Show(False)
        self.pan2.Layout()

        # Make the plots visible.
        pylab.draw()

        # Write the total execution and plotting time to the status bar.
        secs = time.time() - self.t0
        write_to_statusbar("Plots updated", 1)
        write_to_statusbar("%g secs" %(secs), 2)

        # Show widgets previously hidden at the start of this computation.
        self.btn_compute.Enable(True)
        frame = wx.FindWindowByName("AppFrame")
        frame.load_demo_dataset_1_item.Enable(True)
        frame.load_demo_dataset_2_item.Enable(True)


    def OnEdit(self, event):
        """Shows the instrument metadata to the user and allows editing."""

        if self.instr_param.get_instr_idx() < 0:
            display_warning_message(self, "Select an Instrument",
                "Please select an instrument from the drop down list.")
            return
        self.instr_param.edit_metadata()


    def OnReset(self, event):
        """
        Restores default parameters for the currently selected instrument.
        """
        self.instr_param.init_metadata()


    def OnLoadDemoModel1(self, event):
        """Loads Demo Model 1 from a file."""

        filespec = os.path.join(self.app_root_dir, DEMO_MODEL1_DESC)

        # Read the entire input file into a buffer.
        try:
            fd = open(filespec, 'rU')
            demo_model_params = fd.read()
            fd.close()
        except:
            display_warning_message(self, "Load Model Error",
                "Error loading demo model from file "+DEMO_MODEL1_DESC)
            return

        # Replace the contents of the model parameter text control box with
        # the data from the file.
        self.model.Clear()
        self.model.SetValue(demo_model_params)

        # Specify the instrument (NG-1) and set missing required parameters
        # that do not have default values.
        self.instr_param.set_instr_idx(1)
        self.instr_param.set_Tlo(0.5)
        self.instr_param.set_slit1_at_Tlo(0.2)
        self.instr_param.set_slit1_below(0.1)

        # Put the instrument name in the combo box.
        # Note: set background colour before setting the value to update both.
        self.instr_cb.SetBackgroundColour("WHITE")
        self.instr_cb.SetValue(self.instr_param.get_instr_names()[1])

        # Set surface SLD values for experiments 1 and 2 in the inversion and
        # reconstruction paramaters panel.
        # Note that datatype of None means do not change.
        plist = (0.0, 4.5,
                 None, None, None, None, None, None, None, None, None)
        self.inver_param.update_items_in_panel(plist)


    def OnLoadDemoModel2(self, event):
        """Loads Demo Model 2 from a file."""

        filespec = os.path.join(self.app_root_dir, DEMO_MODEL2_DESC)

        # Read the entire input file into a buffer.
        try:
            fd = open(filespec, 'rU')
            demo_model_params = fd.read()
            fd.close()
        except:
            display_warning_message(self, "Load Model Error",
                "Error loading demo model from file "+DEMO_MODEL2_DESC)
            return

        # Replace the contents of the model parameter text control box with
        # the data from the file.
        self.model.Clear()
        self.model.SetValue(demo_model_params)

        # Specify the instrument (Liquids) and set missing required parameters
        # that do not have default values.
        self.instr_param.set_instr_idx(4)
        self.instr_param.set_T(4.0)
        self.instr_param.set_slit1_size(0.8)
        self.instr_param.set_slit2_size(0.8)

        # Put the instrument name in the combo box.
        # Note: set background colour before setting the value to update both.
        self.instr_cb.SetBackgroundColour("WHITE")
        self.instr_cb.SetValue(self.instr_param.get_instr_names()[4])

        # Set surface SLD values for experiments 1 and 2 in the inversion and
        # reconstruction paramaters panel.
        # Note that datatype of None means do not change.
        plist = (0.0, 6.33,
                 None, None, None, None, None, None, None, None, None)
        self.inver_param.update_items_in_panel(plist)


    def OnLoadModel(self, event):
        """Loads the Model from a file."""

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


    def OnSaveModel(self, event):
        """Saves the  Model to a file."""

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

class AnalyzeDataPage(wx.Panel):
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
        self.app_root_dir = get_appdir()

        # Split the panel to separate the input fields from the plots.
        # wx.SP_LIVE_UPDATE can be omitted to disable repaint as sash is moved.
        sp = wx.SplitterWindow(self, style=wx.SP_3D|wx.SP_LIVE_UPDATE)
        sp.SetMinimumPaneSize(100)

        # Create display panels as children of the splitter.
        self.pan1 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan1.SetBackgroundColour(colour)
        self.pan2 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan2.SetBackgroundColour("WHITE")

        self.init_param_panel()
        self.init_plot_panel()

        # Attach the panels to the splitter.
        sp.SplitVertically(self.pan1, self.pan2, sashPosition=310)
        sp.SetSashGravity(0.2)  # on resize grow mostly on right side

        # Put the splitter in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_param_panel(self):
        """Initializes the parameter input panel of the AnalyzeDataPage."""

        #----------------------------
        # Section 1: Input Data Files
        #----------------------------

        # Create a panel for obtaining input file selections.
        self.pan11 = wx.Panel(self.pan1, wx.ID_ANY, style=wx.RAISED_BORDER)
        self.pan11.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        # Create file name entry boxes and labels.
        label1 = wx.StaticText(self.pan11, wx.ID_ANY, label="File 1:")
        label2 = wx.StaticText(self.pan11, wx.ID_ANY, label="File 2:")

        self.TCfile1 = wx.TextCtrl(self.pan11, wx.ID_ANY, value="",
                                   style=wx.TE_RIGHT)
        self.TCfile1.SetBackgroundColour(PALE_YELLOW)
        self.TCfile2 = wx.TextCtrl(self.pan11, wx.ID_ANY, value="",
                                   style=wx.TE_RIGHT)
        self.TCfile2.SetBackgroundColour(PALE_YELLOW)

        # Create file selector button controls.
        # Match the button height to the text box height. Using y = -1 on
        # Windows does this, but not on Linux where the button height is larger.
        x, y = self.TCfile1.GetSizeTuple()
        btn_sel1 = wx.Button(self.pan11, wx.ID_ANY, "...", size=(30, y))
        self.Bind(wx.EVT_BUTTON, self.OnSelectFile1, btn_sel1)
        x, y = self.TCfile2.GetSizeTuple()
        btn_sel2 = wx.Button(self.pan11, wx.ID_ANY, "...", size=(30, y))
        self.Bind(wx.EVT_BUTTON, self.OnSelectFile2, btn_sel2)

        # Create horizontal box sizers for the file selection widgets.
        hbox4_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox4_sizer.Add(label1, 0, border=5,
                        flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
        hbox4_sizer.Add(self.TCfile1, 1, wx.EXPAND|wx.RIGHT, border=10)
        hbox4_sizer.Add(btn_sel1, 0)
        hbox5_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox5_sizer.Add(label2, 0, border=5,
                        flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
        hbox5_sizer.Add(self.TCfile2, 1, wx.EXPAND|wx.RIGHT, border=10)
        hbox5_sizer.Add(btn_sel2, 0)

        # Create a vertical box sizer for the input file selectors.
        vbox1_sizer = wx.BoxSizer(wx.VERTICAL)
        vbox1_sizer.Add(hbox4_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT,
                        border=10)
        vbox1_sizer.Add(hbox5_sizer, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan11.SetSizer(vbox1_sizer)
        vbox1_sizer.Fit(self.pan11)

        # Group file selection widgets into a labelled section and
        # manage them with a static box sizer.
        sbox1 = wx.StaticBox(self.pan1, wx.ID_ANY, "Reflectometry Data Files")
        sbox1_sizer = wx.StaticBoxSizer(sbox1, wx.VERTICAL)
        sbox1_sizer.Add(self.pan11, 0, wx.EXPAND|wx.ALL, border=10)

        #---------------------------------
        # Section 2: Instrument Parameters
        #---------------------------------

        self.instr_param = InstrumentParameters()

        # Create a panel for gathering instrument metadata.
        self.pan12 = wx.Panel(self.pan1, wx.ID_ANY, style=wx.RAISED_BORDER)
        self.pan12.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        # Present a combobox with instrument choices.
        cb_label = wx.StaticText(self.pan12, wx.ID_ANY, "Choose Instrument:")
        instr_names = self.instr_param.get_instr_names()
        cb = wx.ComboBox(self.pan12, wx.ID_ANY,
                         #value=instr_names[self.instr_param.get_instr_idx()],
                         value="",
                         choices=instr_names,
                         style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, cb)
        cb.SetBackgroundColour(PALE_YELLOW)
        self.instr_cb = cb

        # Create a horizontal box sizer for the combo box and its label.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(cb_label, 0,
            wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT,
            border=10)
        hbox1_sizer.Add(cb, 1, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, border=10)

        # Associate the sizer with its container.
        self.pan12.SetSizer(hbox1_sizer)
        hbox1_sizer.Fit(self.pan12)

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
        sbox2 = wx.StaticBox(self.pan1, wx.ID_ANY, "Resolution Parameters")
        sbox2_sizer = wx.StaticBoxSizer(sbox2, wx.VERTICAL)
        sbox2_sizer.Add(self.pan12, 0,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sbox2_sizer.Add(hbox2_sizer, 0, wx.EXPAND|wx.ALL, border=10)

        #---------------------------------------------------
        # Section 3: Inversion and Reconstruction Parameters
        #---------------------------------------------------

        fields = [ ["SLD of Surface for Exp 1:", None, "float", 'RE', None],
                   ["SLD of Surface for Exp 2:", None, "float", 'RE', None],
                   ["SLD of Substrate:", None, "float", 'RE', None],
                   ["Sample Thickness:", None, "float", 'RE', None],
                   ["Qmin:", 0.0, "float", 'RE', None],
                   ["Qmax:", None, "float", 'E', None],
                   ["# Profile Steps:", 128, "int", 'RE', None],
                   ["Over Sampling Factor:", 4, "int", 'REL', None],
                   ["# Inversion Iterations:", 6, "int", 'RE', None],
                   ["# Monte Carlo Trials:", 10, "int", 'RE', None],
                   ["Bound State Energy:", 0.0, "float", 'RE', None],
                ###["Cosine Transform Smoothing:", 0.0, "float", 'RE', None],
                ###["Back Reflectivity:", "True", "str", 'C', ("True", "False")],
                ###["Inversion Noise Factor:", 1, "int", 'RE', None],
                ###["Show Iterations:", "False", "str", ,'CRE', ("True", "False")]
                ###["Monitor:", "", "str", 'RE', None]
                 ]

        self.inver_param = InputListPanel(parent=self.pan1, itemlist=fields,
                                          align=True)

        # Group inversion parameter widgets into a labelled section and
        # manage them with a static box sizer.
        sbox3 = wx.StaticBox(self.pan1, wx.ID_ANY, "Inversion Parameters")
        sbox3_sizer = wx.StaticBoxSizer(sbox3, wx.VERTICAL)
        sbox3_sizer.Add(self.inver_param, 1,
                        wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)

        #---------------------------
        # Section 4: Control Buttons
        #---------------------------

        # Create the Compute button.
        self.btn_compute = wx.Button(self.pan1, wx.ID_ANY, "Compute")
        self.Bind(wx.EVT_BUTTON, self.OnCompute, self.btn_compute)

        # Create a horizontal box sizer for the buttons.
        hbox3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox3_sizer.Add((10,20), 1)  # stretchable whitespace
        hbox3_sizer.Add(self.btn_compute, 0)

        #----------------------------------------
        # Manage all of the widgets in the panel.
        #----------------------------------------

        # Put all section sizers in a vertical box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbox1_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox2_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(sbox3_sizer, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(hbox3_sizer, 0, wx.EXPAND|wx.BOTTOM|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan1.SetSizer(sizer)
        sizer.Fit(self.pan1)


    def init_plot_panel(self):
        """Initializes the plotting panel of the AnalyzeDataPage."""

        INTRO_TEXT = "Phase Reconstruction and Inversion of Experimental Data:"

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the FigureCanvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(self.pan2, wx.ID_ANY, figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for pylab so that when
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

        # Display a title above the plots.
        self.pan2_intro_text = INTRO_TEXT
        self.pan2_intro = wx.StaticText(self.pan2, wx.ID_ANY, label=INTRO_TEXT)
        font = self.pan2_intro.GetFont()
        font.SetPointSize(font.GetPointSize() + 1)
        font.SetWeight(wx.BOLD)
        self.pan2_intro.SetFont(font)

        # Create a progress bar to be displayed during a lengthy computation.
        self.pan2_gauge = WorkingIndicator(self.pan2)
        self.pan2_gauge.Show(False)

        # Create a horizontal box sizer to hold the title and progress bar.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(self.pan2_intro, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox1_sizer.Add((10,25), 1)  # stretchable whitespace
        hbox1_sizer.Add(self.pan2_gauge, 0)

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hbox1_sizer, 0, wx.EXPAND|wx.ALL, border=10)
        sizer.Add(canvas, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(mpl_toolbar, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan2.SetSizer(sizer)
        sizer.Fit(self.pan2)


    def active_page(self):
        """This method is called when user selects (makes current) the page."""

        WHAT_TODO_NEXT = """\
Edit parameters then press the Compute button to generate a density profile \
from the data files."""
        write_to_statusbar(WHAT_TODO_NEXT, 0)
        write_to_statusbar("", 1)
        write_to_statusbar("", 2)


    def OnComboBoxSelect(self, event):
        """Processes the user's choice of instrument."""

        sel = event.GetEventObject().GetSelection()
        self.instr_param.set_instr_idx(sel)
        event.GetEventObject().SetBackgroundColour("WHITE")

        # Show the instrument data to the user and allow edits.
        self.instr_param.edit_metadata()


    def OnCompute(self, event):
        """
        Performs phase reconstruction and phase inversion on the datasets in a
        separate thread.  OnComputeEnd is called when the computation is
        finished to plot the results.
        """

        #-----------------------------------------
        # Step 1: Process Reflectometry Data Files
        #-----------------------------------------

        # Get the names of the data files.
        # Note that we must get the names from the text control box because the
        # user may have edited the names directly and not used the file
        # selection dialog box (or edited after using the file selection box).
        files = [self.TCfile1.GetValue(), self.TCfile2.GetValue()]

        # Verfiy that the user has selected two reflectivity data files.
        if files[0] == "" or files[1] == "":
            display_warning_message(self, "Specify a Dataset",
            "Please specify the names of two reflectometry data files to use.")
            return

        # Make sure the files are accessible so we can display a proper error
        # message instead of getting a Python runtime error later on.
        try:
            fd = open(files[0], 'r')
            fd.close()
        except:
            display_error_message(self, "Load Data Error",
                "Cannot access file "+files[0])
            return

        try:
            fd = open(files[1], 'r')
            fd.close()
        except:
            display_error_message(self, "Load Data Error",
                "Cannot access file "+files[1])
            return

        #-------------------------------------
        # Step 2: Process Inversion Parameters
        #-------------------------------------

        # Explicitly validate all inversion parameters before proceeding.  The
        # panel's Validate method will invoke all validators associated with
        # its top-level input objects and transfer data from them.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the Compute button without
        # making the corrections, so a full validation pass must be done now.
        if not self.inver_param.Validate():
            display_error_message(self, "Data Entry Error", DATA_ENTRY_ERRMSG)
            return

        # Get the validated inversion parameters.
        params = self.inver_param.GetResults()
        if len(sys.argv) > 1 and '-tracep' in sys.argv[1:]:
            print ">>> Inversion parameters:"; print params

        #--------------------------------------
        # Step 3: Process Instrument Parameters
        #--------------------------------------

        # Get instrument parameters based on whether the instrument is
        # monochromatic or polychromatic.
        # Note that these parameters have already been validated.
        '''
        ip = self.instr_param
        if ip.get_instr_idx() <= 3:  # monocromatic
            wavelength = ip.get_wavelength()
            dLoL = ip.get_dLoL()
            d_s1 = ip.get_d_s1()
            d_s2 = ip.get_d_s2()
            Tlo = ip.get_Tlo()
            Thi = ip.get_Thi()
            slit1_at_Tlo = ip.get_slit1_at_Tlo()
            slit2_at_Tlo = ip.get_slit2_at_Tlo()
            slit1_below = ip.get_slit1_below()
            slit2_below = ip.get_slit2_below()
            slit1_above = ip.get_slit1_above()
            slit2_above = ip.get_slit2_above()
            sample_width = ip.get_sample_width()
            sample_broadening = ip.get_sample_broadening()
        else:  # polychromatic
            wavelength_lo = ip.get_wavelength_lo()
            wavelength_hi = ip.get_wavelength_hi()
            dLoL = ip.get_dLoL()
            slit1_size = ip.get_slit1_size()
            slit2_size = ip.get_slit2_size()
            d_s1 = ip.get_d_s1()
            d_s2 = ip.get_d_s2()
            T = ip.get_T()
            sample_width = ip.get_sample_width()
            sample_broadening = ip.get_sample_broadening()
            '''

        #-------------------------------------------------------
        # Step 4: Perform the Phase Reconstruction and Inversion
        #-------------------------------------------------------

        # Hide widgets that can change the active plotting canvas or initiate
        # another compute operation before we're finished with the current one.
        self.btn_compute.Enable(False)
        self.pan11.Enable(False)
        frame = wx.FindWindowByName("AppFrame")
        frame.load_demo_dataset_1_item.Enable(False)
        frame.load_demo_dataset_2_item.Enable(False)

        # Inform the user that we're starting the computation.
        write_to_statusbar("Generating new plots ...", 1)
        write_to_statusbar("", 2)

        # Display the progress gauge.
        self.pan2_gauge.Start()
        self.pan2_gauge.Show(True)
        self.pan2.Layout()

        # Keep track of the time it takes to do the computation and plotting.
        self.t0 = time.time()

        # Set the plotting figure manager for this class as the active one and
        # erase the current figure.
        _pylab_helpers.Gcf.set_active(self.fm)
        pylab.clf()
        pylab.draw()

        # Apply phase reconstruction and direct inversion techniques on the
        # experimental reflectivity datasets.
        try:
            #perform_recon_inver(files, params)
            ExecuteInThread(self.OnComputeEnd, perform_recon_inver,
                                               files, params)
        except Exception, e:
            display_error_message(self, "Operation Failed", str(e))
            return
        else:
            self.pan2_intro.SetLabel(self.pan2_intro_text)
            self.pan2_intro.Refresh()


    def OnComputeEnd(self, delayedResult):
        """
        Callback function that plots the results of a phase reconstruction and
        phase inversion operation.
        """

        # The delayedResult object is not used to get the results because
        # currently no results are passed back; instead plots are generated.

        # Stop and hide the progress gauge.
        self.pan2_gauge.Stop()
        self.pan2_gauge.Show(False)
        self.pan2.Layout()

        # Make the plots visible.
        pylab.draw()

        # Write the total execution and plotting time to the status bar.
        secs = time.time() - self.t0
        write_to_statusbar("Plots updated", 1)
        write_to_statusbar("%g secs" %(secs), 2)

        # Show widgets previously hidden at the start of this computation.
        self.btn_compute.Enable(True)
        self.pan11.Enable(True)
        frame = wx.FindWindowByName("AppFrame")
        frame.load_demo_dataset_1_item.Enable(True)
        frame.load_demo_dataset_2_item.Enable(True)


    def OnEdit(self, event):
        """Shows the instrument metadata to the user and allows editing."""

        if self.instr_param.get_instr_idx() < 0:
            display_warning_message(self, "Select an Instrument",
                "Please select an instrument from the drop down list.")
            return
        self.instr_param.edit_metadata()


    def OnLoadDemoDataset1(self, event):
        """Loads demo 1 reflectometry data files for measurements 1 and 2."""

        # Locate the demo data files.
        datafile_1 = os.path.join(self.app_root_dir, DEMO_REFLDATA1_1)
        datafile_2 = os.path.join(self.app_root_dir, DEMO_REFLDATA1_2)

        # Store the file names in text control boxes and position text so that
        # the file name is visible even if the beginning of the path is not.
        self.TCfile1.SetBackgroundColour("WHITE")
        self.TCfile1.SetValue(datafile_1)
        self.TCfile1.SetInsertionPointEnd()
        self.TCfile2.SetBackgroundColour("WHITE")
        self.TCfile2.SetValue(datafile_2)
        self.TCfile2.SetInsertionPointEnd()

        # Specify the instrument (NG-1) and set missing required parameters
        # that do not have default values.
        self.instr_param.set_instr_idx(1)
        self.instr_param.set_Tlo(0.5)
        self.instr_param.set_slit1_at_Tlo(0.2)
        self.instr_param.set_slit1_below(0.1)

        # Put the instrument name in the combo box.
        # Note: set background colour before setting the value to update both.
        self.instr_cb.SetBackgroundColour("WHITE")
        self.instr_cb.SetValue(self.instr_param.get_instr_names()[1])

        # Set surface SLD values for experiments 1 and 2, the substrate SLD
        # value, the sample thickness, and Qmin in the inversion and
        # reconstruction paramaters panel.
        # Note that datatype of None means do not change.
        plist = (6.33, 0.0, 2.07, 1200, 0.014,
                 None, None, None, None, None, None)
        self.inver_param.update_items_in_panel(plist)

        # Generate the plots and display them.
        self.plot_dataset(datafile_1, datafile_2)


    def OnLoadDemoDataset2(self, event):
        """Loads demo 2 reflectometry data files for measurements 1 and 2."""

        # Locate the demo data files.
        datafile_1 = os.path.join(self.app_root_dir, DEMO_REFLDATA2_1)
        datafile_2 = os.path.join(self.app_root_dir, DEMO_REFLDATA2_2)

        # Store the file names in text control boxes and position text so that
        # the file name is visible even if the beginning of the path is not.
        self.TCfile1.SetBackgroundColour("WHITE")
        self.TCfile1.SetValue(datafile_1)
        self.TCfile1.SetInsertionPointEnd()
        self.TCfile2.SetBackgroundColour("WHITE")
        self.TCfile2.SetValue(datafile_2)
        self.TCfile2.SetInsertionPointEnd()

        # Specify the instrument (Liquids) and set missing required parameters
        # that do not have default values.
        self.instr_param.set_instr_idx(4)
        self.instr_param.set_T(4.0)
        self.instr_param.set_slit1_size(0.8)
        self.instr_param.set_slit2_size(0.8)

        # Put the instrument name in the combo box.
        # Note: set background colour before setting the value to update both.
        self.instr_cb.SetBackgroundColour("WHITE")
        self.instr_cb.SetValue(self.instr_param.get_instr_names()[4])

        # Set surface SLD values for experiments 1 and 2, the substrate SLD
        # value, the sample thickness, and Qmin in the inversion and
        # reconstruction paramaters panel.
        # Note that datatype of None means do not change.
        plist = (0.0, 6.33, 2.07, 400, 0.01,
                 None, None, None, None, None, None)
        self.inver_param.update_items_in_panel(plist)

        # Generate the plots and display them.
        self.plot_dataset(datafile_1, datafile_2)


    def OnReset(self, event):
        """Restores default parameters for the currently selected instrument."""
        self.instr_param.init_metadata()


    def OnSelectFile1(self, event):
        """Selects the first reflectometry data file."""

        # The user can select both file1 and file2 from the file dialog box
        # by using the shift or control key to pick two files.  The order in
        # which they are selected determines which is file1 and file2.
        dlg = wx.FileDialog(self,
                            message="Select 1st Data File",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=(REFL_FILES+"|"+DATA_FILES+"|"+
                                      TEXT_FILES+"|"+ALL_FILES),
                            style=wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        num_files = len(paths)
        if num_files > 2:
            display_error_message(self, "Too Many Files Selected",
                "You can only select two data files, please try again.")
            return
        elif num_files == 2:
            datafile_1 = paths[1]  # files are returned in reverse order!
            datafile_2 = paths[0]  # files are returned in reverse order!
            self.TCfile1.SetBackgroundColour("WHITE")
            self.TCfile1.SetValue(datafile_1)
            self.TCfile1.SetInsertionPointEnd()
            self.TCfile2.SetBackgroundColour("WHITE")
            self.TCfile2.SetValue(datafile_2)
            self.TCfile2.SetInsertionPointEnd()
        elif num_files == 1:
            datafile_1 = paths[0]
            self.TCfile1.SetBackgroundColour("WHITE")
            self.TCfile1.SetValue(datafile_1)
            self.TCfile1.SetInsertionPointEnd()

        # Generate the plots and display them.
        file1 = self.TCfile1.GetValue()
        file2 = self.TCfile2.GetValue()
        if len(file1) > 0 and len(file2) > 0:
            self.plot_dataset(file1, file2)


    def OnSelectFile2(self, event):
        """Selects the second reflectometry data file."""

        dlg = wx.FileDialog(self,
                            message="Select 2nd Data File",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=(REFL_FILES+"|"+DATA_FILES+"|"+
                                      TEXT_FILES+"|"+ALL_FILES),
                            style=wx.OPEN|wx.CHANGE_DIR)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        num_files = len(paths)
        if num_files == 1:
            datafile_2 = paths[0]
            self.TCfile2.SetBackgroundColour("WHITE")
            self.TCfile2.SetValue(datafile_2)
            self.TCfile2.SetInsertionPointEnd()

        # Generate the plots and display them.
        file1 = self.TCfile1.GetValue()
        file2 = self.TCfile2.GetValue()
        if len(file1) > 0 and len(file2) > 0:
            self.plot_dataset(file1, file2)


    def plot_dataset(self, file1, file2):
        """
        Plots the Q, R, and dR of the two data files.
        """

        # Set the plotting figure manager for this class as the active one and
        # erase the current figure.
        _pylab_helpers.Gcf.set_active(self.fm)
        pylab.clf()
        pylab.draw()

        # Make sure the files are accessible so we can display a proper error
        # message now.  This is a bit of overkill since load_data will also
        # open the files, but load_data will be replaced in the future.
        try:
            fd = open(file1, 'r')
            fd.close()
        except:
            display_error_message(self, "File Access Error",
                "Cannot access file "+file1)
            return

        try:
            fd = open(file2, 'r')
            fd.close()
        except:
            display_error_message(self, "File Access Error",
                "Cannot access file "+file2)
            return

        try:
            self.load_data(file1, file2)
        except ValueError, e:
            display_error_message(self, "Data File Error", str(e))
            return
        else:
            self.pan2_intro.SetLabel("Dataset Reflectivity Plots:")
            self.generate_plot()
            pylab.draw()


    def load_data(self, file1, file2):
        """
        Loads the data from files or alternatively from tuples of (Q,R) or
        (Q,R,dR), (Q,dQ,R,dR) or (Q,dQ,R,dR,L).

        This code is cloned from SurroundVariation._load().
        TODO: Replace this loader with a general purpose loader in development.
        """

        # This code assumes the following data file formats:
        # 2-column data: Q, R
        # 3-column data: Q, R, dR
        # 4-column data: Q, dQ, R, dR
        # 5-column data: Q, dQ, R, dR, Lambda
        if isinstance(file1, basestring):
            d1 = numpy.loadtxt(file1).T
            name1 = file1
        else:
            d1 = file1
            name1 = "data1"

        if isinstance(file2, basestring):
            d2 = numpy.loadtxt(file2).T
            name2 = file2
        else:
            d2 = file2
            name2 = "data2"

        ncols = len(d1)
        if ncols <= 1:
            raise ValueError("Data file has less than two columns.")
        elif ncols == 2:
            q1, r1 = d1[0:2]
            q2, r2 = d2[0:2]
            dr1 = dr2 = None
            dq1 = dq2 = None
        elif ncols == 3:
            q1, r1, dr1 = d1[0:3]
            q2, r2, dr2 = d2[0:3]
            dq1 = dq2 = None
        elif ncols == 4:
            q1, dq1, r1, dr1 = d1[0:4]
            q2, dq2, r2, dr2 = d2[0:4]
        elif ncols >= 5:
            q1, dq1, r1, dr1, lambda1 = d1[0:5]
            q2, dq2, r2, dr2, lanbda2 = d2[0:5]

        if not q1.shape == q2.shape or not all(q1==q2):
            raise ValueError("Q points do not match in data files.")

        # Note that q2, dq2, lambda1, and lambda2 are currently discarded.
        self.name1, self.name2 = name1, name2
        self.Qin, self.dQin = q1, dq1
        self.R1in, self.R2in = r1, r2
        self.dR1in, self.dR2in = dr1, dr2


    def generate_plot(self):
        """Plot Q vs R and uncertainly dR if available."""

        '''
        # This simpler version of the function does not handle negative nor
        # very small values of dR gracefully that are sometimes found in
        # reflectivity files collected from real experiments.  Files qrd1.refl
        # and qrd2.refl have both of these issues that are clearly demonstrated
        # in the plots.
        def plot1(Q, R, dR, label, color, hold=True):
            #pylab.plot(Q, R, '.', label=label, color=color, hold=hold)
	        #pylab.gca().set_yscale('symlog', linthreshy=t, linwidthy=0.1)
            pylab.semilogy(Q, R, '.', label=label, color=color, hold=hold)
            if dR is not None:
                pylab.fill_between(Q, (R-dR), (R+dR),
                                       color=color, alpha=0.2, hold=True)
        '''

        def plot1(Q, R, dR, label, color, hold=True):
            # Generate a plot for one data file while trying to deal with bogus
            # negative values for dR or very small values for dR in a sensible
            # way.  This technique was developed by Paul Kienzle and will
            # likely be improved over time.
            if dR is not None:
                minR = numpy.min((R+dR))/10
            else:
                minR = numpy.min(R[R>0])/2

            pylab.semilogy(Q, numpy.maximum(R,minR), '.', label=label,
                              color=color, hold=hold)
            if dR is not None:
                idx = numpy.argsort(Q)
                pylab.fill_between(Q, numpy.maximum(R-dR,minR),
                                      numpy.maximum(R+dR,minR),
                                      color=color, alpha=0.2, hold=True)

        # Only show file.ext portion of the file specification on the plots.
        name1 = os.path.basename(self.name1)
        name2 = os.path.basename(self.name2)

        plot1(self.Qin, self.R1in, self.dR1in, name1, 'green', hold=False)
        plot1(self.Qin, self.R2in, self.dR2in, name2, 'blue', hold=True)

        pylab.legend(prop=FontProperties(size='medium'))
        pylab.ylabel('Reflectivity')
        pylab.xlabel('Q (inv A)')

#==============================================================================

class TestPlotPage(wx.Panel):
    """
    This class adds a page to the notebook for test purposes.
    """

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
        """Initializes the main panel of the TestPlotPage."""

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the FigureCanvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(self.pan1, wx.ID_ANY, figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for pylab so that when
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
        if len(sys.argv) > 1 and '-xtabs' in sys.argv[1:]:
            if (self.fignum == 4 and '-test1' in sys.argv[1:]): test1()
            if (self.fignum == 5 and '-test2' in sys.argv[1:]): test2()
        if self.fignum == 6: test3()
        if self.fignum == 7: test4(figure)


    def active_page(self):
        """This method is called when user selects (makes current) the page."""

        write_to_statusbar("", 0)
        write_to_statusbar("", 1)
        write_to_statusbar("", 2)

#==============================================================================

class InstrumentParameters():
    """
    This class is responsible for processing the instrument parameters
    (also known as instrument metadata) for all supporteds instruments.
    """

    def __init__(self):
        self.instr_classes = [ANDR, NG1, NG7, XRay, Liquids, Magnetic]
        self.instr_location = ["NCNR", "NCNR", "NCNR", "NCNR", "SNS", "SNS"]

        # Get the instrument name and radiation type for each instrument.
        self.instr_names = []; self.radiation = []
        for classname in self.instr_classes:
            self.instr_names.append(classname.instrument)
            self.radiation.append(classname.radiation)
        n = len(self.instr_classes)

        # Editable parameters are stored in 2 x n lists where list[0] contains
        # default values by instrument and list[1] holds their current values.
        # n is the number of instruments supported.  For a given instrument
        # only a subset of the parameters may be applicable.
        self.wavelength =        [[None] * n, [None] * n]  # monochromatic
        self.wavelength_lo =     [[None] * n, [None] * n]  # polychromatic
        self.wavelength_hi =     [[None] * n, [None] * n]  # polychromatic
        self.dLoL =              [[None] * n, [None] * n]  # both
        self.d_s1 =              [[None] * n, [None] * n]  # both
        self.d_s2 =              [[None] * n, [None] * n]  # both
        self.T =                 [[None] * n, [None] * n]  # polychromatic
        self.Tlo =               [[None] * n, [None] * n]  # monochromatic
        self.Thi =               [[None] * n, [None] * n]  # monochromatic
        self.slit1_size =        [[None] * n, [None] * n]  # polychromatic
        self.slit2_size =        [[None] * n, [None] * n]  # polychromatic
        self.slit1_at_Tlo =      [[None] * n, [None] * n]  # monochromatic
        self.slit2_at_Tlo =      [[None] * n, [None] * n]  # monochromatic
        self.slit1_below =       [[None] * n, [None] * n]  # monochromatic
        self.slit2_below =       [[None] * n, [None] * n]  # monochromatic
        self.slit1_above =       [[None] * n, [None] * n]  # monochromatic
        self.slit2_above =       [[None] * n, [None] * n]  # monochromatic
        self.sample_width =      [[None] * n, [None] * n]  # both
        self.sample_broadening = [[None] * n, [None] * n]  # both

        for i, classname in enumerate(self.instr_classes):
            self.set_default_values(i, classname)

        # Indicate that no instrument has been chosen.
        self.instr_idx = -1


    def get_instr_idx(self):
        return self.instr_idx


    def set_instr_idx(self, index):
        self.instr_idx = index


    def set_default_values(self, i, iclass):
        """ Sets default values for reflectometer parameters."""

        if hasattr(iclass, 'wavelength'):
            try:
                self.wavelength_lo[0][i], \
                self.wavelength_hi[0][i] = iclass.wavelength
            except:
                self.wavelength[0][i] = iclass.wavelength
        if hasattr(iclass, 'dLoL'):
            self.dLoL[0][i] = iclass.dLoL
        if hasattr(iclass, 'T'):
            self.T[0][i] = iclass.T
        if hasattr(iclass, 'Tlo'):
            if iclass.Tlo is not inf:  # TODO: resolve handling of inf
                self.Tlo[0][i] = iclass.Tlo
        if hasattr(iclass, 'Thi'):
            if iclass.Thi is not inf:  # TODO: resolve handling of inf
                self.Thi[0][i] = iclass.Thi
        if hasattr(iclass, 'd_s1'):
            self.d_s1[0][i] = iclass.d_s1
        if hasattr(iclass, 'd_s2'):
            self.d_s2[0][i] = iclass.d_s2
        #if hasattr(iclass, 'sample_width'):
        #    self.sample_width[0][i] = iclass.sample_width
        if hasattr(iclass, 'sample_broadening'):
            self.sample_broadening[0][i] = iclass.sample_broadening

        self.instr_idx = i
        self.init_metadata()


    def init_metadata(self):
        """
        Sets current metadata values for insturments to their default values.
        """

        i = self.instr_idx
        self.wavelength[1][i] = self.wavelength[0][i]
        self.wavelength_lo[1][i] = self.wavelength_lo[0][i]
        self.wavelength_hi[1][i] = self.wavelength_hi[0][i]
        self.dLoL[1][i] = self.dLoL[0][i]
        self.d_s1[1][i] = self.d_s1[0][i]
        self.d_s2[1][i] = self.d_s2[0][i]
        self.T[1][i] = self.T[0][i]
        self.Tlo[1][i] = self.Tlo[0][i]
        self.Thi[1][i] = self.Thi[0][i]
        self.slit1_size[1][i] = self.slit1_size[0][i]
        self.slit2_size[1][i] = self.slit2_size[0][i]
        self.slit1_at_Tlo[1][i] = self.slit1_at_Tlo[0][i]
        self.slit2_at_Tlo[1][i] = self.slit2_at_Tlo[0][i]
        self.slit1_below[1][i] = self.slit1_below[0][i]
        self.slit2_below[1][i] = self.slit2_below[0][i]
        self.slit1_above[1][i] = self.slit1_above[0][i]
        self.slit2_above[1][i] = self.slit2_above[0][i]
        self.sample_width[1][i] = self.sample_width[0][i]
        self.sample_broadening[1][i] = self.sample_broadening[0][i]


    def edit_metadata(self):
        """Dispatches to the appropriate class of instrument."""

        if self.instr_idx <= 3:
            self.edit_metadata_monochromatic()
        else:
            self.edit_metadata_polychromatic()


    def edit_metadata_monochromatic(self):
        """
        Allows the user to edit the values for parameters of a monochromatic
        scanning instrument.
        """

        i = self.instr_idx
        fields = [
                   ["Radiation Type:", self.radiation[i], "str", 'RH2B', None,
                       self.instr_names[i]+" Scanning Reflectometer"],
                   ["Instrument location:", self.instr_location[i],
                       "str", 'R', None],
                   ["Wavelength (A):", self.wavelength[1][i],
                       "float", 'REH2', None, "Instrument Attributes"],
                   ["Wavelength Dispersion (dLoL):", self.dLoL[1][i],
                       "float", 'RE', None],
                   ["Distance to Slit 1 (mm):", self.d_s1[1][i],
                       "float", 'RE', None],
                   ["Distance to Slit 2 (mm):", self.d_s2[1][i],
                       "float", 'RE', None],
                   ["Theta Lo (degrees):", self.Tlo[1][i],
                       "float", 'REH2', None, "Measurement Settings"],
                   ["Theta Hi (degrees):", self.Thi[1][i],
                       "float", 'E', None],
                   ["Slit 1 at Theta Lo (mm):", self.slit1_at_Tlo[1][i],
                       "float", 'RE', None],
                   ["Slit 2 at Theta Lo (mm):", self.slit2_at_Tlo[1][i],
                       "float", 'E', None],
                   ["Slit 1 below Theta Lo (mm):", self.slit1_below[1][i],
                       "float", 'RE', None],
                   ["Slit 2 below Theta Lo (mm):", self.slit2_below[1][i],
                       "float", 'E', None],
                   ["Slit 1 above Theta Hi (mm):", self.slit1_above[1][i],
                       "float", 'EL', None],
                   ["Slit 2 above Theta Hi (mm):", self.slit2_above[1][i],
                       "float", 'E', None],
                   ["Sample Width (mm):", self.sample_width[1][i],
                       "float", 'E', None],
                   ["Sample Broadening (mm):", self.sample_broadening[1][i],
                       "float", 'E', None],
                 ]

        # Get instrument and measurement parameters via a pop-up dialog box.
        # Pass in the frame object as the parent window so that the dialog box
        # will inherit font info from it instead of using system defaults.
        frame = wx.FindWindowByName("AppFrame")
        x, y = frame.GetPositionTuple()
        dlg = InputListDialog(parent=frame,
                              title="Edit Instrument Parameters",
                              pos=(x+350, y+50),
                              itemlist=fields,
                              align=True)
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetResultsAltFormat()
            if len(sys.argv) > 1 and '-tracep' in sys.argv[1:]:
                print ">>> Instrument (resolution) parameters:"; print results

            # Skip results[0], the radiation value that is not editable
            # Skip results[1], the location value that is not editable
            (self.wavelength[1][i],
             self.dLoL[1][i],
             self.d_s1[1][i],
             self.d_s2[1][i],
             self.Tlo[1][i],
             self.Thi[1][i],
             self.slit1_at_Tlo[1][i],
             self.slit2_at_Tlo[1][i],
             self.slit1_below[1][i],
             self.slit2_below[1][i],
             self.slit1_above[1][i],
             self.slit2_above[1][i],
             self.sample_width[1][i],
             self.sample_broadening[1][i]
            ) = results[2:]
        dlg.Destroy()


    def edit_metadata_polychromatic(self):
        """
        Allows the user to edit the values for parameters of a polychromatic
        time-of-flight instrument.
        """

        i = self.instr_idx
        fields = [
                   ["Radiation Type:", self.radiation[i], "str", 'RH2B', None,
                       self.instr_names[i]+" Time-of-Flight Reflectometer"],
                   ["Instrument location:", self.instr_location[i],
                       "str", 'R', None],
                   ["Wavelength Lo (A):", self.wavelength_lo[1][i],
                       "float", 'REH2', None, "Instrument Attributes"],
                   ["Wavelength Hi (A):", self.wavelength_hi[1][i],
                       "float", 'RE', None],
                   ["Wavelength Dispersion (dLoL):", self.dLoL[1][i],
                       "float", 'RE', None],
                   ["Distance to Slit 1 (mm):", self.d_s1[1][i],
                       "float", 'RE', None],
                   ["Distance to Slit 2 (mm):", self.d_s2[1][i],
                       "float", 'RE', None],
                   ["Theta (degrees):", self.T[1][i],
                       "float", 'REH2', None, "Measurement Settings"],
                   ["Size of Slit 1 (mm):", self.slit1_size[1][i],
                       "float", 'RE', None],
                   ["Size of Slit 2 (mm):", self.slit2_size[1][i],
                       "float", 'RE', None],
                   ["Sample Width (mm):", self.sample_width[1][i],
                       "float", 'EL', None],
                   ["Sample Broadening (mm):", self.sample_broadening[1][i],
                       "float", 'E', None],
                 ]

        # Get instrument and measurement parameters via a pop-up dialog box.
        # Pass in the frame object as the parent window so that the dialog box
        # will inherit font info from it instead of using system defaults.
        frame = wx.FindWindowByName("AppFrame")
        x, y = frame.GetPositionTuple()
        dlg = InputListDialog(parent=frame,
                              title="Edit Instrument Parameters",
                              pos=(x+350, y+50),
                              itemlist=fields,
                              align=True)
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetResultsAltFormat()
            if len(sys.argv) > 1 and '-tracep' in sys.argv[1:]:
                print ">>> Instrument (resolution) parameters:"; print results

            # Skip results[0], the radiation value that is not editable
            # Skip results[1], the location value that is not editable
            (self.wavelength_lo[1][i],
             self.wavelength_hi[1][i],
             self.dLoL[1][i],
             self.d_s1[1][i],
             self.d_s2[1][i],
             self.T[1][i],
             self.slit1_size[1][i],
             self.slit2_size[1][i],
             self.sample_width[1][i],
             self.sample_broadening[1][i]
            ) = results[2:]

        dlg.Destroy()

    # Get methods (without corresponding set methods).
    def get_instr_names(self):
        return self.instr_names
    def get_instr_classes(self):
        return self.instr_classes
    def get_radiation(self):
        return self.radiation[self.instr_idx]

    # Get methods (with corresponding set methods).
    def get_wavelength(self):
        return self.wavelength[1][self.instr_idx]
    def get_wavelength_lo(self):
        return self.wavelength_lo[1][self.instr_idx]
    def get_wavelength_hi(self):
        return self.wavelength_hi[1][self.instr_idx]
    def get_dLoL(self):
        return self.dLoL[1][self.instr_idx]

    def get_d_s1(self):
        return self.d_s1[1][self.instr_idx]
    def get_d_s2(self):
        return self.d_s2[1][self.instr_idx]

    def get_T(self):
        return self.T[1][self.instr_idx]
    def get_Tlo(self):
        return self.Tlo[1][self.instr_idx]
    def get_Thi(self):
        return self.Thi[1][self.instr_idx]

    def get_slit1_size(self):
        return self.slit1_size[1][self.instr_idx]
    def get_slit2_size(self):
        return self.slit2_size[1][self.instr_idx]
    def get_slit1_at_Tlo(self):
        return self.slit1_at_Tlo[1][self.instr_idx]
    def get_slit2_at_Tlo(self):
        return self.slit2_at_Tlo[1][self.instr_idx]
    def get_slit1_below(self):
        return self.slit1_below[1][self.instr_idx]
    def get_slit2_below(self):
        return self.slit2_below[1][self.instr_idx]
    def get_slit1_above(self):
        return self.slit1_above[1][self.instr_idx]
    def get_slit2_above(self):
        return self.slit2_above[1][self.instr_idx]

    def get_sample_width(self):
        return self.sample_width[1][self.instr_idx]
    def get_sample_broadening(self):
        return self.sample_broadening[1][self.instr_idx]

    # Set methods (with corresponding get methods).
    def set_wavelength(self):
        self.wavelength[1][self.instr_idx] = value
    def set_wavelength_lo(self):
        self.wavelength_lo[1][self.instr_idx] = value
    def set_wavelength_hi(self):
        self.wavelength_hi[1][self.instr_idx] = value
    def set_dLoL(self):
        self.dLoL[1][self.instr_idx] = value

    def set_d_s1(self):
        self.d_s1[1][self.instr_idx] = value
    def set_d_s2(self):
        self.d_s2[1][self.instr_idx] = value

    def set_T(self, value=None):
        self.T[1][self.instr_idx] = value
    def set_Tlo(self, value=None):
        self.Tlo[1][self.instr_idx] = value
    def set_Thi(self, value=None):
        self.Thi[1][self.instr_idx] = value

    def set_slit1_size(self, value=None):
        self.slit1_size[1][self.instr_idx] = value
    def set_slit2_size(self, value=None):
        self.slit2_size[1][self.instr_idx] = value
    def set_slit1_at_Tlo(self, value=None):
        self.slit1_at_Tlo[1][self.instr_idx] = value
    def set_slit2_at_Tlo(self):
        self.slit2_at_Tlo[1][self.instr_idx] = value
    def set_slit1_below(self, value=None):
        self.slit1_below[1][self.instr_idx] = value
    def set_slit2_below(self, value=None):
        self.slit2_below[1][self.instr_idx] = value
    def set_slit1_above(self):
        self.slit1_above[1][self.instr_idx] = value
    def set_slit2_above(self):
        self.slit2_above[1][self.instr_idx] = value

    def set_sample_width(self):
        self.sample_width[1][self.instr_idx] = value
    def set_sample_broadening(self):
        self.sample_broadening[1][self.instr_idx] = value

#==============================================================================

class ExecuteInThread():
    """
    This class executes the specified function in a separate thread and calls a
    designated callback function when the function completes.  Control is
    immediately given back to the caller of ExecuteInThread which executes in
    parallel with the thread.
    """

    def __init__(self, callback, function, *args, **kwargs):
        if callback is None: callback = _callback
        #print "*** ExecuteInThread init:", callback, function, args, kwargs
        delayedresult.startWorker(consumer=callback, workerFn=function,
                                  wargs=args, wkwargs=kwargs)

    def _callback(self, delayedResult):
        '''
        jobID = delayedResult.getJobID()
        assert jobID == self.jobID
        try:
            result = delayedResult.get()
        except Exception, e:
            display_error_message(self, "job %s raised exception: %s"%(jobID, e)
            return
        '''
        return

#==============================================================================

def perform_recon_inver(files, params):
    """
    Performs phase reconstruction and direct inversion on two reflectometry
    data sets to generate a scattering length depth profile of the sample.
    """

    if len(sys.argv) > 1 and '-debug' in sys.argv[1:]:
        print "*** Inputs to perform_recon_inver()"
        print "*** files =", files
        print "*** params =", params

    # Perform phase reconstruction using two reflectivity measurements of a
    # sample where the only change in the setup between the two runs is that a
    # different surrounding media is used (usually for the incident layer).
    phase = SurroundVariation(files[0], files[1], u=params[2],
                              v1=params[0], v2=params[1], stages=100)
    data = phase.Q, phase.RealR, phase.dRealR

    # Perform phase inversion of the real part of a reflectivity amplitude that
    # was computed by the phase reconstruction algorithm.  The result is a step
    # profile of the scattering length density of the sample as a function of
    # depth.
    if params[5] <= params[4]:  # Qmax must be > Qmin
        params[5] = None        # If not, then let algorithm pick Qmax
    res = Inversion(data=data, **dict(substrate=params[2],
                                      thickness=params[3],
                                      Qmin=params[4],
                                      Qmax=params[5],
                                      rhopoints=params[6],
                                      calcpoints=params[7],
                                      iters=params[8],
                                      stages=params[9],
                                      ctf_window=0, #cosine transform smoothing
                                      backrefl=True,
                                      bse=params[10],
                                      noise=1,  # inversion noise factor
                                      showiters=False,
                                      monitor=None))

    # Generate the plots.
    res.run(showiters=False)
    res.plot(phase=phase)

    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right=0.96,
                          top=0.95, bottom=0.08)


def perform_simulation(sample, params, Q=None, dQ=None):
    """
    Simulates reflectometry data sets from model information then performs
    phase reconstruction and direct inversion on the data to generate a
    scattering length density profile.
    """

    if len(sys.argv) > 1 and '-debug' in sys.argv[1:]:
        print "*** Inputs to perform_simulation()"
        print "*** sample =", sample
        print "*** params =", params
        if Q is not None:
            print "***  Q len =", len(Q),  "  Q lo:hi =",  Q[0],  Q[-1]
        if dQ is not None:
            print "*** dQ len =", len(dQ), " dQ lo:hi =", dQ[0], dQ[-1]

    # Construct a dictionary of keyword arguments for the invert_args parameter
    # used by the phase inversion algorithm.
    #
    # Note that the inversion noise factor here is different than the
    # simulation noise parameter (determined by user input)!
    inversion_args = dict(rhopoints=params[4],
                          calcpoints=params[5],
                          iters=params[6],
                          stages=params[7],
                          bse=params[9],
                          noise=1,
                          showiters=False,
                          monitor=None)

    # Construct a dictionary of keyword arguments for the phase_args parameter
    # used by the phase reconstruction algorithm.
    reconstruction_args = dict(stages=100)

    # Convert the noise (uncertainly) parameter from a percentage value to a
    # hundredths value (e.g., if the user enters 5%, change it to 0.05).  Also
    # make the noise a non-zero value as Simulation cannot tolerate a zero.
    noise = params[8]
    if noise < 0.01: noise = 0.01
    noise /= 100.0  # convert percent value to hundreths value

    # Convert flag from a string to a Boolean value.
    perfect_reconstruction = True if params[10] == "True" else False

    # For monochromatic instruments, Q will be None.
    if Q is None:
        Q = numpy.linspace(params[2], params[3], params[4])

    # Create simulated datasets and perform phase reconstruction and phase
    # inversion using the simulated datasets.
    #
    # Note that Simulation internally calls both SurroundVariation and
    # Inversion as is done when simulation is not used to create the datasets.
    sim = Simulation(q=Q,
                     dq=dQ,
                     sample=sample,
                     u=params[11],
                     urough=params[12],
                     v1=params[0],
                     v2=params[1],
                     noise=noise,
                     seed=None,
                     invert_args=inversion_args,
                     phase_args=reconstruction_args,
                     perfect_reconstruction=perfect_reconstruction)

    # Generate the plots.
    sim.plot()
    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right = 0.96,
                          top=0.95, bottom=0.08)


def test1():
    """
    Tests use of the Simulation class in simulation.py using a reconstructed
    reflectometry data file.
    """
    from inversion.core.simulate import Simulation
    from numpy import linspace

    # Roughness parameters (surface, sample, substrate).
    sv, s, su = 3, 5, 2
    # Surround parameters.
    u, v1, v2 = 2.07, 0, 4.5
    # Default sample.
    sample = ([5,100,s], [1,123,s], [3,47,s], [-1,25,s])
    sample[0][2] = sv
    bse = 0

    # Run the simulation.
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


def test2():
    """
    Tests use of the SurroundVariation and Inversion classes in core.py using
    two actual reflectometry data files.
    """
    from inversion.core.core import SurroundVariation, Inversion

    root = get_appdir()
    #args = [os.path.join(root, 'wsh02_re.dat')]
    file_1 = os.path.join(root, DEMO_REFLDATA1_1)
    file_2 = os.path.join(root, DEMO_REFLDATA1_2)
    args = [file_1, file_2]
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


def test3():
    """
    Tests the ability to utilize code that uses the procedural interface
    to pylab to generate subplots.
    """

    pylab.suptitle("Test use of procedural interface to Pylab", fontsize=16)

    pylab.subplot(211)
    x = numpy.arange(0, 6, 0.01)
    y = numpy.sin(x**2)*numpy.exp(-x)
    pylab.xlabel("x-axis")
    pylab.ylabel("y-axis")
    pylab.title("First Plot")
    pylab.plot(x, y)

    pylab.subplot(212)
    x = numpy.arange(0, 8, 0.01)
    y = numpy.sin(x**2)*numpy.exp(-x) + 1
    pylab.xlabel("x-axis")
    pylab.ylabel("y-axis")
    pylab.title("Second Plot")
    pylab.plot(x, y)

    #pylab.show()


def test4(figure):
    """
    Tests the ability to utilize code that uses the object oriented interface
    to pylab to generate subplots.
    """

    axes = figure.add_subplot(311)
    x = numpy.arange(0, 6, 0.01)
    y = numpy.sin(x**2)*numpy.exp(-x)
    axes.plot(x, y)

    axes = figure.add_subplot(312)
    x = numpy.arange(0, 8, 0.01)
    y = numpy.sin(x**2)*numpy.exp(-x) + 1
    axes.plot(x, y)
    axes.set_ylabel("y-axis")

    axes = figure.add_subplot(313)
    x = numpy.arange(0, 4, 0.01)
    y = numpy.sin(x**2)*numpy.exp(-x) + 2
    axes.plot(x, y)
    axes.set_xlabel("x-axis")

    pylab.suptitle("Test use of object oriented interface to Pylab",
                   fontsize=16)
    pylab.subplots_adjust(hspace=0.35)
    #pylab.show()

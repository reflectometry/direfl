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
This module implements the InversionPage class that provides the direct
inversion feature of the application.  It generates a scattering length density
profile of a sample from two reflectometry data files supplied by the user
along with user specified parameter settings.
"""

#==============================================================================
from __future__ import print_function

import os
import sys
import time

import numpy as np

import wx
from wx.lib import delayedresult

import matplotlib

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as Toolbar

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

from ..api.util import isstr
from ..api.invert import SurroundVariation, Inversion
from .utilities import example_data

from .input_list import InputListPanel
from .instrument_params import InstrumentParameters
from .wx_utils import (popup_error_message, popup_warning_message,
                       StatusBarInfo, ExecuteInThread, WorkInProgress)

# Text strings for use in file selection dialog boxes.
REFL_FILES = "Refl files (*.refl)|*.refl"
DATA_FILES = "Data files (*.dat)|*.dat"
TEXT_FILES = "Text files (*.txt)|*.txt"
ALL_FILES = "All files (*.*)|*.*"

# Resource files.
DEMO_REFLDATA1_1 = "qrd1.refl"
DEMO_REFLDATA1_2 = "qrd2.refl"
DEMO_REFLDATA2_1 = "surround_air_4.refl"
DEMO_REFLDATA2_2 = "surround_d2o_4.refl"

# Custom colors.
WINDOW_BKGD_COLOUR = "#ECE9D8"
PALE_YELLOW = "#FFFFB0"

DATA_ENTRY_ERRMSG = """\
Please correct any highlighted field in error,
then retry the operation.\n
Yellow indicates an input value is required.
Red means the input value has incorrect syntax."""

INV_HELP1 = """\
Edit parameters then click Compute to generate a density profile \
from your data."""

#==============================================================================

class InversionPage(wx.Panel):
    """
    This class implements phase reconstruction and direct inversion analysis
    of two surround variation data sets (i.e., experimentally collected data)
    to produce a scattering length density profile of the sample.
    """

    def __init__(self, parent, id=wx.ID_ANY, colour="", fignum=0, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)

        self.fignum = fignum
        self.SetBackgroundColour(colour)
        self.sbi = StatusBarInfo()
        self.sbi.write(1, INV_HELP1)

        # Split the panel into parameter and plot subpanels.
        sp = wx.SplitterWindow(self, style=wx.SP_3D|wx.SP_LIVE_UPDATE)

        if wx.Platform == "__WXMAC__":  # workaround to set sash position on
            sp.SetMinimumPaneSize(300)  # frame.Show() to desired initial value
        else:
            sp.SetMinimumPaneSize(100)

        # Create display panels as children of the splitter.
        self.pan1 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan1.SetBackgroundColour(colour)
        self.pan2 = wx.Panel(sp, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.pan2.SetBackgroundColour("WHITE")

        # Initialize the left and right panels.
        self.init_param_panel()
        self.init_plot_panel()

        # Attach the child panels to the splitter.
        # Below is a workaround to keep width of pan1 in both page0 and page1
        # the same.  For some reason Windows renders this panel a bit too wide.
        if wx.Platform == "__WXMSW__":
            sp.SplitVertically(self.pan1, self.pan2, sashPosition=296)
        else:
            sp.SplitVertically(self.pan1, self.pan2, sashPosition=300)
        sp.SetSashGravity(0.2)  # on resize grow mostly on right side

        # Put the splitter in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_param_panel(self):
        """Initializes the parameter input panel of the InversionPage."""

        # Determine the border size for widgets placed inside a StaticBox.
        # On the Mac, a generous minimum border is provided that is sufficient.
        if wx.Platform == "__WXMAC__":
            SBB = 0
        else:
            SBB = 5

        #----------------------------
        # Section 1: Input Data Files
        #----------------------------

        # Note that a static box must be created before creating the widgets
        # that appear inside it (box and widgets must have the same parent).
        sbox1 = wx.StaticBox(self.pan1, wx.ID_ANY, "Reflectometry Data Files")

        # Create a panel for obtaining input file selections.
        self.pan11 = wx.Panel(self.pan1, wx.ID_ANY, style=wx.RAISED_BORDER)
        self.pan11.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        # Create file name entry boxes and labels.
        label1 = wx.StaticText(self.pan11, wx.ID_ANY, label="File 1:")
        label2 = wx.StaticText(self.pan11, wx.ID_ANY, label="File 2:")

        self.TCfile1 = wx.TextCtrl(self.pan11, wx.ID_ANY, value="",
                                   style=wx.TE_RIGHT)
        self.TCfile1.SetBackgroundColour(PALE_YELLOW)
        self.TCfile1.Bind(wx.EVT_SET_FOCUS, self.OnSetFocusFile1)
        self.TCfile1.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusFile1)
        self.save_file1 = ""

        self.TCfile2 = wx.TextCtrl(self.pan11, wx.ID_ANY, value="",
                                   style=wx.TE_RIGHT)
        self.TCfile2.SetBackgroundColour(PALE_YELLOW)
        self.TCfile2.Bind(wx.EVT_SET_FOCUS, self.OnSetFocusFile2)
        self.TCfile2.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusFile2)
        self.save_file2 = ""

        # Create file selector button controls.
        # Match the button height to the text box height. Using y = -1 on
        # Windows does this, but not on Linux where the button height is larger.
        x, y = self.TCfile1.GetSize()
        btn_sel1 = wx.Button(self.pan11, wx.ID_ANY, "...", size=(30, y))
        self.Bind(wx.EVT_BUTTON, self.OnSelectFile1, btn_sel1)
        x, y = self.TCfile2.GetSize()
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

        # Group file selection widgets into a labeled section and
        # manage them with a static box sizer.
        sbox1_sizer = wx.StaticBoxSizer(sbox1, wx.VERTICAL)
        sbox1_sizer.Add(self.pan11, 0, wx.EXPAND|wx.ALL, border=SBB)

        #---------------------------------
        # Section 2: Instrument Parameters
        #---------------------------------

        sbox2 = wx.StaticBox(self.pan1, wx.ID_ANY, "Resolution Parameters")

        # Instantiate object that manages and stores instrument metadata.
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
        # Currently this field is not a required input.
        #cb.SetBackgroundColour(PALE_YELLOW)
        self.instr_cb = cb

        # Create a horizontal box sizer for the combo box and its label.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(cb_label, 0, border=5,
                        flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
        hbox1_sizer.Add(cb, 1, wx.EXPAND)

        # Create button controls.
        btn_edit = wx.Button(self.pan12, wx.ID_ANY, "Edit")
        self.Bind(wx.EVT_BUTTON, self.OnEdit, btn_edit)
        btn_reset = wx.Button(self.pan12, wx.ID_ANY, "Reset")
        self.Bind(wx.EVT_BUTTON, self.OnReset, btn_reset)

        # Create a horizontal box sizer for the buttons.
        hbox2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox2_sizer.Add((10, -1), 1)  # stretchable whitespace
        hbox2_sizer.Add(btn_edit, 0)
        hbox2_sizer.Add((10, -1), 0)  # non-stretchable whitespace
        hbox2_sizer.Add(btn_reset, 0)

        # Create a vertical box sizer for the input file selectors.
        vbox2_sizer = wx.BoxSizer(wx.VERTICAL)
        vbox2_sizer.Add(hbox1_sizer, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT,
                        border=10)
        vbox2_sizer.Add(hbox2_sizer, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan12.SetSizer(vbox2_sizer)
        vbox2_sizer.Fit(self.pan12)

        # Group instrument metadata widgets into a labeled section and
        # manage them with a static box sizer.
        sbox2_sizer = wx.StaticBoxSizer(sbox2, wx.VERTICAL)
        sbox2_sizer.Add(self.pan12, 0, wx.EXPAND|wx.ALL, border=SBB)

        #---------------------------------------------------
        # Section 3: Inversion and Reconstruction Parameters
        #---------------------------------------------------

        sbox3 = wx.StaticBox(self.pan1, wx.ID_ANY, "Inversion Parameters")

        # Instantiate object that manages and stores inversion parameters.

        fields = [
            ["SLD of Surface for Exp 1:", None, "float", 'RE', None],
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
            ###["Show Iterations:", "False", "str", 'CRE', ("True", "False")]
            ###["Monitor:", "", "str", 'RE', None]
            ]

        self.inver_param = InputListPanel(parent=self.pan1, itemlist=fields,
                                          align=True)

        # Group inversion parameter widgets into a labeled section and
        # manage them with a static box sizer.
        sbox3_sizer = wx.StaticBoxSizer(sbox3, wx.VERTICAL)
        sbox3_sizer.Add(self.inver_param, 1, wx.EXPAND|wx.ALL, border=SBB)

        #---------------------------
        # Section 4: Control Buttons
        #---------------------------

        # Create the Compute button.
        self.btn_compute = wx.Button(self.pan1, wx.ID_ANY, "Compute")
        self.Bind(wx.EVT_BUTTON, self.OnCompute, self.btn_compute)

        # Create a horizontal box sizer for the buttons.
        hbox3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox3_sizer.Add((10, -1), 1)  # stretchable whitespace
        hbox3_sizer.Add(self.btn_compute, 0, wx.TOP, border=4)

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

        # The splitter sash position should be greater than best width size.
        #print("Best size for Inversion Panel is", self.pan1.GetBestSizeTuple())


    def init_plot_panel(self):
        """Initializes the plotting panel of the InversionPage."""

        INTRO_TEXT = "Phase Reconstruction and Inversion Using Experimental Data:"

        # Instantiate a figure object that will contain our plots.
        figure = Figure()

        # Initialize the figure canvas, mapping the figure object to the plot
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
        self.pan2_gauge = WorkInProgress(self.pan2)
        self.pan2_gauge.Show(False)

        # Create a horizontal box sizer to hold the title and progress bar.
        hbox1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox1_sizer.Add(self.pan2_intro, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox1_sizer.Add((10, 25), 1)  # stretchable whitespace
        hbox1_sizer.Add(self.pan2_gauge, 0)

        # Create a vertical box sizer to manage the widgets in the main panel.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hbox1_sizer, 0, wx.EXPAND|wx.ALL, border=10)
        sizer.Add(canvas, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(mpl_toolbar, 0, wx.EXPAND|wx.ALL, border=10)

        # Associate the sizer with its container.
        self.pan2.SetSizer(sizer)
        sizer.Fit(self.pan2)


    def OnActivePage(self):
        """This method is called when user selects (makes current) the page."""
        self.sbi.restore()


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
            popup_warning_message(
                "Specify a Dataset",
                "Please specify the names of two reflectometry data files to use.")
            return

        # Make sure the files are accessible so we can display a proper error
        # message instead of getting a Python runtime error later on.
        try:
            fd = open(files[0], 'r')
            fd.close()
        except Exception:
            popup_error_message("Load Data Error",
                                "Cannot access file "+files[0])
            return

        try:
            fd = open(files[1], 'r')
            fd.close()
        except Exception:
            popup_error_message("Load Data Error",
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
            popup_error_message("Data Entry Error", DATA_ENTRY_ERRMSG)
            return

        # Get the validated inversion parameters.
        params = self.inver_param.GetResults()
        if len(sys.argv) > 1 and '--tracep' in sys.argv[1:]:
            print("*** Inversion parameters:"); print(params)

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

        # Inform the user that we're starting the computation.
        self.sbi.write(2, "Generating new plots ...")

        # Apply phase reconstruction and direct inversion techniques on the
        # experimental reflectivity datasets.
        try:
            #perform_inversion(files, params)
            ExecuteInThread(self.OnComputeEnd, perform_inversion,
                            files, params)
        except Exception as e:
            popup_error_message("Operation Failed", str(e))
            self.sbi.write(2, "")
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
        self.sbi.write(2, "    %g secs" %(secs))

        # Show widgets previously hidden at the start of this computation.
        self.btn_compute.Enable(True)
        self.pan11.Enable(True)
        frame = wx.FindWindowByName("AppFrame")
        frame.load_demo_dataset_1_item.Enable(True)
        frame.load_demo_dataset_2_item.Enable(True)


    def OnEdit(self, event):
        """Shows the instrument metadata to the user and allows editing."""

        if self.instr_param.get_instr_idx() < 0:
            popup_warning_message(
                "Select an Instrument",
                "Please select an instrument to edit from the drop down list.")
            return
        self.instr_param.edit_metadata()


    def OnReset(self, event):
        """Restores default parameters for the currently selected instrument."""
        self.instr_param.init_metadata()


    def OnSetFocusFile1(self, event):
        """Saves existing filespec on entry to the file1 text control box."""
        self.save_file1 = self.TCfile1.GetValue()


    def OnSetFocusFile2(self, event):
        """Saves existing filespec on entry to the file2 text control box."""
        self.save_file2 = self.TCfile2.GetValue()


    def OnKillFocusFile1(self, event):
        """Processes edited filespec on exit from the file1 text control box."""

        file1 = self.TCfile1.GetValue()
        if self.save_file1 == file1:
            return  # there was no change to input field value

        if len(file1) == 0:
            self.TCfile1.SetBackgroundColour(PALE_YELLOW)
        else:
            self.TCfile1.SetBackgroundColour("WHITE")

        # Plot one or both files.
        self.plot_dataset(file1, self.TCfile2.GetValue())


    def OnKillFocusFile2(self, event):
        """Processes edited filespec on exit from the file2 text control box."""

        file2 = self.TCfile2.GetValue()
        if self.save_file2 == file2:
            return  # there was no change to input field value

        if len(file2) == 0:
            self.TCfile2.SetBackgroundColour(PALE_YELLOW)
        else:
            self.TCfile2.SetBackgroundColour("WHITE")

        # Plot one or both files.
        self.plot_dataset(self.TCfile1.GetValue(), file2)


    def OnLoadDemoDataset1(self, event):
        """Loads demo 1 reflectometry data files for measurements 1 and 2."""

        # Locate the demo data files.
        datafile_1 = example_data(DEMO_REFLDATA1_1)
        datafile_2 = example_data(DEMO_REFLDATA1_2)

        # Store the file names in text control boxes and position text so that
        # the file name is visible even if the beginning of the path is not.
        self.TCfile1.SetBackgroundColour("WHITE")
        self.TCfile1.SetValue(datafile_1)
        self.TCfile1.SetInsertionPointEnd()
        self.save_file1 = datafile_1

        self.TCfile2.SetBackgroundColour("WHITE")
        self.TCfile2.SetValue(datafile_2)
        self.TCfile2.SetInsertionPointEnd()
        self.save_file2 = datafile_2

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

        # Plot the files.
        self.plot_dataset(datafile_1, datafile_2)


    def OnLoadDemoDataset2(self, event):
        """Loads demo 2 reflectometry data files for measurements 1 and 2."""

        # Locate the demo data files.
        datafile_1 = example_data(DEMO_REFLDATA2_1)
        datafile_2 = example_data(DEMO_REFLDATA2_2)

        # Store the file names in text control boxes and position text so that
        # the file name is visible even if the beginning of the path is not.
        self.TCfile1.SetBackgroundColour("WHITE")
        self.TCfile1.SetValue(datafile_1)
        self.TCfile1.SetInsertionPointEnd()
        self.save_file1 = datafile_1

        self.TCfile2.SetBackgroundColour("WHITE")
        self.TCfile2.SetValue(datafile_2)
        self.TCfile2.SetInsertionPointEnd()
        self.save_file2 = datafile_2

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

        # Plot the files.
        self.plot_dataset(datafile_1, datafile_2)


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
                            style=wx.FD_OPEN|wx.FD_MULTIPLE|wx.FD_CHANGE_DIR)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        # The user could have selected 1 to n files.
        num_files = len(paths)
        if num_files > 2:
            popup_error_message(
                "Too Many Files Selected",
                "You can select up to two data files, please try again.")
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

        # Plot one or both files.
        self.plot_dataset(self.TCfile1.GetValue(), self.TCfile2.GetValue())


    def OnSelectFile2(self, event):
        """Selects the second reflectometry data file."""

        dlg = wx.FileDialog(self,
                            message="Select 2nd Data File",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=(REFL_FILES+"|"+DATA_FILES+"|"+
                                      TEXT_FILES+"|"+ALL_FILES),
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()
        if sts == wx.ID_CANCEL:
            return  # Do nothing

        # The dialog restricts the user to selecting just one file.
        datafile_2 = paths[0]
        self.TCfile2.SetBackgroundColour("WHITE")
        self.TCfile2.SetValue(datafile_2)
        self.TCfile2.SetInsertionPointEnd()

        # Plot one or both files.
        self.plot_dataset(self.TCfile1.GetValue(), self.TCfile2.GetValue())


    def plot_dataset(self, file1, file2):
        """
        Plots the Q, R, and dR of the two data files.
        """

        if file1 is not None and len(file1) == 0:
            file1 = None
        if file2 is not None and len(file2) == 0:
            file2 = None

        # Set the plotting figure manager for this class as the active one and
        # erase the current figure.
        _pylab_helpers.Gcf.set_active(self.fm)
        pylab.clf()
        pylab.draw()
        self.sbi.write(2, "")

        # Allow just one file to be plotted using common code that expects two.
        # This is inefficient when there is only one file because it will be
        # loaded twice, but otherwise this causes no problems.
        if file1 is None and file2 is None:
            return

        self.plot_file1 = self.plot_file2 = True
        if file1 is None:
            self.plot_file1 = False
            file1 = file2
        if file2 is None:
            self.plot_file2 = False
            file2 = file1

        # Make sure the files are accessible so we can display a proper error
        # message now before load_data tries to read them.
        if self.plot_file1:
            try:
                fd = open(file1, 'r')
                fd.close()
            except Exception:
                self.TCfile1.SetBackgroundColour("PINK")
                self.TCfile1.SetFocus()
                self.TCfile1.Refresh()
                popup_error_message("File Access Error",
                                    "Cannot access file "+file1)
                return

        if self.plot_file2:
            try:
                fd = open(file2, 'r')
                fd.close()
            except Exception:
                self.TCfile2.SetBackgroundColour("PINK")
                self.TCfile2.SetFocus()
                self.TCfile2.Refresh()
                popup_error_message("File Access Error",
                                    "Cannot access file "+file2)
                return

        # Now we can load and plot the dataset.
        try:
            self.load_data(file1, file2)
        except ValueError as e:
            popup_error_message("Data File Error", str(e))
            return
        else:
            self.pan2_intro.SetLabel("Dataset Reflectivity Plots:")
            self.generate_plot()
            pylab.draw()


    def load_data(self, file1, file2):
        """
        Loads the data from files or alternatively from tuples of (Q, R) or
        (Q, R, dR), (Q, dQ, R, dR) or (Q, dQ, R, dR, L).

        This code is adapted from SurroundVariation._load().
        TODO: Replace this loader with a general purpose loader that will be
              able to parse instrument metadata in the file.
        """

        # This code assumes the following data file formats:
        # 2-column data: Q, R
        # 3-column data: Q, R, dR
        # 4-column data: Q, dQ, R, dR
        # 5-column data: Q, dQ, R, dR, Lambda
        if isstr(file1):
            d1 = np.loadtxt(file1).T
            name1 = file1
        else:
            d1 = file1
            name1 = "data1"

        if isstr(file2):
            d2 = np.loadtxt(file2).T
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
            q2, dq2, r2, dr2, lambda2 = d2[0:5]

        if not q1.shape == q2.shape or not (q1 == q2).all():
            raise ValueError("Q points do not match in data files.")

        # Note that q2, dq2, lambda1, and lambda2 are currently discarded.
        self.name1, self.name2 = name1, name2
        self.Qin, self.dQin = q1, dq1
        self.R1in, self.R2in = r1, r2
        self.dR1in, self.dR2in = dr1, dr2


    def generate_plot(self):
        """Plot Q vs R and dR (uncertainty) if available."""

        '''
        # This simpler version of the function does not handle negative nor
        # very small values of dR gracefully that are sometimes found in
        # reflectivity files collected from real experiments.  Files qrd1.refl
        # and qrd2.refl have both of these issues that are clearly demonstrated
        # in the plots.
        def plot1(Q, R, dR, label, color):
            #pylab.plot(Q, R, '.', label=label, color=color)
	        #pylab.gca().set_yscale('symlog', linthreshy=t, linwidthy=0.1)
            pylab.semilogy(Q, R, '.', label=label, color=color)
            if dR is not None:
                pylab.fill_between(Q, (R-dR), (R+dR),
                                       color=color, alpha=0.2)
        '''

        def plot1(Q, R, dR, label, color):
            # Generate a plot for one data file while trying to deal with bogus
            # negative values for dR or very small values for dR in a sensible
            # way.  This technique was developed by Paul Kienzle and will
            # likely be improved over time.
            if dR is not None:
                minR = np.min((R+dR))/10
            else:
                minR = np.min(R[R > 0])/2

            pylab.semilogy(Q, np.maximum(R, minR), '.', label=label,
                           color=color)
            if dR is not None:
                idx = np.argsort(Q)
                pylab.fill_between(Q, np.maximum(R-dR, minR),
                                   np.maximum(R+dR, minR),
                                   color=color, alpha=0.2)

        # Only show file.ext portion of the file specification on the plots.
        name1 = os.path.basename(self.name1)
        name2 = os.path.basename(self.name2)

        if self.plot_file1:
            pylab.cla()
            plot1(self.Qin, self.R1in, self.dR1in, name1, 'blue')
        if self.plot_file2:
            plot1(self.Qin, self.R2in, self.dR2in, name2, 'green')

        pylab.legend(prop=FontProperties(size='medium'))
        pylab.ylabel('Reflectivity')
        pylab.xlabel('Q (inv A)')

#==============================================================================

def perform_inversion(files, params):
    """
    Performs phase reconstruction and direct inversion on two reflectometry
    data sets to generate a scattering length depth profile of the sample.
    """

    if len(sys.argv) > 1 and '--debug' in sys.argv[1:]:
        print("*** Inputs to perform_inversion()")
        print("*** files =", files)
        print("*** params =", params)

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
    inv = Inversion(data=data, **dict(substrate=params[2],
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
                                      noise=1,      # inversion noise factor
                                      showiters=False,
                                      monitor=None))

    # Generate the plots.
    inv.run(showiters=False)

    if len(sys.argv) > 1 and '--plot6' in sys.argv[1:]:
        inv.plot6(phase=phase)
    else:
        inv.plot(phase=phase)

    pylab.subplots_adjust(wspace=0.25, hspace=0.33,
                          left=0.09, right=0.96,
                          top=0.95, bottom=0.08)

    # If the user requests, create data files to capture the data used to
    # generate the plots.
    if len(sys.argv) > 1 and '--write' in sys.argv[1:]:
        outfile = 'inv_phase.dat'
        phase.save(outfile=outfile, uncertainty=True)
        print("*** Created", outfile)

        outfile = 'inv_refl.dat'
        phase.save_inverted(profile=(inv.z, inv.rho), outfile=outfile)
        print("*** Created", outfile)

        outfile = 'inv_profile.dat'
        inv.save(outfile=outfile)
        print("*** Created", outfile)

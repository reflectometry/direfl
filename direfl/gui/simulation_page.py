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
This module implements the SimulationPage class that provides the simulation
feature of the application.  It creates simulated reflectometry data files from
the user's model description and user specified parameter settings which are
then used to perform a direct inversion to generate a scattering length density
profile of the sample.
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


from ..api.resolution import bins, binwidths
from ..api.simulate import Simulation
from .utilities import example_data

from .input_list import InputListPanel
from .instrument_params import InstrumentParameters
from .wx_utils import (popup_error_message, popup_warning_message,
                       StatusBarInfo, ExecuteInThread, WorkInProgress)

# Text strings for use in file selection dialog boxes.
DATA_FILES = "Data files (*.dat)|*.dat"
TEXT_FILES = "Text files (*.txt)|*.txt"
ALL_FILES = "All files (*.*)|*.*"

# Resource files.
DEMO_MODEL1_DESC = "demo_model_1.dat"
DEMO_MODEL2_DESC = "demo_model_2.dat"
DEMO_MODEL3_DESC = "demo_model_3.dat"

# Custom colors.
WINDOW_BKGD_COLOUR = "#ECE9D8"
PALE_YELLOW = "#FFFFB0"

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
Please specify an instrument to be used for calculating
resolution for the simulated datasets, or disable this
calculation by answering 'No' to the 'With Resolution'
question at the bottom of the page."""

SIM_HELP1 = """\
Edit parameters then click Compute to generate a density profile \
from your model."""

#==============================================================================

class SimulationPage(wx.Panel):
    """
    This class implements phase reconstruction and direct inversion analysis
    of two simulated surround variation data sets (generated from a model)
    to produce a scattering length density profile of the sample.
    """

    def __init__(self, parent, id=wx.ID_ANY, colour="", fignum=0, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)

        self.fignum = fignum
        self.SetBackgroundColour(colour)
        self.sbi = StatusBarInfo()
        self.sbi.write(1, SIM_HELP1)

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
        sp.SplitVertically(self.pan1, self.pan2)
        sp.SetSashPosition(300) # on Mac needs to be set after frame.Show()
        sp.SetSashGravity(0.2)  # on resize grow mostly on right side

        # Put the splitter in a sizer attached to the main panel of the page.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


    def init_param_panel(self):
        """Initializes the parameter input panel of the SimulationPage."""

        # Determine the border size for widgets placed inside a StaticBox.
        # On the Mac, a generous minimum border is provided that is sufficient.
        if wx.Platform == "__WXMAC__":
            SBB = 0
        else:
            SBB = 5

        #----------------------------
        # Section 1: Model Parameters
        #----------------------------

        # Note that a static box must be created before creating the widgets
        # that appear inside it (box and widgets must have the same parent).
        sbox1 = wx.StaticBox(self.pan1, wx.ID_ANY, "Model Parameters")

        # Create instructions for using the model description input box.
        line1 = wx.StaticText(self.pan1, wx.ID_ANY,
                              label="Define the Surface, Sample, and Substrate")
        line2 = wx.StaticText(self.pan1, wx.ID_ANY,
                              label="layers of your model (one layer per line):")

        demo_model_params = \
            "# SLDensity  Thickness  Roughness" + \
            NEWLINES_2 + NEWLINES_2 + NEWLINES_2 + NEWLINE

        # Create an input box to enter and edit the model description and
        # populate it with a header but no layer information.
        # Note that the number of lines determines the height of the box.
        self.model = wx.TextCtrl(self.pan1, wx.ID_ANY, value=demo_model_params,
                                 style=wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.RAISED_BORDER)
        self.model.SetBackgroundColour(WINDOW_BKGD_COLOUR)

        # Group model parameter widgets into a labeled section and
        # manage them with a static box sizer.
        sbox1_sizer = wx.StaticBoxSizer(sbox1, wx.VERTICAL)
        sbox1_sizer.Add(line1, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=SBB)
        sbox1_sizer.Add(line2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=SBB)
        sbox1_sizer.Add((-1, 4), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=SBB)
        sbox1_sizer.Add(self.model, 1, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT,
                        border=SBB)

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
        cb.SetBackgroundColour(PALE_YELLOW)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, cb)
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
            ###["SLD of Substrate:", 2.07, "float", 'RE', None],
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

        # Group inversion parameter widgets into a labeled section and
        # manage them with a static box sizer.
        sbox3_sizer = wx.StaticBoxSizer(sbox3, wx.VERTICAL)
        sbox3_sizer.Add(self.inver_param, 1, wx.EXPAND|wx.ALL, border=SBB)

        #---------------------------
        # Section 4: Control Buttons
        #---------------------------

        sbox4 = wx.StaticBox(self.pan1, wx.ID_ANY, "")

        # Create radio buttons to enable/disable resolution calculation.

        calc_reso = wx.StaticText(self.pan1, wx.ID_ANY,
                                  label="Resolution:  ")
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

        sbox4_sizer = wx.StaticBoxSizer(sbox4, wx.HORIZONTAL)
        sbox4_sizer.Add(calc_reso, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sbox4_sizer.Add(grid1, 0, wx.ALIGN_CENTER_VERTICAL)

        # Create the Compute button.
        self.btn_compute = wx.Button(self.pan1, wx.ID_ANY, "Compute")
        self.Bind(wx.EVT_BUTTON, self.OnCompute, self.btn_compute)

        # Create a horizontal box sizer for the buttons.
        hbox3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hbox3_sizer.Add(sbox4_sizer, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox3_sizer.Add((10, -1), 1)  # stretchable whitespace
        hbox3_sizer.Add(self.btn_compute, 0, wx.TOP, border=4)

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

        # The splitter sash position should be greater than best width size.
        #print("Best size for Simulation panel is", self.pan1.GetBestSizeTuple())


    def init_plot_panel(self):
        """Initializes the plotting panel of the SimulationPage."""

        INTRO_TEXT = "Phase Reconstruction and Inversion Using Simulated Data:"

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


    def OnCalcResoSelect(self, event):
        """Process the With Resolution radio button select event."""

        radio_selected = event.GetEventObject()
        if self.radio1 is radio_selected:
            self.pan12.Enable(True)
            self.radio1.SetValue(True)
            self.radio2.SetValue(False)
            self.calc_resolution = True
        else:
            self.pan12.Enable(False)
            self.radio1.SetValue(False)
            self.radio2.SetValue(True)
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
            if lin.startswith('#'):
                continue  # skip over comment line
            if len(lin) == 0:
                continue  # discard blank line
            keep = lin.split('#')
            lin = keep[0]  # discard trailing comment
            ln = lin.split(None, 4)  # we'll break into a max of 4 items
            if len(ln) == 1:
                ln.append('100')  # default thickness to 100
            if len(ln) == 2:
                ln.append('0')  # default roughness to 0.0

            try:
                temp = [float(ln[0]), float(ln[1]), float(ln[2])]
            except Exception:
                popup_error_message(
                    "Syntax Error",
                    "Please correct syntax error in model description.")
                return

            layers.append(temp)

        if len(layers) < 3:
            popup_error_message(
                "Less Than 3 Layers Defined",
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
            popup_error_message("Data Entry Error", DATA_ENTRY_ERRMSG)
            return

        # Get the validated inversion parameters.
        params = self.inver_param.GetResults()
        if len(sys.argv) > 1 and '--tracep' in sys.argv[1:]:
            print("*** Simulation parameters:"); print(params)

        sample = layers[1:-1]
        params.append(layers[-1][0])  # add SLD of substrate to list
        params.append(layers[-1][2])  # add roughness of substrate to list
        if len(sys.argv) > 1 and '--tracep' in sys.argv[1:]:
            print("*** Model parameters (all layers):"); print(layers)
            print("*** Sample layers excluding Surround:"); print(sample)

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
            popup_error_message("Choose an Instrument", INSTR_CALC_RESO_ERRMSG)
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
            if slit2_at_Tlo is None:
                slits_at_Tlo = slit1_at_Tlo
            slits_below = (slit1_below, slit2_below)
            if slit2_below is None:
                slits_below = slit1_below
            slits_above = (slit1_above, slit2_above)
            if slit2_above is None:
                slits_above = slit1_above
            if sample_width is None:
                sample_width = 1e10  # set to a large value
            if sample_broadening is None:
                sample_broadening = 0.0

            if (wavelength is None or
                    dLoL is None or
                    d_s1 is None or
                    d_s2 is None or
                    Tlo is None or
                    slits_at_Tlo is None):
                popup_error_message("Need Instrument Parameters",
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
            Q = np.linspace(params[2], params[3], params[4])
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
            if slit2_size is None:
                slits = slit1_size
            if sample_width is None:
                sample_width = 1e10  # set to a large value
            if sample_broadening is None:
                sample_broadening = 0.0

            if (wavelength is None or
                    dLoL is None or
                    d_s1 is None or
                    d_s2 is None or
                    T is None or
                    slits is None):
                popup_error_message("Need Instrument Parameters",
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
            Q = np.linspace(params[2], params[3], params[4])
            res = instrument.resolution(Q=Q, L=L, dL=dL)
            print("*** len of Q, res.Q, res.dQ, L:",
                  len(Q), len(res.Q), len(res.dQ), len(L))
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
            ExecuteInThread(self.OnComputeEnd, perform_simulation,
                            sample, params, Q=Q, dQ=dQ)
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
        """
        Restores default parameters for the currently selected instrument.
        """
        self.instr_param.init_metadata()


    def OnLoadDemoModel1(self, event):
        """Loads Demo Model 1 from a file."""

        filespec = example_data(DEMO_MODEL1_DESC)

        # Read the entire input file into a buffer.
        try:
            fd = open(filespec, 'rU')
            demo_model_params = fd.read()
            fd.close()
        except Exception:
            popup_warning_message(
                "Load Model Error",
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

        # Set surface SLD values for simulations 1 and 2 in the inversion and
        # reconstruction paramaters panel.
        # Note that datatype of None means do not change.
        plist = (0.0, 4.5,
                 None, None, None, None, None, None, None, None, None)
        self.inver_param.update_items_in_panel(plist)


    def OnLoadDemoModel2(self, event):
        """Loads Demo Model 2 from a file."""

        filespec = example_data(DEMO_MODEL2_DESC)

        # Read the entire input file into a buffer.
        try:
            fd = open(filespec, 'rU')
            demo_model_params = fd.read()
            fd.close()
        except Exception:
            popup_warning_message(
                "Load Model Error",
                "Error loading demo model from file "+DEMO_MODEL2_DESC)
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

        # Set surface SLD values for simulations 1 and 2 in the inversion and
        # reconstruction paramaters panel.
        # Note that datatype of None means do not change.
        plist = (0.0, 6.33,
                 None, None, None, None, None, None, None, None, None)
        self.inver_param.update_items_in_panel(plist)


    def OnLoadDemoModel3(self, event):
        """Loads Demo Model 3 from a file."""

        filespec = example_data(DEMO_MODEL3_DESC)

        # Read the entire input file into a buffer.
        try:
            fd = open(filespec, 'rU')
            demo_model_params = fd.read()
            fd.close()
        except Exception:
            popup_warning_message(
                "Load Model Error",
                "Error loading demo model from file "+DEMO_MODEL3_DESC)
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

        # Set surface SLD values for simulations 1 and 2 in the inversion and
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
                            style=wx.FD_OPEN)
        # Wait for user to close the dialog.
        sts = dlg.ShowModal()
        if sts == wx.ID_OK:
            pathname = dlg.GetDirectory()
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
        except Exception:
            popup_error_message(
                "Load Model Error",
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
            pathname = dlg.GetDirectory()
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
        except Exception:
            popup_error_message("Save Model Error",
                                "Error saving model to file "+filename)
            return

#==============================================================================

def perform_simulation(sample, params, Q=None, dQ=None):
    """
    Simulates reflectometry data sets from model information then performs
    phase reconstruction and direct inversion on the data to generate a
    scattering length density profile.
    """

    if len(sys.argv) > 1 and '--debug' in sys.argv[1:]:
        print("*** Inputs to perform_simulation()")
        print("*** sample =", sample)
        print("*** params =", params)
        if Q is not None:
            print("***  Q len =", len(Q), "  Q lo:hi =", Q[0], Q[-1])
        if dQ is not None:
            print("*** dQ len =", len(dQ), " dQ lo:hi =", dQ[0], dQ[-1])

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
    if noise < 0.01:
        noise = 0.01
    noise /= 100.0  # convert percent value to hundreths value

    # Convert flag from a string to a Boolean value.
    perfect_reconstruction = True if params[10] == "True" else False

    # For monochromatic instruments, Q will be None.
    if Q is None:
        Q = np.linspace(params[2], params[3], params[4])

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
                          left=0.09, right=0.96,
                          top=0.95, bottom=0.08)

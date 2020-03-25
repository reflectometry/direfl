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
This module implements the InstrumentParameters class for obtaining data used
for calculating resolution.
"""

#==============================================================================
from __future__ import print_function

import sys

import wx

from numpy import inf

from ..api.ncnrdata import ANDR, NG1, NG7, XRay, NCNRLoader
from ..api.snsdata import Liquids, Magnetic, SNSLoader

from .input_list import InputListDialog

#==============================================================================

class InstrumentParameters():
    """
    This class is responsible for gathering instrument parameters (also known
    as resoution parameters or instrument metadata) from the user.
    """

    def __init__(self):
        self.instr_classes = [ANDR, NG1, NG7, XRay, Liquids, Magnetic]
        self.instr_location = ["NCNR", "NCNR", "NCNR", "NCNR", "SNS", "SNS"]

        # Get the instrument name and radiation type for each instrument.
        self.instr_names = []
        self.radiation = []
        for classname in self.instr_classes:
            self.instr_names.append(classname.instrument)
            self.radiation.append(classname.radiation)
        n = len(self.instr_classes)

        # Editable parameters are stored in 2 x n lists where list[0] contains
        # default values by instrument and list[1] holds their current values.
        # n is the number of instruments supported.  For a given instrument
        # only a subset of the parameters may be applicable.
        self.wavelength = [[None] * n, [None] * n]  # monochromatic
        self.wavelength_lo = [[None] * n, [None] * n]  # polychromatic
        self.wavelength_hi = [[None] * n, [None] * n]  # polychromatic
        self.dLoL = [[None] * n, [None] * n]  # both
        self.d_s1 = [[None] * n, [None] * n]  # both
        self.d_s2 = [[None] * n, [None] * n]  # both
        self.T = [[None] * n, [None] * n]  # polychromatic
        self.Tlo = [[None] * n, [None] * n]  # monochromatic
        self.Thi = [[None] * n, [None] * n]  # monochromatic
        self.slit1_size = [[None] * n, [None] * n]  # polychromatic
        self.slit2_size = [[None] * n, [None] * n]  # polychromatic
        self.slit1_at_Tlo = [[None] * n, [None] * n]  # monochromatic
        self.slit2_at_Tlo = [[None] * n, [None] * n]  # monochromatic
        self.slit1_below = [[None] * n, [None] * n]  # monochromatic
        self.slit2_below = [[None] * n, [None] * n]  # monochromatic
        self.slit1_above = [[None] * n, [None] * n]  # monochromatic
        self.slit2_above = [[None] * n, [None] * n]  # monochromatic
        self.sample_width = [[None] * n, [None] * n]  # both
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
            except Exception:
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
             "float", 'REH2', None, "Instrument Settings"],
            ["Wavelength Dispersion (dLoL):", self.dLoL[1][i],
             "float", 'RE', None],
            ["Distance to Slit 1 (mm):", self.d_s1[1][i],
             "float", 'RE', None],
            ["Distance to Slit 2 (mm):", self.d_s2[1][i],
             "float", 'RE', None],
            ["Theta Lo (deg):", self.Tlo[1][i],
             "float", 'REH2', None, "Measurement Settings"],
            ["Theta Hi (deg):", self.Thi[1][i],
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
            ["Sample Broadening (deg):", self.sample_broadening[1][i],
             "float", 'E', None],
            ]

        # Get instrument and measurement parameters via a pop-up dialog box.
        # Pass in the frame object as the parent window so that the dialog box
        # will inherit font info from it instead of using system defaults.
        frame = wx.FindWindowByName("AppFrame")
        x, y = frame.GetPosition()
        dlg = InputListDialog(parent=frame,
                              title="Instrument Properties",
                              pos=(x+350, y+50),
                              itemlist=fields,
                              align=True)
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetResultsAltFormat()
            if len(sys.argv) > 1 and '--tracep' in sys.argv[1:]:
                print("*** Instrument (resolution) parameters:")
                print(results)

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
             "float", 'REH2', None, "Instrument Settings"],
            ["Wavelength Hi (A):", self.wavelength_hi[1][i],
             "float", 'RE', None],
            ["Wavelength Dispersion (dLoL):", self.dLoL[1][i],
             "float", 'RE', None],
            ["Distance to Slit 1 (mm):", self.d_s1[1][i],
             "float", 'RE', None],
            ["Distance to Slit 2 (mm):", self.d_s2[1][i],
             "float", 'RE', None],
            ["Theta (deg):", self.T[1][i],
             "float", 'REH2', None, "Measurement Settings"],
            ["Size of Slit 1 (mm):", self.slit1_size[1][i],
             "float", 'RE', None],
            ["Size of Slit 2 (mm):", self.slit2_size[1][i],
             "float", 'RE', None],
            ["Sample Width (mm):", self.sample_width[1][i],
             "float", 'EL', None],
            ["Sample Broadening (deg):", self.sample_broadening[1][i],
             "float", 'E', None],
            ]

        # Get instrument and measurement parameters via a pop-up dialog box.
        # Pass in the frame object as the parent window so that the dialog box
        # will inherit font info from it instead of using system defaults.
        frame = wx.FindWindowByName("AppFrame")
        x, y = frame.GetPosition()
        dlg = InputListDialog(parent=frame,
                              title="Instrument Properties",
                              pos=(x+350, y+50),
                              itemlist=fields,
                              align=True)
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetResultsAltFormat()
            if len(sys.argv) > 1 and '--tracep' in sys.argv[1:]:
                print("*** Instrument (resolution) parameters:")
                print(results)

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

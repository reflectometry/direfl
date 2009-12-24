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
This module implements the generic Item List Input Box and a helper class for
validating user input.
"""

import wx
from wx.lib.scrolledpanel import ScrolledPanel


class ItemListValidator(wx.PyValidator):
    """
    This class implements a custom item list validator.  Each instance of this
    class services one data entry field of the display.  The parameter item is
    a list where element:
    - [0] is not used by this class
    - [1] contains the default value and will be updated with the final result
    - [2] specifies the datatype of the field
    - [3] is not used by this class
    - [4] is not used by this class
    """

    def __init__(self, item):
        wx.PyValidator.__init__(self)
        self.item = item
        self.value = item[1]
        self.type = item[2]


    def Clone(self):
        # Every validator must implement the Clone() method that returns a
        # instance of the class as follows:
        return ItemListValidator(self.item)


    def Validate(self, win):
        """
        Verify that user input is of the datatype specified:
        - 'float', a floating point value
        - 'int', a signed or unsigned integer value
        - 'str', a string of non-zero length after whitespace has been trimmed
        - 'any', a string of any length after whitespace has been trimmed
        - '' or an unknown string, a raw string with input validation disabled
        On error, the field is highlighted and the cursor is placed there.
        """
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()

        try:
            if self.type == "float":
                if len(text) == 0:
                    self.value = 0.0
                else:
                    self.value = float(text)
            elif self.type == "int":
                if len(text) == 0:
                    self.value = 0
                else:
                    self.value = int(text)
            elif self.type == "str":
                self.value = str(text).strip()
                if len(self.value) == 0:
                    wx.MessageBox("Please fill in the box.     ",
                                  "Blank Field", wx.ICON_EXCLAMATION|wx.OK)
                    textCtrl.SetBackgroundColour("yellow")
                    textCtrl.SetFocus()
                    textCtrl.Refresh()
                    return False
            elif self.type == "any":
                self.value = str(text).strip()
            else:
                self.value = str(text)

            textCtrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            self.TransferFromWindow()
            return True

        except:
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False


    def TransferToWindow(self):
        # The parent of this class is responsible for setting the default value
        # for the field (e.g., by calling wx.TextCtrl() or wx.ComboBox() or
        # instance.SetValue(), etc.).
        return True


    def TransferFromWindow(self):
        # Save the final result of the edit that has already been validated.
        # If more validation is needed (such as limit checking), it should be
        # performed by the caller after retrieving this data.
        self.item[1] = self.value
        return True

#==============================================================================

class ItemListInput(ScrolledPanel):
    """
    This class implements the generic Item List Input Box.
    It displays one or more input fields each preceded by a label.  The input
    fields can be a combination of data entry boxes or drop down combo boxes.
    Automatic validation of user input is performed.  The caller can use the
    GetResults() method to obtain the final results from all fields in the form
    of a list of values.

    The layout is:

    +-------------------------------------+
    |                                     |
    |  Label-1:   [<drop down list>  |V]  |
    |                                     |    Note that drop down lists and
    |  Label-2:   [<data entry field-2>]  |    simple data entry fields can be
    |  ...                                |    in any order.
    |  Label-n:   [<data entry field-n>]  |
    |                                     |
    +-------------------------------------+

    The itemlist parameter controls the display.  It is a list containing one
    or more 5-element lists where each list specifies a:
    - label string
    - default value
    - datatype for validation (see ItemListValidator.Validate() for details)
    - list of values for a combo box or None for a simple data entry field
    - flag to indicate that the field accepts user input (True) or the field is
      grayed-out (False); grayed-out fields have their default values returned
    """

    def __init__(self, parent, id=wx.ID_ANY, itemlist=[], **kwargs):
        ScrolledPanel.__init__(self, parent, id,
                               style=(wx.BORDER_RAISED|wx.TAB_TRAVERSAL),
                               **kwargs)

        self.itemlist = itemlist
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))

        # Specify the widget layout using sizers.
        # The main_sizer is the top-level sizer that manages everything.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        sbox = wx.StaticBox(self, wx.ID_ANY, "Parameters")
        sbox_sizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)

        # Create the text controls for labels and associated input fields.
        self._add_items_to_input_box()

        # Create the grid sizer that organizes the labels and input fields.
        grid_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        grid_sizer.AddGrowableCol(1)
        self._add_items_to_sizer(grid_sizer)

        sbox_sizer.Add(grid_sizer, 1)

        # Add the grid sizer to the main sizer.
        main_sizer.Add(sbox_sizer, 0, wx.EXPAND|wx.ALL, 10)

        # Finalize the sizer and establish the dimensions of the input box.
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        # Enable scrolling and initialize the validators (required when
        # validators are not used within a dialog box).
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.InitDialog()


    def _add_items_to_input_box(self):
        # Note that the validator will update self.itemlist successful
        # validation of user input.
        self.labels = []; self.inputs = []
        for x in xrange(len(self.itemlist)):
            text, default, datatype, combolist, editable = self.itemlist[x]

            self.labels.append(wx.StaticText(self, wx.ID_ANY, label=text))

            if combolist is None:  # it is a simple data entry field
                self.inputs.append(wx.TextCtrl(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(self.itemlist[x])))
                self.Bind(wx.EVT_TEXT, self.OnText, self.inputs[x])
            else:                  # it is a drop down combo box list
                self.inputs.append(wx.ComboBox(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(self.itemlist[x]),
                                   choices=combolist,
                                   style=wx.CB_DROPDOWN|wx.CB_READONLY))
                self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, self.inputs[x])

            if not editable:
                self.inputs[x].Enable(False)  # disallow edits to field


    def _add_items_to_sizer(self, sizer):
        for x in xrange(len(self.itemlist)):
            sizer.Add(self.labels[x], 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.inputs[x], 0, wx.EXPAND)


    def _update_items_in_input_box(self, new_values):
        for x in xrange(len(self.inputs)):
            if new_values[x] is not None:
                self.inputs[x].SetValue(str(new_values[x]))


    def GetResults(self):
        # Return a list of values, one for each input field.  The value of for
        # a field is either its initial (default) value or the last value
        # entered by the user that has been successfully validated.  An input
        # that fails validation is not returned by the validator from the
        # window.  For a non-editable field, its initial value is returned.
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(self.itemlist[x][1])
        return ret


    def GetRawValues(self):
        # Return a list of strings corresponding to each input field.  These
        # are the current values from the text control widgets when may have
        # failed validation.  All values are returned as strings (i.e., they
        # are not converted to floats or ints).
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(str(self.inputs[x].GetValue()))
        return ret


    def OnText(self, event):
        """
        This method gets called each time a key stroke is entered in a text
        control box.  It should be subclassed if special processing is needed.
        """

        # Get index of the input box that triggered the event.
        textCtrl = event.GetEventObject()
        for box_idx, box_instance in enumerate(self.inputs):
            if textCtrl is box_instance:
                break
        # Get the edited string.
        text = textCtrl.GetValue()
        # box_idx, text

        # Run the validator bound to the text control box that has been edited.
        textCtrl.GetValidator().Validate(textCtrl)
        event.Skip()


    def OnComboBoxSelect(self, event):
        """
        This method captures combo box selection actions by the user from all
        combo boxes instantiated by the ItemListInput class.  This method
        should be subclassed if the caller wants to perform some action in
        response to a selection event.  The sample code below shows how to
        obtain the index of the box and index of the item selected.

        # Get index of selected item in combo box dropdown list.
        item_idx = event.GetSelection()
        # Get index of combo box that triggered the event.
        current_box = event.GetEventObject()
        for box_idx, box_instance in enumerate(self.inputs):
            if current_box is box_instance:
                break
        print box_idx, item_idx, self.itemlist[box_idx][3][item_idx]
        """
        event.Skip()

#==============================================================================

if __name__ == '__main__':
    """GUI unit test of the ItemListInput class and input field validation."""

    fields = [ ["Integer:", 123, "int", None, True],
               ["Floating Point:", 45.678, "float", None, True],
               ["Non-editable field:", "Cannot be changed!", "str", None, False],
               ["String (1 or more char):", "Error if blank", "str", None, True],
               ["String (0 or more char):", "", "any", None, True],
               ["ComboBox String:", "Two", "str", ("One", "Two", "Three"), True],
               ["String (no validation):", "DANSE Project", "", None, True]
             ]

    app = wx.PySimpleApp()

    # Test 1
    dlg = ItemListInput(parent=None)
    if dlg.ShowModal() == wx.ID_OK:
        print "Results from all input fields:"
        print "  ", dlg.GetResults()
    dlg.Destroy()

    # Test 2
    dlg = ItemListInput(parent=None,
                         title="Test of ItemListInput Box",
                         itemlist=fields)
    if dlg.ShowModal() == wx.ID_OK:
        print "Results from all input fields:"
        print "  ", dlg.GetResults()
    dlg.Destroy()

    app.MainLoop()

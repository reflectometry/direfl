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

# Author: James Krycka

"""
This module implements the generic Item List Input Box and a helper class for
validating user input.
"""

import wx
from wx.lib.scrolledpanel import ScrolledPanel

BKGD_COLOUR_WINDOW = "#ECE9D8"


class ItemListValidator(wx.PyValidator):
    """
    This class implements a custom item list validator.  Each instance of this
    class services one data entry field of the display.  Parameters are:

    - datatype of the field used during input validation as follows:
      o 'int'       => signed or unsigned integer value
      o 'float'     => floating point value
      o 'str'       => string of characters
      o 'str_alpha' => string of alphabetic characters {A-Z, a-z}
      o 'str_alnum' => string of alphanumeric characters {A-Z, a-z, 0-9}
      o 'str_id'    => string identifier consisting of {A-Z, a-z, 0-9, _, -}
      o '' or any unknown datatype is treated the same as 'str'

    - flag to indicate whether user input is required (True) or optional (False)
    """

    def __init__(self, datatype='str', required=True):
        wx.PyValidator.__init__(self)
        self.datatype = datatype
        self.required = required


    def Clone(self):
        # Every validator must implement the Clone() method that returns a
        # instance of the class as follows:
        return ItemListValidator(self.datatype, self.required)


    def Validate(self, win):
        """
        Verify user input according to the expected datatype.  Leading and
        trailing whitespace is always stripped before evaluation.  Floating and
        integer values are returned as normalized float or int objects; thus
        conversion can generate an error.  On error, the field is highlighted
        and the cursor is placed there.  Note that all string datatypes are
        returned stripped of leading and trailing whitespace.
        """

        text_ctrl = self.GetWindow()
        text = text_ctrl.GetValue().strip()

        try:
            if self.datatype == "int":
                if len(text) == 0:
                    self.value = 0
                    self.value_alt = None
                    if self.required:
                        raise RuntimeError("input required")
                else:
                    self.value = self.value_alt = int(text)
            elif self.datatype == "float":
                if len(text) == 0:
                    self.value = 0.0
                    self.value_alt = None
                    if self.required:
                        raise RuntimeError("input required")
                else:
                    self.value = self.value_alt = float(text)
            elif self.datatype == 'str_alpha':
                if len(text) == 0:
                    self.value = ''
                    self.value_alt = None
                    if self.required:
                        raise RuntimeError("input required")
                else:
                    if text.isalpha():
                        self.value = self.value_alt = str(text)
                    else:
                        raise ValueError("input must be alphabetic")
            elif self.datatype == 'str_alnum':
                if len(text) == 0:
                    self.value = ''
                    self.value_alt = None
                    if self.required:
                        raise RuntimeError("input required")
                else:
                    if text.isalnum():
                        self.value = self.value_alt = str(text)
                    else:
                        raise ValueError("input must be alphanumeric")
            elif self.datatype == 'str_id':
                if len(text) == 0:
                    self.value = ''
                    self.value_alt = None
                    if self.required:
                        raise RuntimeError("input required")
                else:
                    temp = text.replace('_', 'a').replace('-','a')
                    if temp.isalnum():
                        self.value = self.value_alt = str(text)
                    else:
                        raise ValueError("input must be alphanumeric, _, or -")
            else:  # For self.datatype of "str", "", or any unrecognized type.
                if len(text) == 0:
                    self.value = ''
                    self.value_alt = None
                    if self.required:
                        raise RuntimeError("input required")
                else:
                    self.value = self.value_alt = str(text)

            text_ctrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.Refresh()
            self.TransferFromWindow()
            return True

        except RuntimeError:
            text_ctrl.SetBackgroundColour("YELLOW")
            text_ctrl.SetFocus()
            text_ctrl.Refresh()
            return False

        except:
            text_ctrl.SetBackgroundColour("PINK")
            text_ctrl.SetFocus()
            text_ctrl.Refresh()
            return False


    def TransferToWindow(self):
        # The parent of this class is responsible for setting the default value
        # for the field (e.g., by calling wx.TextCtrl() or wx.ComboBox() or
        # instance.SetValue(), etc.).
        return True  # Default is False for failure


    def TransferFromWindow(self):
        # Data has already been transferred from the window and validated
        # in Validate(), so there is nothing useful to do here.
        return True  # Default is False for failure


    def GetValidatedInput(self):
        # Return the validated value or zero or blank for a null input.
        return self.value


    def GetValidatedInputAlt(self):
        # Return the validated value or None for a null input.
        return self.value_alt

#==============================================================================

class InputListPanel(ScrolledPanel):
    """
    This class implements a general purpose mechanism for obtaining and
    validating user input from several fields in a window with scroll bars.
    (See InputListDialog that uses a dialog box instead of a scrolled window.)

    It creates a scrolled window in which to display one or more input fields
    each preceded by a label.  The input fields can be a combination of simple
    data entry boxes or drop down combo boxes.  Automatic validation of user
    input is performed.  The caller can use the GetResults() method to obtain
    the final results from all fields in the form of a list of values.

    The scrolled window object is created as a child of the parent panel passed
    in.  Normally the caller of this class puts this returned object in a sizer
    attached to the parent panel to allow it to expand or contract based on the
    size constraints imposed by its parent.

    The layout is:

    +-------------------------------------+-+
    |                                     |v|
    |  Label-1:   [<drop down list>  |V]  |e|
    |                                     |r|   Note that drop down lists and
    |  Label-2:   [<data entry field-2>]  |t|   simple data entry fields can
    |  ...                                |||   be specified in any order.
    |  Label-n:   [<data entry field-n>]  |||
    |                                     |v|
    +-------------------------------------+-+   Note that scroll bars are
    |      horizontal scroll bar -->      | |   visible only when needed.
    +-------------------------------------+-+

    The itemlist parameter controls the display.  It is a list containing one
    or more 5-element lists where each list specifies a:
    - label string
    - default value
    - datatype for validation (see the ItemListValidator docstring for details)
    - list of values for a combo box or None for a simple data entry field
    - flags in the form of a string of characters to specify:
      o input is required ('R') or is optional ('r') and therefore can be blank
      o field is editable by the user ('E') or cannot be changed ('e) and is
        grayed-out; a non-editable field has its default value returned
      The default flags value is required and editable ('RE').
    """

    def __init__(self,
                 parent,
                 id       = wx.ID_ANY,
                 pos      = wx.DefaultPosition,
                 size     = wx.DefaultSize,
                 style    =(wx.BORDER_RAISED|wx.TAB_TRAVERSAL),
                 name     = "",
                 itemlist = []
                ):
        ScrolledPanel.__init__(self, parent, id, pos, size, style, name)

        self.itemlist = itemlist
        self.SetBackgroundColour(BKGD_COLOUR_WINDOW)

        # Specify the widget layout using sizers.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the text controls for labels and associated input fields.
        self.add_items_to_input_box()

        # Create the grid sizer that organizes the labels and input fields.
        grid_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        grid_sizer.AddGrowableCol(1)
        self.add_items_to_sizer(grid_sizer)

        # Add the grid sizer to the main sizer.
        main_sizer.Add(grid_sizer, 1, wx.EXPAND|wx.ALL, border=10)

        # Finalize the sizer and establish the dimensions of the input box.
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        # Enable scrolling and initialize the validators (required when
        # validators are not used in the context of a dialog box).
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.InitDialog()


    def add_items_to_input_box(self):
        # Note that the validator will update self.itemlist upon successful
        # validation of user input.
        self.labels = []; self.inputs = []
        for x in xrange(len(self.itemlist)):
            text, default, datatype, combolist, flags = self.itemlist[x]
            required = True
            if flags.find('r') >= 0: required = False
            editable = True
            if flags.find('e') >= 0: editable = False

            self.labels.append(wx.StaticText(self, wx.ID_ANY, label=text))

            if combolist is None:  # it is a simple data entry field
                self.inputs.append(wx.TextCtrl(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required)))
                self.Bind(wx.EVT_TEXT, self.OnText, self.inputs[x])
            else:                  # it is a drop down combo box list
                self.inputs.append(wx.ComboBox(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required),
                                   choices=combolist,
                                   style=wx.CB_DROPDOWN|wx.CB_READONLY))
                self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, self.inputs[x])

            if not editable:
                self.inputs[x].Enable(False)  # disallow edits to the field


    def add_items_to_sizer(self, sizer):
        for x in xrange(len(self.itemlist)):
            sizer.Add(self.labels[x], 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.inputs[x], 0, wx.EXPAND)


    def update_items_in_input_box(self, new_values):
        for x in xrange(len(self.inputs)):
            if new_values[x] is not None:
                self.inputs[x].SetValue(str(new_values[x]))


    def GetResults(self):
        # Returns a list of values, one for each input field.  The value for
        # a field is either its initial (default) value or the last value
        # entered by the user that has been successfully validated.  An input
        # that fails validation is not returned by the validator from the
        # window.  For a non-editable field, its initial value is returned.
        # Blank input is converted to 0.0, 0, or a null string as appropriate
        # for the datatype of the field
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(self.inputs[x].GetValidator().GetValidatedInput())
        return ret


    def GetResultsAltFormat(self):
        # Returns a list of values, one for each input field.  The value for
        # a field is either its initial (default) value or the last value
        # entered by the user that has been successfully validated.  An input
        # that fails validation is not returned by the validator from the
        # window.  For a non-editable field, its initial value is returned.
        # Blank input is returned as a value of None.
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(self.inputs[x].GetValidator().GetValidatedInputAlt())
        return ret


    def GetResultsRawInput(self):
        # Returns a list of strings corresponding to each input field.  These
        # are the current values from the text control widgets which may have
        # failed validation.  All values are returned as strings (i.e., they
        # are not converted to floats or ints and whitespace is not stripped).
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(str(self.inputs[x].GetValue()))
        return ret


    def OnText(self, event):
        """
        This method is called each time a key stroke is entered in any text
        control box.  It should be subclassed if special processing is needed.
        The sample code below shows how to obtain the index of the box and its
        value.  Note that the box's index is 0 to n, where n is the number of
        input and combo boxes, not just the number of input boxes.

        # Get index of the input box that triggered the event.
        text_ctrl = event.GetEventObject()
        for box_idx, box_instance in enumerate(self.inputs):
            if text_ctrl is box_instance:
                break
        # Get the edited string.
        text = text_ctrl.GetValue()
        print "Field:", box_idx, text
        """

        # Run the validator bound to the text control box that has been edited.
        # If the validation fails, the validator will highlight the input field
        # to alert the user of the error.
        text_ctrl = event.GetEventObject()
        text_ctrl.GetValidator().Validate(text_ctrl)
        event.Skip()


    def OnComboBoxSelect(self, event):
        """
        This method captures combo box selection actions by the user from all
        combo boxes instantiated by the InputListPanel class.  This method
        should be subclassed if the caller wants to perform some action in
        response to a selection event.  The sample code below shows how to
        obtain the index of the box, the index of the item selected, and the
        value.  Note that the box's index is 0 to n, where n is the number of
        combo and input boxes, not just the number of combo boxes.

        # Get index of selected item in combo box dropdown list.
        item_idx = event.GetSelection()
        # Get index of combo box that triggered the event.
        current_box = event.GetEventObject()
        for box_idx, box_instance in enumerate(self.inputs):
            if current_box is box_instance:
                break
        print "Combo:", box_idx, item_idx, self.itemlist[box_idx][3][item_idx]
        """
        event.Skip()

#==============================================================================

class InputListDialog(wx.Dialog):
    """
    This class implements a general purpose mechanism for obtaining and
    validating user input from several fields in a pop-up dialog box.
    (See InputListPanel that uses a scrolled window instead of a dialog box.)

    It creates a pop-up dialog box in which to display one or more input fields
    each preceded by a label.  The input fields can be a combination of simple
    data entry boxes or drop down combo boxes.  Automatic validation of user
    input is performed.  OK and Cancel buttons are provided at the bottom of
    the dialog box for the user to signal completion of data entry whereupon
    the caller can use the GetResults() method to obtain the final results from
    all fields in the form of a list of values.  As with any dialog box, when
    the user presses OK or Cancel the dialog disappears from the screen, but
    the caller of this class is responsible for destroying the dialog box.

    The dialog box is automatically sized to fit the fields and buttons with
    reasonable spacing between the widgets.  The layout is:

    +-------------------------------------+
    |  Title                          [X] |
    +-------------------------------------+
    |                                     |
    |  Label-1:   [<drop down list>  |V]  |
    |                                     |     Note that drop down lists and
    |  Label-2:   [<data entry field-2>]  |     simple data entry fields can
    |  ...                                |     be specified in any order.
    |  Label-n:   [<data entry field-n>]  |
    |                                     |
    |       [  OK  ]      [Cancel]        |
    |                                     |
    +-------------------------------------+

    The itemlist parameter controls the display.  It is a list containing one
    or more 5-element lists where each list specifies a:
    - label string
    - default value
    - datatype for validation (see the ItemListValidator docstring for details)
    - list of values for a combo box or None for a simple data entry field
    - flags in the form of a string of characters to specify:
      * input is required ('R') or is optional ('r') and therefore can be blank
      * field is editable by the user ('E') or cannot be changed ('e) and is
        grayed-out; a non-editable field has its default value returned
      The default flags value is required and editable ('RE').
    """

    def __init__(self,
                 parent   = None,
                 id       = wx.ID_ANY,
                 title    = "Enter Data",
                 pos      = wx.DefaultPosition,
                 size     = (300, -1),  # x is min_width; y will be calculated
                 style    = wx.DEFAULT_DIALOG_STYLE,
                 name     = "",
                 itemlist = []
                ):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)

        self.itemlist = itemlist

        # Create the text controls for labels and associated input fields.
        self.add_items_to_dialog_box()

        # Create the button controls (OK and Cancel) and bind their events.
        ok_button = wx.Button(self, wx.ID_OK, "OK")
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)

        # Specify the widget layout using sizers.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the grid sizer that organizes the labels and input fields.
        grid_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        grid_sizer.AddGrowableCol(1)
        self.add_items_to_sizer(grid_sizer)

        # Add the grid sizer to the main sizer.
        main_sizer.Add(grid_sizer, 0, wx.EXPAND|wx.ALL, 20)

        # Create the button sizer that will put the buttons in a row, right
        # justified, and with a fixed amount of space between them.  This
        # emulates the Windows convention for placing a set of buttons at the
        # bottom right of the window.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add((10,20), 1)  # stretchable whitespace
        button_sizer.Add(ok_button, 0)
        button_sizer.Add((10,20), 0)  # non-stretchable whitespace
        button_sizer.Add(cancel_button, 0)

        # Add the button sizer to the main sizer.
        main_sizer.Add(button_sizer, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT, border=20)

        # Finalize the sizer and establish the dimensions of the dialog box.
        # The minimum width is explicitly set because the sizer is not able to
        # take into consideration the width of the enclosing frame's title.
        self.SetSizer(main_sizer)
        main_sizer.SetMinSize((size[0], -1))
        main_sizer.Fit(self)


    def add_items_to_dialog_box(self):
        # Note that the validator will update self.itemlist upon successful
        # validation of user input.
        self.labels = []; self.inputs = []
        for x in xrange(len(self.itemlist)):
            text, default, datatype, combolist, flags = self.itemlist[x]
            required = True
            if flags.find('r') >= 0: required = False
            editable = True
            if flags.find('e') >= 0: editable = False

            self.labels.append(wx.StaticText(self, wx.ID_ANY, label=text))

            if combolist is None:  # it is a simple data entry field
                self.inputs.append(wx.TextCtrl(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required)))
                self.Bind(wx.EVT_TEXT, self.OnText, self.inputs[x])
            else:                  # it is a drop down combo box list
                self.inputs.append(wx.ComboBox(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required),
                                   choices=combolist,
                                   style=wx.CB_DROPDOWN|wx.CB_READONLY))
                self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, self.inputs[x])

            if not editable:
                self.inputs[x].Enable(False)  # disallow edits to the field


    def add_items_to_sizer(self, sizer):
        for x in xrange(len(self.itemlist)):
            sizer.Add(self.labels[x], 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.inputs[x], 0, wx.EXPAND)


    def update_items_in_dialog_box(self, new_values):
        for x in xrange(len(self.inputs)):
            if new_values[x] is not None:
                self.inputs[x].SetValue(str(new_values[x]))


    def GetResults(self):
        # Returns a list of values, one for each input field.  The value for
        # a field is either its initial (default) value or the last value
        # entered by the user that has been successfully validated.  An input
        # that fails validation is not returned by the validator from the
        # window.  For a non-editable field, its initial value is returned.
        # Blank input is converted to 0.0, 0, or a null string as appropriate
        # for the datatype of the field
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(self.inputs[x].GetValidator().GetValidatedInput())
        return ret


    def GetResultsAltFormat(self):
        # Returns a list of values, one for each input field.  The value for
        # a field is either its initial (default) value or the last value
        # entered by the user that has been successfully validated.  An input
        # that fails validation is not returned by the validator from the
        # window.  For a non-editable field, its initial value is returned.
        # Blank input is returned as a value of None.
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(self.inputs[x].GetValidator().GetValidatedInputAlt())
        return ret


    def GetResultsRawInput(self):
        # Returns a list of strings corresponding to each input field.  These
        # are the current values from the text control widgets which may have
        # failed validation.  All values are returned as strings (i.e., they
        # are not converted to floats or ints and whitespace is not stripped).
        ret = []
        for x in xrange(len(self.itemlist)):
            ret.append(str(self.inputs[x].GetValue()))
        return ret


    def OnOk(self, event):
        """
        This method gets called when the user presses the OK button.
        It is intended to be subclassed if special processing is needed.
        """

        MSG_TEXT = """\
Please correct all highlighted fields in error.
Yellow means an input value is required.
Pink denotes a syntax error."""

        # Explicitly validate all input values before proceeding.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the OK button without making
        # the corrections, so we'll do a full validation pass now.  The only
        # purpose is to display an explicit error if any input fails validation.
        if not self.Validate():
            wx.MessageBox(caption="Data Entry Error",
                          message=MSG_TEXT,
                          style=wx.ICON_ERROR|wx.OK)
            return  # keep the dialog box open

        # When the wx.ID_OK event is skipped (to allow handlers up the chain to
        # run), the Validate methods for all text control boxes will be called.
        # If all report success, the TransferFromWindow methods will be called
        # and the dialog box will close.  However, if any Validate method fails
        # this process will stop and the dialog box will remain open allowing
        # the user to either correct the problem(s) or cancel the dialog.
        event.Skip()


    def OnText(self, event):
        """
        This method is called each time a key stroke is entered in any text
        control box.  It should be subclassed if special processing is needed.
        The sample code below shows how to obtain the index of the box and its
        value.  Note that the box's index is 0 to n, where n is the number of
        input and combo boxes, not just the number of input boxes.

        # Get index of the input box that triggered the event.
        text_ctrl = event.GetEventObject()
        for box_idx, box_instance in enumerate(self.inputs):
            if text_ctrl is box_instance:
                break
        # Get the edited string.
        text = text_ctrl.GetValue()
        print "Field:", box_idx, text
        """

        # Run the validator bound to the text control box that has been edited.
        # If the validation fails, the validator will highlight the input field
        # to alert the user of the error.
        text_ctrl = event.GetEventObject()
        text_ctrl.GetValidator().Validate(text_ctrl)
        event.Skip()


    def OnComboBoxSelect(self, event):
        """
        This method captures combo box selection actions by the user from all
        combo boxes instantiated by the InputListDialog class.  This method
        should be subclassed if the caller wants to perform some action in
        response to a selection event.  The sample code below shows how to
        obtain the index of the box, the index of the item selected, and the
        value.  Note that the box's index is 0 to n, where n is the number of
        combo and input boxes, not just the number of combo boxes.

        # Get index of selected item in combo box dropdown list.
        item_idx = event.GetSelection()
        # Get index of combo box that triggered the event.
        current_box = event.GetEventObject()
        for box_idx, box_instance in enumerate(self.inputs):
            if current_box is box_instance:
                break
        print "Combo:", box_idx, item_idx, self.itemlist[box_idx][3][item_idx]
        """
        event.Skip()

#==============================================================================

class AppTestFrame(wx.Frame):
    """
    Interactively test both the InputListPanel and the InputListDialog classes.
    Both will display the same input fields.  Enter invalid data to verify
    char-by-char error processing.  Press the Submit and OK buttons with an
    uncorrected highlighted field in error to generate a pop-up error box.
    Resize the main window to see scroll bars disappear and reappear.
    """

    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="InputListPanel Test", size=(300, 600))
        panel = wx.Panel(self, wx.ID_ANY, style=wx.RAISED_BORDER)
        panel.SetBackgroundColour("PALE GREEN")

        # Define fields for both InputListPanel and InputListDialog to display.
        self.fields = [
            ["Integer (int, optional):", 12345, "int", None, 'rE'],
            ["Integer (int, optional):", "", "int", None, 'rE'],
            ["Integer (int, required):", -60, "int", None, 'RE'],
            ["Floating Point (float, optional):", 2.34567e-5, "float", None, 'rE'],
            ["Floating Point (float, optional):", "", "float", None, 'rE'],
            ["Floating Point (float, required):", 1.0, "float", None, 'RE'],
            ["String (str, optional):", "DANSE", "str", None, 'rE'],
            ["String (str, reqiured):", "", "str", None, 'RE'],
            # Pass in a null string for flags to test default values of 'RE'
            ["String (str, required):", "delete me", "str", None, ''],
            ["Non-editable field:", "Cannot be changed!", "foo", None, 're'],
            ["ComboBox String:", "Two", "str", ("One", "Two", "Three"), 'RE'],
            ["ComboBox String:", "", "int", ("100", "200", "300"), 'rE'],
            ["String (alphabetic):", "Aa", "str_alpha", None, 'rE'],
            ["String (alphanumeric):", "Aa1", "str_alnum", None, 'rE'],
            ["String (A-Z, a-z, 0-9, _, -):", "A-1_a", "str_id", None, 'rE'],
                      ]
        # Create the scrolled window with input boxes.  Due to the size of the
        # frame and the parent panel, both scroll bars should be displayed.
        self.scrolled = InputListPanel(parent=panel, itemlist=self.fields)

        # Create a button to request the popup dialog box.
        show_button = wx.Button(panel, wx.ID_ANY, "Show Pop-up Dialog Box")
        self.Bind(wx.EVT_BUTTON, self.OnShow, show_button)

        # Create a button to signal end of user edits and one to exit program.
        submit_button = wx.Button(panel, wx.ID_ANY, "Submit")
        self.Bind(wx.EVT_BUTTON, self.OnSubmit, submit_button)
        exit_button = wx.Button(panel, wx.ID_ANY, "Exit")
        self.Bind(wx.EVT_BUTTON, self.OnExit, exit_button)

        # Create a horizontal sizer for the buttons.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add((10,20), 1)  # stretchable whitespace
        button_sizer.Add(submit_button, 0)
        button_sizer.Add((10,20), 0)  # non-stretchable whitespace
        button_sizer.Add(exit_button, 0)

        # Create a vertical box sizer for the panel and layout widgets in it.
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(show_button, 0, wx.ALIGN_CENTER|wx.ALL, border=10)
        box_sizer.Add(self.scrolled, 1, wx.EXPAND|wx.ALL, border=10)
        box_sizer.Add(button_sizer, 0, wx.EXPAND|wx.BOTTOM|wx.ALL, border=10)

        # Associate the sizer with its container.
        panel.SetSizer(box_sizer)
        box_sizer.Fit(panel)


    def OnShow(self, event):
        # Display the same fields shown in the frame in a pop-up dialog box.
        dlg = InputListDialog(parent=None,
                              title="InputListDialog Test",
                              itemlist=self.fields)
        if dlg.ShowModal() == wx.ID_OK:
            print "****** Dialog Box results from validated input fields:"
            print "  ", dlg.GetResults()
            print "****** Dialog Box results from validated input fields (or None):"
            print "  ", dlg.GetResultsAltFormat()
            print "****** Dialog Box results from raw input fields:"
            print "  ", dlg.GetResultsRawInput()
        dlg.Destroy()


    def OnSubmit(self, event):
        # Explicitly validate all input parameters before proceeding.  Even
        # though char-by-char validation would have warned the user about any
        # invalid entries, the user could have pressed the Done button without
        # making the corrections, so a full validation pass is necessary.
        if not self.scrolled.Validate():
            wx.MessageBox(caption="Data Entry Error",
                message="Please correct the highlighted fields in error.",
                style=wx.ICON_ERROR|wx.OK)
            return  # keep the dialog box open
        print "****** Scrolled Panel results from validated input fields:"
        print "  ", self.scrolled.GetResults()
        print "****** Scrolled Panel results from validated input fields (or None):"
        print "  ", self.scrolled.GetResultsAltFormat()
        print "****** Scrolled Panel results from raw input fields:"
        print "  ", self.scrolled.GetResultsRawInput()


    def OnExit(self, event):
        # Terminate the program.
        self.Close()


if __name__ == '__main__':
    # Interactively test both the InputListPanel and the InputListDialog classes.
    app = wx.PySimpleApp()
    frame = AppTestFrame()
    frame.Show(True)
    app.MainLoop()

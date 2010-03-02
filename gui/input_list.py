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
This module implements InputListPanel, InputListDialog, and InputListValidator
classes to provide general purpose mechanisms for obtaining and validating user
input from a structured list of input fields.
"""

import wx
from wx.lib.scrolledpanel import ScrolledPanel

BKGD_COLOUR_WINDOW = "#ECE9D8"
PALE_YELLOW = "#FFFFB0"

DATA_ENTRY_ERRMSG = """\
Please correct any highlighted field in error.
Yellow means an input value is required.
Pink indicates a syntax error."""


class ItemListValidator(wx.PyValidator):
    """
    This class implements a custom input field validator.  Each instance of
    this class services one data entry field (typically implemented as
    wx.TextCtrl or a wx.ComboBox widget).  Parameters are:

    - datatype of the field (used when validating user input) as follows:
      o 'int'       => signed or unsigned integer value
      o 'float'     => floating point value
      o 'str'       => string of characters
      o 'str_alpha' => string of alphabetic characters {A-Z, a-z}
      o 'str_alnum' => string of alphanumeric characters {A-Z, a-z, 0-9}
      o 'str_id'    => string identifier consisting of {A-Z, a-z, 0-9, _, -}
      o '' or any unknown datatype is treated the same as 'str'

    - flag to indicate whether user input is required (True) or optional (False)
    """

    def __init__(self, datatype='str', required=False):
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
            text_ctrl.SetBackgroundColour(PALE_YELLOW)
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
    or more 5-element or 6-element lists where each list specifies a:

    - label string
    - default value
    - datatype for validation (see the ItemListValidator docstring for details)
    - flags parameter in the form of a string of characters to specify:
      o input is required ('R'),otherwise optional and therefore can be blank
      o field is editable by the user ('E'), otherwise non-editable and box is
        grayed-out; a non-editable field has its default value returned
      o field is a combobox ('C'), otherwise is it a simple data entry box
      o font size for header: small ('S'), medium ('M') default, or large ('L')
      Options can be combined in the flags string such as 'RE'.
    - list of values for a combo box or None for a simple data entry field
    - header string to be displayed above the label string of the input field
      (this list element is optional; if given it can be a text string or None)

    See the AppTestFrame class for a comprehensive example.
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

        self.SetBackgroundColour(BKGD_COLOUR_WINDOW)
        self.itemlist = itemlist
        self.item_cnt = len(self.itemlist)
        if self.item_cnt == 0:
            return

        # Specify the widget layout using sizers.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the text controls for labels and associated input fields
        # and any optional headers.
        self.add_items_to_panel()

        # Divide the input items into sections prefaced by header text (except
        # that the first section is not required to have a header).  A section
        # list is created that contains the index of the item that starts a new
        # section plus a final entry that is one beyond the last item.
        sect = [0]  # declare item 0 to be start of a new section
        for i in xrange(self.item_cnt):
            if i > 0 and self.headers[i] is not None:
                sect.append(i)
        sect.append(self.item_cnt)

        # Place the items for each section in its own flex grid sizer.
        for i in xrange(len(sect)-1):
            j = sect[i]; k = sect[i+1] - 1
            fg_sizer = self.add_items_to_sizer(j, k)

            # Add the flex grid sizer to the main sizer.
            if self.headers[j] is not None:  # self.headers[0] could be None
                main_sizer.Add(self.headers[j], 0, border=10,
                               flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT)
            main_sizer.Add(fg_sizer, 0, border=10,
                           flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT)

        # Finalize the sizer and establish the dimensions of the input box.
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        # Enable scrolling and initialize the validators (required when
        # validators are not used in the context of a dialog box).
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.InitDialog()


    def add_items_to_panel(self):
        """
        For each input item, create a header (optional), label, and input box
        widget to instantiate it.  Put the handles for these widgets in the
        headers, labels, and inputs lists where the length of each list is the
        same as the number of input boxes.
        """

        self.headers = []; self.labels = []; self.inputs = []

        for x in xrange(self.item_cnt):
            params = len(self.itemlist[x])
            if params == 6:
                text, default, datatype, flags, plist, header = self.itemlist[x]
            elif params == 5:
                text, default, datatype, flags, plist = self.itemlist[x]
                header = None
            required = False
            if flags.find('R') >= 0: required = True
            editable = False
            if flags.find('E') >= 0: editable = True
            combo = False
            if flags.find('C') >= 0: combo = True
            font_size = 8  # small
            if flags.find('M') >= 0: font_size = 9
            if flags.find('L') >= 0: font_size = 10

            if header is None:
                self.headers.append(None)
            else:
                hdr = wx.StaticText(self, wx.ID_ANY, label=header,
                                    style=wx.ALIGN_CENTER)
                hdr.SetFont(wx.Font(font_size, wx.SWISS, wx.NORMAL, wx.BOLD))
                self.headers.append(hdr)

            self.labels.append(wx.StaticText(self, wx.ID_ANY, label=text))

            if combo:              # it is a drop down combo box list
                self.inputs.append(wx.ComboBox(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required),
                                   choices=plist,
                                   style=wx.CB_DROPDOWN|wx.CB_READONLY))
                self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, self.inputs[x])
            else:                  # it is a simple data entry field
                self.inputs.append(wx.TextCtrl(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required)))
                self.Bind(wx.EVT_TEXT, self.OnText, self.inputs[x])

            if not editable:
                # disallow edits to the field
                self.inputs[x].Enable(False)

            # Validate the default value and highlight the field if the value is
            # in error or if input is required and the value is a null string.
            self.inputs[x].GetValidator().Validate(self.inputs[x])


    def add_items_to_sizer(self, start, end):
        sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        for x in xrange(start, end+1):
            sizer.Add(self.labels[x], 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.inputs[x], 0, wx.EXPAND)
        sizer.AddGrowableCol(1)
        return sizer


    def update_items_in_panel(self, new_values):
        for x in xrange(len(self.inputs)):
            if new_values[x] is not None:
                self.inputs[x].SetValue(str(new_values[x]))


    def GetResults(self):
        """
        Returns a list of values, one for each input field.  The value for
        a field is either its initial (default) value or the last value
        entered by the user that has been successfully validated.  An input
        that fails validation is not returned by the validator from the
        window.  For a non-editable field, its initial value is returned.
        Blank input is converted to 0.0, 0, or a null string as appropriate
        for the datatype of the field
        """

        ret = []
        for x in xrange(self.item_cnt):
            ret.append(self.inputs[x].GetValidator().GetValidatedInput())
        return ret


    def GetResultsAltFormat(self):
        """
        Returns a list of values, one for each input field.  The value for
        a field is either its initial (default) value or the last value
        entered by the user that has been successfully validated.  An input
        that fails validation is not returned by the validator from the
        window.  For a non-editable field, its initial value is returned.
        Blank input is returned as a value of None.
        """

        ret = []
        for x in xrange(self.item_cnt):
            ret.append(self.inputs[x].GetValidator().GetValidatedInputAlt())
        return ret


    def GetResultsRawInput(self):
        """
        Returns a list of strings corresponding to each input field.  These
        are the current values from the text control widgets which may have
        failed validation.  All values are returned as strings (i.e., they
        are not converted to floats or ints and whitespace is not stripped).
        """

        ret = []
        for x in xrange(self.item_cnt):
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
        This method is called each time a selection is made in any combo box.
        It should be subclassed if the caller wants to perform some action in
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

        # Run the validator bound to the combo box that has a selection event.
        # This should not fail unless the combo options were setup incorrectly.
        # If the validation fails, the validator will highlight the input field
        # to alert the user of the error.
        combo_box = event.GetEventObject()
        combo_box.GetValidator().Validate(combo_box)
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
    or more 5-element or 6-element lists where each list specifies a:

    - label string
    - default value
    - datatype for validation (see the ItemListValidator docstring for details)
    - flags parameter in the form of a string of characters to specify:
      o input is required ('R'),otherwise optional and therefore can be blank
      o field is editable by the user ('E'), otherwise non-editable and box is
        grayed-out; a non-editable field has its default value returned
      o field is a combobox ('C'), otherwise is it a simple data entry box
      o font size for header: small ('S'), medium ('M') default, or large ('L')
      Options can be combined in the flags string such as 'RE'.
    - list of values for a combo box or None for a simple data entry field
    - header string to be displayed above the label string of the input field
      (this list element is optional; if given it can be a text string or None)

    See the AppTestFrame class for a comprehensive example.
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
        self.item_cnt = len(self.itemlist)
        if self.item_cnt == 0:
            return

        # Create the button controls (OK and Cancel) and bind their events.
        ok_button = wx.Button(self, wx.ID_OK, "OK")
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)

        # Specify the widget layout using sizers.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the text controls for labels and associated input fields
        # and any optional headers.
        self.add_items_to_dialog_box()

        # Divide the input items into sections prefaced by header text (except
        # that the first section is not required to have a header).  A section
        # list is created that contains the index of the item that starts a new
        # section plus a final entry that is one beyond the last item.
        sect = [0]  # declare item 0 to be start of a new section
        for i in xrange(self.item_cnt):
            if i > 0 and self.headers[i] is not None:
                sect.append(i)
        sect.append(self.item_cnt)
        #print "Section index list:", sect

        # Place the items for each section in its own flex grid sizer.
        for i in xrange(len(sect)-1):
            j = sect[i]; k = sect[i+1] - 1
            #print "Items per section:", j, "to", k
            fg_sizer = self.add_items_to_sizer(j, k)

            # Add the flex grid sizer to the main sizer.
            if self.headers[j] is not None:  # self.headers[0] could be None
                main_sizer.Add(self.headers[j], 0, border=10,
                               flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT)
            main_sizer.Add(fg_sizer, 0, border=10,
                           flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT)

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
        main_sizer.Add(button_sizer, 0, border=10,
                       flag=wx.EXPAND|wx.TOP|wx.BOTTOM|wx.RIGHT)

        # Finalize the sizer and establish the dimensions of the dialog box.
        # The minimum width is explicitly set because the sizer is not able to
        # take into consideration the width of the enclosing frame's title.
        self.SetSizer(main_sizer)
        main_sizer.SetMinSize((size[0], -1))
        main_sizer.Fit(self)


    def add_items_to_dialog_box(self):
        """
        For each input item, create a header (optional), label, and input box
        widget to instantiate it.  Put the handles for these widgets in the
        headers, labels, and inputs lists where the length of each list is the
        same as the number of input boxes.
        """

        self.headers = []; self.labels = []; self.inputs = []

        for x in xrange(self.item_cnt):
            params = len(self.itemlist[x])
            if params == 6:
                text, default, datatype, flags, plist, header = self.itemlist[x]
            elif params == 5:
                text, default, datatype, flags, plist = self.itemlist[x]
                header = None
            required = False
            if flags.find('R') >= 0: required = True
            editable = False
            if flags.find('E') >= 0: editable = True
            combo = False
            if flags.find('C') >= 0: combo = True
            font_size = 8  # small
            if flags.find('M') >= 0: font_size = 9
            if flags.find('L') >= 0: font_size = 10

            if header is None:
                self.headers.append(None)
            else:
                hdr = wx.StaticText(self, wx.ID_ANY, label=header,
                                    style=wx.ALIGN_CENTER)
                hdr.SetFont(wx.Font(font_size, wx.SWISS, wx.NORMAL, wx.BOLD))
                self.headers.append(hdr)

            self.labels.append(wx.StaticText(self, wx.ID_ANY, label=text))

            if combo:              # it is a drop down combo box list
                self.inputs.append(wx.ComboBox(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required),
                                   choices=plist,
                                   style=wx.CB_DROPDOWN|wx.CB_READONLY))
                self.Bind(wx.EVT_COMBOBOX, self.OnComboBoxSelect, self.inputs[x])
            else:                  # it is a simple data entry field
                self.inputs.append(wx.TextCtrl(self, wx.ID_ANY,
                                   value=str(default),
                                   validator=ItemListValidator(datatype, required)))
                self.Bind(wx.EVT_TEXT, self.OnText, self.inputs[x])

            if not editable:
                # disallow edits to the field
                self.inputs[x].Enable(False)

            # Validate the default value and highlight the field if the value is
            # in error or if input is required and the value is a null string.
            self.inputs[x].GetValidator().Validate(self.inputs[x])


    def add_items_to_sizer(self, start, end):
        sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        for x in xrange(start, end+1):
            sizer.Add(self.labels[x], 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.inputs[x], 0, wx.EXPAND)
        sizer.AddGrowableCol(1)
        return sizer


    def update_items_in_dialog_box(self, new_values):
        for x in xrange(len(self.inputs)):
            if new_values[x] is not None:
                self.inputs[x].SetValue(str(new_values[x]))


    def GetResults(self):
        """
        Returns a list of values, one for each input field.  The value for
        a field is either its initial (default) value or the last value
        entered by the user that has been successfully validated.  An input
        that fails validation is not returned by the validator from the
        window.  For a non-editable field, its initial value is returned.
        Blank input is converted to 0.0, 0, or a null string as appropriate
        for the datatype of the field
        """

        ret = []
        for x in xrange(self.item_cnt):
            ret.append(self.inputs[x].GetValidator().GetValidatedInput())
        return ret


    def GetResultsAltFormat(self):
        """
        Returns a list of values, one for each input field.  The value for
        a field is either its initial (default) value or the last value
        entered by the user that has been successfully validated.  An input
        that fails validation is not returned by the validator from the
        window.  For a non-editable field, its initial value is returned.
        Blank input is returned as a value of None.
        """

        ret = []
        for x in xrange(self.item_cnt):
            ret.append(self.inputs[x].GetValidator().GetValidatedInputAlt())
        return ret


    def GetResultsRawInput(self):
        """
        Returns a list of strings corresponding to each input field.  These
        are the current values from the text control widgets which may have
        failed validation.  All values are returned as strings (i.e., they
        are not converted to floats or ints and whitespace is not stripped).
        """

        ret = []
        for x in xrange(self.item_cnt):
            ret.append(str(self.inputs[x].GetValue()))
        return ret


    def OnOk(self, event):
        """
        This method gets called when the user presses the OK button.
        It is intended to be subclassed if special processing is needed.
        """

        # Explicitly validate all input values before proceeding.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the OK button without making
        # the corrections, so we'll do a full validation pass now.  The only
        # purpose is to display an explicit error if any input fails validation.
        if not self.Validate():
            wx.MessageBox(caption="Data Entry Error",
                          message=DATA_ENTRY_ERRMSG,
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
        This method is called each time a selection is made in any combo box.
        It should be subclassed if the caller wants to perform some action in
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

        # Run the validator bound to the combo box that has a selection event.
        # This should not fail unless the combo options were setup incorrectly.
        # If the validation fails, the validator will highlight the input field
        # to alert the user of the error.
        combo_box = event.GetEventObject()
        combo_box.GetValidator().Validate(combo_box)
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
            ["Integer (int, optional):", 12345, "int", 'EL', None,
                "Test Header INT (10-pt)"],
            # Test specification of integer default value as a string
            ["Integer (int, optional):", "-60", "int", 'E', None],
            # Default value is null, so the required field should be highlighted
            ["Integer (int, required):", "", "int", 'RE', None],
            ["Floating Point (float, optional):", 2.34567e-5, "float", 'EM', None,
                "Test Header FP (9-pt)"],
            ["Floating Point (float, optional):", "", "float", 'E', None],
            ["Floating Point (float, required):", 1.0, "float", 'RE', None],
            # Test unknown datatype which should be treated as 'str'
            ["String (str, optional):", "DANSE", "foo", 'ES', None,
                "Test Header STR (8-pt)"],
            ["String (str, reqiured):", "delete me", "str", 'RE', None],
            ["Non-editable field:", "Cannot be changed!", "str", '', None],
            ["ComboBox String:", "Two", "str", 'CRE', ("One", "Two", "Three")],
            # ComboBox items must be specified as strings
            ["ComboBox String:", "", "int", 'CE', ("100", "200", "300")],
            ["String (alphabetic):", "Aa", "str_alpha", 'E', None],
            ["String (alphanumeric):", "Aa1", "str_alnum", 'E', None],
            ["String (A-Z, a-z, 0-9, _, -):", "A-1_a", "str_id", 'E', None],
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
            print "****** Dialog Box results from validated input fields" +\
                  " (None if no input):"
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
        print "****** Scrolled Panel results from validated input fields" +\
              " (None if no input):"
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

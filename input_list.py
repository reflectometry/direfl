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

        text_ctrl = self.GetWindow()
        text = text_ctrl.GetValue()

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
                    wx.MessageBox(message="Please fill in the box.",
                                  caption="Blank Field",
                                  style=wx.ICON_EXCLAMATION|wx.OK)
                    text_ctrl.SetBackgroundColour("yellow")
                    text_ctrl.SetFocus()
                    text_ctrl.Refresh()
                    return False
            elif self.type == "any":
                self.value = str(text).strip()
            else:
                self.value = str(text)

            text_ctrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.Refresh()
            self.TransferFromWindow()
            return True

        except:
            text_ctrl.SetBackgroundColour("pink")
            text_ctrl.SetFocus()
            text_ctrl.Refresh()
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
    This class implements the generic Item List Input Panel.
    (See ItemListDialog that uses a dialog box instead of a scrolled window.)

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
    - datatype for validation (see ItemListValidator.Validate() for details)
    - list of values for a combo box or None for a simple data entry field
    - flag to indicate that the field accepts user input (True) or the field is
      grayed-out (False); grayed-out fields have their default values returned
    """

    def __init__(self,
                 parent,
                 id       = wx.ID_ANY,
                 pos      = wx.DefaultPosition,
                 size     = wx.DefaultSize,
                 style=(wx.BORDER_RAISED|wx.TAB_TRAVERSAL),
                 name     = "",
                 itemlist = []
                ):
        ScrolledPanel.__init__(self, parent, id, pos, size, style, name)

        self.itemlist = itemlist
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))

        # Specify the widget layout using sizers.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the text controls for labels and associated input fields.
        self._add_items_to_input_box()

        # Create the grid sizer that organizes the labels and input fields.
        grid_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=10)
        grid_sizer.AddGrowableCol(1)
        self._add_items_to_sizer(grid_sizer)

        # Add the grid sizer to the main sizer.
        main_sizer.Add(grid_sizer, 1, wx.EXPAND|wx.ALL, border=10)

        # Finalize the sizer and establish the dimensions of the input box.
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        # Enable scrolling and initialize the validators (required when
        # validators are not used in the context of a dialog box).
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.InitDialog()


    def _add_items_to_input_box(self):
        # Note that the validator will update self.itemlist upon successful
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
        combo boxes instantiated by the ItemListDialog class.  This method
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

class ItemListDialog(wx.Dialog):
    """
    This class implements the generic Item List Dialog Box.
    (See ItemListInput that uses a scrolled window instead of a dialog box.)

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
    - datatype for validation (see ItemListValidator.Validate() for details)
    - list of values for a combo box or None for a simple data entry field
    - flag to indicate that the field accepts user input (True) or the field is
      grayed-out (False); grayed-out fields have their default values returned
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
        self._add_items_to_dialog_box()

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
        self._add_items_to_sizer(grid_sizer)

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


    def _add_items_to_dialog_box(self):
        # Note that the validator will update self.itemlist upon successful
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


    def _update_items_in_dialog_box(self, new_values):
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


    def OnOk(self, event):
        """
        This method gets called when the user presses the OK button.
        It is intended to be subclassed if special processing is needed.
        """

        # Explicitly validate all input values before proceeding.  Although
        # char-by-char validation would have warned the user about any invalid
        # entries, the user could have pressed the OK button without making
        # the corrections, so we'll do a full validation pass now.  Its only
        # purpose is to display an explicit error if any input fails validation.
        if not self.Validate():
            wx.MessageBox(caption="Data Entry Error",
                message="Please correct the highlighted fields in error.",
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
        combo boxes instantiated by the ItemListDialog class.  This method
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
    Interactively test both the ItemListDialog and the ItemListInput classes.
    Both will display the same input fields.  Enter invalid data to verify
    char-by-char error processing.  Press the OK and Done buttons with an
    uncorrected highlighted field in error to generate a pop-up error box.
    Resize the main window to see scroll bars disappear and reappear.
    """

    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="ItemListInput Test", size=(260, 360))
        panel = wx.Panel(self, wx.ID_ANY, style=wx.RAISED_BORDER)
        panel.SetBackgroundColour("PALE GREEN")

        # Define fields for both ItemListInput and ItemListDialog to display.
        self.fields = [
            ["Integer:", 123, "int", None, True],
            ["Floating Point:", 45.678, "float", None, True],
            ["Non-editable field:", "Cannot be changed!", "str", None, False],
            ["String (1 or more char):", "Error if blank", "str", None, True],
            ["String (0 or more char):", "", "any", None, True],
            ["ComboBox String:", "Two", "str", ("One", "Two", "Three"), True],
            ["String (no validation):", "DANSE Project", "", None, True]
                      ]

        # Create the scrolled window with input boxes.  Due to the size of the
        # frame and the parent panel, both scroll bars should be displayed.
        self.scrolled = ItemListInput(parent=panel, itemlist=self.fields)

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
        # Display the same fields shown in the frame in a a pop-up dialog box.
        dlg = ItemListDialog(parent=None,
                             title="ItemListDialog Test",
                             itemlist=self.fields)
        if dlg.ShowModal() == wx.ID_OK:
            print "Results from all input fields of the dialog box:"
            print "  ", dlg.GetResults()
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
        print "Results from all input fields of the scrolled panel:"
        print "  ", self.scrolled.GetResults()


    def OnExit(self, event):
        # Terminate the program.
        self.Close()


if __name__ == '__main__':
    # Interactively test both the ItemListInput and the ItemListDialog classes.
    app = wx.PySimpleApp()
    frame = AppTestFrame()
    frame.Show(True)
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# activity.py by:
#    Agustin Zubiaga <aguzubiaga97@gmail.com>
#    Gonzalo Odiard <godiard@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import gobject

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.graphics.toolbutton import ToolButton

from charts import BarChart


class SimpleGraph(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle, True)

        self.max_participiants = 1

        # CHART_OPTIONS

        self.x_label = None
        self.y_label = None
        self.chart_title = None
        self.chart_color = None
        self.chart_line_color = None
        self.current_chart = None
        self.chart_data = []

        # TOOLBARS
        self.toolbarbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        self.toolbarbox.toolbar.insert(self.activity_button, 0)

        self.add_v = ToolButton("gtk-add")
        self.add_v.connect("clicked", self.add_value)
        self.add_v.set_tooltip("Add a value")

        self.toolbarbox.toolbar.insert(self.add_v, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        self.toolbarbox.toolbar.insert(separator, -1)

        self.add_vbar_chart = ToolButton("vbar")
        self.add_vbar_chart.connect("clicked", self.add_chart_cb, "vbar")
        self.add_vbar_chart.set_tooltip("Create a Vertical bar chart")
        self.toolbarbox.toolbar.insert(self.add_vbar_chart, -1)

        self.add_hbar_chart = ToolButton("hbar")
        self.add_hbar_chart.connect("clicked", self.add_chart_cb, "hbar")
        self.add_hbar_chart.set_tooltip("Create a horizontal bar chart")
        self.toolbarbox.toolbar.insert(self.add_hbar_chart, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        self.toolbarbox.toolbar.insert(separator, -1)

        self.stopbtn = StopButton(self)
        self.toolbarbox.toolbar.insert(self.stopbtn, -1)

        self.set_toolbar_box(self.toolbarbox)

        # CANVAS
        self.paned = gtk.HPaned()
        self.box = gtk.VBox()

        self.labels_and_values = TreeView()

        self.labels_and_values.connect("label-changed", self.label_changed)
        self.labels_and_values.connect("value-changed", self.value_changed)

        self.box.pack_start(self.labels_and_values, True, True, 0)

        self.options = Options()

        self.options.connect("title-changed", self.set_chart_title)
        self.options.connect("hlabel-changed", self.set_h_label)
        self.options.connect("vlabel-changed", self.set_v_label)
        self.options.connect("chart-color-changed", self.set_chart_color)
        self.options.connect("line-color-changed", self.set_chart_line_color)

        self.box.pack_end(self.options, False, True, 10)

        self.paned.add1(self.box)

        # CHARTS AREA
        self.charts_area = gtk.Image()
        self.paned.add2(self.charts_area)

        self.set_canvas(self.paned)

        self.show_all()

    def add_value(self, widget):
        self.labels_and_values.add_value("Unknown", "0")
        self.chart_data.append(("Unknown", "0"))

    def add_chart_cb(self, widget, type="vbar"):
        if type == "vbar":
            self.current_chart = BarChart(type="vertical")

        elif type == "hbar":
            self.current_chart = BarChart(type="horizontal")

        print self.chart_data

        self.current_chart.data_set(self.chart_data)
        self.current_chart.set_title(self.chart_title)
        self.current_chart.set_x_label(self.x_label)
        self.current_chart.set_y_label(self.y_label)
        self.current_chart.set_chart_color(self.chart_color)
        self.current_chart.set_line_color(self.chart_line_color)
        self.current_chart.connect("ready", lambda w, f:
                                              self.charts_area.set_from_file(f))
        self.current_chart.render()

    def label_changed(self, tw, path, new_label):
        path = int(path)
        self.chart_data[path] = (new_label, self.chart_data[path][1])

    def value_changed(self, tw, path, new_value):
        path = int(path)
        self.chart_data[path] = (self.chart_data[path][0], int(new_value))

    def set_h_label(self, options, label):
        self.x_label = label

    def set_v_label(self, options, label):
        self.y_label = label

    def set_chart_title(self, options, title):
        self.chart_title = title

    def set_chart_color(self, options, color):
        self.chart_color = color

    def set_chart_line_color(self, options, color):
        self.chart_line_color = color


class TreeView(gtk.TreeView):

    __gsignals__ = {
             'label-changed': (gobject.SIGNAL_RUN_FIRST, None, [str, str], ),
             'value-changed': (gobject.SIGNAL_RUN_FIRST, None, [str, str], ), }

    def __init__(self):

        gtk.TreeView.__init__(self)

        self.model = gtk.ListStore(str, str)
        self.set_model(self.model)

        # Label column

        column = gtk.TreeViewColumn("Label")
        label = gtk.CellRendererText()
        label.set_property('editable', True)
        label.connect("edited", self.label_changed, self.model)

        column.pack_start(label)
        column.set_attributes(label, text=0)
        self.append_column(column)

        # Value column

        column = gtk.TreeViewColumn("Value")
        value = gtk.CellRendererText()
        value.set_property('editable', True)
        value.connect("edited", self.value_changed, self.model)

        column.pack_start(value)
        column.set_attributes(value, text=1)

        self.append_column(column)

        self.show_all()

    def add_value(self, label, value):
        self.model.append([label, value])
        print "Added: %s, Value: %s" % (label, value)

    def label_changed(self, cell, path, new_text, model):
        print "Change '%s' to '%s'" % (model[path][0], new_text)
        model[path][0] = new_text

        self.emit("label-changed", str(path), new_text)

    def value_changed(self, cell, path, new_text, model):
        print "Change '%s' to '%s'" % (model[path][1], new_text)
        is_number = True
        try:
            float(new_text)
        except:
            is_number = False

        if is_number:
            model[path][1] = new_text

            self.emit("value-changed", str(path), new_text)

        elif not is_number:
            error = gtk.MessageDialog(None,
                              gtk.DIALOG_MODAL,
                              gtk.MESSAGE_ERROR,
                              gtk.BUTTONS_OK, \
                              'The value must be a number (integer or float)')

            response = error.run()
            if response == gtk.RESPONSE_OK:
                error.destroy()


class Options(gtk.VBox):

    __gsignals__ = {
             'title-changed': (gobject.SIGNAL_RUN_FIRST, None, [str]),
             'hlabel-changed': (gobject.SIGNAL_RUN_FIRST, None, [str]),
             'vlabel-changed': (gobject.SIGNAL_RUN_FIRST, None, [str]),
             'chart-color-changed': (gobject.SIGNAL_RUN_FIRST, None, [object]),
             'line-color-changed': (gobject.SIGNAL_RUN_FIRST, None, [object])}

    def __init__(self):
        gtk.VBox.__init__(self)

        hbox = gtk.HBox()
        title = gtk.Label("Title:")
        hbox.pack_start(title, False, True, 0)

        entry = gtk.Entry(max=0)
        entry.connect("changed", lambda w: self.emit("title-changed",
                                                                  w.get_text()))
        hbox.pack_end(entry, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        hbox = gtk.HBox()
        title = gtk.Label("Horizontal label:")
        hbox.pack_start(title, False, True, 0)

        entry = gtk.Entry(max=0)
        entry.connect("changed", lambda w: self.emit("hlabel-changed",
                                                                  w.get_text()))
        hbox.pack_end(entry, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        hbox = gtk.HBox()
        title = gtk.Label("Vertical label:")
        hbox.pack_start(title, False, True, 0)

        entry = gtk.Entry(max=0)
        entry.connect("changed", lambda w: self.emit("vlabel-changed",
                                                                  w.get_text()))
        hbox.pack_end(entry, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        hbox = gtk.HBox()
        title = gtk.Label("Background Color:")
        hbox.pack_start(title, False, True, 0)

        btn = gtk.Button()
        btn.id = 0
        label = gtk.Label("Color")
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color("#000000"))
        btn.add(label)
        btn.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#F3F9FB"))
        btn.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.Color("#F3F9FB"))
        btn.connect("clicked", self.color_selector)
        hbox.pack_end(btn, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        hbox = gtk.HBox()
        title = gtk.Label("Lines Color:")
        hbox.pack_start(title, False, True, 0)

        btn = gtk.Button()
        btn.id = 1
        label = gtk.Label("Color")
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color("#000000"))
        btn.add(label)
        btn.connect("clicked", self.color_selector)
        btn.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#D1E5EC"))
        btn.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.Color("#D1E5EC"))
        hbox.pack_end(btn, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        self.show_all()

    def color_selector(self, widget):
        selector = gtk.ColorSelectionDialog("Color Selector")
        selector.get_color_selection().connect("color-changed",
                                                     self.color_changed, widget)
        selector.ok_button.connect("clicked", lambda w: selector.destroy())
        selector.cancel_button.destroy()
        selector.help_button.destroy()
        selector.show_all()

    def color_changed(self, widget, btn):
        color = widget.get_current_color()
        btn.modify_bg(gtk.STATE_NORMAL, color)
        btn.modify_bg(gtk.STATE_PRELIGHT, color)

        red = "%x" % int(color.red / 65535.0 * 255)
        if len(red) == 1:
                red = "0%s" % red

        green = "%x" % int(color.green / 65535.0 * 255)

        if len(green) == 1:
                green = "0%s" % green

        blue = "%x" % int(color.blue / 65535.0 * 255)

        if len(blue) == 1:
                blue = "0%s" % blue

        new_color = "#%s%s%s" % (red, green, blue)

        if not btn.id:
            self.emit("chart-color-changed", new_color)

        elif btn.id:
            self.emit("line-color-changed", new_color)

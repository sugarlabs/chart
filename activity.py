#!/usr/bin/env python
# -*- coding: utf-8 -*-

# activity.py by:
#    Agustin Zubiaga <aguz@sugarlabs.com>
#    Gonzalo Odiard <godiard@gmail.com>
#    Manuel Quiñones <manuq@laptop.org>

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

import os
import gconf

import logging

from gettext import gettext as _

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toggletoolbutton import ToggleToolButton
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.datastore import datastore

from pycha.color import basicColors as basic_colors

from charts import Chart, CHART_IMAGE


def rgb_to_html(color):
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

        return new_color


def get_user_color():
    color = gconf.client_get_default().get_string("/desktop/sugar/user/color")
    return color.split(",")


COLOR1 = gtk.gdk.Color(get_user_color()[0])
COLOR2 = gtk.gdk.Color(get_user_color()[1])

ACTIVITY_DIR = os.path.join(activity.get_activity_root(), "data/")
CHART_FILE = os.path.join(ACTIVITY_DIR, "chart-1.png")
num = 0

while os.path.exists(CHART_FILE):
    num += 1
    CHART_FILE = os.path.join(ACTIVITY_DIR, "chart-" + str(num) + ".png")

del num

logger = logging.getLogger("SimpleGraph")


class SimpleGraph(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle, True)

        self.max_participiants = 1

        # CHART_OPTIONS

        self.x_label = ""
        self.y_label = ""
        self.chart_color = get_user_color()[0]
        self.chart_line_color = get_user_color()[1]
        self.current_chart = None
        self.chart_data = []

        # TOOLBARS
        toolbarbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        activity_btn_toolbar = activity_button.page

        save_as_image = ToolButton("save-as-image")
        save_as_image.connect("clicked", self._save_as_image)
        save_as_image.set_tooltip(_("Save as image"))
        activity_btn_toolbar.insert(save_as_image, -1)

        save_as_image.show()
        activity_btn_toolbar.keep.hide()

        toolbarbox.toolbar.insert(activity_button, 0)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        add_v = ToolButton("row-insert")
        add_v.connect("clicked", self._add_value)
        add_v.set_tooltip(_("Add a value"))

        toolbarbox.toolbar.insert(add_v, -1)

        remove_v = ToolButton("row-remove")
        remove_v.connect("clicked", self._remove_value)
        remove_v.set_tooltip(_("Remove the selected value"))

        toolbarbox.toolbar.insert(remove_v, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        add_vbar_chart = RadioToolButton()
        add_vbar_chart.connect("clicked", self._add_chart_cb, "vbar")
        add_vbar_chart.set_tooltip(_("Create a vertical bar chart"))
        add_vbar_chart.props.icon_name = "vbar"
        charts_group = add_vbar_chart

        toolbarbox.toolbar.insert(add_vbar_chart, -1)

        add_hbar_chart = RadioToolButton()
        add_hbar_chart.connect("clicked", self._add_chart_cb, "hbar")
        add_hbar_chart.set_tooltip(_("Create a horizontal bar chart"))
        add_hbar_chart.props.icon_name = "hbar"
        add_hbar_chart.props.group = charts_group
        toolbarbox.toolbar.insert(add_hbar_chart, -1)

        add_line_chart = RadioToolButton()
        add_line_chart.connect("clicked", self._add_chart_cb, "line")
        add_line_chart.set_tooltip(_("Create a line chart"))
        add_line_chart.props.icon_name = "line"
        add_line_chart.props.group = charts_group
        toolbarbox.toolbar.insert(add_line_chart, -1)

        add_pie_chart = RadioToolButton()
        add_pie_chart.connect("clicked", self._add_chart_cb, "pie")
        add_pie_chart.set_tooltip(_("Create a pie chart"))
        add_pie_chart.props.icon_name = "pie"
        add_pie_chart.props.group = charts_group
        add_pie_chart.set_active(True)
        toolbarbox.toolbar.insert(add_pie_chart, -1)

        self.chart_type_buttons = [add_vbar_chart,
                                   add_hbar_chart,
                                   add_line_chart,
                                   add_pie_chart]

        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        options_button = ToggleToolButton('preferences-system')
        options_button.connect("clicked", self.__options_toggled_cb)
        options_button.set_tooltip(_('Show or hide options'))
        toolbarbox.toolbar.insert(options_button, -1)
        
        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        fullscreen_btn = ToolButton('view-fullscreen')
        fullscreen_btn.set_tooltip(_('Fullscreen'))
        fullscreen_btn.connect("clicked", self.__fullscreen_cb)

        toolbarbox.toolbar.insert(fullscreen_btn, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        toolbarbox.toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbarbox.toolbar.insert(stopbtn, -1)

        self.set_toolbar_box(toolbarbox)

        # CANVAS
        paned = gtk.HPaned()
        box = gtk.VBox()
        self.box = box

        # Set the info box width to 1/3 of the screen:
        def size_allocate_cb(widget, allocation):
            paned.disconnect(self._setup_handle)
            box_width = allocation.width / 3
            box.set_size_request(box_width, -1)

        self._setup_handle = paned.connect('size_allocate',
                    size_allocate_cb)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.labels_and_values = ChartData()
        scroll.add(self.labels_and_values)

        self.labels_and_values.connect("label-changed", self._label_changed)
        self.labels_and_values.connect("value-changed", self._value_changed)

        box.pack_start(scroll, True, True, 0)

        self.options = Options(self)

        self.options.connect("hlabel-changed", self._set_h_label)
        self.options.connect("vlabel-changed", self._set_v_label)
        self.options.connect("chart-color-changed", self._set_chart_color)
        self.options.connect("line-color-changed", self._set_chart_line_color)

        box.pack_end(self.options, False, True, 10)

        paned.add1(box)

        # CHARTS AREA
        self.charts_area = gtk.Image()
        paned.add2(self.charts_area)

        self.set_canvas(paned)

        self.show_all()
        self.options.set_visible(False)

    def _add_value(self, widget, label="", value="0.0"):
        pos = self.labels_and_values.add_value(label, value)
        self.chart_data.insert(pos, (label, float(value)))
        self._update_chart_data()

    def _remove_value(self, widget):
        path = self.labels_and_values.remove_selected_value()
        del self.chart_data[path]
        self._update_chart_data()

    def _add_chart_cb(self, widget, type="vbar"):
        self.current_chart = Chart(type)

        self.update_chart()
        
    def unfullscreen(self):
		self.box.show()
		self._render_chart(fullscreen=False)
		activity.Activity.unfullscreen(self)
        
    def __fullscreen_cb(self, button):
		self.box.hide()
		self._render_chart(fullscreen=True)
		activity.Activity.fullscreen(self)

    def __options_toggled_cb(self, widget):
        is_active = widget.get_active()
        self.options.set_visible(is_active)

    def _render_chart(self, fullscreen=False):
        if self.current_chart is None:
            return

        # Resize the chart for all the screen sizes
        x, y, w, h = self.get_allocation()
        
        if fullscreen:
			new_width = w
			new_height = h
        
        if not fullscreen:
			bx, by, bw, bh = self.box.get_allocation()

			surface_max_height = self.charts_area.get_allocation().height
			print surface_max_height

			new_width = w - bw - 40
			new_height = surface_max_height - 40

        self.current_chart.width = new_width
        self.current_chart.height = new_height

        # Set options
        self.current_chart.set_color_scheme(color=self.chart_color)
        self.current_chart.set_line_color(self.chart_line_color)
        if self.current_chart.type == "pie":
            self.current_chart.render(self)
        else:
            self.current_chart.render()

    def _update_chart_data(self):
        if self.current_chart is None:
            return
        self.current_chart.data_set(self.chart_data)
        self._render_chart()

    def _update_chart_labels(self):
        if self.current_chart is None:
            return
        self.current_chart.set_x_label(self.x_label)
        self.current_chart.set_y_label(self.y_label)
        self._render_chart()

    def update_chart(self):
        if self.current_chart:
            self.current_chart.data_set(self.chart_data)
            self.current_chart.set_title(self.metadata["title"])
            self.current_chart.set_x_label(self.x_label)
            self.current_chart.set_y_label(self.y_label)
            self.current_chart.connect("ready", lambda w, f:
                                          self.charts_area.set_from_file(f))
            self._render_chart()

    def _label_changed(self, tw, path, new_label):
        path = int(path)
        self.chart_data[path] = (new_label, self.chart_data[path][1])
        self._update_chart_data()

    def _value_changed(self, tw, path, new_value):
        path = int(path)
        self.chart_data[path] = (self.chart_data[path][0], float(new_value))
        self._update_chart_data()

    def _set_h_label(self, options, label):
        self.x_label = label
        self._update_chart_labels()

    def _set_v_label(self, options, label):
        self.y_label = label
        self._update_chart_labels()

    def _set_chart_color(self, options, color):
        self.chart_color = color
        self._render_chart()

    def _set_chart_line_color(self, options, color):
        self.chart_line_color = color
        self._render_chart()

    def _save_as_image(self, widget):
        if self.current_chart:
            jobject = datastore.create()

            jobject.metadata['title'] = self.metadata["title"]
            jobject.metadata['mime_type'] = "image/png"

            image = open(CHART_IMAGE, "r")
            jfile = open(CHART_FILE, "w")

            jfile.write(image.read())

            jfile.close()
            image.close()

            jobject.set_file_path(CHART_FILE)

            datastore.write(jobject)

    def write_file(self, file_path):
        self.metadata['mime_type'] = "activity/x-simplegraph"
        if self.current_chart:

            jfile = open(file_path, "w")

            jfile.write(self.metadata["title"] + "\n")
            jfile.write(self.x_label + "\n")
            jfile.write(self.y_label + "\n")
            jfile.write(self.chart_color + "\n")
            jfile.write(self.chart_line_color + "\n")

            string = ""
            for item in self.chart_data:
                string += item[0] + ":" + str(item[1]) + ","

            jfile.write(string)
            jfile.write("\n" + self.current_chart.type)

            jfile.close()

    def read_file(self, file_path):
        jfile = open(file_path, "r")

        num = 0
        type = None

        for line in jfile.readlines():
            num += 1

            if num != 7:
                                num2 = 0
                                l = len(line)
                                string = ""

                                for char in line:
                                        num2 += 1

                                        if num2 != l:
                                                string += char

                                line = string

            if num == 1:
                self.metadata["title"] = line

            elif num == 2:
                self.options.hlabel_entry.set_text(line)
                self.x_label = line

            elif num == 3:
                self.options.vlabel_entry.set_text(line)
                self.y_label = line

            elif num == 4:
                self.chart_color = line
                self.options.chart_color.modify_bg(gtk.STATE_NORMAL,
                                                   gtk.gdk.Color(line))

                self.options.chart_color.modify_bg(gtk.STATE_PRELIGHT,
                                                   gtk.gdk.Color(line))

            elif num == 5:
                self.chart_line_color = line
                self.options.lines_color.modify_bg(gtk.STATE_NORMAL,
                                                   gtk.gdk.Color(line))

                self.options.lines_color.modify_bg(gtk.STATE_PRELIGHT,
                                                   gtk.gdk.Color(line))

            elif num == 6:
                for x in line.split(","):
                    try:
                        data = x.split(":")
                        label = data[0]
                        value = float(data[1])
                        if data != ('',):
                            self._add_value(None, label=label, value=value)
                    except:
                        pass

            elif num == 7:
                type = line

        if type == "vbar":
            self.chart_type_buttons[0].set_active(True)

        elif type == "hbar":
            self.chart_type_buttons[1].set_active(True)

        elif type == "line":
            self.chart_type_buttons[2].set_active(True)

        elif type == "pie":
            self.chart_type_buttons[3].set_active(True)

        self._add_chart_cb(None, type=type)

        jfile.close()


class ChartData(gtk.TreeView):

    __gsignals__ = {
             'label-changed': (gobject.SIGNAL_RUN_FIRST, None, [str, str], ),
             'value-changed': (gobject.SIGNAL_RUN_FIRST, None, [str, str], ), }

    def __init__(self):

        gtk.TreeView.__init__(self)

        self.model = gtk.ListStore(str, str)
        self.set_model(self.model)

        # Label column

        column = gtk.TreeViewColumn(_("Label"))
        label = gtk.CellRendererText()
        label.set_property('editable', True)
        label.connect("edited", self._label_changed, self.model)

        column.pack_start(label)
        column.set_attributes(label, text=0)
        self.append_column(column)

        # Value column

        column = gtk.TreeViewColumn(_("Value"))
        value = gtk.CellRendererText()
        value.set_property('editable', True)
        value.connect("edited", self._value_changed, self.model)

        column.pack_start(value)
        column.set_attributes(value, text=1)

        self.append_column(column)

        self.show_all()

    def add_value(self, label, value):
        selected = self.get_selection().get_selected()[1]
        if not selected:
            path = 0

        elif selected:
            path = self.model.get_path(selected)[0]

        iter = self.model.insert(path, [label, value])

        self.set_cursor(self.model.get_path(iter),
                        self.get_column(1),
                        True)

        logger.info("Added: %s, Value: %s" % (label, value))

        return path

    def remove_selected_value(self):
        path, column = self.get_cursor()
        path = path[0]

        model, iter = self.get_selection().get_selected()
        self.model.remove(iter)

        return path

    def _label_changed(self, cell, path, new_text, model):
        logger.info("Change '%s' to '%s'" % (model[path][0], new_text))
        model[path][0] = new_text

        self.emit("label-changed", str(path), new_text)

    def _value_changed(self, cell, path, new_text, model):
        logger.info("Change '%s' to '%s'" % (model[path][1], new_text))
        is_number = True
        try:
            float(new_text)
        except:
            is_number = False

        if is_number:
            model[path][1] = str(float(new_text))

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
             'hlabel-changed': (gobject.SIGNAL_RUN_FIRST, None, [str]),
             'vlabel-changed': (gobject.SIGNAL_RUN_FIRST, None, [str]),
             'chart-color-changed': (gobject.SIGNAL_RUN_FIRST, None, [object]),
             'line-color-changed': (gobject.SIGNAL_RUN_FIRST, None, [object])}

    def __init__(self, activity):
        gtk.VBox.__init__(self)

        hbox = gtk.HBox()
        title = gtk.Label(_("Horizontal label:"))
        hbox.pack_start(title, False, True, 0)

        entry = gtk.Entry(max=0)
        entry.connect("changed", lambda w: self.emit("hlabel-changed",
                                                              w.get_text()))
        hbox.pack_end(entry, False, True, 5)

        self.hlabel_entry = entry

        self.pack_start(hbox, False, True, 3)

        hbox = gtk.HBox()
        title = gtk.Label(_("Vertical label:"))
        hbox.pack_start(title, False, True, 0)

        entry = gtk.Entry(max=0)
        entry.connect("changed", lambda w: self.emit("vlabel-changed",
                                                              w.get_text()))
        hbox.pack_end(entry, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        self.vlabel_entry = entry

        hbox = gtk.HBox()
        title = gtk.Label(_("Chart color:"))
        hbox.pack_start(title, False, True, 0)

        btn = gtk.Button(_("Color"))
        btn.id = 1
        btn.modify_bg(gtk.STATE_NORMAL, COLOR1)
        btn.modify_bg(gtk.STATE_PRELIGHT, COLOR1)
        btn.connect("clicked", self._color_selector)
        hbox.pack_end(btn, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        self.chart_color = btn

        hbox = gtk.HBox()
        title = gtk.Label(_("Lines Color:"))
        hbox.pack_start(title, False, True, 0)

        btn = gtk.Button()
        btn.id = 2
        label = gtk.Label(_("Color"))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color("#000000"))
        btn.add(label)
        btn.connect("clicked", self._color_selector)
        btn.modify_bg(gtk.STATE_NORMAL, COLOR2)
        btn.modify_bg(gtk.STATE_PRELIGHT, COLOR2)
        hbox.pack_end(btn, False, True, 5)

        self.pack_start(hbox, False, True, 3)

        self.lines_color = btn

        self.activity = activity

        self.show_all()

    def _color_selector(self, widget):
        selector = gtk.ColorSelectionDialog(_("Color Selector"))

        if widget.id == 1:

            box = gtk.HBox()

            for color in basic_colors.keys():
                btn = gtk.Button()
                btn.set_size_request(40, 40)
                btn.set_property("has-tooltip", True)
                btn.set_property("tooltip-text", str(color).capitalize())
                btn.color = gtk.gdk.Color(basic_colors[color])
                btn.connect("clicked", lambda w:
                               selector.colorsel.set_current_color(w.color))
                btn.modify_bg(gtk.STATE_NORMAL, btn.color)
                btn.modify_bg(gtk.STATE_PRELIGHT, btn.color)
                box.pack_start(btn, False, True, 1)

            selector.vbox.pack_end(box, False, True, 0)
            selector.colorsel.set_current_color(
                                   gtk.gdk.Color(self.activity.chart_color))

        elif widget.id == 2:
            selector.colorsel.set_current_color(
                              gtk.gdk.Color(self.activity.chart_line_color))

        selector.get_color_selection().connect("color-changed",
                                                 self._color_changed, widget)

        selector.ok_button.connect("clicked", lambda w: selector.destroy())
        selector.cancel_button.destroy()
        selector.help_button.destroy()
        selector.show_all()

    def _color_changed(self, widget, btn):
        color = widget.get_current_color()
        btn.modify_bg(gtk.STATE_NORMAL, color)
        btn.modify_bg(gtk.STATE_PRELIGHT, color)

        new_color = rgb_to_html(color)

        if btn.id == 2:
            self.emit("line-color-changed", new_color)

        elif btn.id == 1:
            self.emit("chart-color-changed", new_color)

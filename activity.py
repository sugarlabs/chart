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
import pango

import os
import gconf
import simplejson

import logging

from gettext import gettext as _

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.activity.widgets import ToolbarButton
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.colorbutton import ColorToolButton
from sugar.graphics.icon import Icon
from sugar.graphics.alert import Alert
from sugar.datastore import datastore

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

WHITE = gtk.gdk.color_parse("white")

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

        self.max_participants = 1

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

        options_button = ToolbarButton(icon_name='preferences-system')
        options_toolbar = gtk.Toolbar()

        self.chart_color_btn = ColorToolButton()
        self.chart_color_btn.set_color(COLOR1)
        self.chart_color_btn.set_title(_("Chart Color"))
        self.chart_color_btn.connect('notify::color', self._set_chart_color)
        options_toolbar.insert(self.chart_color_btn, -1)

        self.line_color_btn = ColorToolButton()
        self.line_color_btn.set_color(COLOR2)
        self.line_color_btn.set_title(_("Line Color"))
        self.line_color_btn.connect('notify::color',
                self._set_chart_line_color)
        options_toolbar.insert(self.line_color_btn, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        options_toolbar.insert(separator, -1)

        h_label_icon = Icon(icon_name="hlabel")
        h_label_tool_item = gtk.ToolItem()
        h_label_tool_item.add(h_label_icon)
        options_toolbar.insert(h_label_tool_item, -1)

        self.h_label = Entry(_("Horizontal label..."))
        self.h_label.entry.connect("changed", self._set_h_label)
        options_toolbar.insert(self.h_label, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(False)
        options_toolbar.insert(separator, -1)

        v_label_icon = Icon(icon_name="vlabel")
        v_label_tool_item = gtk.ToolItem()
        v_label_tool_item.add(v_label_icon)
        options_toolbar.insert(v_label_tool_item, -1)

        self.v_label = Entry(_("Vertical label..."))
        self.v_label.entry.connect("changed", self._set_v_label)
        options_toolbar.insert(self.v_label, -1)

        options_button.props.page = options_toolbar
        options_toolbar.show_all()

        toolbarbox.toolbar.insert(options_button, -1)

        self.options = [self.chart_color_btn, self.line_color_btn,
                self.h_label, self.v_label]

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
        self.labels_and_values = ChartData(self)
        scroll.add(self.labels_and_values)

        self.labels_and_values.connect("label-changed", self._label_changed)
        self.labels_and_values.connect("value-changed", self._value_changed)

        box.pack_start(scroll, True, True, 0)

        paned.add1(box)

        # CHARTS AREA
        eventbox = gtk.EventBox()
        self.charts_area = gtk.Image()
        self.charts_area.set_from_file(_("icons/simplegraph.svg"))

        eventbox.modify_bg(gtk.STATE_NORMAL, WHITE)

        eventbox.add(self.charts_area)
        paned.add2(eventbox)

        self.set_canvas(paned)

        self.show_all()

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
            sx, sy, width, height = self.charts_area.get_allocation()

            new_width = width - 40
            new_height = height - 40

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

    def _set_h_label(self, widget):
        self.x_label = widget.get_text()
        self._update_chart_labels()

    def _set_v_label(self, widget):
        self.y_label = widget.get_text()
        self._update_chart_labels()

    def _set_chart_color(self, widget, pspec):
        self.chart_color = rgb_to_html(widget.get_color())
        self._render_chart()

    def _set_chart_line_color(self, widget, pspec):
        self.chart_line_color = rgb_to_html(widget.get_color())
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

            data = {}
            data['title'] = self.metadata["title"]
            data['x_label'] = self.x_label
            data['y_label'] = self.y_label
            data['chart_color'] = self.chart_color
            data['chart_line_color'] = self.chart_line_color
            data['current_chart.type'] = self.current_chart.type
            data['chart_data'] = self.chart_data

            f = open(file_path, 'w')
            try:
                simplejson.dump(data, f)
            finally:
                f.close()

    def read_file(self, file_path):
        f = open(file_path, 'r')
        try:
            data = simplejson.load(f)
        finally:
            f.close()

        self.metadata["title"] = data['title']
        self.x_label = data['x_label']
        self.y_label = data['y_label']
        self.chart_color = data['chart_color']
        self.chart_line_color = data['chart_line_color']
        self.current_chart.type = data['current_chart.type']
        chart_data = data['chart_data']

        # Update the controls in the config subtoolbar
        self.chart_color_btn.set_color(gtk.gdk.Color(self.chart_color))
        self.line_color_btn.set_color(gtk.gdk.Color(self.chart_line_color))
        self.h_label.entry.set_text(self.x_label)
        self.v_label.entry.set_text(self.y_label)

        #load the data
        for row  in chart_data:
            self._add_value(None, label=row[0], value=float(row[1]))

        self.update_chart()


class ChartData(gtk.TreeView):

    __gsignals__ = {
             'label-changed': (gobject.SIGNAL_RUN_FIRST, None, [str, str], ),
             'value-changed': (gobject.SIGNAL_RUN_FIRST, None, [str, str], ), }

    def __init__(self, activity):

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
        value.connect("edited", self._value_changed, self.model, activity)

        column.pack_start(value)
        column.set_attributes(value, text=1)

        self.append_column(column)
        self.set_enable_search(False)

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

    def _value_changed(self, cell, path, new_text, model, activity):
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
            alert = Alert()

            alert.props.title = _('Invalid Value')
            alert.props.msg = \
					_('The value must be a number (integer or decimal)')

            ok_icon = Icon(icon_name='dialog-ok')
            alert.add_button(gtk.RESPONSE_OK, _('Ok'), ok_icon)
            ok_icon.show()

            alert.connect('response', lambda a, r: activity.remove_alert(a))

            activity.add_alert(alert)

            alert.show()


class Entry(gtk.ToolItem):

    def __init__(self, text):
        gtk.ToolItem.__init__(self)

        self.entry = gtk.Entry()
        self.entry.set_text(text)
        self.entry.connect("focus-in-event", self._focus_in)
        self.entry.connect("focus-out-event", self._focus_out)
        self.entry.modify_font(pango.FontDescription("italic"))

        self.text = text

        self.add(self.entry)

        self.show_all()

    def _focus_in(self, widget, event):
        if widget.get_text() == self.text:
            widget.set_text("")
            widget.modify_font(pango.FontDescription(""))

    def _focus_out(self, widget, event):
        if widget.get_text() == "":
            widget.set_text(self.text)
            widget.modify_font(pango.FontDescription("italic"))

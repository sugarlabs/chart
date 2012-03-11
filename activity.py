#!/usr/bin/env python
# -*- coding: utf-8 -*-

# activity.py by:
#    Agustin Zubiaga <aguz@sugarlabs.org>
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
import simplejson
import locale
import logging
import utils

from gettext import gettext as _

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.activity.widgets import ToolbarButton
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.colorbutton import ColorToolButton
from sugar.graphics.objectchooser import ObjectChooser
from sugar.graphics.icon import Icon
from sugar.graphics.alert import Alert
from sugar.datastore import datastore

from charts import Chart
from readers import StopWatchReader
from readers import MeasureReader
import simplegraphhelp

# Mime types
_STOPWATCH_MIME_TYPE = "application/x-stopwatch-activity"
_CSV_MIME_TYPE = "text/csv"

# GUI Colors
_COLOR1 = utils.get_user_fill_color()
_COLOR2 = utils.get_user_stroke_color()
_WHITE = gtk.gdk.color_parse("white")

# Paths
_ACTIVITY_DIR = os.path.join(activity.get_activity_root(), "data/")
_CHART_FILE = utils.get_chart_file(_ACTIVITY_DIR)

# Logging
_logger = logging.getLogger('simplegraph-activity')
_logger.setLevel(logging.DEBUG)
logging.basicConfig()


class ChartArea(gtk.DrawingArea):

    def __init__(self, parent):
        """A class for Draw the chart"""
        super(ChartArea, self).__init__()
        self._parent = parent
        self.add_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.VISIBILITY_NOTIFY_MASK)
        self.connect("expose-event", self._expose_cb)

    def _expose_cb(self, widget, event):
        context = self.window.cairo_create()

        xpos, ypos, width, height = self.get_allocation()

        # White Background:
        context.rectangle(0, 0, width, height)
        context.set_source_rgb(255, 255, 255)
        context.fill()

        # Paint the chart:
        chart_width = self._parent.current_chart.width
        chart_height = self._parent.current_chart.height

        cxpos = xpos + width / 2 - chart_width / 2
        cypos = ypos + height / 2 - chart_height / 2

        context.set_source_surface(self._parent.current_chart.surface,
                                   cxpos,
                                   cypos)
        context.paint()


class SimpleGraph(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle, True)

        self.max_participants = 1

        # CHART_OPTIONS

        self.x_label = ""
        self.y_label = ""
        self.chart_color = utils.get_user_fill_color('str')
        self.chart_line_color = utils.get_user_stroke_color('str')
        self.current_chart = None
        self.charts_area = None
        self.chart_data = []

        # TOOLBARS
        toolbarbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        activity_btn_toolbar = activity_button.page

        activity_btn_toolbar.title.connect('changed', self._set_chart_title)

        save_as_image = ToolButton("save-as-image")
        save_as_image.connect("clicked", self._save_as_image)
        save_as_image.set_tooltip(_("Save as image"))
        activity_btn_toolbar.insert(save_as_image, -1)

        save_as_image.show()

        import_stopwatch = ToolButton("import-stopwatch")
        import_stopwatch.connect("clicked", self.__import_stopwatch_cb)
        import_stopwatch.set_tooltip(_("Read StopWatch data"))
        activity_btn_toolbar.insert(import_stopwatch, -1)

        import_stopwatch.show()

        import_measure = ToolButton("import-measure")
        import_measure.set_tooltip(_("Read Measure data"))

        if utils.get_channels() == 1:
            import_measure.connect("clicked", self.__import_measure_cb, 1)

        else:
            import_measure.connect("clicked", self._measure_btn_clicked)
            self._create_measure_palette(import_measure)

        activity_btn_toolbar.insert(import_measure, -1)

        import_measure.show()

        activity_btn_toolbar.keep.hide()

        toolbarbox.toolbar.insert(activity_button, 0)

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
        add_vbar_chart.set_tooltip(_("Vertical Bar Chart"))
        add_vbar_chart.props.icon_name = "vbar"
        charts_group = add_vbar_chart

        toolbarbox.toolbar.insert(add_vbar_chart, -1)

        add_hbar_chart = RadioToolButton()
        add_hbar_chart.connect("clicked", self._add_chart_cb, "hbar")
        add_hbar_chart.set_tooltip(_("Horizontal Bar Chart"))
        add_hbar_chart.props.icon_name = "hbar"
        add_hbar_chart.props.group = charts_group
        toolbarbox.toolbar.insert(add_hbar_chart, -1)

        add_line_chart = RadioToolButton()
        add_line_chart.connect("clicked", self._add_chart_cb, "line")
        add_line_chart.set_tooltip(_("Line Chart"))
        add_line_chart.props.icon_name = "line"
        add_line_chart.props.group = charts_group
        toolbarbox.toolbar.insert(add_line_chart, -1)

        add_pie_chart = RadioToolButton()
        add_pie_chart.connect("clicked", self._add_chart_cb, "pie")
        add_pie_chart.set_tooltip(_("Pie Chart"))
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
        self.chart_color_btn.set_color(_COLOR1)
        self.chart_color_btn.set_title(_("Chart Color"))
        self.chart_color_btn.connect('notify::color', self._set_chart_color)
        options_toolbar.insert(self.chart_color_btn, -1)

        self.line_color_btn = ColorToolButton()
        self.line_color_btn.set_color(_COLOR2)
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

        simplegraphhelp.create_help(toolbarbox.toolbar)

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
        self.charts_area = ChartArea(self)
        self.charts_area.connect('size_allocate', self._chart_size_allocate)

        eventbox.modify_bg(gtk.STATE_NORMAL, _WHITE)

        eventbox.add(self.charts_area)
        paned.add2(eventbox)

        self.set_canvas(paned)

        self.show_all()

    def _create_measure_palette(self, button):
        palette = button.get_palette()
        hbox = gtk.HBox()

        channel1 = ToolButton("measure-channel-1")
        channel1.connect("clicked", self.__import_measure_cb, 1)

        channel2 = ToolButton("measure-channel-2")
        channel2.connect("clicked", self.__import_measure_cb, 2)

        hbox.pack_start(channel1, False, True, 0)
        hbox.pack_end(channel2, False, True, 0)

        hbox.show_all()

        palette.set_content(hbox)

    def _measure_btn_clicked(self, button):
        palette = button.get_palette()
        palette.popup()

    def _add_value(self, widget, label="", value="0.0"):
        data = (label, float(value))
        if not data in self.chart_data:
            pos = self.labels_and_values.add_value(label, value)
            self.chart_data.insert(pos, data)
            self._update_chart_data()

    def _remove_value(self, widget):
        path = self.labels_and_values.remove_selected_value()
        del self.chart_data[path]
        self._update_chart_data()

    def _add_chart_cb(self, widget, type="vbar"):
        self.current_chart = Chart(type)

        self.update_chart()

    def _chart_size_allocate(self, widget, allocation):
        self._render_chart()

    def unfullscreen(self):
        self.box.show()
        activity.Activity.unfullscreen(self)

    def __fullscreen_cb(self, button):
        self.box.hide()
        self._render_chart(fullscreen=True)
        activity.Activity.fullscreen(self)

    def _render_chart(self, fullscreen=False):
        if self.current_chart is None or self.charts_area is None:
            return

        try:
            # Resize the chart for all the screen sizes
            xpos, ypos, width, height = self.get_allocation()

            if fullscreen:
                new_width = width
                new_height = height

            if not fullscreen:
                sxpos, sypos, width, height = self.charts_area.get_allocation()

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
            self.charts_area.queue_draw()

        except (ZeroDivisionError, ValueError):
            pass

        return False

    def _update_chart_data(self):
        if self.current_chart is None:
            return
        self.current_chart.data_set(self.chart_data)
        self._update_chart_labels()

    def _set_chart_title(self, widget):
        self._update_chart_labels(title=widget.get_text())

    def _update_chart_labels(self, title=""):
        if self.current_chart is None:
            return

        if not title and self.metadata["title"]:
            title = self.metadata["title"]

        self.current_chart.set_title(title)
        self.current_chart.set_x_label(self.x_label)
        self.current_chart.set_y_label(self.y_label)
        self._render_chart()

    def update_chart(self):
        if self.current_chart:
            self.current_chart.data_set(self.chart_data)
            self.current_chart.set_title(self.metadata["title"])
            self.current_chart.set_x_label(self.x_label)
            self.current_chart.set_y_label(self.y_label)
            self._render_chart()

    def _label_changed(self, treeview, path, new_label):
        path = int(path)
        self.chart_data[path] = (new_label, self.chart_data[path][1])
        self._update_chart_data()

    def _value_changed(self, treeview, path, new_value):
        path = int(path)
        self.chart_data[path] = (self.chart_data[path][0], float(new_value))
        self._update_chart_data()

    def _set_h_label(self, widget):
        new_text = widget.get_text()

        if new_text != self.h_label._text:
            self.x_label = new_text
            self._update_chart_labels()

    def _set_v_label(self, widget):
        new_text = widget.get_text()

        if new_text != self.v_label._text:
            self.y_label = new_text
            self._update_chart_labels()

    def _set_chart_color(self, widget, pspec):
        self.chart_color = utils.rgb2html(widget.get_color())
        self._render_chart()

    def _set_chart_line_color(self, widget, pspec):
        self.chart_line_color = utils.rgb2html(widget.get_color())
        self._render_chart()

    def _object_chooser(self, mime_type, type_name):
        chooser = ObjectChooser()
        matches_mime_type = False

        response = chooser.run()
        if response == gtk.RESPONSE_ACCEPT:
            jobject = chooser.get_selected_object()
            metadata = jobject.metadata
            file_path = jobject.file_path

            if metadata['mime_type'] == mime_type:
                matches_mime_type = True

            else:
                alert = Alert()

                alert.props.title = _('Invalid object')
                alert.props.msg = \
                       _('The selected object must be a %s file' % (type_name))

                ok_icon = Icon(icon_name='dialog-ok')
                alert.add_button(gtk.RESPONSE_OK, _('Ok'), ok_icon)
                ok_icon.show()

                alert.connect('response', lambda a, r: self.remove_alert(a))

                self.add_alert(alert)

                alert.show()

        return matches_mime_type, file_path, metadata['title']

    def _graph_from_reader(self, reader):
        self.labels_and_values.model.clear()
        self.chart_data = []

        chart_data = reader.get_chart_data()

        horizontal, vertical = reader.get_labels_name()

        self.v_label.entry.set_text(horizontal)
        self.h_label.entry.set_text(vertical)

        # Load the data
        for row  in chart_data:
            self._add_value(None,
                            label=row[0], value=float(row[1]))

            self.update_chart()

    def __import_stopwatch_cb(self, widget):
        matches_mime_type, file_path, title = self._object_chooser(
                                                      _STOPWATCH_MIME_TYPE,
                                                      _('StopWatch'))

        if matches_mime_type:
            f = open(file_path)
            reader = StopWatchReader(f)
            self._graph_from_reader(reader)

            f.close()

    def __import_measure_cb(self, widget, channel=1):
        matches_mime_type, file_path, title = self._object_chooser(
                                                         _CSV_MIME_TYPE,
                                                         _('Measure'))

        if matches_mime_type:
            f = open(file_path)
            reader = MeasureReader(f, channel)
            self._graph_from_reader(reader)

            f.close()

    def _save_as_image(self, widget):
        if self.current_chart:
            jobject = datastore.create()

            jobject.metadata['title'] = self.metadata["title"]
            jobject.metadata['mime_type'] = "image/png"

            self.current_chart.as_png(_CHART_FILE)
            jobject.set_file_path(_CHART_FILE)

            datastore.write(jobject)

    def write_file(self, file_path):
        self.metadata['mime_type'] = "application/x-simplegraph-activity"
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

        # Update charts buttons
        type = data["current_chart.type"]
        if type == "vbar":
            self.chart_type_buttons[0].set_active(True)

        elif type == "hbar":
            self.chart_type_buttons[1].set_active(True)

        elif type == "line":
            self.chart_type_buttons[2].set_active(True)

        elif type == "pie":
            self.chart_type_buttons[3].set_active(True)

        # Update the controls in the config subtoolbar
        self.chart_color_btn.set_color(gtk.gdk.Color(self.chart_color))
        self.line_color_btn.set_color(gtk.gdk.Color(self.chart_line_color))

        # If the saved label is not '', set the text entry with the saved label
        if self.x_label != '':
            self.h_label.entry.set_text(self.x_label)

        if self.y_label != '':
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
            path = self.model.get_path(selected)[0] + 1

        iter = self.model.insert(path, [label, value])

        self.set_cursor(self.model.get_path(iter),
                        self.get_column(1),
                        True)

        _logger.info("Added: %s, Value: %s" % (label, value))

        return path

    def remove_selected_value(self):
        path, column = self.get_cursor()
        path = path[0]

        model, iter = self.get_selection().get_selected()
        self.model.remove(iter)

        return path

    def _label_changed(self, cell, path, new_text, model):
        _logger.info("Change '%s' to '%s'" % (model[path][0], new_text))
        model[path][0] = new_text

        self.emit("label-changed", str(path), new_text)

    def _value_changed(self, cell, path, new_text, model, activity):
        _logger.info("Change '%s' to '%s'" % (model[path][1], new_text))
        is_number = True
        number = new_text.replace(",", ".")
        try:
            float(number)
        except ValueError:
            is_number = False

        if is_number:
            decimals = utils.get_decimals(str(float(number)))
            new_text = locale.format('%.' + decimals + 'f', float(number))
            model[path][1] = str(new_text)

            self.emit("value-changed", str(path), number)

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

        self._text = text

        self.add(self.entry)

        self.show_all()

    def _focus_in(self, widget, event):
        if widget.get_text() == self._text:
            widget.set_text("")
            widget.modify_font(pango.FontDescription(""))

    def _focus_out(self, widget, event):
        if widget.get_text() == "":
            widget.set_text(self.text)
            widget.modify_font(pango.FontDescription("italic"))

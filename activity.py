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

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject
import os
import re

import json

import locale
import logging
import utils
import ast, operator


from io import StringIO
from gettext import gettext as _

from sugar3.activity import activity
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ToolbarButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolcombobox import ToolComboBox
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics.colorbutton import ColorToolButton
from sugar3.graphics.objectchooser import ObjectChooser
from sugar3.graphics.style import Color
from sugar3.graphics.icon import Icon
from sugar3.graphics.alert import Alert
from sugar3.datastore import datastore
from sugar3.graphics import style

from fontcombobox import FontComboBox
from fontcombobox import FontSize

from readers import StopWatchReader
from readers import MeasureReader
from readers import ClipboardReader
import charthelp
import chart as charts

# Mime types
_STOPWATCH_MIME_TYPE = 'application/x-stopwatch-activity'
_CSV_MIME_TYPE = 'text/csv'

# GUI Colors
_COLOR1 = utils.get_user_fill_color()
_COLOR2 = utils.get_user_stroke_color()
_WHITE = Gdk.color_parse('white')

# Font options
TITLE_FONT = 'title'
LABELS_FONT = 'labels'
TICK_FONT = 'ticks'

# Paths
_ACTIVITY_DIR = os.path.join(activity.get_activity_root(), 'data/')
_CHART_FILE = utils.get_chart_file(_ACTIVITY_DIR)

# Logging
_logger = logging.getLogger('chart-activity')
_logger.setLevel(logging.DEBUG)
logging.basicConfig()


def _invalid_number_alert(activity):
    alert = Alert()

    alert.props.title = _('Invalid Value')
    alert.props.msg = _('The value must be a number (integer or decimal)')

    ok_icon = Icon(icon_name='dialog-ok')
    alert.add_button(Gtk.ResponseType.OK, _('Ok'), ok_icon)
    ok_icon.show()

    alert.connect('response', lambda a, r: activity.remove_alert(a))
    activity.add_alert(alert)
    alert.show()


def _extract_value(value):
    if isinstance(value, str):

        binOps = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }

        node = ast.parse(value, mode='eval')
        
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.BinOp):
                return binOps[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.Num):
                return node.n
            else:
                print(node, type(node))
                raise Exception('Invalid expression.')
            return _eval(node.body)

        value = round(_eval(node), 2)
        
    decimals_found = re.findall("\d+\.\d+", str(value))
    integers_found = re.findall("\d+", str(value))

    if decimals_found != []:
        return decimals_found[0]
    elif integers_found != []:
        return integers_found[0]
    return None


class ChartArea(Gtk.DrawingArea):

    def __init__(self, parent):
        '''A class for Draw the chart'''
        super(ChartArea, self).__init__()
        self._parent = parent
        self.add_events(Gdk.EventMask.EXPOSURE_MASK |
                        Gdk.EventMask.VISIBILITY_NOTIFY_MASK)
        self.connect('draw', self._draw_cb)

        self.drag_dest_set_target_list(Gtk.TargetList.new([]))
        self.drag_dest_add_text_targets()
        self.connect('drag_data_received', self._drag_data_received)

    def _draw_cb(self, widget, context):
        alloc = self.get_allocation()

        # White Background:
        context.rectangle(0, 0, alloc.width, alloc.height)
        context.set_source_rgb(255, 255, 255)
        context.fill()

        if self._parent.current_chart is None:
            return

        # Paint the chart:
        chart_width = self._parent.current_chart.width
        chart_height = self._parent.current_chart.height

        cxpos = alloc.width / 2 - chart_width / 2
        cypos = alloc.height / 2 - chart_height / 2

        context.set_source_surface(self._parent.current_chart.surface,
                                   cxpos,
                                   cypos)
        context.paint()

    def _drag_data_received(self, w, context, x, y, data, info, time):
        if data and data.format == 8:
            io_file = StringIO(data.data)
            reader = ClipboardReader(io_file)
            self._parent._graph_from_reader(reader)
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)


class ChartActivity(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle, True)

        self.max_participants = 1

        # CHART_OPTIONS

        self._font_option = TITLE_FONT
        self.x_label = ''
        self.y_label = ''
        self.chart_color = utils.get_user_fill_color('str')
        self.chart_line_color = utils.get_user_stroke_color('str')
        self.current_chart = None
        self.charts_area = None
        self.chart_data = []
        self.chart_type_buttons = []
        self._font_options = {
            'titleColor': '#000000',
            'titleFont': 'Sans',
            'titleFontSize': 12,
            'axis': {
                'tickFont': 'Sans',
                'tickFontSize': 12,
                'tickColor': '#000000',
                'labelFontSize': 14,
                'labelColor': '#666666',
                'labelFont': 'Sans',
                'lineColor': '#b3b3b3'}}

        # TOOLBARS
        self._labels_font = RadioToolButton()
        self._title_font = RadioToolButton()

        toolbarbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        activity_btn_toolbar = activity_button.page

        activity_btn_toolbar.title.connect('changed', self._set_chart_title)

        save_as_image = ToolButton('save-as-image')
        save_as_image.connect('clicked', self._save_as_image)
        save_as_image.set_tooltip(_('Save as image'))
        activity_btn_toolbar.insert(save_as_image, -1)

        save_as_image.show()

        import_stopwatch = ToolButton('import-stopwatch')
        import_stopwatch.connect('clicked', self.__import_stopwatch_cb)
        import_stopwatch.set_tooltip(_('Read StopWatch data'))
        activity_btn_toolbar.insert(import_stopwatch, -1)

        import_stopwatch.show()

        import_measure = ToolButton('import-measure')
        import_measure.set_tooltip(_('Read Measure data'))

        if utils.get_channels() == 1:
            import_measure.connect('clicked', self.__import_measure_cb, 1)

        else:
            import_measure.connect('clicked', self._measure_btn_clicked)
            self._create_measure_palette(import_measure)

        activity_btn_toolbar.insert(import_measure, -1)
        import_measure.show()

        toolbarbox.toolbar.insert(activity_button, 0)

        add_v = ToolButton('gtk-add')
        add_v.connect('clicked', self._add_value)
        add_v.set_tooltip(_('Add a value'))

        toolbarbox.toolbar.insert(add_v, -1)

        remove_v = ToolButton('gtk-remove')
        remove_v.connect('clicked', self._remove_value)
        remove_v.set_tooltip(_('Remove the selected value'))

        toolbarbox.toolbar.insert(remove_v, -1)

        self._remove_v = remove_v

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        # We create two sets: one for the main toolbar and one for the
        # chart toolbar. We choose which set to use based on the
        # screen width.
        self._create_chart_buttons(toolbarbox.toolbar)

        self._chart_button = ToolbarButton(icon_name='vbar')
        chart_toolbar = Gtk.Toolbar()
        self._create_chart_buttons(chart_toolbar)
        self._chart_button.props.page = chart_toolbar
        chart_toolbar.show_all()
        toolbarbox.toolbar.insert(self._chart_button, -1)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        self._options_button = ToolbarButton(icon_name='preferences-system')
        options_toolbar = Gtk.Toolbar()

        self.chart_color_btn = ColorToolButton()
        self.chart_color_btn.set_color(_COLOR1)
        self.chart_color_btn.set_title(_('Chart Color'))
        options_toolbar.insert(self.chart_color_btn, -1)
        GObject.timeout_add(1000,
                            self._connect_color_btn,
                            self.chart_color_btn,
                            self._set_chart_color)

        self.line_color_btn = ColorToolButton()
        self.line_color_btn.set_color(_COLOR2)
        self.line_color_btn.set_title(_('Line Color'))
        options_toolbar.insert(self.line_color_btn, -1)
        GObject.timeout_add(1000,
                            self._connect_color_btn,
                            self.line_color_btn,
                            self._set_chart_line_color)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        options_toolbar.insert(separator, -1)

        h_label_icon = Icon(icon_name='hlabel')
        h_label_tool_item = Gtk.ToolItem()
        h_label_tool_item.add(h_label_icon)
        options_toolbar.insert(h_label_tool_item, -1)

        self.h_label = Entry(_('Horizontal label...'))
        self.h_label.entry.connect('changed', self._set_h_label)
        options_toolbar.insert(self.h_label, -1)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(False)
        options_toolbar.insert(separator, -1)

        v_label_icon = Icon(icon_name='vlabel')
        v_label_tool_item = Gtk.ToolItem()
        v_label_tool_item.add(v_label_icon)
        options_toolbar.insert(v_label_tool_item, -1)

        self.v_label = Entry(_('Vertical label...'))
        self.v_label.entry.connect('changed', self._set_v_label)
        options_toolbar.insert(self.v_label, -1)

        self._options_button.props.page = options_toolbar
        options_toolbar.show_all()

        toolbarbox.toolbar.insert(self._options_button, -1)

        text_toolbar_btn = ToolbarButton()
        text_toolbar_btn.props.icon_name = 'format-text'
        text_toolbar_btn.props.label = _('Text')
        toolbarbox.toolbar.insert(text_toolbar_btn, -1)
        self._text_options_btn = text_toolbar_btn

        texttoolbar = Gtk.Toolbar()

        self.font_name_combo = FontComboBox()
        self.font_name_combo.set_font_name('Sans')

        def set_font_name(w):
            self._set_chart_font_options(font=w.get_font_name())

        self.font_name_combo.connect("changed", set_font_name)
        texttoolbar.insert(ToolComboBox(self.font_name_combo), -1)

        self.font_size = FontSize()

        def set_font_size(w):
            self._set_chart_font_options(size=w.get_font_size())

        self.font_size.connect("changed", set_font_size)
        texttoolbar.insert(self.font_size, -1)

        self.text_color_btn = ColorToolButton()
        self.text_color_btn.set_color(style.COLOR_BLACK.get_gdk_color())
        self.text_color_btn.set_title(_('Font Color'))
        texttoolbar.insert(self.text_color_btn, -1)
        GObject.timeout_add(1000, self._connect_color_btn,
                            self.text_color_btn,
                            self._set_text_color)

        # self._title_font created in the top of the file
        self._title_font.connect('clicked', self._set_font_option,
                                 TITLE_FONT)
        self._title_font.set_tooltip(_('Title font'))
        self._title_font.props.icon_name = 'title-font'
        op_group = self._title_font

        texttoolbar.insert(self._title_font, 0)

        # self._labels_font created in the top of the file
        self._labels_font.connect('clicked', self._set_font_option,
                                  LABELS_FONT)
        self._labels_font.set_tooltip(_('Labels font'))
        self._labels_font.props.icon_name = 'labels-font'
        self._labels_font.props.group = op_group
        texttoolbar.insert(self._labels_font, 1)

        tick_font = RadioToolButton()
        tick_font.connect('clicked', self._set_font_option, TICK_FONT)
        tick_font.set_tooltip(_('Tick font'))
        tick_font.props.icon_name = 'tick-font'
        tick_font.props.group = op_group
        texttoolbar.insert(tick_font, 2)

        separator = Gtk.SeparatorToolItem()
        texttoolbar.insert(separator, 3)

        text_toolbar_btn.props.page = texttoolbar
        texttoolbar.show_all()

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        separator.set_expand(False)
        toolbarbox.toolbar.insert(separator, -1)

        self._fullscreen_button = ToolButton('view-fullscreen')
        self._fullscreen_button.set_tooltip(_("Fullscreen"))
        self._fullscreen_button.props.accelerator = '<Alt>Return'
        self._fullscreen_button.connect('clicked', self.__fullscreen_cb)
        toolbarbox.toolbar.insert(self._fullscreen_button, -1)

        charthelp.create_help(toolbarbox.toolbar)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        toolbarbox.toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbarbox.toolbar.insert(stopbtn, -1)

        self.set_toolbar_box(toolbarbox)

        # CANVAS
        paned = Gtk.HPaned()
        box = Gtk.VBox()
        self.box = box

        def size_allocate_cb(widget, allocation):
            paned.disconnect(self._setup_handle)
            box_width = allocation.width / 6
            box.set_size_request(min(170, box_width), -1)

        self._setup_handle = paned.connect('size_allocate',
                                           size_allocate_cb)

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_width(min(170, Gdk.Screen.width() / 6))
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.labels_and_values = ChartData(self)
        scroll.add(self.labels_and_values)

        self.labels_and_values.connect('label-changed', self._label_changed)
        self.labels_and_values.connect('value-changed', self._value_changed)

        box.pack_start(scroll, True, True, 0)

        liststore_toolbar = Gtk.Toolbar()

        move_up = ToolButton('go-up')
        move_up.set_tooltip(_('Move up'))
        move_up.connect('clicked', self._move_up)

        move_down = ToolButton('go-down')
        move_down.set_tooltip(_('Move down'))
        move_down.connect('clicked', self._move_down)

        liststore_toolbar.insert(move_up, 0)
        liststore_toolbar.insert(move_down, 1)

        box.pack_end(liststore_toolbar, False, False, 0)

        paned.add1(box)

        # CHARTS AREA
        eventbox = Gtk.EventBox()
        self.charts_area = ChartArea(self)

        eventbox.modify_bg(Gtk.StateType.NORMAL, _WHITE)
        eventbox.add(self.charts_area)

        self._notebook = Gtk.Notebook()
        self._notebook.set_property('show-tabs', False)
        self._notebook.append_page(eventbox, Gtk.Label())

        # EMPTY WIDGETS
        empty_widgets = Gtk.EventBox()
        empty_widgets.modify_bg(Gtk.StateType.NORMAL,
                                style.COLOR_WHITE.get_gdk_color())

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        mvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(mvbox, True, False, 0)

        image_icon = Icon(pixel_size=style.LARGE_ICON_SIZE,
                          icon_name='chart',
                          stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                          fill_color=style.COLOR_TRANSPARENT.get_svg())
        mvbox.pack_start(image_icon, False, False, style.DEFAULT_PADDING)

        label = Gtk.Label('<span foreground="%s"><b>%s</b></span>' %
                          (style.COLOR_BUTTON_GREY.get_html(),
                           _('No data')))
        label.set_use_markup(True)
        mvbox.pack_start(label, False, False, style.DEFAULT_PADDING)

        hbox = Gtk.Box()
        open_image_btn = Gtk.Button()
        open_image_btn.connect('clicked', self._add_value)
        add_image = Gtk.Image.new_from_stock(Gtk.STOCK_ADD,
                                             Gtk.IconSize.BUTTON)
        buttonbox = Gtk.Box()
        buttonbox.pack_start(add_image, False, True, 0)
        buttonbox.pack_end(Gtk.Label(_('Add a value')), True, True, 5)
        open_image_btn.add(buttonbox)
        hbox.pack_start(open_image_btn, True, False, 0)
        mvbox.pack_start(hbox, False, False, style.DEFAULT_PADDING)

        empty_widgets.add(vbox)
        empty_widgets.show_all()
        self._notebook.append_page(empty_widgets, Gtk.Label())

        paned.add2(self._notebook)

        self.set_canvas(paned)
        self.charts_area.connect('size_allocate', self._chart_size_allocate)

        self.show_all()

        Gdk.Screen.get_default().connect('size-changed', self._configure_cb)
        self._configure_cb()

    def _set_text_color(self, *args):
        color = utils.rgb2html(args[-1].get_color())
        self._set_chart_font_options(color=color)

    def _set_chart_font_options(self, font=None, size=None, color=None):
        op = self._font_options
        if self._font_option == TITLE_FONT:
            op['titleFont'] = font or op['titleFont']
            op['titleFontSize'] = size or op['titleFontSize']
            op['titleColor'] = color or op['titleColor']

        elif self._font_option == LABELS_FONT:
            op['axis']['labelFont'] = font or op['axis']['labelFont']
            op['axis']['labelFontSize'] = size or op['axis']['labelFontSize']
            op['axis']['labelColor'] = color or op['axis']['labelColor']

        elif self._font_option == TICK_FONT:
            op['axis']['tickFont'] = font or op['axis']['tickFont']
            op['axis']['tickFontSize'] = size or op['axis']['tickFontSize']
            op['axis']['tickColor'] = color or op['axis']['tickColor']

        self._font_options = op
        self._render_chart()

    def _get_chart_font_options(self, option):
        chart_options = self._font_options
        if option == TITLE_FONT:
            font = chart_options['titleFont']
            size = chart_options['titleFontSize']
            color = chart_options['titleColor']

        elif option == LABELS_FONT:
            font = chart_options['axis']['labelFont']
            size = chart_options['axis']['labelFontSize']
            color = chart_options['axis']['labelColor']

        elif option == TICK_FONT:
            font = chart_options['axis']['tickFont']
            size = chart_options['axis']['tickFontSize']
            color = chart_options['axis']['tickColor']

        else:
            return None, None, None
        return font, size, color

    def _set_font_option(self, *args):
        if not hasattr(self, 'font_name_combo'):
            return

        self._font_option = args[-1]

        font, size, color = self._get_chart_font_options(self._font_option)

        self.font_name_combo.set_font_name(font)
        self.font_size.set_font_size(size)
        self.text_color_btn.set_color(Color(color).get_gdk_color())

    def _create_chart_buttons(self, toolbar):
        add_vbar_chart = RadioToolButton()
        add_vbar_chart.set_tooltip(_('Vertical Bar Chart'))
        add_vbar_chart.props.icon_name = 'vbar'
        charts_group = add_vbar_chart

        toolbar.insert(add_vbar_chart, -1)

        add_hbar_chart = RadioToolButton()
        add_hbar_chart.set_tooltip(_('Horizontal Bar Chart'))
        add_hbar_chart.props.icon_name = 'hbar'
        add_hbar_chart.props.group = charts_group
        toolbar.insert(add_hbar_chart, -1)

        add_line_chart = RadioToolButton()
        add_line_chart.set_tooltip(_('Line Chart'))
        add_line_chart.props.icon_name = 'line'
        add_line_chart.props.group = charts_group
        toolbar.insert(add_line_chart, -1)

        add_pie_chart = RadioToolButton()
        add_pie_chart.set_active(True)
        add_pie_chart.set_tooltip(_('Pie Chart'))
        add_pie_chart.props.icon_name = 'pie'
        add_pie_chart.props.group = charts_group
        toolbar.insert(add_pie_chart, -1)

        add_vbar_chart.connect('toggled', self._add_chart_cb,
                               charts.VERTICAL_BAR)
        add_hbar_chart.connect('toggled', self._add_chart_cb,
                               charts.HORIZONTAL_BAR)
        add_line_chart.connect('toggled', self._add_chart_cb, charts.LINE)
        add_pie_chart.connect('toggled', self._add_chart_cb, charts.PIE)

        self.chart_type_buttons.append(add_vbar_chart)
        self.chart_type_buttons.append(add_hbar_chart)
        self.chart_type_buttons.append(add_line_chart)
        self.chart_type_buttons.append(add_pie_chart)

        self._add_chart_cb(add_vbar_chart, charts.VERTICAL_BAR)

    def _show_empty_widgets(self):
        if hasattr(self, '_notebook') and \
           self._notebook.get_current_page() == 0:
            self._notebook.set_current_page(1)
            self._remove_v.set_sensitive(False)

            for btn in self.chart_type_buttons:
                btn.set_sensitive(False)

            self._options_button.set_sensitive(False)
            self._text_options_btn.set_sensitive(False)
            self._fullscreen_button.set_sensitive(False)

    def _show_chart_area(self):
        if self._notebook.get_current_page() == 1:
            self._notebook.set_current_page(0)
            self._remove_v.set_sensitive(True)

            for btn in self.chart_type_buttons:
                btn.set_sensitive(True)

            self._options_button.set_sensitive(True)
            self._text_options_btn.set_sensitive(True)
            self._fullscreen_button.set_sensitive(True)

    def _create_measure_palette(self, button):
        palette = button.get_palette()
        hbox = Gtk.HBox()

        channel1 = ToolButton('measure-channel-1')
        channel1.connect('clicked', self.__import_measure_cb, 1)

        channel2 = ToolButton('measure-channel-2')
        channel2.connect('clicked', self.__import_measure_cb, 2)

        hbox.pack_start(channel1, False, True, 0)
        hbox.pack_end(channel2, False, True, 0)

        hbox.show_all()

        palette.set_content(hbox)

    def _measure_btn_clicked(self, button):
        palette = button.get_palette()
        palette.popup(immediate=True)

    def _add_value(self, widget, label='', value='0.0', bulk=False):
        before = len(self.chart_data)

        if label == '':
            label = str(before + 1)

        is_number = True
        try:
            float(value)
        except ValueError:
            _logger.debug('data (%s) not a number' % (str(value)))
            is_number = False

        if is_number:
            data = (label, float(value))
            if data not in self.chart_data:
                pos = self.labels_and_values.add_value(
                    label, value, bulk=bulk)
                self.chart_data.insert(pos, data)
                self._show_chart_area()
                self._update_chart_data()

        elif not is_number:
            _invalid_number_alert(activity)

    def _remove_value(self, widget):
        value = self.labels_and_values.remove_selected_value()
        self.chart_data.remove(value)
        self._update_chart_data()

    def _add_chart_cb(self, widget, type=charts.VERTICAL_BAR):
        if not widget.get_active():
            return

        self.current_chart = charts.Chart(type)

        def update_btn():
            if (type == charts.PIE and
                    not self.chart_type_buttons[3].get_active() and
                    not self.chart_type_buttons[7].get_active()):
                self.chart_type_buttons[3].set_active(True)
                self.chart_type_buttons[7].set_active(True)

        GObject.idle_add(update_btn)

        self.update_chart()

    def _configure_cb(self, event=None):
        # If we have room, put buttons on the main toolbar
        if Gdk.Screen.width() / 14 > style.GRID_CELL_SIZE:
            self._chart_button.set_expanded(False)
            self._chart_button.hide()
            for i in range(4):
                self.chart_type_buttons[i].show()
                self.chart_type_buttons[i + 4].hide()
        else:
            self._chart_button.show()
            self._chart_button.set_expanded(True)
            for i in range(4):
                self.chart_type_buttons[i].hide()
                self.chart_type_buttons[i + 4].show()

    def _chart_size_allocate(self, widget, allocation):
        self._render_chart()

    def unfullscreen(self):
        self.box.show()
        activity.Activity.unfullscreen(self)
        GObject.idle_add(self._render_chart)

    def __fullscreen_cb(self, button):
        self.box.hide()
        self._render_chart(fullscreen=True)
        activity.Activity.fullscreen(self)

    def _render_chart(self, fullscreen=False):
        if not self.chart_data:
            self._show_empty_widgets()
            return

        if self.current_chart is None or self.charts_area is None:
            return

        try:
            # Resize the chart for all the screen sizes
            alloc = self.get_allocation()

            if fullscreen:
                new_width = alloc.width
                new_height = alloc.height
                self.current_chart.width = alloc.width
                self.current_chart.height = alloc.height
            if not fullscreen:
                alloc = self.charts_area.get_allocation()
                new_width = alloc.width - 40
                new_height = alloc.height - 40
            self.current_chart.width = new_width
            self.current_chart.height = new_height

            # Set options
            self.current_chart.set_color_scheme(color=self.chart_color)
            self.current_chart.set_line_color(self.chart_line_color)
            self.current_chart.set_font_options(self._font_options)

            if self.current_chart.type == charts.PIE:
                self.current_chart.render(self)
            else:
                self.current_chart.render()
            self.charts_area.queue_draw()

        except (ZeroDivisionError, ValueError):
            pass

        self._show_chart_area()
        return False

    def _update_chart_active_button(self, type=None):
        if self.current_chart is None and type is None:
            return

        _type = type or self.current_chart.type

        if _type == charts.VERTICAL_BAR:
            self.chart_type_buttons[0].set_active(True)
            self.chart_type_buttons[4].set_active(True)

        elif _type == charts.HORIZONTAL_BAR:
            self.chart_type_buttons[1].set_active(True)
            self.chart_type_buttons[5].set_active(True)

        elif _type == charts.LINE:
            self.chart_type_buttons[2].set_active(True)
            self.chart_type_buttons[6].set_active(True)

        elif _type == charts.PIE:
            self.chart_type_buttons[3].set_active(True)
            self.chart_type_buttons[7].set_active(True)
            self._labels_font.set_sensitive(False)

    def _update_chart_data(self):
        if self.current_chart is None:
            return
        self.current_chart.data_set(self.chart_data)
        self._update_chart_labels()

    def _set_chart_title(self, widget):
        self._update_chart_labels(title=widget.get_text())

    def _update_chart_labels(self, title=''):
        if self.current_chart is None:
            return

        if not title and self.metadata['title']:
            title = self.metadata['title']

        self.current_chart.set_title(title)
        self.current_chart.set_x_label(self.x_label)
        self.current_chart.set_y_label(self.y_label)
        self._render_chart()

    def update_chart(self):
        if self.current_chart:
            self.current_chart.data_set(self.chart_data)
            self.current_chart.set_title(self.metadata['title'])
            self.current_chart.set_x_label(self.x_label)
            self.current_chart.set_y_label(self.y_label)
            self._set_font_option(self._font_option)
            self._render_chart()

    def _label_changed(self, treeview, path, new_label):
        path = int(path)
        self.chart_data[path] = (new_label, self.chart_data[path][1])
        self._update_chart_data()

    def _value_changed(self, treeview, path, new_value):
        path = int(path)
        self.chart_data[path] = (self.chart_data[path][0], float(new_value))
        self._show_chart_area()
        self._update_chart_data()

    def _move_up(self, widget):
        old, new = self.labels_and_values.move_up()
        _object = self.chart_data[old]
        self.chart_data.remove(_object)
        self.chart_data.insert(new, _object)
        self._update_chart_data()

    def _move_down(self, widget):
        old, new = self.labels_and_values.move_down()
        if old is not None:
            _object = self.chart_data[old]
            self.chart_data.remove(_object)
            self.chart_data.insert(new, _object)
            self._update_chart_data()

    def _set_h_label(self, widget):
        self.x_label = widget.get_text()
        self._update_chart_labels()

    def _set_v_label(self, widget):
        self.y_label = widget.get_text()
        self._update_chart_labels()

    def _set_chart_color(self, *args):
        self.chart_color = utils.rgb2html(args[-1].get_color())
        self._render_chart()

    def _set_chart_line_color(self, *args):
        self.chart_line_color = utils.rgb2html(args[-1].get_color())
        self._render_chart()

    def _connect_color_btn(self, colorbtn, function):
        if colorbtn._palette is None:
            return True

        for scale in colorbtn._palette._scales:
            scale.connect('button-release-event', function, colorbtn)

        for button in colorbtn._palette._swatch_tray.get_children():
            button.connect('clicked', function, colorbtn)

        return False

    def _object_chooser(self, mime_type, type_name):
        chooser = ObjectChooser()
        matches_mime_type = False

        response = chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
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
                alert.add_button(Gtk.ResponseType.OK, _('Ok'), ok_icon)
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
        for row in chart_data:
            self._add_value(
                None, label=row[0], value=str(row[1]), bulk=True)

        self.update_chart()

    def __import_stopwatch_cb(self, widget):
        matches_mime_type, file_path, title = \
            self._object_chooser(_STOPWATCH_MIME_TYPE, _('StopWatch'))

        if matches_mime_type:
            f = open(file_path)
            reader = StopWatchReader(f)
            self._graph_from_reader(reader)

            f.close()

    def __import_measure_cb(self, widget, channel=1):
        matches_mime_type, file_path, title = \
            self._object_chooser(_CSV_MIME_TYPE, _('Measure'))

        if matches_mime_type:
            f = open(file_path)
            reader = MeasureReader(f, channel)
            self._graph_from_reader(reader)

            f.close()

    def _save_as_image(self, widget):
        if self.current_chart:
            jobject = datastore.create()

            jobject.metadata['title'] = self.metadata['title'] + " Image"
            jobject.metadata['mime_type'] = 'image/png'

            self.current_chart.as_png(_CHART_FILE)
            jobject.set_file_path(_CHART_FILE)

            datastore.write(jobject)

    def load_from_file(self, f):
        try:
            data = json.load(f)
        finally:
            f.close()

        self.x_label = data['x_label']
        self.y_label = data['y_label']
        self.chart_color = data['chart_color']
        self.chart_line_color = data['chart_line_color']
        self.current_chart.type = data['current_chart.type']

        # Make it compatible with old Chart instances
        if 'font_options' in data:
            self._font_options = data['font_options']

        chart_data = data['chart_data']

        # Update charts buttons
        self._update_chart_active_button()

        # Update the controls in the config subtoolbar
        self.chart_color_btn.set_color(Color(self.chart_color).get_gdk_color())
        self.line_color_btn.set_color(Color(self.chart_line_color).
                                      get_gdk_color())

        # If the saved label is not '', set the text entry with the saved label
        if self.x_label != '':
            self.h_label.entry.set_text(self.x_label)

        if self.y_label != '':
            self.v_label.entry.set_text(self.y_label)

        # load the data
        for row in chart_data:
            self._add_value(
                None, label=row[0], value=str(row[1]), bulk=True)

        self.update_chart()

    def write_file(self, file_path):
        self.metadata['mime_type'] = 'application/x-chart-activity'
        if self.current_chart:

            data = {}
            data['x_label'] = self.x_label
            data['y_label'] = self.y_label
            data['chart_color'] = self.chart_color
            data['chart_line_color'] = self.chart_line_color
            data['current_chart.type'] = self.current_chart.type
            data['chart_data'] = self.chart_data
            data['font_options'] = self._font_options

            f = open(file_path, 'w')
            try:
                json.dump(data, f)
            finally:
                f.close()

    def read_file(self, file_path):
        f = open(file_path, 'r')
        GObject.idle_add(self.load_from_file, f)


class ChartData(Gtk.TreeView):

    __gsignals__ = {
        'label-changed': (GObject.SignalFlags.RUN_FIRST, None, [str, str]),
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, [str, str]),
    }

    def __init__(self, activity):

        GObject.GObject.__init__(self)

        self.model = Gtk.ListStore(str, str)
        self.set_model(self.model)

        # TreeSelection
        self._selection = self.get_selection()
        self._selection.set_mode(Gtk.SelectionMode.SINGLE)

        # Label column

        column = Gtk.TreeViewColumn(_('Label'))
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        label = Gtk.CellRendererText()
        label.set_property('editable', True)
        label.connect('edited', self._label_changed, self.model)

        column.pack_start(label, True)
        column.add_attribute(label, 'text', 0)
        self.append_column(column)

        # Value column

        column = Gtk.TreeViewColumn(_('Value'))
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        value = Gtk.CellRendererText()
        value.set_property('editable', True)
        value.connect('edited', self._value_changed, self.model, activity)

        column.pack_start(value, True)
        column.add_attribute(value, 'text', 1)

        self.append_column(column)
        self.set_enable_search(False)

        # Items count
        self._items_count = 0

        self.show_all()

    def add_value(self, label, value, bulk=False):
        treestore, selected = self._selection.get_selected()
        if not selected:
            path = 0

        elif selected:
            path = int(str(self.model.get_path(selected))) + 1

        if bulk:
            _iter = self.model.append([label, value])
        else:
            _iter = self.model.insert(path, [label, value])

        self.set_cursor(self.model.get_path(_iter),
                        self.get_column(1),
                        not bulk)

        self._items_count += 1

        _logger.info('Added: %s, Value: %s' % (label, value))

        return path

    def remove_selected_value(self):
        model, iter = self._selection.get_selected()
        value = (self.model.get(iter, 0)[0],
                 float(self.model.get(iter, 1)[0].replace(',', '.')))
        _logger.info('VALUE: ' + str(value))
        self.model.remove(iter)

        self._items_count -= 1

        return value

    def move_up(self):
        selected_iter = self._selection.get_selected()[1]
        p = int(str(self.model.get_path(selected_iter)))
        if p == 0:
            return (0,0)

        position = self.model.get_iter(p - 1)
        self.model.move_before(selected_iter, position)

        selected_path = int(str(self.model.get_path(selected_iter)))
        new_position_path = int(str(self.model.get_path(position)))
        return (selected_path, new_position_path)

    def move_down(self):
        selected_iter = self._selection.get_selected()[1]
        position = self.model.iter_next(selected_iter)
        position_path = int(str(self.model.get_path(selected_iter)))

        if not position_path == self._items_count - 1:
            self.model.move_after(selected_iter, position)

            selected_path = int(str(self.model.get_path(selected_iter)))
            new_position_path = int(str(self.model.get_path(position)))
            return (selected_path, new_position_path)

        else:
            return (None, None)

    def _label_changed(self, cell, path, new_text, model):
        _logger.info('Label change "%s" to "%s"' % (model[path][0], new_text))
        model[path][0] = new_text

        self.emit('label-changed', str(path), new_text)

    def _value_changed(self, cell, path, new_text, model, activity):
        _logger.info('Value change "%s" to "%s"' % (model[path][1], new_text))
        is_number = True
        number = new_text.replace(',', '.')
        try:
            float(number)
        except ValueError:
            is_number = False

        if is_number:
            decimals = utils.get_decimals(str(float(number)))
            new_text = locale.format('%.' + decimals + 'f', float(number))
            model[path][1] = str(new_text)

            self.emit('value-changed', str(path), number)

        else:
            if _extract_value(number) is not None:
                number = str(_extract_value(number))

                decimals = utils.get_decimals(str(float(number)))
                new_text = locale.format('%.' + decimals + 'f', float(number))
                model[path][1] = str(new_text)

                self.emit('value-changed', str(path), number)
            else:
                _invalid_number_alert(activity)


class Entry(Gtk.ToolItem):

    def __init__(self, text):
        GObject.GObject.__init__(self)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(text)
        self.add(self.entry)

        self.show_all()

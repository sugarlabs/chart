#!/usr/bin/env python
# -*- coding: utf-8 -*-

# charts.py by:
#    Agustin Zubiaga <aguzubiaga97@gmail.com>
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

import pycha.bar
import pycha.line
import pycha.pie

import cairo
import gobject


class Chart(gobject.GObject):
    def __init__(self, type="vertical", width=600, height=460):
        gobject.GObject.__init__(self)

        self.dataSet = None
        self.options = None
        self.surface = None

        self.type = type
        self.width = width
        self.height = height

    def data_set(self, data):
        """Set chart data (dataSet)"""

        self.dataSet = (
            ('Puntos', [(i, l[1]) for i, l in enumerate(data)]),
            )

        self.options = {
            'legend': {'hide': True},
            'axis': {
                'x': {
                    'ticks': [dict(v=i, label=l[0]) for i,
                                                        l in enumerate(data)],
                    'label': 'X',
                },
                'y': {
                    'tickCount': 5,
                    'label': 'Y',
                }
            },
            'background': {
                'chartColor': '#FFFFFF',
                'lineColor': '#d1e5ec'
            },
            'colorScheme': {
                'name': 'gradient',
                'args': {
                    'initialColor': 'blue',
                },
            },
        }

    def set_color_scheme(self, color='blue'):
        """Set the chart color scheme"""
        self.options["colorScheme"]["args"] = {'initialColor': color}

    def set_line_color(self, color='#d1e5ec'):
        """Set the chart line color"""
        self.options["background"]["lineColor"] = color

    def set_x_label(self, text="X"):
        """Set the X Label"""
        self.options["axis"]["x"]["label"] = str(text)

    def set_y_label(self, text="Y"):
        """Set the Y Label"""
        self.options["axis"]["y"]["label"] = str(text)

    def set_type(self, type="vertical"):
        """Set chart type (vertical, horizontal, line, pie)"""
        self.type = type

    def set_title(self, title="SimpleGraph Chart"):
        """Set the chart title"""
        self.options["title"] = title

    def render(self, sg=None):
        """Draw the chart
           Use the self.surface variable for show the chart"""
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                            self.width,
                                            self.height)

        if self.type == "vbar":
            chart = pycha.bar.VerticalBarChart(self.surface, self.options)

        elif self.type == "hbar":
            chart = pycha.bar.HorizontalBarChart(self.surface, self.options)

        elif self.type == "line":
            chart = pycha.line.LineChart(self.surface, self.options)

        elif self.type == "pie":
            self.options["legend"] = {"hide": "False"}
            chart = pycha.pie.PieChart(self.surface, self.options)
            self.dataSet = [(data[0],
                            [[0, data[1]]]) for data in sg.chart_data]

        chart.addDataset(self.dataSet)
        chart.render()

    def as_png(self, file):
        """Save the chart as png image"""
        self.surface.write_to_png(file)

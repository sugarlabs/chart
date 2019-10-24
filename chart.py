#!/usr/bin/env python
# -*- coding: utf-8 -*-

# chart.py by:
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

import sugarpycha.bar
import sugarpycha.line
import sugarpycha.pie

import cairo
from gi.repository import GObject

# Chart types
VERTICAL_BAR = 1
HORIZONTAL_BAR = 2
LINE = 3
PIE = 4


class Chart(GObject.GObject):

    def __init__(self, type=VERTICAL_BAR, width=600, height=460):
        GObject.GObject.__init__(self)

        self.dataSet = None
        self.options = None
        self.surface = None

        self.type = type
        self.width = width
        self.height = height

    def data_set(self, data):
        '''Set chart data (dataSet)'''

        self.dataSet = (
            ('Dots', [(i, l[1]) for i, l in enumerate(data)]),
        )

        self.options = {
            'legend': {'hide': True},
            'titleColor': '#000000',
            'titleFont': 'Tahoma',
            'titleFontSize': 12,
            'axis': {
                'tickColor': '#000000',
                'tickFont': 'Sans',
                'tickFontSize': 12,
                'labelFontSize': 14,
                'labelColor': '#666666',
                'labelFont': 'Sans',
                'lineColor': '#b3b3b3',
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
            'yvals': {'fontColor': '#000000'},
            'stroke': {
                'width': 3
            },
            'background': {
                'chartColor': '#FFFFFF',
                'lineColor': '#CCCCCC'
            },
            'colorScheme': {
                'name': 'gradient',
                'args': {
                    'initialColor': 'blue',
                },
            },
        }

    def set_font_options(self, op):
        self.options['titleFont'] = op['titleFont']
        self.options['titleFontSize'] = op['titleFontSize']
        self.options['titleColor'] = op['titleColor']
        self.options['axis']['labelFont'] = op['axis']['labelFont']
        self.options['axis']['labelFontSize'] = op['axis']['labelFontSize']
        self.options['axis']['labelColor'] = op['axis']['labelColor']
        self.options['axis']['tickFont'] = op['axis']['tickFont']
        self.options['axis']['tickFontSize'] = op['axis']['tickFontSize']
        self.options['axis']['tickColor'] = op['axis']['tickColor']

        if self.type == PIE:
            self.options['axis']['labelFont'] = op['axis']['tickFont']
            self.options['axis']['labelFontSize'] = op['axis']['tickFontSize']
            self.options['axis']['labelColor'] = op['axis']['tickColor']

    def set_color_scheme(self, color='blue'):
        '''Set the chart color scheme'''
        self.options['colorScheme']['args'] = {'initialColor': color}

    def set_line_color(self, color='#000000'):
        '''Set the chart line color'''
        self.options['stroke']['color'] = color

    def set_x_label(self, text='X'):
        '''Set the X Label'''
        self.options['axis']['x']['label'] = str(text)

    def set_y_label(self, text='Y'):
        '''Set the Y Label'''
        self.options['axis']['y']['label'] = str(text)

    def set_type(self, type=VERTICAL_BAR):
        '''Set chart type (VERTICAL_BAR, HORIZONTAL_BAR, LINE, PIE)'''
        self.type = type

    def set_title(self, title='Chart'):
        '''Set the chart title'''
        self.options['title'] = title

    def render(self, sg=None):
        '''Draw the chart
           Use the self.surface variable for show the chart'''
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                          self.width,
                                          self.height)

        if self.type == VERTICAL_BAR:
            chart = sugarpycha.bar.VerticalBarChart(self.surface, self.options)

        elif self.type == HORIZONTAL_BAR:
            chart = sugarpycha.bar.HorizontalBarChart(self.surface,
                                                      self.options)

        elif self.type == LINE:
            chart = sugarpycha.line.LineChart(self.surface, self.options)

        elif self.type == PIE:
            self.options['legend'] = {'hide': 'False'}
            chart = sugarpycha.pie.PieChart(self.surface, self.options)
            self.dataSet = [(data[0],
                            [[0, data[1]]]) for data in sg.chart_data]

        chart.addDataset(self.dataSet)
        chart.render()

    def as_png(self, file):
        '''Save the chart as png image'''
        self.surface.write_to_png(file)

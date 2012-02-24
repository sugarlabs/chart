#!/usr/bin/env python
# -*- coding: utf-8 -*-

# utils.py by:
#    Agustin Zubiaga <aguzubiaga97@gmail.com>

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

import os
import gconf


def rgb_to_html(color):
    '''Returns a html string from a Gdk color'''
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
    '''Returns the user colors'''
    color = gconf.client_get_default().get_string("/desktop/sugar/user/color")
    return color.split(",")


def get_chart_file(activity_dir):
    '''Returns a path for write the chart in a png image'''
    chart_file = os.path.join(activity_dir, "chart-1.png")
    num = 0

    while os.path.exists(chart_file):
        num += 1
        chart_file = os.path.join(activity_dir, "chart-" + str(num) + ".png")

    return chart_file


def get_decimals(number):
    '''Returns the decimals count of a number'''
    return str(len(number.split('.')[1]))

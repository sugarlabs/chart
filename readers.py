#!/usr/bin/env python
# -*- coding: utf-8 -*-

# readers.py by:
#    Agustin Zubiaga <aguz@sugarlabs.com>

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

import cPickle
import csv


class StopWatch():

    def set_data(self, data):
        self.data = cPickle.load(data)

    def get_stopwatchs_with_marks(self):
        count = 0
        stopwatchs_list = []
        for i in self.data[-1]:
            if i:
                count += 1
                stopwatchs_list.append([count, self.data[1][count - 1]])

        return stopwatchs_list, count

    def get_stopwatch_name(self, num=0):
        return self.data[1][num]

    def marks_to_chart_data(self, num=0, chart_data=[]):
        marks_count = 0

        marks = self.data[-1][num]
        marks.sort()

        for i in marks:
            marks_count += 1
            chart_data.append((str(marks_count), round(i, 2)))

        return chart_data

    def times_to_chart_data(self):
        times = [i[0][0] for i in self.data[2]]

        times_count = 0
        chart_data = []

        for i in times:
            times_count += 1
            chart_data.append((self.get_stopwatch_name(times_count - 1),
                              round(i, 2)))

        return chart_data


class Measure():

    def set_data(self, data):
        self.reader = csv.reader(data)

    def get_chart_data(self):
        count = 0
        chart_data = []

        for row in self.reader:
            count += 1

            if count > 6:
                label, value = row[0].split(": ")
                chart_data.append((label, float(value)))

        return chart_data

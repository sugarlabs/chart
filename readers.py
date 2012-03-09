#!/usr/bin/env python
# -*- coding: utf-8 -*-

# readers.py by:
#    Agustin Zubiaga <aguz@sugarlabs.org>

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

from gettext import gettext as _


class StopWatchReader():

    """Reader for StopWatch activity.

    If the data has only one stopwatch with marks, graphic the marks.
    Else, graphic the final time of the stopwatches.

    """

    def __init__(self, data):
        """Import chart data from file."""

        self._data = cPickle.load(data)

        self._v_label = _('Time')
        self._h_label = ''

    def get_chart_data(self):
        """Return data suitable for pyCHA."""

        count = self._get_stopwatchs_with_marks()
        chart_data = []

        if count == 1:
            self._h_label = _('Mark')

            marks_count = 0

            for x in self._data[-1]:
                x.sort()
                for y in x:
                    marks_count += 1
                    chart_data.append((str(marks_count), round(y, 2)))

        elif count == 0 or count > 1:
            self._h_label = _('StopWatch')

            times = [i[0][0] for i in self._data[2]]

            times_count = 0
            chart_data = []

            for i in times:
                times_count += 1
                chart_data.append((self._get_stopwatch_name(times_count - 1),
                                  round(i, 2)))

        return chart_data

    def get_labels_name(self):
        """Return the h_label and y_label names."""

        return self._v_label, self._h_label

    def _get_stopwatchs_with_marks(self):
        count = 0
        for i in self._data[-1]:
            if i:
                count += 1

        return count

    def _get_stopwatch_name(self, num=0):
        return self._data[1][num]


class MeasureReader():

    def __init__(self, file, channel):
        """Import chart data from file."""

        self._reader = csv.reader(file)
        self._channel = str(channel - 1)

    def get_chart_data(self):
        """Return data suitable for pyCHA."""

        count = 0
        chart_data = []

        for row in self._reader:
            count += 1

            if count > 6:
                label, value = row[0].split(": ")
                split = label.split(".")

                if len(split) > 1:
                    if split[1] == self._channel:
                        chart_data.append((split[0], float(value)))

                elif len(split) < 1:
                    chart_data.append((split[0], float(value)))

        return chart_data

    def get_labels_name(self):
        """Return the h_label and y_label names."""

        v_label = _('Values')
        h_label = _('Samples')

        return v_label, h_label

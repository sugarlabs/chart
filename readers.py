#!/usr/bin/env python
# -*- coding: utf-8 -*-

# readers.py by:
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

import cPickle

class StopWatch():
    
    def set_data(self, data):
        self.data = cPickle.load(data)
    
    def get_stopwatchs_with_marks_count(self):
        count = 0
        for i in self.data[-1]:
            if i: count += 1
        
        return count
        
    def marks_to_chart_data(self, num=0):
        chart_data = []
        marks_count = 0
        
        for i in self.data[-1][num]:
            marks_count += 1
            chart_data.append((str(marks_count), i))
            
        return chart_data




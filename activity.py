#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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
import os

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.toolbarbox import ToolbarBox

class SimpleGraph(activity.Activity):
    
    def __init__(self, handle):
        
        activity.Activity.__init__(self, handle, True)
        
        self.max_participiants = 1
        
        # TOOLBARS
        self.toolbarbox = ToolbarBox()
        
        self.activity_button = ActivityToolbarButton(self)
        self.toolbarbox.toolbar.insert(self.activity_button, 0)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        self.toolbarbox.toolbar.insert(separator, -1)

        self.stopbtn = StopButton(self)
        self.toolbarbox.toolbar.insert(self.stopbtn, -1)

        self.set_toolbar_box(self.toolbarbox) 
        
        # CANVAS
        self.paned = gtk.HPaned()
        
        self.treeview = TreeView()
        self.paned.add1(self.treeview)
        
        self.set_canvas(self.paned)
        
        self.show_all()
        
class TreeView(gtk.TreeView):
    
    def __init__(self):
        gtk.TreeView.__init__(self)
        
        self.model = gtk.ListStore(str, str)
        self.set_model(self.model)
        
        # Label column
        
        column = gtk.TreeViewColumn("Label")
        label = gtk.CellRendererText()

        column.pack_start(label)
        column.set_attributes(label, text=0)
        self.append_column(column)

        # Value column
        
        column = gtk.TreeViewColumn("Value")
        value = gtk.CellRendererText()

        column.pack_start(value)
        column.set_attributes(value, text=1)
        
        self.append_column(column)
           
        self.show_all()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import gtk

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.graphics.toolbarbox import ToolbarBox

class SimpleGraph(actvitiy.Activity):
    
    def __init__(self, handle):
        
        activity.Activity.__init__(self, handle, True)
        
        self.max_participiants = 0
        
        # TOOLBARS
        self.toolbarbox = ToolbarBox()
        
        self.activity_button = ActivityToolbarButton(self)
        self.toolbarbox.toolbar.insert(self.activity_button)
        
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
        
        self.model = gtk.ListStore()
        
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

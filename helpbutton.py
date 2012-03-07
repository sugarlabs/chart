#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2012, Gonzalo Odiard <godiard@gmail.com>

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

# HelpButton widget

from gettext import gettext as _

import gtk

from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.icon import Icon
from sugar.graphics import style


class HelpButton(gtk.ToolItem):

    def __init__(self, **kwargs):
        gtk.ToolItem.__init__(self)

        help_button = ToolButton('help-icon')
        help_button.set_tooltip(_('Help'))
        self.add(help_button)

        self._palette = help_button.get_palette()

        sw = gtk.ScrolledWindow()
        sw.set_size_request(int(gtk.gdk.screen_width() / 3),
            gtk.gdk.screen_height() - style.GRID_CELL_SIZE * 3)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self._max_text_width = int(gtk.gdk.screen_width() / 3) - 20
        self._vbox = gtk.VBox()
        self._vbox.set_homogeneous(False)
        sw.add_with_viewport(self._vbox)

        self._palette.set_content(sw)
        sw.show_all()

        help_button.connect('clicked', self.__help_button_clicked_cb)

    def __help_button_clicked_cb(self, button):
        self._palette.popup(immediate=True, state=1)

    def add_section(self, section_text):
        hbox = gtk.HBox()
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_markup('<b>%s</b>' % section_text)
        label.set_line_wrap(True)
        label.set_size_request(self._max_text_width, -1)
        hbox.add(label)
        hbox.show_all()
        self._vbox.pack_start(hbox, False, False, padding=5)

    def add_paragraph(self, text, icon=None):
        hbox = gtk.HBox()
        label = gtk.Label(text)
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_line_wrap(True)
        hbox.add(label)
        if icon is not None:
            _icon = Icon(icon_name=icon)
            hbox.add(_icon)
            label.set_size_request(self._max_text_width - 20, -1)
        else:
            label.set_size_request(self._max_text_width, -1)

        hbox.show_all()
        self._vbox.pack_start(hbox, False, False, padding=5)

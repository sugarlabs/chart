#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sharing.py by:
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

import utils

from dbus.service import signal
from dbus.gobject_service import ExportedGObject

# Tube
SERVICE = 'org.sugarlabs.SimpleGraph'
IFACE = SERVICE
PATH = '/org/sugarlabs/SimpleGraph'


class Receive(object):

    def __init__(self, parent, logger):
        """A class for receive (and process)"""
        super(Receive, self).__init__()

        self._parent = parent
        self._logger = logger
        self._processing_methods = None

        self._setup_dispatch_table()

    def _setup_dispatch_table(self):
        """Associate tokens with commands."""
        self._processing_methods = {
            'a': [self._add_value, 'value added'],
            'r': [self._remove_value, 'value removed'],
            'v': [self._value_changed, 'value changed'],
            'l': [self._label_changed, 'label changed'],
            't': [self._type_changed, 'chart type changed'],
            'x': [self._set_x_label, 'x label changed'],
            'y': [self._set_y_label, 'y label changed'],
            'cc': [self._set_chart_color, 'chart color changed'],
            'lc': [self._set_line_color, 'line color changed'],
            }

    def event_received_cb(self, event_message):
        """Data from a tube has arrived."""
        if len(event_message) == 0:
            return
        try:
            command, payload = event_message.split('|', 2)
        except ValueError:
            self._logger.debug('Could not split event \
                                 message %s' % (event_message))
            return

        data = utils.json_load(payload)
        event = self._processing_methods[command]

        self._logger.info('Event received: %s' % (event[1]))

        event[0](payload)
        self._logger.info('Processing data: %s' % (data))

    def _add_value(self, data):
        self._parent._add_value(None, data[0], data[1], data[2])

    def _remove_value(self, data):
        self._parent.labels_and_values.model.remove(data[0])
        del self._parent.chart_data[data[0]]
        self._parent._update_chart_data()

    def _value_changed(self, data):
        self._parent._value_changed(None, data[0], data[1])

    def _label_changed(self, data):
        self._parent._label_changed(None, data[0], data[1])

    def _type_changed(self, data):
        self._parent.current_chart.type = data
        self._parent._render_chart()

    def _set_x_label(self, data):
        self._parent.x_label = data
        self._parent._update_chart_labels()

    def _set_y_label(self, data):
        self._parent.y_label = data
        self._parent._update_chart_labels()

    def _set_chart_color(self, data):
        self._parent.chart_color = data
        self._parent._render_chart()

    def _set_line_color(self, data):
        self._parent.chart_line_color = data
        self._parent._render_chart()


class Send(object):

    def __init__(self, parent):
        """A class for send data"""
        super(Send, self).__init__()

        self._parent = parent

    def _send(self, data):
        self._parent.chattube.SendText(data)

    def add_value(self, data):
        dump = utils.json_dump(data)
        data = "a|%s" % (dump)
        self._send(data)

    def remove_value(self, data):
        dump = utils.json_dump(data)
        data = "r|%s" % (dump)
        self._send(data)

    def value_changed(self, data):
        dump = utils.json_dump(data)
        data = "v|%s" % (dump)
        self._send(data)

    def label_changed(self, data):
        dump = utils.json_dump(data)
        data = "l|%s" % (dump)
        self._send(data)

    def type_changed(self, data):
        dump = utils.json_dump(data)
        data = "t|%s" % (dump)
        self._send(data)

    def set_x_label(self, data):
        dump = utils.json_dump(data)
        data = "x|%s" % (dump)
        self._send(data)

    def set_y_label(self, data):
        dump = utils.json_dump(data)
        data = "y|%s" % (dump)
        self._send(data)

    def set_chart_color(self, data):
        dump = utils.json_dump(data)
        data = "cc|%s" % (dump)
        self._send(data)

    def set_line_color(self, data):
        dump = utils.json_dump(data)
        data = "lc|%s" % (dump)
        self._send(data)


class ChatTube(ExportedGObject):
    """ Class for setting up tube for sharing """

    def __init__(self, tube, is_initiator, stack_received_cb):
        super(ChatTube, self).__init__(tube, PATH)
        self.tube = tube
        self.is_initiator = is_initiator  # Are we sharing or joining activity?
        self.stack_received_cb = stack_received_cb
        self.stack = ''

        self.tube.add_signal_receiver(self.send_stack_cb, 'SendText', IFACE,
                                      path=PATH, sender_keyword='sender')

    def send_stack_cb(self, text, sender=None):
        if sender == self.tube.get_unique_name():
            return
        self.stack = text
        self.stack_received_cb(text)

    @signal(dbus_interface=IFACE, signature='s')
    def SendText(self, text):
        self.stack = text

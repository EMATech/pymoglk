# -*- coding: utf-8 *-*
"""A class to communicate with Matrix Orbital's GLK series LCD displays"""
# Copyright (C) 2012 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import serial
import glk


class PyMoGlk:

    def __init__(self, serialport='/dev/ttyUSB0', baudrate=19200, timeout=5):
        self.port = serial.Serial(serialport, baudrate, timeout)

    def write(self, text):
        self.port.write(text)

    def read(self):
        return self.port.read()

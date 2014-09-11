# -*- coding: utf-8 *-*
"""A class to communicate with Matrix Orbital's GLK series LCD displays"""
# Copyright (C) 2012-2014 Raphaël Doursenaud <rdoursenaud@free.fr>
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

##Source :
# Matrix Orbital
# GLK19264-7T-1U
# Technical Manual
# Revision: 1.2
# http://www.matrixorbital.ca/manuals/GLK_Series/GLK_GLC_Legacy/GLK19264-7T-1U/GLK19264-7T-1U.pdf

## I2C PROTOCOL
# START : Toggle SDA high to low
# Address : '\x50' (write) or '\x51' (read)
# Information : '\x48' '\x45' '\x4C' '\x4C' '\x4F'
# STOP : Toggle SDA low to high

# TODO: I2C implementation and unavailable commands in this mode

##COMMANDS AND RETURN CODES
# Format :
#    Command1/Return1    Code in HEX format
#                Parameter1[Range]
#                (Comments)
#                Parameter2[Range]
#                (Comments)
#                ...
#                Parametern[Range]
#                (Comments)
#    Command1/Return2    Code in HEX format
#                ...

## GENERAL COMMENTS
# Coordinates are always absolute from the top left corner
# Display is 192x64 so legal values are x[0-191] y[0-63]

import serial
from binascii import hexlify
import struct

class PyMoGlk:
    _DEBUG = True

    mode = 'serial'

    ##COMMUNICATION
    _CMD_INIT = b'\xFE'
    # (Must be issued before any command)
    _CMD_FLOW_CONTROL_ON = b'\x3A'
    #                    full[0-128]
    #                    (Number of bytes before almost full
    #                     0: full)
    #                    empty[0-128]
    #                    (Number of bytes before almost empty
    #                     128: empty)

    _RET_ALMOST_FULL = b'\xFE'
    _RET_ALMOST_EMPTY = b'\xFF'

    _CMD_FLOW_CONTROL_OFF = b'\x3B'

    _CMD_I2C_ADDRESS = b'\x33'

    _CMD_BAUD_RATE = b'\x39'
    #                    speed[See table below]

    _BAUD_RATE_9600 = b'\xCF'
    _BAUD_RATE_14400 = b'\x8A'
    _BAUD_RATE_19200 = b'\x67'
    _BAUD_RATE_28800 = b'\x44'
    _BAUD_RATE_38400 = b'\x33'
    _BAUD_RATE_57600 = b'\x22'
    _BAUD_RATE_76800 = b'\x19'
    _BAUD_RATE_115200 = b'\x10'

    _CMD_NON_STANDARD_BAUD_RATE = b'\xA4'
    #                    speed[12-2047]
    #                    (2 bytes,
    #                    LSB then MSB,
    #                    Out of bounds value can cause display
    #                    to stop working
    #                    Value should be within 3% for the device
    #                    to communicate)

    #                    Formula :
    #                             CrystalSpeed (16MHz)
    #                    speed = ---------------------  -  1
    #                              8 x DesiredBaud

    ## FONTS
    # FONT FILE FORMAT
    #  Header (4 bytes)
    #    Nominal Width (1 byte)
    #    Height (1 byte)
    #    ASCII Start Value (1 byte)
    #    ASCII End Value (1 byte)
    #  Character Table (3 bytes per character)
    #    High Offset MSB (1 byte)
    #    Low Offset LSB (1 byte)
    #    Character Width (1 byte)
    #  Bitmap Data

    # Each character is encoded horizontally then padded to form a full last byte

    # TODO: implement font file format

    _CMD_UPLOAD_FONT = b'\x24'
    #                    fontid
    #                    lsbsize
    #                    msbsize
    #                    fontfile
    # (Don't forget to set the new font metrics,
    #  see FILESYSTEM file transfer protocol)
    _CMD_USE_FONT = b'\x31'
    #                    fontid
    _CMD_FONT_METRICS = b'\x32'
    #                    lm
    #                    (Left Margin: Location in pi\xels)
    #                    tm
    #                    (Top Margin: Location in pi\xels)
    #                    csp
    #                    (Character Spacing in pi\xels)
    #                    lsp
    #                    (Line Spacing in pi\xels)
    #                    srow
    #                    (Scroll Row:
    #                    Y location of last row in pi\xels)
    _CMD_BOX_SPACE_MODE = b'\xAC'
    #                    value[0-1]
    #                    (0: Off,
    #                     1: On)

    ## TEXT
    _LINE_FEED = b'\x0A'

    _CMD_HOME = b'\x48'
    _CMD_CURSOR_POSITION = b'\x47'
    #                    col
    #                    row
    #                    (Derived from current font base size)
    _CMD_CURSOR_COORDINATE = b'\x79'
    #                    x
    #                    y
    _CMD_AUTO_SCROLL_ON = b'\x51'
    _CMD_AUTO_SCROLL_OFF = b'\x52'

    ## BITMAPS
    # BITMAP FILE FORMAT
    #  The bitmap is encoded into bytes horizontally

    _CMD_UPLOAD_BMP = b'\x5E'
    #                    bitmapid
    #                    lsbsize
    #                    msbsize
    #                    bitmapfile
    # (see FILESYSTEM file transfer protocol)
    _CMD_DRAW_MEMORY_BMP = b'\x62'
    #                    bitmapid
    #                    x
    #                    y
    _CMD_DRAW_BMP = b'\x64'
    #                    x
    #                    y
    #                    width
    #                    height
    #                    data

    ## BAR GRAPHS & DRAWING
    _CMD_DRAWING_COLOR = b'\x63'
    #                    color[0-255]
    #                    (0:     White,
    #                     1-255: Black)
    _CMD_DRAW_PIXEL = b'\x70'
    #                    x
    #                    y
    _CMD_DRAW_LINE = b'\x6C'
    #                    x1
    #                    y1
    #                    x2
    #                    y2
    # (Lines may interpolate differently Left to Right and Right to Left)
    _CMD_CONTINUE_LINE = b'\x65'
    #                    x
    #                    y
    _CMD_DRAW_RECTANGLE = b'\x72'
    #                    color[0-255]
    #                    (0:     White,
    #                     1-255: Black)
    #                    x1
    #                    y1
    #                    x2
    #                    y2
    _CMD_DRAW_SOLID_RECTANGLE = b'\x78'
    #                    color[0-255]
    #                    (0:     White,
    #                     1-255: Black)
    #                    x1
    #                    y1
    #                    x2
    #                    y2
    _CMD_INITIALIZE_BAR_GRAPH = b'\x67'
    #                    bgid[0-15]
    #                    type[0-3]
    #                    (0: Vertical from bottom,
    #                     1: Horizontal from left,
    #                     2: Vertical from top,
    #                     3: Horizontal from right)
    #                    x1
    #                    y1
    #                    x2
    #                    (x1<x2)
    #                    y2
    #                    (y1<y2)
    # (Beware of overlapping bar graphs)
    _CMD_DRAW_BAR_GRAPH = b'\x69'
    #                    bgid[0-15]
    #                    value
    #                    (In pi\xels)
    _CMD_INITIALIZE_STRIP_CHART = b'\x6A'
    #                    scid[0-6]
    #                    x1
    #                    y1
    #                    x2
    #                    (x1<x2)
    #                    y2
    #                    (y1<y2)
    _CMD_SHIFT_STRIP_CHART = b'\x6B'
    #                    ref
    #                    (LSB: scid,
    #                     MSB: direction
    #                     0: Left,
    #                     1: Right)

    ## GPO
    # (Hardwired to 3 tricolor LEDs)
    # LEDS LAYOUT
    #    LED 1 - Top     GPO 2   GPO 1
    #    LED 2 - Middle  GPO 4   GPO 3
    #    LED 3 - Bottom  GPO 6   GPO 5
    #    Yellow          0   0
    #    Green           0   1
    #    Red             1   0
    #    Off             1   1

    _CMD_GPO_OFF = b'\x56'
    #                    num[1-6]
    _CMD_GPO_ON = b'\x57'
    #                    num[1-6]
    _CMD_STARTUP_GPO_STATE = b'\xC3'
    #                    num[1-6]
    #                    state[0-1]
    #                    (0: Off,
    #                     1: On)
    # (Doesn't affect current state)

    ## KEYPAD
    # Default layout:
    _RET_UP = b'\x42'
    _RET_DOWN = b'\x48'
    _RET_LEFT = b'\x44'
    _RET_RIGHT = b'\x43'
    _RET_CENTER = b'\x45'
    _RET_TOP = b'\x41'
    _RET_BOTTOM = b'\x47'
    _RET_RELEASE_UP = b'\x62'
    _RET_RELEASE_DOWN = b'\x68'
    _RET_RELEASE_LEFT = b'\x64'
    _RET_RELEASE_RIGHT = b'\x63'
    _RET_RELEASE_CENTER = b'\x65'
    _RET_RELEASE_TOP = b'\x61'
    _RET_RELEASE_BOTTOM = b'\x67'

    _CMD_AUTO_TRANSMIT_KEY_ON = b'\x41'
    _CMD_AUTO_TRANSMIT_KEY_OFF = b'\x4F'
    # (The keypad buffer is reset after 10 key presses)
    _CMD_POLL_KEY = b'\x26'
    # (Returned code MSB flags 'more than one key press in buffer')

    _RET_NO_KEY = b'\x00'

    _CMD_CLEAR_KEY_BUFFER = b'\x45'
    _CMD_DEBOUNCE_TIME = b'\x55'
    #                    time[0-255]
    #                    (6.554ms increments,
    #                     Default: 8)
    _CMD_AUTO_REPEAT_MODE = b'\x7E'
    #                    mode[0-1]
    #                    (0: Resend Key,
    #                     1: Key Up/Down)
    _CMD_AUTO_REPEAT_OFF = b'\x60'
    _CMD_CUSTOM_KEYPAD_CODES = b'\xD5'
    #                    kdown[See table bellow]
    #                    (9 bytes)
    #                    kup[See table bellow]
    #                    (9 bytes)
    #                    Byte  Button
    #                    1    Top
    #                    2    Up
    #                    3    Right
    #                    4    Left
    #                    5    Center
    #                    6    N/A
    #                    7    Bottom
    #                    8    Down
    #                    9    N/A

    # FI\XME: Report it missing from codes list

    ## DISPLAY
    _CMD_CLEAR_SCREEN = b'\x58'
    _CMD_DISPLAY_ON = b'\x42'
    #                    min[0-90]
    _CMD_DISPLAY_OFF = b'\x46'
    _CMD_BRIGHTNESS = b'\x99'
    #                    brightness[0-255]
    #                    (Default: 255)
    _CMD_DEFAULT_BRIGHTNESS = b'\x98'
    #                    brightness[0-255]
    #                    (Default: 255)
    _CMD_CONTRAST = b'\x50'
    #                    contrast[0-255]
    #                    (Default: 128)
    _CMD_DEFAULT_CONTRAST = b'\x91'
    #                    contrast[0-255]
    #                    (Default: 128)

    ## FILESYSTEM
    # FILE TRANSFER PROTOCOL
    #  Host                  Display
    #  CMD_INIT
    #  CMD_UPLOAD(_FS | _FONT | _BMP)
    #  (parameters)
    #  (RET_CONFIRM | RET_DECLINE)
    #  CMD_CONFIRM
    #  -------------------Loop Here----------------------------
    #  NE\XT_BYTE
    #  NE\XT_BYTE
    #  (CMD_CONFIRM | CMD_DECLINE)
    #  -------------------End Loop-----------------------------

    # TODO: Implement file transfer protocol

    _RET_CONFIRM = b'\x01'
    _RET_DECLINE = b'\x08'

    _CMD_CONFIRM = b'\x01'
    _CMD_DECLINE = b'\x08'

    _CMD_WIPE_FILESYSTEM = b'\x21', b'\x59', b'\x21'
    # (Be carefull with this one!)
    _CMD_DELETE_FILE = b'\xAD'
    #                    type[0-1]
    #                    (0: Font,
    #                     1: Bitmap)
    #                     fontid or bitmapid
    _CMD_FREE_SPACE = b'\xAF'

    # FREE SPACE RETURN FORMAT
    # Free space size (4 bytes LSB to MSB)

    _CMD_DIRECTORY = b'\xB3'

    # DIRECTORY RETURN FORMAT
    #  Header (1 byte)
    #    Number of entries (1 byte)1 byte)
    #    Number of entries (1 byte)
    #  File Entry (4 bytes)
    #    Flag (1 byte)
    #    (b'\x00': Not used)
    #    FileID/Type (1 byte)
    #    (1st bit: File Type
    #    Next seven bits: FileID)
    #    File size LSB (1 byte)
    #    File size MSB (1 byte)

    _CMD_UPLOAD_FS = b'\xB0'
    #                    fsimagefile
    #                    (Must be 16KB)
    _CMD_DOWNLOAD_FILE = b'\xB2'
    #                    type[0-1]
    #                    (0: Font,
    #                     1: Bitmap)
    #                    fontid or bitmapid

    _CMD_MOVE_FILE = b'\xB4'
    #                    oldtype[0-1]
    #                    (0: Font,
    #                     1: Bitmap)
    #                    oldid
    #                    newtype[0-1]
    #                    (0: Font,
    #                     1: Bitmap)
    #                    newid
    _CMD_DUMP_FS = b'\x30'

    #  DOWNLOAD_FILE AND DUMP_FS RETURN FORMAT
    #  File size (4 bytes)
    #  (LSB to MSB)
    #  File Data

    # Undocumented command! Seems to dump the settings.
    _CMD_DUMP_SETTINGS = b'\xD0'

    ## SECURITY
    _CMD_REMEMBER = b'\x93'
    #                    value[0-1]
    #                    (0: Do not remember,
    #                     1: Remember)
    _CMD_LOCK_LEVEL = b'\xCA', b'\xF5', b'\xA0'
    #                    level
    #                    (Lock bits:
    #                     0-2:  Reserved leave 0,
    #                     3:    Communication speed,
    #                     4:    Settings,
    #                     5:    Filesystem,
    #                     6:    Command,
    #                     7:    Display)
    _CMD_DEFAULT_LOCK_LEVEL = b'\xCB', b'\xF5', b'\xA0'
    #                    level
    #                    (Lock bits:
    #                     0-2:  Reserved leave 0,
    #                     3:    Communication speed,
    #                     4:    Settings,
    #                     5:    Filesystem,
    #                     6:    Command,
    #                     7:    Display)

    # FI\XME: Report it missing from codes list
    _CMD_WRITE_CUSTOMER_DATA = b'\x34'
    #                    data
    #                    (16B are accessible)
    _CMD_READ_CUSTOMER_DATA = b'\x35'

    #  READ_CUSTOMER_DATA RETURN FORMAT
    #  Data (16 bytes)

    ## MISC
    _CMD_VERSION_NUMBER = b'\x36'

    #  VERSION_NUMBER RETURN FORMAT
    #  Version (1 byte)
    #  (Represents the version number
    #   Hex  Version
    #   b'\x19'  1.9
    #   b'\x57'  5.7)

    _CMD_MODULE_TYPE = b'\x37'

    #  MODULE_TYPE RETURN FORMAT
    #  Type (1 byte)
    #  (One of the following return codes)
    _RET_LCD0821 = b'\x01'
    _RET_LCD2021 = b'\x02'
    _RET_LCD2041 = b'\x05'
    _RET_LCD4021 = b'\x06'
    _RET_LCD4041 = b'\x07'
    _RET_LK202_25 = b'\x08'
    _RET_LK204_25 = b'\x09'
    _RET_LK404_55 = b'\x0A'
    _RET_VFD2021 = b'\x0B'
    _RET_VFD2041 = b'\x0C'
    _RET_VFD4021 = b'\x0D'
    _RET_VK202_25 = b'\x0E'
    _RET_VK204_25 = b'\x0F'
    _RET_GLC12232 = b'\x10'
    _RET_GLC24064 = b'\x13'
    _RET_GLK24064_25 = b'\x15'
    _RET_GLK12232_25 = b'\x22'
    _RET_GLK12232_25_SM = b'\x24'
    _RET_GLK24064_16_1U_USB = b'\x25'
    _RET_GLK24064_16_1U = b'\x26'
    _RET_GLK19264_7T_1U_USB = b'\x27'
    _RET_GLK12236_16 = b'\x28'
    _RET_GLK12232_16_SM = b'\x29'
    _RET_GLK19264_7T_1U = b'\x2A'
    _RET_LK204_7T_1U = b'\x2B'
    _RET_LK204_7T_1U_USB = b'\x2C'
    _RET_LK404_AT = b'\x31'
    _RET_MOS_AV_162A = b'\x32'
    _RET_LK402_12 = b'\x33'
    _RET_LK162_12 = b'\x34'
    _RET_LK204_25PC = b'\x35'
    _RET_LK202_24_USB = b'\x36'
    _RET_VK202_24_USB = b'\x37'
    _RET_LK204_24_USB = b'\x38'
    _RET_VK204_24_USB = b'\x39'
    _RET_PK162_12 = b'\x3A'
    _RET_VK162_12 = b'\x3B'
    _RET_MOS_AP_162A = b'\x3C'
    _RET_PK202_25 = b'\x3D'
    _RET_MOS_AL_162A = b'\x3E'
    _RET_MOS_AL_202A = b'\x3F'
    _RET_MOS_AV_202A = b'\x40'
    _RET_MOS_AP_202A = b'\x41'
    _RET_PK202_24_USB = b'\x42'
    _RET_MOS_AL_082 = b'\x43'
    _RET_MOS_AL_204 = b'\x44'
    _RET_MOS_AV_204 = b'\x45'
    _RET_MOS_AL_402 = b'\x46'
    _RET_MOS_AV_402 = b'\x47'
    _RET_LK082_12 = b'\x48'
    _RET_VK402_12 = b'\x49'
    _RET_VK404_55 = b'\x4A'
    _RET_LK402_25 = b'\x4B'
    _RET_VK402_25 = b'\x4C'
    _RET_PK204_25 = b'\x4D'
    _RET_MOS = b'\x4F'
    _RET_MOI = b'\x50'
    _RET_XBOARD_S = b'\x51'
    _RET_XBOARD_I = b'\x52'
    _RET_MOU = b'\x53'
    _RET_XBOARD_U = b'\x54'
    _RET_LK202_25_USB = b'\x55'
    _RET_VK202_25_USB = b'\x56'
    _RET_LK204_25_USB = b'\x57'
    _RET_VK204_25_USB = b'\x58'
    _RET_LK162_12_TC = b'\x5B'
    _RET_GLK240128_25 = b'\x72'
    _RET_LK404_25 = b'\x73'
    _RET_VK404_25 = b'\x74'

    def __init__(self, serialport='/dev/ttyUSB0', baudrate=19200, timeout=5):
        self.port = serial.Serial(serialport, baudrate=baudrate, timeout=timeout)
        if self._DEBUG:
            print("DEBUG: port parameters")
            print(self.port.getSettingsDict())

    def __del__(self):
        self.port.close()

    def write(self, text):
        if self._DEBUG:
            print("DEBUG: write(" + text + ")")
        self.port.write(bytearray(text, 'ascii'))

    def send(self, message):
        if self._DEBUG:
            print("DEBUG: send(" + hexlify(message) + ")")
        self.port.write(message)

    def read(self, size=1):
        data = self.port.read(size=size)
        if self._DEBUG:
            print("DEBUG: read(" + str(size) + ") = " + hexlify(data) + "")
        return data

    # 4.2
    def turn_flow_control_on(self, full=0, empty=128):
        # TODO: declare custom exceptions
        if self.mode == 'i2c':
            raise Exception
        if (0 <= full <= 128) or (0 <= empty <= 128):
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_FLOW_CONTROL_ON, full, empty])
        self.send(msg)

    # 4.3
    def turn_flow_control_off(self):
        # TODO: declare custom exceptions
        if self.mode == 'i2c':
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_FLOW_CONTROL_OFF])
        self.send(msg)

    def set_flow_control(self, state=False):
        if state:
            self.turn_flow_control_on()
        else:
            self.turn_flow_control_off()

        # 4.4
    def set_i2c_slave_address(self, adr='\x50'):
        # TODO: declare custom exceptions
        if not '\x00' <= adr <= '\xFF':
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_I2C_ADDRESS, adr])
        self.send(msg)

    # 4.5
    def set_baud_rate(self, speed=_BAUD_RATE_19200):
        # TODO: declare custom exceptions
        if speed not in ('\xCF', '\x8A', '\x67', '\x44', '\x33', '\x22', '\x19', '\x10'):
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_BAUD_RATE, speed])
        self.send(msg)

    # 4.6
    def set_non_standard_baud_rate(self, speed):
        # TODO: declare custom exceptions
        if not 12 <= speed <= 2047:
            raise Exception
        # FIXME: Extract lsb and msb from speed
        raise NotImplementedError
        msg = bytearray([self._CMD_INIT, self._CMD_BAUD_RATE, lsb, msb])
        self.send(msg)

    #5.2
    def upload_font(self, ref, data):
        return NotImplemented

    #5.3
    def set_font(self, ref):
        msg = bytearray([self._CMD_INIT, self._CMD_USE_FONT, ref])
        self.send(msg)

    #5.4
    def set_font_metrics(self, lm, tm, csp, lsp, srow):
        msg = bytearray([self._CMD_INIT, self._CMD_FONT_METRICS, lm, tm, csp, lsp, srow])
        self.send(msg)

    # 5.5
    def set_box_space_mode(self, state=True):
        if state:
            value = '\x01'
        else:
            value = '\x00'
        msg = bytearray([self._CMD_INIT, self._CMD_BOX_SPACE_MODE, value])
        self.send(msg)

    #6.2
    def set_cursor_home(self):
        msg = bytearray([self._CMD_INIT, self._CMD_HOME])
        self.send(msg)

    #6.3
    def set_cursor_position(self, col, row):
        msg = bytearray([self._CMD_INIT, self._CMD_CURSOR_POSITION, col, row])
        self.send(msg)

    # 6.4
    def set_cursor_coordinates(self, x, y):
        msg = bytearray([self._CMD_INIT, self._CMD_CURSOR_COORDINATE, x, y])
        self.send(msg)

    # 6.5
    def enable_autoscroll(self):
        msg = bytearray([self._CMD_INIT, self._CMD_AUTO_SCROLL_ON])
        self.send(msg)

    # 6.6
    def disable_autoscroll(self):
        msg = bytearray([self._CMD_INIT, self._CMD_AUTO_SCROLL_OFF])
        self.send(msg)

    def set_autoscroll(self, state=True):
        if state:
            self.enable_autoscroll()
        else:
            self.disable_autoscroll()

    #7.2
    def upload_bitmap(self, ref, data):
        return NotImplemented

    #7.3
    def draw_memory_bitmap(self, ref, x=0, y=0):
        # TODO: make sure x/y is in available range for the display
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_MEMORY_BMP, ref, x, y])
        self.send(msg)

    #7.4
    def draw_bitmap(self, w, h, data, x=0, y=0):
        # TODO: check data is ok from w and h
        raise NotImplementedError
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_BMP, x, y, w, h, data])
        self.send(msg)

    #8.2
    def set_drawing_color(self, color):
        # TODO: declare custom exceptions
        if not 0 <= color <= 255:
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_DRAWING_COLOR, color])
        self.send(msg)

    #8.3
    def draw_pixel(self, x, y):
        # TODO: make sure x/y is OK for display
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_PIXEL, x, y])
        self.send(msg)

    #8.4
    def draw_line(self, x1, y1, x2, y2):
        # TODO: make sure x/y is OK for display
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_LINE, x1, y1, x2, y2])
        self.send(msg)

    #8.5
    def continue_line(self, x, y):
        # TODO: make sure x/y is OK for display
        msg = bytearray([self._CMD_INIT, self._CMD_CONTINUE_LINE, x, y])
        self.send(msg)

    #8.6
    def draw_rectangle(self, color, x1, y1, x2, y2):
        # TODO: make sure x/y is OK for display
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_RECTANGLE, color, x1, y1, x2, y2])
        self.send(msg)

    #8.7
    def draw_solid_rectangle(self, color, x1, y1, x2, y2):
        # TODO: make sure x/y is OK for display
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_SOLID_RECTANGLE, color, x1, y1, x2, y2])
        self.send(msg)

    #8.8
    def init_bargraph(self, ref, type, x1, y1, x2, y2):
        # TODO: declare custom exceptions
        if not 0 <= ref <= 15:
            raise Exception
        if not 0 <= type <= 3:
            raise Exception
        if x1 > x2:
            raise Exception
        if y1 > y2:
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_INITIALIZE_BAR_GRAPH, ref, type, x1, y1, x2, y2])
        self.send(msg)

    #8.9
    def draw_bargraph(self, ref, value):
        msg = bytearray([self._CMD_INIT, self._CMD_DRAW_BAR_GRAPH, ref, value])
        self.send(msg)

    #8.10
    def init_stripchart(self, ref, x1, y1, x2, y2):
        # TODO: declare custom exceptions
        if not 0 <= ref <= 6:
            raise Exception
        # X def must lie on byte boundaries
        if x1 % '\x08' or x2 % '\x08':
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_INITIALIZE_STRIP_CHART, ref, x1, y1, x2, y2])
        self.send(msg)

    #8.11
    def shift_stripchart(self, ref, dir):
        return NotImplemented
        msg = bytearray([self._CMD_INIT, self._CMD_SHIFT_STRIP_CHART, ref])
        self.send(msg)

    #9.2
    def turn_gpo_off(self, num):
        # TODO: declare custom exceptions
        if not 0 < num <= 6:
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_GPO_OFF, num])
        self.send(msg)

    #9.3
    def turn_gpo_on(self, num):
        # TODO: declare custom exceptions
        if not 0 < num <= 6:
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_GPO_ON, num])
        self.send(msg)

    #9.4
    def set_startup_gpo_state(self, num, state):
        # TODO: declare custom exceptions
        if num == 0 or num > 6:
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_STARTUP_GPO_STATE, num, state])
        self.send(msg)

    def set_gpo(self, num, state, store=False):
        # TODO: declare custom exceptions
        if not 0 < num <= 6:
            raise Exception
        if state:
            self.turn_gpo_on(num)
        else:
            self.turn_gpo_off(num)
        if store:
            self.set_startup_gpo_state(num, state)

    def set_led(self, num, color, store=False):
        if not 0 < num <= 3:
            raise Exception
        if store:
            # TODO: use set_startup_gpo_state
            raise NotImplementedError
        if color == 'off':
            self.turn_gpo_on(num * 2 - 1)
            self.turn_gpo_on(num * 2)
        if color == 'red':
            self.turn_gpo_off(num * 2 - 1)
            self.turn_gpo_on(num * 2)
        if color == 'orange':
            self.turn_gpo_off(num * 2 - 1)
            self.turn_gpo_off(num * 2)
        if color == 'green':
            self.turn_gpo_on(num * 2 - 1)
            self.turn_gpo_off(num * 2)

    #10.2
    def enable_key_autotransmit(self):
        msg = bytearray([self._CMD_INIT, self._CMD_AUTO_TRANSMIT_KEY_ON])
        self.send(msg)

    #10.3
    def disable_key_autotransmit(self):
        msg = bytearray([self._CMD_INIT, self._CMD_AUTO_TRANSMIT_KEY_OFF])
        self.send(msg)

    #10.4
    def poll_keypress(self):
        msg = bytearray([self._CMD_INIT, self._CMD_POLL_KEY])
        self.send(msg)
        result = []
        # FIXME: this doesn't work
        while True:
            key = self.read()
            if key != '\x00':
                result.append(key)
            if (struct.unpack('b', key)[0] & (1 << 7)) == 0:
                break
            else:
                print("DEBUG: keypress in buffer, reading again")
        return result

    #10.5
    def clear_keybuffer(self):
        msg = bytearray([self._CMD_INIT, self._CMD_CLEAR_KEY_BUFFER])
        self.send(msg)

    #10.6
    def set_debounce(self, time=8):
        msg = bytearray([self._CMD_INIT, self._CMD_DEBOUNCE_TIME, time])
        self.send(msg)

    #10.7
    def set_autorepeat_mode(self, mode):
        msg = bytearray([self._CMD_INIT, self._CMD_AUTO_REPEAT_MODE, mode])
        self.send(msg)

    #10.8
    def disable_autorepeat(self):
        msg = bytearray([self._CMD_INIT, self._CMD_AUTO_REPEAT_OFF])
        self.send(msg)

    #10.9
    def assign_keycodes(self, kdown, kup):
        return NotImplemented
        msg = bytearray([self._CMD_INIT, self._CMD_CUSTOM_KEYPAD_CODES, kdown, kup])
        self.send(msg)

    #11.2
    def clearscreen(self):
        msg = bytearray([self._CMD_INIT, self._CMD_CLEAR_SCREEN])
        self.send(msg)

    #11.3
    def display_on(self, time=0):
        msg = bytearray([self._CMD_INIT, self._CMD_DISPLAY_ON, time])
        self.send(msg)

    #11.4
    def display_off(self):
        msg = bytearray([self._CMD_INIT, self._CMD_DISPLAY_OFF])
        self.send(msg)

    def set_backlight(self, state):
        if state:
            self.display_on()
        else:
            self.display_off()

    #11.5
    def set_brightness(self, brightness=255):
        msg = bytearray([self._CMD_INIT, self._CMD_BRIGHTNESS, brightness])
        self.send(msg)

    #11.6
    def set_save_brightness(self, brightness=255):
        msg = bytearray([self._CMD_INIT, self._CMD_DEFAULT_BRIGHTNESS, brightness])
        self.send(msg)

    #11.7
    def set_contrast(self, contrast=128):
        msg = bytearray([self._CMD_INIT, self._CMD_CONTRAST, contrast])
        self.send(msg)

    #11.8
    def set_save_contrast(self, contrast=128):
        msg = bytearray([self._CMD_INIT, self._CMD_DEFAULT_CONTRAST, contrast])
        self.send(msg)

    #12.2
    def wipe_fs(self):
        msg = bytearray([self._CMD_INIT, self._CMD_WIPE_FILESYSTEM])
        self.send(msg)
        return 'Restart display to ensure FS integrity'

    #12.3
    def delete_file(self, type, ref):
        # TODO: declare custom exceptions
        if not 0 <= type <= 1:
           raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_DELETE_FILE, type, ref])
        self.send(msg)
        return 'Restart display to ensure FS integrity'

    #12.4
    def get_fs_space(self):
        msg = bytearray([self._CMD_INIT, self._CMD_FREE_SPACE])
        self.send(msg)
        return self.read()

    #12.5
    def get_fs_dir(self):
        msg = bytearray([self._CMD_INIT, self._CMD_DIRECTORY])
        self.send(msg)
        return self.read()

    #12.6
    def upload_fs(self, data):
        msg = bytearray([self._CMD_INIT, self._CMD_UPLOAD_FS, data])
        self.send(msg)

    #12.7
    def download_file(self, type, ref):
        # TODO: declare custom exceptions
        if not 0 <= type <= 1:
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_DOWNLOAD_FILE, type, ref])
        self.send(msg)
        return self.read()

    #12.8
    def move_file(self, oldtype, oldref, newtype, newref):
        # TODO: declare custom exceptions
        if not (0 <= oldtype <= 1 or 0 <= newtype <= 1):
            raise Exception
        msg = bytearray([self._CMD_INIT, self._CMD_MOVE_FILE, oldtype, oldref, newtype, newref])
        self.send(msg)

    #13.2
    def set_remember(self, switch=0):
        msg = bytearray([self._CMD_INIT, self._CMD_REMEMBER, switch])
        self.send(msg)

    #13.3
    def set_locklevel(self, level):
        msg = bytearray([self._CMD_INIT, self._CMD_LOCK_LEVEL, level])
        self.send(msg)

    #13.4
    def set_save_locklevel(self, level):
        msg = bytearray([self._CMD_INIT, self._CMD_DEFAULT_LOCK_LEVEL, level])
        self.send(msg)

    #13.5
    def dump_fs(self):
        msg = bytearray([self._CMD_INIT, self._CMD_DUMP_FS])
        self.send(msg)
        return self.read()

    #13.6
    def write_customerdata(self, data):
        msg = bytearray([self._CMD_INIT, self._CMD_WRITE_CUSTOMER_DATA])
        self.send(msg)

    #13.7
    def read_customerdata(self):
        msg = bytearray([self._CMD_INIT, self._CMD_READ_CUSTOMER_DATA])
        self.send(msg)
        return self.read()

    #14.2
    def read_version(self):
        msg = bytearray([self._CMD_INIT, self._CMD_VERSION_NUMBER])
        self.send(msg)
        return self.read()

    #14.3
    def read_type(self):
        msg = bytearray([self._CMD_INIT, self._CMD_MODULE_TYPE])
        self.send(msg)
        version = self.read()
        version = version.encode('hex')
        return version

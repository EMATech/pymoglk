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
# Address : 0x50 (write) or 0x51 (read)
# Information : 0x48 0x45 0x4C 0x4C 0x4F
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

##COMMUNICATION
_CMD_INIT = 0xFE
# (Must be issued before any command)
_CMD_FLOW_CONTROL_ON = 0x3A
#                    full[0-128]
#                    (Number of bytes before almost full
#                     0: full)
#                    empty[0-128]
#                    (Number of bytes before almost empty
#                     128: empty)

_RET_ALMOST_FULL = 0xFE
_RET_ALMOST_EMPTY = 0xFF

_CMD_FLOW_CONTROL_OFF = 0x3B

_CMD_BAUD_RATE = 0x39
#                    speed[See table below]

_BAUD_RATE_9600 = 0xCF
_BAUD_RATE_14400 = 0x8A
_BAUD_RATE_19200 = 0x67
_BAUD_RATE_28800 = 0x44
_BAUD_RATE_38400 = 0x33
_BAUD_RATE_57600 = 0x22
_BAUD_RATE_76800 = 0x19
_BAUD_RATE_115200 = 0x10

_CMD_NON_STANDARD_BAUD_RATE = 0xA4
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

_CMD_UPLOAD_FONT = 0x24
#                    fontid
#                    lsbsize
#                    msbsize
#                    fontfile
# (Don't forget to set the new font metrics,
#  see FILESYSTEM file transfer protocol)
_CMD_USE_FONT = 0x31
#                    fontid
_CMD_FONT_METRICS = 0x32
#                    lm
#                    (Left Margin: Location in pixels)
#                    tm
#                    (Top Margin: Location in pixels)
#                    csp
#                    (Character Spacing in pixels)
#                    lsp
#                    (Line Spacing in pixels)
#                    srow
#                    (Scroll Row:
#                    Y location of last row in pixels)
_CMD_BOX_SPACE_MODE = 0xAC
#                    value[0-1]
#                    (0: Off,
#                     1: On)

## TEXT
_CMD_HOME = 0x48
_CMD_CURSOR_POSITION = 0x47
#                    col
#                    row
#                    (Derived from current font base size)
_CMD_CURSOR_COORDINATE = 0x79
#                    x
#                    y
_CMD_AUTO_SCROLL_ON = 0x51
_CMD_AUTO_SCROLL_OFF = 0x52

## BITMAPS
# BITMAP FILE FORMAT
#  The bitmap is encoded into bytes horizontally

_CMD_UPLOAD_BMP = 0x5E
#                    bitmapid
#                    lsbsize
#                    msbsize
#                    bitmapfile
# (see FILESYSTEM file transfer protocol)
_CMD_DRAW_MEMORY_BMP = 0x62
#                    bitmapid
#                    x
#                    y
_CMD_DRAW_BMP = 0x64
#                    x
#                    y
#                    width
#                    height
#                    data

## BAR GRAPHS & DRAWING
_CMD_DRAWING_COLOR = 0x63
#                    color[0-255]
#                    (0:     White,
#                     1-255: Black)
_CMD_DRAW_PIXEL = 0x70
#                    x
#                    y
_CMD_DRAW_LINE = 0x6C
#                    x1
#                    y1
#                    x2
#                    y2
# (Lines may interpolate differently Left to Right and Right to Left)
_CMD_CONTINUE_LINE = 0x65
#                    x
#                    y
_CMD_DRAW_RECTANGLE = 0x72
#                    color[0-255]
#                    (0:     White,
#                     1-255: Black)
#                    x1
#                    y1
#                    x2
#                    y2
_CMD_DRAW_SOLID_RECTANGLE = 0x78
#                    color[0-255]
#                    (0:     White,
#                     1-255: Black)
#                    x1
#                    y1
#                    x2
#                    y2
_CMD_INITIALIZE_BAR_GRAPH = 0x67
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
_CMD_DRAW_BAR_GRAPH = 0x69
#                    bgid[0-15]
#                    value
#                    (In pixels)
_CMD_INITIALIZE_STRIP_CHART = 0x6A
#                    scid[0-6]
#                    x1
#                    y1
#                    x2
#                    (x1<x2)
#                    y2
#                    (y1<y2)
_CMD_SHIFT_STRIP_CHART = 0x6B
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

_CMD_GPO_OFF = 0x56
#                    num[1-6]
_CMD_GPO_ON = 0x57
#                    num[1-6]
_CMD_STARTUP_GPO_STATE = 0xC3
#                    num[1-6]
#                    state[0-1]
#                    (0: Off,
#                     1: On)
# (Doesn't affect current state)

## KEYPAD
# Default layout:
_RET_UP = 0x42
_RET_DOWN = 0x48
_RET_LEFT = 0x44
_RET_RIGHT = 0x43
_RET_CENTER = 0x45
_RET_TOP = 0x41
_RET_BOTTOM = 0x47
_RET_RELEASE_UP = 0x62
_RET_RELEASE_DOWN = 0x68
_RET_RELEASE_LEFT = 0x64
_RET_RELEASE_RIGHT = 0x63
_RET_RELEASE_CENTER = 0x65
_RET_RELEASE_TOP = 0x61
_RET_RELEASE_BOTTOM = 0x67

_CMD_AUTO_TRANSMIT_KEY_ON = 0x41
_CMD_AUTO_TRANSMIT_KEY_OFF = 0x4F
# (The keypad buffer is reset after 10 key presses)
_CMD_POLL_KEY = 0x26
# (Returned code MSB flags 'more than one key press in buffer')

_RET_NO_KEY = 0x00

_CMD_CLEAR_KEY_BUFFER = 0x45
_CMD_DEBOUNCE_TIME = 0x55
#                    time[0-255]
#                    (6.554ms increments,
#                     Default: 8)
_CMD_AUTO_REPEAT_MODE = 0x7E
#                    mode[0-1]
#                    (0: Resend Key,
#                     1: Key Up/Down)
_CMD_AUTO_REPEAT_OFF = 0x60
_CMD_CUSTOM_KEYPAD_CODES = 0xD5
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

# FIXME: Report it missing from codes list

## DISPLAY
_CMD_CLEAR_SCREEN = 0x58
_CMD_DISPLAY_ON = 0x42
#                    min[0-90]
_CMD_DISPLAY_OFF = 0x46
_CMD_BRIGHTNESS = 0x99
#                    brightness[0-255]
#                    (Default: 255)
_CMD_DEFAULT_BRIGHTNESS = 0x98
#                    brightness[0-255]
#                    (Default: 255)
_CMD_CONTRAST = 0x50
#                    contrast[0-255]
#                    (Default: 128)
_CMD_DEFAULT_CONTRAST = 0x91
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
#  NEXT_BYTE
#  NEXT_BYTE
#  (CMD_CONFIRM | CMD_DECLINE)
#  -------------------End Loop-----------------------------

# TODO: Implement file transfer protocol

_RET_CONFIRM = 0x01
_RET_DECLINE = 0x08

_CMD_CONFIRM = 0x01
_CMD_DECLINE = 0x08

_CMD_WIPE_FILESYSTEM = 0x21, 0x59, 0x21
# (Be carefull with this one!)
_CMD_DELETE_FILE = 0xAD
#                    type[0-1]
#                    (0: Font,
#                     1: Bitmap)
#                     fontid or bitmapid
_CMD_FREE_SPACE = 0xAF

# FREE SPACE RETURN FORMAT
# Free space size (4 bytes LSB to MSB)

_CMD_DIRECTORY = 0xB3

# DIRECTORY RETURN FORMAT
#  Header (1 byte)
#    Number of entries (1 byte)1 byte)
#    Number of entries (1 byte)
#  File Entry (4 bytes)
#    Flag (1 byte)
#    (0x00: Not used)
#    FileID/Type (1 byte)
#    (1st bit: File Type
#    Next seven bits: FileID)
#    File size LSB (1 byte)
#    File size MSB (1 byte)

_CMD_UPLOAD_FS = 0xB0
#                    fsimagefile
#                    (Must be 16KB)
_CMD_DOWNLOAD_FILE = 0xB2
#                    type[0-1]
#                    (0: Font,
#                     1: Bitmap)
#                    fontid or bitmapid

_CMD_MOVE_FILE = 0xB4
#                    oldtype[0-1]
#                    (0: Font,
#                     1: Bitmap)
#                    oldid
#                    newtype[0-1]
#                    (0: Font,
#                     1: Bitmap)
#                    newid
_CMD_DUMP_FS = 0x30

#  DOWNLOAD_FILE AND DUMP_FS RETURN FORMAT
#  File size (4 bytes)
#  (LSB to MSB)
#  File Data

# Undocumented command! Seems to dump the settings.
_CMD_DUMP_SETTINGS = 0xD0

## SECURITY
_CMD_REMEMBER = 0x93
#                    value[0-1]
#                    (0: Do not remember,
#                     1: Remember)
_CMD_LOCK_LEVEL = 0xCA, 0xF5, 0xA0
#                    level
#                    (Lock bits:
#                     0-2:  Reserved leave 0,
#                     3:    Communication speed,
#                     4:    Settings,
#                     5:    Filesystem,
#                     6:    Command,
#                     7:    Display)
_CMD_DEFAULT_LOCK_LEVEL = 0xCB, 0xF5, 0xA0
#                    level
#                    (Lock bits:
#                     0-2:  Reserved leave 0,
#                     3:    Communication speed,
#                     4:    Settings,
#                     5:    Filesystem,
#                     6:    Command,
#                     7:    Display)

# FIXME: Report it missing from codes list
_CMD_WRITE_CUSTOMER_DATA = 0x34
#                    data
#                    (16B are accessible)
_CMD_READ_CUSTOMER_DATA = 0x35

#  READ_CUSTOMER_DATA RETURN FORMAT
#  Data (16 bytes)

## MISC
_CMD_VERSION_NUMBER = 0x36

#  VERSION_NUMBER RETURN FORMAT
#  Version (1 byte)
#  (Represents the version number
#   Hex  Version
#   0x19  1.9
#   0x57  5.7)

_CMD_MODULE_TYPE = 0x37

#  MODULE_TYPE RETURN FORMAT
#  Type (1 byte)
#  (One of the following return codes)
_RET_LCD0821 = 0x01
_RET_LCD2021 = 0x02
_RET_LCD2041 = 0x05
_RET_LCD4021 = 0x06
_RET_LCD4041 = 0x07
_RET_LK202_25 = 0x08
_RET_LK204_25 = 0x09
_RET_LK404_55 = 0x0A
_RET_VFD2021 = 0x0B
_RET_VFD2041 = 0x0C
_RET_VFD4021 = 0x0D
_RET_VK202_25 = 0x0E
_RET_VK204_25 = 0x0F
_RET_GLC12232 = 0x10
_RET_GLC24064 = 0x13
_RET_GLK24064_25 = 0x15
_RET_GLK12232_25 = 0x22
_RET_GLK12232_25_SM = 0x24
_RET_GLK24064_16_1U_USB = 0x25
_RET_GLK24064_16_1U = 0x26
_RET_GLK19264_7T_1U_USB = 0x27
_RET_GLK12236_16 = 0x28
_RET_GLK12232_16_SM = 0x29
_RET_GLK19264_7T_1U = 0x2A
_RET_LK204_7T_1U = 0x2B
_RET_LK204_7T_1U_USB = 0x2C
_RET_LK404_AT = 0x31
_RET_MOS_AV_162A = 0x32
_RET_LK402_12 = 0x33
_RET_LK162_12 = 0x34
_RET_LK204_25PC = 0x35
_RET_LK202_24_USB = 0x36
_RET_VK202_24_USB = 0x37
_RET_LK204_24_USB = 0x38
_RET_VK204_24_USB = 0x39
_RET_PK162_12 = 0x3A
_RET_VK162_12 = 0x3B
_RET_MOS_AP_162A = 0x3C
_RET_PK202_25 = 0x3D
_RET_MOS_AL_162A = 0x3E
_RET_MOS_AL_202A = 0x3F
_RET_MOS_AV_202A = 0x40
_RET_MOS_AP_202A = 0x41
_RET_PK202_24_USB = 0x42
_RET_MOS_AL_082 = 0x43
_RET_MOS_AL_204 = 0x44
_RET_MOS_AV_204 = 0x45
_RET_MOS_AL_402 = 0x46
_RET_MOS_AV_402 = 0x47
_RET_LK082_12 = 0x48
_RET_VK402_12 = 0x49
_RET_VK404_55 = 0x4A
_RET_LK402_25 = 0x4B
_RET_VK402_25 = 0x4C
_RET_PK204_25 = 0x4D
_RET_MOS = 0x4F
_RET_MOI = 0x50
_RET_XBOARD_S = 0x51
_RET_XBOARD_I = 0x52
_RET_MOU = 0x53
_RET_XBOARD_U = 0x54
_RET_LK202_25_USB = 0x55
_RET_VK202_25_USB = 0x56
_RET_LK204_25_USB = 0x57
_RET_VK204_25_USB = 0x58
_RET_LK162_12_TC = 0x5B
_RET_GLK240128_25 = 0x72
_RET_LK404_25 = 0x73
_RET_VK404_25 = 0x74

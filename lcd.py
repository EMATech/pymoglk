#!/usr/bin/env python
# -*- coding: utf-8 *-*
import glk
import time
import math
from itertools import cycle

def tricolor_light():
    lcd.set_led(1, 'red')
    lcd.set_led(2, 'off')
    lcd.set_led(3, 'off')
    time.sleep(1)
    lcd.set_led(1, 'off')
    lcd.set_led(2, 'orange')
    lcd.set_led(3, 'off')
    time.sleep(1)
    lcd.set_led(1, 'off')
    lcd.set_led(2, 'off')
    lcd.set_led(3, 'green')
    time.sleep(1)


def blink_green():
    while True:
        lcd.set_led(1, 'green')
        lcd.set_led(2, 'green')
        lcd.set_led(3, 'green')
        time.sleep(0.5)
        lcd.set_led(1, 'off')
        lcd.set_led(2, 'off')
        lcd.set_led(3, 'off')
        time.sleep(0.5)


def sixteen_bargraph():
    lcd.set_font(1)
    lcd.set_font_metrics(0, 0, 0, 0, 0)
    for num in range(1, 17):
        lcd.set_cursor_position(num * 2 - 1, 9)
        lcd.write(str(num))
        lcd.init_bargraph(num - 1, 0, ((num - 1) * 8) + (4 * (num - 1)), 0, (num * 8 - 1) + (4 * num), 54)


def sinwave():
    num = 1
    for angle in cycle(range(0, 360, 1)):
        y = math.sin(math.radians(angle))
        y += 1
        y /= 2
        value = int(y * 55.0)
        lcd.draw_bargraph(num, value)
        if num < 16:
            num += 1
        else:
            num = 1


lcd = glk.PyMoGlk(_debug=True)

lcd.clearscreen()
lcd.set_backlight(True)

print(lcd.read_type())
print(lcd.read_version())

#tricolor_light()
#blink_green()

#sixteen_bargraph()
#sinwave()

#for i in range(1, 6):
#    lcd.set_gpo(i, True)
#    lcd.set_gpo(i+1, False)
#    time.sleep(1)
#    lcd.set_gpo(i, False)


#lcd.disable_key_autotransmit()
#print(lcd.poll_keypress())

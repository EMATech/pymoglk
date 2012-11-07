#!/usr/bin/env python2
# -*- coding: utf-8 *-*
import pymoglk

lcd = pymoglk.PyMoGlk()
lcd.write('test')
print lcd.read()

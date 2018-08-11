#!/usr/bin/python

import os
import sys

folder = os.path.dirname(os.path.realpath(__file__))
folder += "/flux_led" 
sys.path.append(folder)
from flux_led import WifiLedBulb, BulbScanner, LedTimer

print sys.argv

try:
  address = sys.argv[1]
  id      = sys.argv[2]
  action  = sys.argv[3].lower()
  values  = sys.argv[4:]
except:
  sys.exit(1)

#scanner = BulbScanner()
#scanner.scan(timeout=4)
#bulb_info = scanner.getBulbInfoByID(address)
#address = bulb_info['ipaddr']

bulb = WifiLedBulb(address)
msg = 'MagicLED bulb at %s ' % address

if action == 'on':
  val = int(values[0])
  if val > 0:
    msg += 'turned on'
    bulb.turnOn()
  else:
    msg += 'turned off'
    bulb.turnOff()

if action == 'color':
  r = int(values[0])
  g = int(values[1])
  b = int(values[2])
  msg += 'set to color (%s, %s, %s)' % (r, g, b)
  bulb.setRgb(r, g, b, persist=False)

print msg

sys.exit(0)

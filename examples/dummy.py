#!/usr/bin/python

import sys

print sys.argv

try:
  id      = sys.argv[1]
  action  = sys.argv[2].lower()
  values  = sys.argv[3:]
except:
  sys.exit(1)

msg = 'Bulb (%s) ' % id
if action == 'on':
  val = int(values[0])
  if val > 0:
    msg += 'turned on'
  else:
    msg += 'turned off'

if action == 'bri':
  msg += 'set brightness to %s' % int(values[0])

if action == 'color':
  r = int(values[0])
  g = int(values[1])
  b = int(values[2])
  msg += 'set to color (%s, %s, %s)' % (r, g, b)

print msg

sys.exit(0)

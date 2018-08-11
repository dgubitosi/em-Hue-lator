#!/usr/bin/python

import paho.mqtt.publish as publish

import os
import sys

print sys.argv

try:
  id      = sys.argv[1]
  action  = sys.argv[2].lower()
  values  = sys.argv[3:]
except:
  sys.exit(1)

BROKER = "iot.eclipse.org"
TOPIC = "test/lumen/%s" % id

msg = 'Tabu Lumen bulb at id %s ' % id

if action == 'on':
  val = int(values[0])
  if val > 0:
    # this can be removed as there is no actual "on" command
    msg += 'turned on'
    publish.single(TOPIC + "/white", "99", hostname=BROKER)
  else:
    msg += 'turned off'
    publish.single(TOPIC + "/mode", "off", hostname=BROKER)

if action == 'color':
  r = int(values[0])
  g = int(values[1])
  b = int(values[2])
  RGB = "RGB(%s,%s,%s)" % (r, g, b)
  msg += 'set to color %s' % RGB
  publish.single(TOPIC + "/color", RGB, hostname=BROKER)

print msg

sys.exit(0)

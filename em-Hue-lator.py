#!/usr/bin/python

from Hue.HueServer import HueServer
import time
import sys

print "Starting em-Hue-lator..."
myHue = HueServer()

# manually define bridge properties
# change config
#myHue.setBridgeConfig(name='MyBridge', mac='00:17:88:14:AA:BB')

# add test users
USERS = [
  {"username": "My3bIyaaAWREppKCgLYnyyoG8VdWNEbn67U42RWx",
      "device": "Hue 2#Genymotion Google N"},
  {"username": "Q4m7fmUW3vYaibIEErw0uiKsuNjKdGZrPa65dLGw",
      "device": "hue_ios_app#iPhone"}
]
for id in USERS:
    myHue.addUser(id["device"], id["username"])

# add some lights, they get id's in order
myHue.addLight(name="Bedroom Lighstrip", modelid='LST001',
    _external=['examples/lumen-mqtt-publish.py'])
myHue.addLight(name="Bedroom Left", modelid='LCT001',
    _proxy=['192.168.1.191','2303feac3643fd6f34ecce8422175907', 7])
myHue.addLight(name="Bedroom Right", modelid='LCT001',
    _proxy=['192.168.1.191','2303feac3643fd6f34ecce8422175907', 6])
myHue.addLight(name="Den1", modelid='LCT002')
myHue.addLight(name="Den2", modelid='LCT002')
myHue.addLight(name="Alcove Lightstrip", modelid='LST001',
    _external=['examples/magic.py', '192.168.1.217'])
myHue.addLight(name="Dining Room Lightstrip", modelid='LST001',
    _external=['examples/magic.py', '192.168.1.190'])
myHue.addLight(name="Downstairs1", modelid='LCT002')
myHue.addLight(name="Downstairs2", modelid='LCT002')

# lights added without any properties will get a random name and default dimmable type
myHue.addLight()
myHue.addLight()

# add some groups, can only add lights by id
myHue.addGroup("Bedroom", lights=[1, 2, 3])
myHue.addGroup("Den", lights=[4, 5])
myHue.addGroup("Downstairs", lights=[8, 9])

# NOTE: official Hue app does not recognize LightGroups
myHue.addGroup("Magic Home Lightstrips", lights=[6, 7], type="LightGroup")

# once the server is running, all changes must be made via api
myHue.runServer()

# wait for control-c to exit
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print "Exiting ... Ctrl-c pressed ..."
        sys.exit(1)


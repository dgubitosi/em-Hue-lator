"""
    Hue Group
"""

from HueLight import HueLight
from HueState import HueState, HueGroupActionDimmable, HueGroupActionColor, HueGroupActionExtendedColor
import json
import utility

ROOMS = [
  'Living room', 'Kitchen', 'Dining', 'Bedroom', 'Kids bedroom', 'Bathroom',
  'Nursery', 'Recreation', 'Office', 'Gym', 'Hallway', 'Toilet', 'Front door',
  'Garage', 'Terrace', 'Garden', 'Driveway', 'Carport', 'Other'
]


class HueGroup(object):

    def __init__(self, name, _lights={}, **kwargs):

        if not name:
            name = utility.getRandomString(20)

        self.name = name
        self.state = {
          "all_on": False,
          "any_on": False
        }

        # internal properties
        # api id
        self._id = ''

        # description
        self._desc = kwargs.get('_desc', '')

        # default to dimmable
        self._group = 'dimmable'

        # reference to all lights in the bridge
        self._lights = _lights

        # unpack kwargs ( type, class, _desc )
        type = kwargs.get('type', 'Room')
        if type not in ['Room', 'LightGroup']:
            type = 'Room'
        self.type = type
        if type == 'Room':
            # default class is Other
            klass = kwargs.get('klass', ROOMS[-1])
            if klass not in ROOMS:
                klass = 'Other'
            self.klass = klass
        else:
            self.recycle = False

        # group action is dependent on the lights
        self._action = {
          'dimmable': HueGroupActionDimmable(),
          'color': HueGroupActionColor(),
          'extended': HueGroupActionExtendedColor()
        }
        self.action = self._action[self._group]

        # lights in the group
        # dict to ensure key uniqueness
        self.lights = {}

        # set dispatcher
        self._setAttr = {
          'name': self.setName,
          'lights': self.addLights,
          'class': self.setClass
        }

    def setIndex(self, id):

        self._id = id

    def getIndex(self):

        return self._id

    def setName(self, name):

        self.name = name

    def addLight(self, index):

        if index in self._lights.keys():
            self.lights.update({index: True})
            self._lights[index].addGroup(self.getIndex())
            type = self._lights[index].getType().lower()
            if self._group == 'dimmable':
                self._group = type
            elif self._group == 'color':
                if type == 'extended':
                    self._group = type
            self.action = self._action[self._group]

    def addLights(self, lights):

        for index in lights:
            print "... adding Light %d to Group % (%)" % (index, self._id, self.name)
            self.addLight(index)

    def setLights(self, lights):

        # setLights removes all lights
        for li in self.lights:
            self._lights[li].removeGroup(self.getIndex())
        self.lights.clear()
        self.action = self._action['dimmable']

        # then adds the new set of lights
        self.addLights(lights)

    def setClass(self, klass):

        if self.type == 'Room':
            if klass not in ROOMS:
                klass = 'Other'
            self.klass = klass

    def setAction(self, params):

        # group action is triggering light state change
        for li in self.lights:
            self._lights[li].setState(params)
        self.updateState()

        response = []
        for k, v in params.items():
            addr = "/groups/%s/action/%s" % (self.getIndex(), k)
            if self.action.setState(k, v):
                # update state
                success = {"success": {addr: v}}
                response.append(success)
            else:
                desc = "parameter, %s, not available" % k
                error = {"error": {"type": 6, "address": addr, "description": desc}}
                response.append(error)
        return response

    def getAction(self, var):

        if var in self.action._get.keys():
            return self.action._get[var]()

    def updateState(self):

        lightCount = len(self.lights.keys())
        lightsOn = 0
        for li in self.lights:
            if self._lights[li].getState('on'):
                lightsOn += 1

        if lightsOn > 0:
            self.action.setState('on', True)
            self.state['any_on'] = True
            if lightsOn == lightCount:
                self.state['all_on'] = True
        else:
            self.action.setState('on', False)
            self.state['any_on'] = False
            self.state['all_on'] = False

    def setAttribute(self, attr, val):

        if attr in self._setAttr.keys():
            self._setAttr[attr](val)
            return True
        return False

    def setAttributes(self, params):

        response = []
        for k, v in params.items():
            if self.setAttribute(k, v):
                addr = "/groups/%s/%s" % (self.getIndex(), k)
                success = {"success": {addr: v}}
                response.append(success)
            else:
                addr = "/groups/%s/%s" % (self.getIndex(), k)
                desc = "parameter, %s, not available" % k
                error = {"error": {"type": 6, "address": addr, "description": desc}}
                response.append(error)
        return response

    def getObj(self):

        obj = {}
        for k, v in self.__dict__.items():
            # skip internal properties
            if k[0] == '_':
                continue
            # serialize the action object
            elif isinstance(v, HueState):
                obj[k] = v.getObj()
            # order the lights
            elif k == 'lights':
                obj[k] = sorted(self.lights.keys())
            # rename klass -> class
            elif k == 'klass':
                obj['class'] = v
            else:
                obj[k] = v
        return obj

    def __str__(self):

        return json.dumps(self.getObj())

    def _getObjInternal(self):

        ALLOWED = ['_id', '_desc', '_group']
        obj = {}
        for k, v in self.__dict__.items():
            # return these specific internal properties
            if k in ALLOWED:
                obj[k] = v
            # skip other internal properties
            if k[0] == '_':
                continue
            # serialize the action object
            elif isinstance(v, HueState):
                obj[k] = v.getObj()
            # serialize lights
            elif k == 'lights':
                obj[k] = {}
                for li in sorted(self.lights.keys()):
                    # show the properties of the light
                    try:
                        obj[k].update({li: self._lights[li]._getObjInternal()})
                    except:
                        obj[k].update({li: self.lights[li]})
            # rename klass -> class
            elif k == 'klass':
                obj['class'] = v
            else:
                obj[k] = v
        return obj

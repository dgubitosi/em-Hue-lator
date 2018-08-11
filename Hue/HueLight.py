"""
    Hue Light
"""

from HueState import HueState, HueLightStateDimmable, HueLightStateColor, HueLightStateExtendedColor
import HueColor
import utility
import json
import requests
import subprocess


class HueLight(object):

    def __init__(self, name, **kwargs):

        if not name:
            name = utility.getRandomString(20)
        self.name = name
        self.manufacturername = "Philips"
        self.modelid = "LWB004"
        self.uniqueid = "00:17:88:01:00:ab:cd:ef-0b"

        # internal properties
        # api id
        self._id = ''

        # description
        self._desc = kwargs.get('_desc', '')

        # list of groups containing this light
        # dict to ensure key uniqueness
        self._groups = {}

        # external command to execute
        self._external = []
        # proxy command to a light on a real hue bridge
        self._proxy = []

        # check kwargs [ modelid, uniqueid, _external, _proxy ]
        # modelid
        modelid = kwargs.get('modelid', 'LWB004')
        if modelid not in ['LWB004', 'LCT001', 'LCT002', 'LST001']:
            modelid = 'LWB004'
        self.modelid = modelid

        # uniqueid
        uniqueid = kwargs.get('uniqueid', '')
        if not utility.validateUniqueId(uniqueid):
            uniqueid = ''
        if not uniqueid:
            mac = '0017880100' + utility.getRandomHexString(6)
            uniqueid = ':'.join(utility.splitString(mac, 2))
            uniqueid += '-0b'
        self.uniqueid = uniqueid

        # external command
        external = kwargs.get('_external', [])
        if external:
            self.setExternalCommand(external)

        # proxy command
        proxy = kwargs.get('_proxy', [])
        if proxy:
            self.setProxyCommand(proxy)

        # white dimmable lights
        if modelid in ['LWB004']:
            self.type = "Dimmable light"
            self.swversion = "5.38.2.19136"
            self.state = HueLightStateDimmable()
        # color lights
        if modelid in ['LST001']:
            self.type = "Color light"
            self.swversion = "5.23.1.13542"
            self.state = HueLightStateColor()
        # extended color lights
        if modelid in ['LCT001', 'LCT002']:
            self.type = "Extended color light"
            self.swversion = "5.23.1.13542"
            self.state = HueLightStateExtendedColor()

        # internal property
        self._type = self.type.lower().split(" ")[0]

        # set dispatcher
        self._setAttr = {
          'name': self.setName
        }

    def setIndex(self, id):

        self._id = id

    def getIndex(self):

        return self._id

    def setAttribute(self, attr, val):

        if attr in self._setAttr.keys():
            self._setAttr[attr](val)
            return True
        return False

    def setAttributes(self, params):

        response = []
        for k, v in params.items():
            addr = "/lights/%s/%s" % (self.getIndex(), k)
            if self.setAttribute(k, v):
                success = {"success": {addr: v}}
                response.append(success)
            else:
                desc = "parameter, %s, not available" % k
                error = {"error": {"type": 6, "address": addr, "description": desc}}
                response.append(error)
        return response

    def setState(self, params):

        # proxy commands are sent directly to linked light
        proxy = self.getProxyCommand()
        if proxy:
            url = 'http://' + proxy[0] + '/api/' + proxy[1] + '/lights/' + str(proxy[2]) + '/state'
            headers = {"Content-Type": "application/json"}
            data = json.dumps(params)
            req = requests.put(url, headers=headers, data=data)
            print '** Sending proxy command: PUT ' + data + ' -> ' + url

        previous = self.state.getOn()
        response = []
        for k, v in params.items():
            addr = "/lights/%s/state/%s" % (self.getIndex(), k)
            if self.state.setState(k, v):
                success = {"success": {addr: v}}
                response.append(success)
            else:
                desc = "paramater, %s, not available" % k
                error = {"error": {"type": 6, "address": addr, "description": desc}}
                response.append(error)

        if self.getExternalCommand():
            self.executeCommand(previous)
        return response

    def getState(self, var):

        if var in self.state._get.keys():
            return self.state._get[var]()

    def executeCommand(self, previous):

        on = self.state.getOn()

        # has the bulb state changed?
        if on ^ previous:
          self.executeCommandInternal('on', on)

        if on:
            # change state if the bulb state is on
            colormode = self.state.getColormode()
            b = self.state.getBri()

            # dimmable bulb, send brightness
            if colormode is None:
                self.executeCommandInternal('bri', b)
                return

            # color light, convert to RGB
            RGB = []
            if colormode == 'hs':
                h = self.state.getHue()
                s = self.state.getSat()
                RGB = HueColor.hsb_to_rgb(h, s, b)

            if colormode == 'ct':
                ct = self.state.getCT()
                RGB = HueColor.ct_to_rgb(ct, b)

            if colormode == 'xy':
                xy = self.state.getXY()
                RGB = HueColor.xy_to_rgb(xy, b)

            if RGB:
                self.executeCommandInternal('color', RGB)

    def executeCommandInternal(self, st, val):

        # list of the command and arguments
        # followed by the id, action, and value(s)
        # examples:
        #   magic.py 192.168.1.121 1 on 1
        #   magic.py 192.168.1.121 1 color 128 255 128

        execute = []
        execute.extend(self.getExternalCommand())
        execute.extend([self.getIndex(), st])

        # convert values to opts list
        opts = []
        if isinstance(val, list):
            opts.extend(val)
        else:
            opts.append(val)

        # convert opts list to strings
        i = 0
        while i < len(opts):
            # convert booleans
            if isinstance(opts[i], bool):
                if opts[i]:
                    opts[i] = 1
                else:
                    opts[i] = 0
            opts[i] = str(opts[i])
            i += 1

        execute.extend(opts)
        print "** Executing:", execute
        try:
            p = subprocess.check_output(execute, stderr=subprocess.STDOUT)
            print p.strip()
        except:
            print "** Error excuting command!"

    def setExternalCommand(self, command):

        self._external[:] = []
        if isinstance(command, list):
            self._external.extend(command)
        else:
            self._external.append(command)

    def getExternalCommand(self):

        return self._external

    def setProxyCommand(self, command):

        # proxy command requires following parameters in order:
        # bridge ip address
        # username on bridge
        # light id on bridge

        if not isinstance(command, list):
            return
        if len(command) < 3:
            return
        if not utility.validateIpAddress(command[0]):
            return
        self._proxy[:] = []
        self._proxy.extend(command[:3])

    def getProxyCommand(self):

        return self._proxy

    def addGroup(self, group):

        if group not in self._groups.keys():
            self._groups.update({group: True})

    def removeGroup(self, group):

        if group in self._groups.keys():
            del self._groups[group]

    def getGroups(self):

        return self._groups.keys()

    def getType(self):

        return self._type

    def setName(self, name):

        self.name = name

    def getObj(self):

        obj = {}
        for k, v in self.__dict__.items():
            # skip internal properties
            if k[0] == '_':
                continue
            # serialize the state object
            elif isinstance(v, HueState):
                obj[k] = v.getObj()
            else:
                obj[k] = v
        return obj

    def __str__(self):

        return json.dumps(self.getObj())

    def _getObjInternal(self):

        ALLOWED = ['_id', '_desc', '_type', '_groups', '_external', '_proxy']
        obj = {}
        for k, v in self.__dict__.items():
            # return these specific internal properties
            if k in ALLOWED:
                obj[k] = v
            # skip other internal properties
            if k[0] == '_':
                continue
            # serialize the state object
            elif isinstance(v, HueState):
                obj[k] = v.getObj()
            else:
                obj[k] = v
        return obj

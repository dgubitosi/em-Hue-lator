"""
    Hue Bridge
"""

from HueUser import HueUser
from HueLight import HueLight
from HueGroup import HueGroup
import utility
import timezones


class HueBridge(object):

    def __init__(self, name='em-Hue-lator', mac='00:17:88:14:90:90',
                 ip='127.0.0.1', netmask='255.0.0.0', gateway='127.0.0.1'):

        self._config = {
          "name": "Hue-Emulator",
          "zigbeechannel": 11,
          "bridgeid": "001788FFFE149090",
          "mac": "00:17:88:14:90:90",
          "dhcp": True,
          "ipaddress": "127.0.0.1",
          "netmask": "255.0.0.0",
          "gateway": "127.0.0.1",
          "proxyaddress": "none",
          "proxyport": 0,
          "UTC": "2016-08-27T19:23:49",
          "localtime": "2016-08-27T15:23:49",
          "timezone": "America/New_York",
          "modelid": "BSB001",
          "swversion": "01038802",
          "apiversion": "1.16.0",
          "datastoreversion": "59",
          "swupdate": {
            "updatestate": 0,
            "checkforupdate": False,
            "devicetypes": {
              "bridge": False,
              "lights": [],
              "sensors": []
            },
            "url": "",
            "text": "",
            "notify": True
          },
          "linkbutton": False,
          "portalservices": False,
          "portalconnection": "connected",
          "portalstate": {
            "signedon": False,
            "incoming": False,
            "outgoing": False,
            "communication": "disconnected"
            },
          "factorynew": False,
          "replacesbridgeid": None,
          "backup": {
            "status": "idle",
            "errorcode": 0
          },
          "whitelist": {}
        }

        self.users = {}
        self.lights = {}
        self.groups = {}

        # group 0 is the internal group for all lights
        group0 = HueGroup(
                    "Group 0",
                    _lights=self.lights,
                    type="LightGroup")
        self.groups.update({"0": group0})
        self.groups["0"].setIndex("0")

        self._config['name'] = name
        self.setNetwork(ip, netmask, gateway)
        self.setMacInternal(mac)
        self.updateUTC()

        # unemulated features
        self._unemulated = {
          "schedules": {},
          "scenes": {},
          "sensors": {},
          "rules": {},
          "resourcelinks": {}
        }

    def setBridgeConfig(self, user, params):

        error = self.checkUser(user, "/config")
        if error:
            return error

        response = []
        ALLOWED = ['name', 'UTC']
        for k, v in params.items():
            if k in ALLOWED:
                self._config[k] = v
                addr = "/config/%s" % k
                response.append(self.genSuccess(addr, v))
            else:
                addr = "/config/%s" % k
                desc = "parameter, %s, not available" % k
                response.append(self.genError(6, addr, desc))
        return response

    def getDescription(self):

        name = self._config["name"]
        ip = self._config["ipaddress"]
        port = self.port
        mac = self.mac

        xml = '<root xmlns="urn:schemas-upnp-org:device-1-0">\n'
        xml += '<specVersion>\n'
        xml += '<major>1</major>\n'
        xml += '<minor>0</minor>\n'
        xml += '</specVersion>\n'
        xml += '<URLBase>http://{}:{}/</URLBase>\n'.format(ip, port)
        xml += '<device>\n'
        xml += '<deviceType>urn:schemas-upnp-org:device:Basic:1</deviceType>\n'
        xml += '<friendlyName>{} ({})</friendlyName>\n'.format(name, ip)
        xml += '<manufacturer>Royal Philips Electronics</manufacturer>\n'
        xml += '<manufacturerURL>http://www.philips.com</manufacturerURL>\n'
        xml += '<modelDescription>Philips hue Personal Wireless Lighting</modelDescription>\n'
        xml += '<modelName>Philips hue bridge 2012</modelName>\n'
        xml += '<modelNumber>929000226503</modelNumber>\n'
        xml += '<modelURL>http://www.meethue.com</modelURL>\n'
        xml += '<serialNumber>{}</serialNumber>\n'.format(mac)
        xml += '<UDN>uuid:2f402f80-da50-11e1-9b23-{}</UDN>\n'.format(mac)
        xml += '<presentationURL>index.html</presentationURL>\n'
        xml += '<iconList>\n'
        xml += '<icon>\n'
        xml += '<mimetype>image/png</mimetype>\n'
        xml += '<height>48</height>\n'
        xml += '<width>48</width>\n'
        xml += '<depth>24</depth>\n'
        xml += '<url>hue_logo_0.png</url>\n'
        xml += '</icon>\n'
        xml += '</iconList>\n'
        xml += '</device>\n'
        xml += '</root>'

        return xml

    def setBridgeConfigInternal(self, params):

        response = []
        ALLOWED = ['name', 'mac', 'ipaddress', 'netmask', 'gateway']
        for k, v in params.items():
            if k in ALLOWED:
                if k == 'mac':
                    self.setMacInternal(v)
                else:
                    self._config[k] = v
                addr = "/config/%s" % k
                response.append(self.genSuccess(addr, v))
            else:
                addr = "/config/%s" % k
                desc = "parameter, %s, not available" % k
                response.append(self.genError(6, addr, desc))
        return response

    def setLinkButton(self, button=False):

        self._config['linkbutton'] = button

    def getLinkButton(self):

        return self._config['linkbutton']

    def setNetwork(self, ip='127.0.0.1', netmask='255.255.255.0', gateway='127.0.0.1'):

        self._config['ipaddress'] = ip
        self._config['netmask'] = netmask
        self._config['gateway'] = gateway

    def setMacInternal(self, mac):

        mac = mac.upper()
        if utility.validateMacAddress(mac):
            self._config['mac'] = mac
            mac = ''.join(self._config['mac'].split(':'))
            self.mac = mac
            self._config['bridgeid'] = mac[:6] + 'FFFE' + mac[6:]

    def updateUTC(self):

        self._config['UTC'] = utility.getUTCNow()

    def addUser(self, params):

        response = []
        ALLOWED = ['devicetype']
        for k, v in params.items():
            if k in ALLOWED:
                response.append(self.addUserInternal(v))
            else:
                addr = "/%s" % k
                desc = "parameter, %s, not available" % k
                response.append(self.genError(6, addr, desc))
        return response

    def addUserInternal(self, name, username=''):

        myUser = HueUser(name, username)
        username = myUser.username
        self.users.update({username: myUser})

        # when an app adds a new user,
        # it expects the link button to be pressed
        # and keeps fetching the config to check
        self.setLinkButton(True)

        return self.genSuccess("username", username)

    def getMacAddress(self):

        return self.mac

    def setPort(self, port):

        self.port = port

    def getPort(self):

        return self.port

    def getBridgeId(self):

        return self._config['bridgeid']

    def getUser(self, user):

        if user in self.users.keys():
            self.users[user].updateLastUse()
            return True
        return False

    def checkUser(self, user, addr):

        error = []
        if not self.getUser(user):
            error.append(self.genError(1, addr, "unauthorized user"))
        return error

    def getWhitelist(self):

        whitelist = {}
        for myUser in self.users.values():
            whitelist[myUser.username] = myUser.getConfig()
        return whitelist

    def deleteUser(self, user, user2):

        error = self.checkUser(user, "/config/whitelist")
        if error:
            return error

        response = []
        addr = "/config/whitelist/%s" % user2
        if not self.getUser(user2):
            desc = "resource, /config/whitelist/%s, not available" % user2
            response.append(self.genError(3, addr, desc))
        else:
            del self.users[user2]
            desc = addr + " deleted."
            # why is this success response different than all the others?!?!
            success = {"success": desc}
            response.append(success)
        return response

    def getBridgeConfig(self, user):

        # update UTC time
        self.updateUTC()

        if self.getUser(user):
            config = self._config
            config['whitelist'] = self.getWhitelist()

            # clear link button if it pressed by addUser
            if self.getLinkButton():
                self.setLinkButton(False)

            return config

        # an unauthorized user is allowed a partial config
        temp = {}
        ALLOWED = ['name', 'swversion', 'apiversion', 'mac', 'bridgeid', 'factorynew', 'replacesbridgeid', 'modelid']
        for i in ALLOWED:
            temp[i] = self._config[i]
        return temp

    def getCapabilities(self, user):

        error = self.checkUser(user, "/capabilities")
        if error:
            return error

        temp = {}
        temp['lights'] = {"available": 60}
        temp['sensors'] = {"available": 0, "clip":{"available": 0}, "zll":{"available": 0}, "zgp":{"available": 0}}
        temp['groups'] = {"available": 60}
        temp['scenes'] = {"available": 0, "lightstates": {"available": 0}}
        temp['schedules'] = {"available": 0}
        temp['rules'] = {"available": 0, "conditions":{"available": 0}, "actions":{"available": 0}}
        temp['resourcelinks'] = {"available": 0}
        temp['timezones'] = {"values": timezones.getTimezones()}
        return temp

    def getTimezones(self, user):

        error = self.checkUser(user, "/info")
        if error:
            return error

        return timezones.getTimezones()

    def getLights(self):

        lights = {}
        for id in self.lights.keys():
            lights.update({id: self.lights[id].getObj()})
        return lights

    def getLightsInternal(self, id=''):

        if id in self.lights.keys():
            return self.lights[id]._getObjInternal()
        else:
            lights = {}
            for id in self.lights.keys():
                lights.update({id: self.lights[id]._getObjInternal()})
            return lights

    def getLight(self, id=''):

        if id in self.lights.keys():
            return self.lights[id].getObj()
        else:
            error = []
            addr = "/lights/%s" % id
            desc = "resource, /lights/%s, not available" % id
            error.append(self.genError(3, addr, desc))
            return error

    def getGroups(self):

        groups = {}
        for id in self.groups.keys():
            # group 0 is not returned as part of all groups
            if id == "0":
                continue
            groups.update({id: self.groups[id].getObj()})
        return groups

    def getGroupsInternal(self, id=''):

        if id in self.groups.keys():
            return self.groups[id]._getObjInternal()
        else:
            groups = {}
            for id in self.groups.keys():
                groups.update({id: self.groups[id]._getObjInternal()})
            return groups

    def getGroup(self, id=''):

        if id in self.groups.keys():
            return self.groups[id].getObj()
        else:
            error = []
            addr = "/groups/%s" % id
            desc = "resource, /groups/%s, not available" % id
            error.append(self.genError(3, addr, desc))
            return error

    def getFullConfig(self, user):

        error = self.checkUser(user, "/")
        if error:
            return error

        # update UTC time
        self.updateUTC()

        # config, lights, groups
        temp = {}
        temp['config'] = self._config
        temp['config']['whitelist'] = self.getWhitelist()
        temp['lights'] = self.getLights()
        temp['groups'] = self.getGroups()
        for config in self._unemulated.keys():
            temp[config] = self._unemulated[config]
        return temp

    def unemulatedFeature(self, user, path):

        addr = "/%s" % path
        error = self.checkUser(user, addr)
        if error:
            return error

        return self._unemulated[path]

    def unknownPath(self, user, path, method):

        addr = "/%s" % path
        error = self.checkUser(user, addr)
        if error:
            return error

        desc = "method, %s, not available for resource, %s" % (method, addr)
        error.append(self.genError(4, addr, desc))
        return error

    def genError(self, type, addr, desc):

        error = {"error": {"type": type, "address": addr, "description": desc}}
        return error

    def genSuccess(self, addr, val):

        success = {}
        success = {"success": {addr: val}}
        return success

    def getConfigInternal(self):

        # config, lights, groups
        temp = {}
        temp['config'] = self._config
        temp['config']['whitelist'] = self.getWhitelist()
        temp['lights'] = self.getLightsInternal()
        temp['groups'] = self.getGroupsInternal()
        temp['_unemulated'] = self._unemulated
        return temp

    def getLightsConfig(self, user, id):

        addr = "/lights"
        if id > 0:
            addr += "/%s" % id

        error = self.checkUser(user, addr)
        if error:
            return error

        if not id:
            return self.getLights()

        return self.getLight(id)

    def getGroupsConfig(self, user, id):

        addr = "/groups"
        if id >= 0:
            addr += "/%s" % id

        error = self.checkUser(user, addr)
        if error:
            return error

        if not id:
            return self.getGroups()

        return self.getGroup(id)

    def getNextIndex(self, type):

        i = 0
        if type:
            i = int(sorted(type.keys(), key=int)[-1])
        return str(i+1)

    def addLight(self, name='', **kwargs):

        myLight = HueLight(name, **kwargs)
        index = self.getNextIndex(self.lights)
        self.lights.update({index: myLight})
        self.lights[index].setIndex(index)

        # all lights are members of Group 0
        self.groups["0"].addLight(index)

        return index

    def addLightInternal(self, params):

        response = []
        index = self.addLight(**params)
        if index:
            response.append(self.genSuccess("id", index))
        return response

    def setLightCommand(self, id, proxy='', external=''):

        response = []
        if not proxy and not external:
            error = {"error": {"/internal/lights/command": "no external or proxy command provided"}}
            response.append(error)
            return response

        if id not in self.lights.keys():
            desc = "invalid light id, %s" % id
            error = {"error": desc}
            response.append(error)
            return error

        if proxy:
            self.lights[id].setProxyCommand(proxy)
            addr = "/lights/%s/proxy" % id
            desc = self.lights[id].getProxyCommand()
            response.append(self.genSuccess(addr, desc))
            return response

        if external:
            self.lights[id].setExternalCommand(external)
            addr = "/lights/%s/external" % id
            desc = self.lights[id].getExternalCommand()
            response.append(self.genSuccess(addr, desc))
            return response

    def setLightAttributes(self, user, id, params):

        addr = "/lights/%s" % id
        error = self.checkUser(user, addr)
        if error:
            return error

        # invalid id
        if id not in self.lights.keys():
            addr = "/lights/%s" % id
            desc = "resource, /lights/%s, not available" % id
            error.append(self.genError(3, addr, desc))
            return error

        return self.lights[id].setAttributes(params)

    def setLightState(self, user, id, opt, params):

        addr = "/lights/%s" % id
        error = self.checkUser(user, addr)
        if error:
            return error

        # invalid id
        if id not in self.lights.keys():
            addr = "/lights/%s" % id
            desc = "resource, /lights/%s, not available" % id
            error.append(self.genError(3, addr, desc))
            return error

        # invalid operation
        if opt != 'state':
            addr = "/lights/%s/%s" % (id, opt)
            desc = "parameter, %s, not available"
            error.append(self.genError(6, addr, desc))
            return error

        # update light state
        response = self.lights[id].setState(params)

        # update group states
        for i in self.lights[id].getGroups():
            self.groups[i].updateState()

        return response

    def addGroup(self, name='', lights=[], **kwargs):

        myGroup = HueGroup(name, _lights=self.lights, **kwargs)
        index = self.getNextIndex(self.groups)
        self.groups.update({index: myGroup})
        self.groups[index].setIndex(index)

        for i in lights:
            li = str(i)
            if li in self.lights.keys():
                self.groups[index].addLight(li)

        return index

    def createGroup(self, user, params):

        error = self.checkUser(user, "/groups")
        if error:
            return error

        response = []
        opts = {}
        ALLOWED = ['name', 'lights', 'type', 'class']
        for k, v in params.items():
            if k in ALLOWED:
                # rename class -> klass
                if k == 'class':
                    k = 'klass'
                opts[k] = v
            else:
                addr = "/groups/%s" % k
                desc = "parameter, %s, not available" % k
                response.append(self.genError(6, addr, desc))

        # need to push this into the group object
        index = self.addGroup(**opts)
        response.append(self.genSuccess("id", index))
        return response

    def setGroupAttributes(self, user, id, params):

        addr = "/groups/%s" % id
        error = self.checkUser(user, addr)
        if error:
            return error

        # invalid id
        if id == "0" or id not in self.groups.keys():
            addr = "/groups/%s" % id
            desc = "resource, /groups/%s, not available" % id
            error.append(self.genError(3, addr, desc))
            return error

        return self.groups[id].setAttributes(params)

    def setGroupAction(self, user, id, opt, params):

        addr = "/groups/%s" % id
        error = self.checkUser(user, addr)
        if error:
            return error

        # invalid id
        if id not in self.lights.keys():
            addr = "/groups/%s" % id
            desc = "resource, /groups/%s, not available" % id
            error.append(self.genError(3, addr, desc))
            return error

        # invalid operation
        if opt != 'action':
            addr = "/groups/%s/%s" % (id, opt)
            desc = "parameter, %s, not available"
            error.append(self.genError(6, addr, desc))
            return error

        return self.groups[id].setAction(params)

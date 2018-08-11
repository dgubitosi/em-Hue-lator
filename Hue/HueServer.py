"""
    Hue Server
"""

from werkzeug.serving import WSGIRequestHandler
from flask import Flask, Response, json, jsonify, request
import pprint
from HueBridge import HueBridge
from HueSSDP import runDiscovery
from threading import Thread
import socket


# http://stackoverflow.com/questions/25466904/print-raw-http-request-in-flask-or-wsgi
# http://stackoverflow.com/questions/530526/accessing-post-data-from-wsgi
class LoggingMiddleware(object):
    def __init__(self, app):
        self._app = app

    def __call__(self, environ, resp):
        print "\n"
        pprint.pprint(('REQUEST', environ))
        length = 0
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
        except:
            pass
        if length > 0:
            pprint.pprint(('CONTENT', environ['wsgi.input'].read(length)))

        def log_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers))
            return resp(status, headers, *args)

        return self._app(environ, log_response)


# wrapper to clean up response types
def reply(content):
    # dictionary for objects
    if type(content) is dict:
        return jsonify(content)
    # list for success and error responses
    elif type(content) is list:
        return Response(json.dumps(content), mimetype='application/json')
    # json as string
    elif type(content) is str:
        return Response(content, mimetype='application/json')
    # oops
    else:
        return Response("Server Error", status=500)


# wrapper to clean up posted data
def getJsonContent(req):
    content = req.get_json(force=True, silent=True)
    if content is None:
        content = {}
    return content


class HueServer(object):

    def __init__(self, port=80, discovery=True, threaded=True, debug=False):

        self.port = port
        self.discovery = discovery
        self.threaded = threaded
        self.debug = debug

        # get IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip = s.getsockname()[0]

        self.bridge = HueBridge()
        self.bridge.setPort(self.port)
        self.bridge.setNetwork(self.ip)
        self.api = self.create_api()

    def runServer(self):

        if self.discovery:
            id = self.bridge.getBridgeId()
            mac = self.bridge.getMacAddress()
            self.upnp = Thread(target=runDiscovery, args=(self.ip, self.port, id, mac))
            self.upnp.setDaemon(True)
            self.upnp.start()
        self.api.run(host=self.ip, port=self.port, threaded=self.threaded, debug=self.debug)

    def setBridgeConfig(self, **kwargs):

        self.bridge.setBridgeConfigInternal(kwargs)

    def addUser(self, device, username=''):

        if not username:
            user = {"devicetype": device}
            self.bridge.addUser(user)
        else:
            self.bridge.addUserInternal(device, username)

    def addLight(self, **kwargs):

        self.bridge.addLightInternal(kwargs)

    def addGroup(self, name='', lights=[], **kwargs):

        self.bridge.addGroup(name, lights, **kwargs)

    def create_api(self):

        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        api = Flask('em-Hue-lator')
        #api.wsgi_app = LoggingMiddleware(api.wsgi_app)

        # debugging catch all url
        @api.route("/<path:path>", methods=['GET', 'PUT', 'POST', 'DELETE'])
        def catch(path=None):
            content = getJsonContent(request)
            print "Request:\n  %s %s" % (request.method, request.path)
            if content:
                print "Content:\n  %s" % json.dumps(content)
            return Response("Not Implemented", status=404)

        #
        # internal api
        #

        @api.route("/internal/config", methods=['GET'])
        def internalConfig():
            return reply(self.bridge.getConfigInternal())

        @api.route("/internal/config", methods=['PUT'])
        def internalSetConfig():
            # { "name": name, "mac": mac, "ipaddress": ipaddres, "netmask": netmask, "gateway": gateway }
            content = getJsonContent(request)
            return reply(self.bridge.setBridgeConfigInternal(content))

        @api.route("/internal/lights", methods=['GET'])
        @api.route("/internal/lights/<int:id>", methods=['GET'])
        def internalLights(id=None):
            index = ''
            if id > 0:
                index = str(id)
            return reply(self.bridge.getLightsInternal(index))

        @api.route("/internal/lights", methods=['POST'])
        def internalAddLight():
            # { "name": name, "modelid": modelid }
            content = getJsonContent(request)
            return reply(self.bridge.addLightInternal(content))

        @api.route("/internal/lights/<int:id>/command", methods=['PUT'])
        def internalSetLightCommand(id):
            # { "external": "command" }
            # { "external": [ "command", "arg1", "arg2", .. ] }
            # { "proxy": [ "ip-address", "username", "id" ] }
            index = str(id)
            content = getJsonContent(request)
            command = content.get('proxy', '')
            if command:
                return reply(self.bridge.setLightCommand(index, proxy=command))
            command = content.get('external', '')
            if command:
                return reply(self.bridge.setLightCommand(index, external=command))

        @api.route("/internal/groups", methods=['GET'])
        @api.route("/internal/groups/<int:id>", methods=['GET'])
        def interalGroups(id=None):
            index = ''
            if id >= 0:
                index = str(id)
            return reply(self.bridge.getGroupsInternal(index))

        #
        # UPnP description.xml
        #

        @api.route("/description.xml", methods=['GET'])
        def description():
            return self.bridge.getDescription()

        #
        # configuration api
        # http://www.developers.meethue.com/documentation/configuration-api
        #

        # new user request
        @api.route("/api/", strict_slashes=False, methods=['POST'])
        def addUser():
            content = getJsonContent(request)
            return reply(self.bridge.addUser(content))

        # get bridge config
        @api.route("/api/<user>/config", methods=['GET'])
        @api.route("/api/<user>/config/<path:path>", methods=['GET'])
        def getBridgeConfig(user, path=None):
            if path:
                return notAvailable('config', path)
            return reply(self.bridge.getBridgeConfig(user))

        # set bridge config
        @api.route("/api/<user>/config", methods=['PUT'])
        def setBridgeConfig(user):
            content = getJsonContent(request)
            return reply(self.bridge.setBridgeConfig(user, content))

        # delete user
        @api.route("/api/<user>/config/whitelist/<user2>", methods=['DELETE'])
        def deleteUser(user, user2):
            return reply(self.bridge.deleteUser(user, user2))

        # get full config
        @api.route("/api/<user>/", strict_slashes=False, methods=['GET'])
        def getFullConfig(user):
            return reply(self.bridge.getFullConfig(user))

        #
        # info api
        # http://www.developers.meethue.com/documentation/info-api
        #

        @api.route("/api/<user>/info", methods=['GET'])
        @api.route("/api/<user>/info/<path:path>", methods=['GET'])
        def getTimezones(user, path=None):
            if path == 'timezones':
                return reply(self.bridge.getTimezones(user))
            return notAvailable('info', path)

        #
        # capabilities api
        # https://www.developers.meethue.com/documentation/capabilities-api
        #

        @api.route("/api/<user>/capabilities", methods=['GET'])
        @api.route("/api/<user>/capabilities/<path:path>", methods=['GET'])
        def getCapabilities(user, path=''):
            if path:
                return notAvailable('capabilities', path)
            return reply(self.bridge.getCapabilities(user))

        #
        # lights api
        # http://www.developers.meethue.com/documentation/lights-api
        #

        # get lights
        @api.route("/api/<user>/lights", methods=['GET'])
        @api.route("/api/<user>/lights/<int:id>", methods=['GET'])
        @api.route("/api/<user>/lights/<path:path>", methods=['GET'])
        def getLightsConfig(user, id=None, path=None):
            if path:
                return notAvailable('lights', path)
            index = ''
            if id > 0:
                index = str(id)
            return reply(self.bridge.getLightsConfig(user, index))

        # new lights status
        @api.route("/api/<user>/lights/new", methods=['GET'])
        def newLights(user):
            # fake response
            raw = '{"lastscan":"none"}'
            return reply(raw)

        # scan for new lights
        @api.route("/api/<user>/lights", methods=['POST'])
        def scanLights(user):
            # fake response
            success = []
            success.append(self.bridge.genSuccess("/lights", "Searching for new devices"))
            return reply(success)

        # set light attributes
        @api.route("/api/<user>/lights/<int:id>", methods=['PUT'])
        def setLightAttributes(user, id):
            content = getJsonContent(request)
            return reply(self.bridge.setLightAttributes(user, str(id), content))

        # set light state
        @api.route("/api/<user>/lights/<int:id>/<opt>", methods=['PUT'])
        def setLightState(user, id, opt=None):
            content = getJsonContent(request)
            return reply(self.bridge.setLightState(user, str(id), opt, content))

        # delete light
        @api.route("/api/<user>/lights/<int:id>", methods=['DELETE'])
        def deleteLight(user, id):
            # disabled for now
            error = []
            error.append(self.bridge.genError(901, "/lights", "Internal Error, 901"))
            return reply(error)

        #
        # groups api
        # http://www.developers.meethue.com/documentation/groups-api
        #

        # get groups
        @api.route("/api/<user>/groups", methods=['GET'])
        @api.route("/api/<user>/groups/<int:id>", methods=['GET'])
        @api.route("/api/<user>/groups/<path:path>", methods=['GET'])
        def getGroupsConfig(user, id=None, path=None):
            if path:
                return notAvailable('groups', path)
            index = ''
            if id >= 0:
                index = str(id)
            return reply(self.bridge.getGroupsConfig(user, index))

        # create group
        @api.route("/api/<user>/groups", methods=['POST'])
        def createGroup(user):
            content = getJsonContent(request)
            return reply(self.bridge.createGroup(user, content))

        # set group attributes
        @api.route("/api/<user>/groups/<int:id>", methods=['PUT'])
        def setGroupAttributes(user, id):
            content = getJsonContent(request)
            return reply(self.bridge.setGroupAttributes(user, str(id), content))

        # set group action
        @api.route("/api/<user>/groups/<int:id>/<opt>", methods=['PUT'])
        def setGroupAction(user, id, opt=None):
            content = getJsonContent(request)
            return reply(self.bridge.setGroupAction(user, str(id), opt, content))

        # delete group
        @api.route("/api/<user>/groups/<int:id>", methods=['DELETE'])
        def deleteGroup(user, id):
            # disabled for now
            error = []
            error.append(self.bridge.genError(901, "/groups", "Internal Error, 901"))
            return reply(error)

        # unemulated features
        @api.route("/api/<user>/schedules", methods=['GET'])
        @api.route("/api/<user>/scenes", methods=['GET'])
        @api.route("/api/<user>/sensors", methods=['GET'])
        @api.route("/api/<user>/rules", methods=['GET'])
        @api.route("/api/<user>/resourcelinks", methods=['GET'])
        def unemulatedFeature(user):
            path = request.path.split('/')
            return reply(self.bridge.unemulatedFeature(user, path[-1]))

        # catch incorrect urls with the proper format
        @api.route("/api/<user>", methods=['GET', 'PUT', 'POST', 'DELETE'])
        @api.route("/api/<user>/<path:path>", methods=['GET', 'PUT', 'POST', 'DELETE'])
        def unknownPath(user, path=None):
            return reply(self.bridge.unknownPath(user, path, request.method))

        # generate error
        def notAvailable(root, path=None):
            error = []
            addr = '/{}'.format(root)
            if path:
                addr += '/{}'.format(path)
            desc = "resource, {}, not available".format(addr)
            error.append(self.bridge.genError(3, addr, desc))
            return reply(error)

        return api

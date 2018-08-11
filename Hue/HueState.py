"""
    Hue State
"""

import json


class HueState(object):

    def __init__(self):

        # base attributes
        self.on = False
        self.bri = 200
        self.alert = "none"

        # base setters
        self._set = {
          'on': self.setOn,
          'bri': self.setBri,
          'bri_inc': self.incBri,
          'alert': self.setAlert,
        }

        # base getters
        self._get = {
          'on': self.getOn,
          'bri': self.getBri,
          'alert': self.getAlert
        }

    def setState(self, st, val):

        if st in self._set.keys():
            self._set[st](val)
            return True
        return False

    def setOn(self, on='True'):

        self.on = on

    def getOn(self):

        return self.on

    def setOff(self):

        self.on(False)

    def setBri(self, bri):

        # clamp brightness 1:254
        bri = max(1, min(bri, 254))
        self.bri = bri

    def getBri(self):

        return self.bri

    def incBri(self, val):

        if val < -254 or val > 254:
            return
        bri = self.bri + val
        self.setBri(bri)

    def setAlert(self, mode):

        if mode in ["none", "select", "lselect"]:
            self.alert = mode

    def getAlert(self):

        return self.alert

    def getHue(self):

        return None

    def getSat(self):

        return None

    def getXY(self):

        return None

    def getEffect(self):

        return None

    def getColormode(self):

        return None

    def getCT(self):

        return None

    def getObj(self):

        obj = {}
        for k, v in self.__dict__.items():
            # skip internal properties
            if k[0] == '_':
                continue
            else:
                obj[k] = v
        return obj

    def __str__(self):

        return json.dumps(self.getObj())


class HueStateColor(HueState):

    def __init__(self):

        HueState.__init__(self)

        # color attributes
        self.hue = 34497
        self.sat = 232
        self.effect = "none"
        self.xy = [0.3151, 0.3251]
        self.colormode = "xy"

        # color setters
        self._set.update({
            'hue': self.setHue,
            'hue_inc': self.incHue,
            'sat': self.setSat,
            'sat_inc': self.incSat,
            'xy': self.setXY,
            'xy_inc': self.incXY,
            'effect': self.setEffect,
            'colormode': self.setColormode
        })

        # color getters
        self._get.update({
            'hue': self.getHue,
            'sat': self.getSat,
            'xy': self.getXY,
            'effect': self.getEffect,
            'colormode': self.getColormode
        })

    def setEffect(self, mode):

        if mode in ["none", "colorloop"]:
            self.effect = mode

    def getEffect(self):

        return self.effect

    def setHue(self, hue):

        # clamp hue 0:65535
        hue = max(0, min(hue, 65535))
        self.hue = hue
        self.setColormode("hs")

    def getHue(self):

        return self.hue

    def incHue(self, val):

        if val < -65534 or val > 65534:
            return

        # hue rotates around
        hue = self.hue + val
        if hue > 65535:
            hue -= 65536
        if hue < 0:
            hue += 65536
        self.setHue(hue)

    def setSat(self, sat):

        # clamp saturation 0:254
        sat = max(0, min(sat, 254))
        self.sat = sat
        self.setColormode("hs")

    def getSat(self):

        return self.sat

    def incSat(self, val):

        if val < -254 or val > 254:
            return
        sat = self.sat + val
        self.setSat(sat)

    def setXY(self, xy):

        self.xy[0] = xy[0]
        self.xy[1] = xy[1]
        self.setColormode("xy")

    def getXY(self):

        return self.xy

    def incXY(self, val):

        if val < -0.5 or val > 0.5:
            return
        xy = self.xy
        xy[0] += val
        xy[1] += val
        self.setXY(xy)

    def setColormode(self, mode):

        if mode in ["hs", "xy"]:
            self.colormode = mode

    def getColormode(self):

        return self.colormode


class HueStateExtendedColor(HueStateColor):

    def __init__(self):

        HueStateColor.__init__(self)

        # extended color attributes
        self.ct = 155

        # extended color setters
        self._set.update({
            'ct': self.setCT,
            'ct_inc': self.incCT
        })

        # extended color getters
        self._get.update({
            'ct': self.getCT
        })

    def setCT(self, ct):

        # clamp colortemp 153:500
        ct = max(153, min(ct, 500))
        self.ct = ct
        self.setColormode("ct")

    def getCT(self):

        return self.ct

    def incCT(self, val):

        if val < -65534 or val > 65534:
            return
        ct = self.ct + val
        self.setCT(ct)

    def setColormode(self, mode):

        if mode in ["hs", "xy", "ct"]:
            self.colormode = mode


# light states have a reachable property
class HueLightStateDimmable(HueState):

    def __init__(self):

        HueState.__init__(self)
        self.reachable = True


class HueLightStateColor(HueStateColor):

    def __init__(self):

        HueStateColor.__init__(self)
        self.reachable = True


class HueLightStateExtendedColor(HueStateExtendedColor):

    def __init__(self):

        HueStateExtendedColor.__init__(self)
        self.reachable = True


# group states do not have a reachable property
class HueGroupActionDimmable(HueState):

    def __init__(self):

        HueState.__init__(self)


class HueGroupActionColor(HueStateColor):

    def __init__(self):

        HueStateColor.__init__(self)


class HueGroupActionExtendedColor(HueStateExtendedColor):

    def __init__(self):

        HueStateExtendedColor.__init__(self)

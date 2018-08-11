"""
    Hue User
"""

import utility


class HueUser(object):

    def __init__(self, name, username=''):

        if not username:
            username = utility.getRandomString(40)
        self.username = username

        self._config = {
            "name": "",
            "create date": "",
            "last use date": ""
            }

        self._config['name'] = name

        now = utility.getUTCNow()
        self._config['create date'] = now
        self._config['last use date'] = now

    def getConfig(self):

        return self._config

    def updateLastUse(self):

        self._config['last use date'] = utility.getUTCNow()

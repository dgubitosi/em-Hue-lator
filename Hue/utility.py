"""
    Utility Functions
"""

import datetime
import random
import re
import socket


def getUTCNow():

    return datetime.datetime.strftime(
        datetime.datetime.utcnow(), '%Y-%m-%dT%H:%M:%S')


def splitString(s, n):

    return [s[i:i+n] for i in xrange(0, len(s), n)]


def randomString(chars, n):

    return ''.join((random.choice(chars) for i in xrange(n)))


def getRandomString(n=40):

    digits = map(chr, range(ord('0'), ord('9')+1))
    upper = map(chr, range(ord('A'), ord('Z')+1))
    lower = map(chr, range(ord('a'), ord('z')+1))
    alphanumeric = digits + upper + lower
    return randomString(alphanumeric, n)


def getRandomHexString(n=6):

    hexdigits = '0123456789abcdef'
    return randomString(hexdigits, n)


def validateUniqueId(id):

    # 00:17:88:01:00:ab:cd:ef-0b
    if not re.match(r'^([0-9A-F]{2}:){7}[0-9A-F]{2}-0b$', id, re.I):
        return False
    if not re.match(r'^00:17:88:01:00', id):
        return False
    return True


def validateMacAddress(mac):

    # 00:17:88:14:aa:bb
    if not re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', mac, re.I):
        return False
    if not re.match(r'^00:17:88:14', mac):
        return False
    return True


def validateIpAddress(ip):

    # 255.255.255.255
    if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
        return False
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

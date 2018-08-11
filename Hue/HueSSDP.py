"""
    HueSSDP
"""

import socket
import struct
import time

GROUP = '239.225.255.250'
PORT = 1900

SSDP = """HTTP/1.1 200 OK
HOST: 239.255.255.250:1900
EXT:
CACHE-CONTROL: max-age=100
LOCATION: http://{}:{}/description.xml
SERVER: FreeRTOS/7.4.2 UPnP/1.0 IpBridge/1.16.0
hue-bridgeid: {}
ST: urn:schemas-upnp-org:device:basic:1
USN: uuid:2f402f80-da50-11e1-9b23-{}

"""


def runDiscovery(ip, port, id, mac):
    # adapted from https://pymotw.com/2/socket/multicast.html

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))

    try:
        s.bind(('', PORT))
    except Exception, e:
        print "ERROR: Failed to bind port:" % e

    mreq = struct.pack("4sl", socket.inet_aton(GROUP), socket.INADDR_ANY)
    try:
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except Exception, e:
        print "ERROR: Failed to join multicast group:" % e

    reply = SSDP.format(ip, port, id, mac).replace("\n", "\r\n")
    while True:
        try:
            data, addr = s.recvfrom(65507)
            if 'M-SEARCH' in data:
                s.sendto(reply, addr)
        except:
            pass

        time.sleep(0.1)

    s.close()

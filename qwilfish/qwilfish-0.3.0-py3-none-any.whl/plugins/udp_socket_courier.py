# Standard lib imports
import platform
import socket

# Local imports
from qwilfish.session_builder import register_courier

def initialize():
    '''Registers UDPSocketCourier as a plugin.'''
    register_courier(UDPSocketCourier.PLUGIN_IDENTIFIER, UDPSocketCourier)

class UDPSocketCourier:
    '''Delivers fuzz data to the SUT by sending a UDP packet.'''

    # Plugin identifier
    PLUGIN_IDENTIFIER = "udp_socket_courier"

    # WA for missing socket.IP_PKTINFO, src: https://bugs.python.org/issue31203
    IP_PKTINFO = 8

    def __init__(self, src="127.0.0.1", dst="127.0.0.1", port=5683):
        if platform.system() != "Linux":
            raise NotImplementedError(
                f"Raw sockets not supported on {platform.system()}")
        else:
            self.sock = None
            self.src = src
            self.dst = dst
            self.port = port

    def init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def deliver(self, data):
        src_bytes = socket.inet_aton(self.src)
        anc = (socket.IPPROTO_IP,
               UDPSocketCourier.IP_PKTINFO,
               b"\x00\x00\x00\x00" + src_bytes + b"\x00\x00\x00\x00")
        self.sock.sendmsg([bytes(data, 'utf-8')],
                          [anc],
                          0,
                          (self.dst, self.port))
        return True

    def destroy(self):
        self.sock.close()

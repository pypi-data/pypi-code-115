# Standard lib imports
import platform
import socket

# Local imports
from qwilfish.session_builder import register_courier

def initialize():
    '''Registers RawL2SocketCourier as a plugin.'''
    register_courier(RawL2SocketCourier.PLUGIN_IDENTIFIER, RawL2SocketCourier)

class RawL2SocketCourier:
    '''Delivers fuzz data to a system by writing to a raw socket.'''

    # Plugin identifier
    PLUGIN_IDENTIFIER = "raw_socket_courier"

    def __init__(self, interface="lo"):
        if platform.system() != "Linux":
            raise NotImplementedError(
                f"Raw sockets not supported on {platform.system()}")
        else:
            self.interface = interface
            self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)

    def init(self):
        self.sock.bind((self.interface, 0))

    def deliver(self, data):
        frame = []
        for byte in range(0, len(data), 8):
            frame.append(int(data[byte:byte+8], 2))

        frame = bytes(frame)

        return self.sock.send(frame) == len(frame) # True if succesful send

    def destroy(self):
        self.sock.close()

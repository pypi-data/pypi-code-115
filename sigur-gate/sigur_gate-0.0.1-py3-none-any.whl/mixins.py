import socket
from sigure_emulator.main import SigurEmulator


class SigurMixin:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port


class SocketMixin:
    socket = socket.socket()


class SocketEmulatorMixin:
    socket = SigurEmulator()


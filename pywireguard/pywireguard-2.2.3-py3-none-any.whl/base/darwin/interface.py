from pathlib import Path
import socket

from ..exceptions import BadInterfaceName
from ..userspace.interface import UserspaceInterface


class DarwinInterface(UserspaceInterface):
    SOCKET_PATH = '/var/run/wireguard/'

    def __init__(self, name):
        self.name = name
        self.file_socket_name = f'{self.SOCKET_PATH}{self.name}.name'
        socket_name = Path(self.file_socket_name)
        if socket_name.exists():
            name = socket_name.read_text().strip()
            if not Path(f'{self.SOCKET_PATH}{name}.sock').exists():
                raise BadInterfaceName()
        else:
            raise BadInterfaceName()

    def _get_socket(self) -> socket.socket:
        socket_name = Path(self.file_socket_name).read_text().strip()
        socket_address = f'{self.SOCKET_PATH}{socket_name}.sock'
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_address)
        return sock

    def _command_get(self) -> str:
        buffer = ''
        sock = self._get_socket()
        sock.sendall(b'get=1\n\n')
        while '\n\n' not in buffer:
            buffer += sock.recv(1024).decode()
        sock.close()
        return buffer

    def _command_set(self, command: str):
        buffer = ''
        sock = self._get_socket()
        final_cmd = f'set=1\n{command}\n\n'
        sock.sendall(final_cmd.encode())
        while '\n\n' not in buffer:
            buffer += sock.recv(1024).decode()
        sock.close()

from sigur_worker import mixins
from sigur_worker import functions


class Point:
    """
    Status description:
    0 - unknown
    1 - lock
    2 - normal
    3 - unlock
    """
    socket = None
    point_num = None
    ip = None
    port = None
    status = None

    def make_connection(self):
        print('Подключение к контролеру скуд')
        self.socket.connect((self.ip, self.port))
        self.socket.send(b'"LOGIN" 1.8 "Administrator" ""\r\n')
        return self.socket.recv(1024)

    def lock(self):
        msg = 'SETAPMODE LOCKED {}\r\n'.format(self.point_num)
        self.socket.send(bytes(msg, encoding='utf-8'))
        return self.socket.recv(1024)

    def unlock(self):
        msg = 'SETAPMODE UNLOCKED {}\r\n'.format(self.point_num)
        self.socket.send(bytes(msg, encoding='utf-8'))
        return self.socket.recv(1024)

    def normal(self):
        msg = 'SETAPMODE NORMAL {}\r\n'.format(self.point_num)
        self.socket.send(bytes(msg, encoding='utf-8'))
        return self.socket.recv(1024)

    def get_status(self):
        command = 'GETAPINFO {}\r\n'.format(self.point_num)
        self.socket.send(bytes(command, encoding='utf-8'))
        data = self.socket.recv(1024)
        parsed_data = functions.parse_ap_status(data)
        self.status = parsed_data
        return self.status


class Gate(mixins.SigurMixin, Point):
    def __init__(self, ip, port, point_num):
        self.point_num = point_num
        super().__init__(ip=ip, port=port)

    def open(self):
        self.unlock()

    def close(self):
        self.lock()


class GateReal(mixins.SocketMixin, Gate):
    pass


class GateTest(mixins.SocketEmulatorMixin, Gate):
    pass

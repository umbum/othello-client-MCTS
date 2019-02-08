# 네트워크와 관련된 코드는 여기에.

import socket
import struct
import json


class NetworkManager:
    """
    static class
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    loop_running  = None

    @classmethod
    def initNetwork(cls, HOST, PORT):
        cls.sock.connect((HOST, PORT))

    @classmethod
    def send(cls, msg):
        return cls.sock.sendall((serialize(msg)))

    @classmethod
    def recvLoop(cls, callback):
        """
        thread로 실행할 것.

        Raises
        ------
        ConnectionResetError
            util.deserialize()
        """
        cls.loop_running = True
        while cls.loop_running:
            msg = deserialize(cls.sock)    # blocking.
            callback(msg)   


def serialize(msg):
    body = json.dumps(msg).encode()
    msg_len = struct.pack('>L', len(body))
    return msg_len + body


def deserialize(sock):
    """

    Raises
    ------
    ConnectionResetError
    """
    _msg_len = sock.recv(4)
    if len(_msg_len) < 4:
        raise ConnectionResetError
    msg_len = struct.unpack('>L', _msg_len)[0]
    msg_raw = sock.recv(msg_len)
    while len(msg_raw) < msg_len:
        msg_raw += sock.recv(msg_len - len(msg_raw))
    msg = json.loads(msg_raw)
    return msg

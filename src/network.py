import socket
import threading
import time

from util import *
from protocol_enum import *
from board import *


class NetworkManager:
    """
    static class
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_color = None
    op_color = None
    my_turn  = False
    loop_running  = None

    @classmethod
    def initNetwork(cls, HOST, PORT):
        cls.sock.connect((HOST, PORT))

    @classmethod
    def send(cls, msg):
        return cls.sock.sendall((serialize(msg)))

    @classmethod
    def recvLoop(cls):
        """
        thread로 실행할 것.

        Raises
        ------
        ConnectionResetError
            util.deserialize()
        """
        cls.loop_running = True
        while cls.loop_running:
            msg = deserialize(cls.sock)

            # handle message
            board_lock.acquire()
            
            if msg["type"] == MsgType.READY:
                print("recv READY")
            elif msg["type"] == MsgType.START:
                cls.my_color = msg["color"]
                cls.op_color = Color.WHITE if (cls.my_color == Color.BLACK) else Color.BLACK
                print("START : {}".format(cls.my_color))
            elif msg["type"] == MsgType.TURN:
                if msg["opponent_put"] is not None:
                    i, j = msg["opponent_put"]
                    putStone(cls.op_color, i, j)
                    reverseStones(cls.op_color, i, j)
                cls.my_turn = True
                setAvailablePoints(msg["available_points"])
            elif msg["type"] == MsgType.ACCEPT:
                # msg["opponent_time_limit"]
                print("ACCEPT")
            elif msg["type"] == MsgType.NOPOINT:
                i, j = msg["opponent_put"]
                putStone(cls.op_color, i, j)
                reverseStones(cls.op_color, i, j)
            elif msg["type"] == MsgType.GAMEOVER:
                print("GAMEOVER")
                if msg.get("opponent_put") is not None:
                    i, j = msg["opponent_put"]
                    putStone(cls.op_color, i, j)
                    reverseStones(cls.op_color, i, j)
                print(msg)
                exit()
            elif msg["type"] == MsgType.ERROR:
                print("ERROR!")
                print(msg)

            board_lock.release()

    

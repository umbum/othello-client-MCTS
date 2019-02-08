# 비즈니스 로직과 관련된 코드는 여기에.

from board import *
from network import NetworkManager as nm
from protocol_enum import *


class OthelloState:
    def __init__(self):
        self.my_turn = False
        self.__my_color = None
        self.op_color = None

    @property
    def my_color(self):
        return self.__my_color

    @my_color.setter
    def my_color(self, value: Color):
        self.__my_color = value
        self.op_color = 3 - value  # Color가 1 아니면 2 이므로, 3 - value로 상대 Color를 구할 수 있음.


st = OthelloState()


def handleMsg(msg):
    """
    recvLoop에 callback으로 넘겨서 recv Thread가 실행하게 될 함수.
    """

    board_lock.acquire()
    
    if msg["type"] == MsgType.READY:
        print("recv READY")
    elif msg["type"] == MsgType.START:
        st.my_color = msg["color"]
        print("START : {}".format(st.my_color))
    elif msg["type"] == MsgType.TURN:
        if msg["opponent_put"] is not None:
            i, j = msg["opponent_put"]
            putStone(st.op_color, i, j)
            reverseStones(st.op_color, i, j)
        st.my_turn = True
        setAvailablePoints(msg["available_points"])
    elif msg["type"] == MsgType.ACCEPT:
        # msg["opponent_time_limit"]
        print("ACCEPT")
    elif msg["type"] == MsgType.NOPOINT:
        i, j = msg["opponent_put"]
        putStone(st.op_color, i, j)
        reverseStones(st.op_color, i, j)
    elif msg["type"] == MsgType.GAMEOVER:
        print("GAMEOVER")
        if msg.get("opponent_put") is not None:
            i, j = msg["opponent_put"]
            putStone(st.op_color, i, j)
            reverseStones(st.op_color, i, j)
        print(msg)
        exit()
    elif msg["type"] == MsgType.ERROR:
        print("ERROR!")
        print(msg)

    board_lock.release()


def clickEventHandler(i, j):
    if st.my_turn:
        board_lock.acquire()
        if board[i][j].available == True:
            clearAvailablePoints()
            putStone(st.my_color, i, j)
            reverseStones(st.my_color, i, j)
            nm.send({
                "type": proto.ClntType.PUT,
                "point": (i, j)
            })
            st.my_turn = False
        else:
            print("not available point")
        board_lock.release()
    else:
        print("opponent's turn")
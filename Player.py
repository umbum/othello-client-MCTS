# 비즈니스 로직과 관련된 코드는 여기에.

from concurrent.futures import ProcessPoolExecutor, as_completed

from network import NetworkManager as nm
from protocol_enum import *
import MCTS
from OthelloState import DummyLock
from log import logger

# TODO : class Player를 만들어서 handleMsg를 상속받고 playTurn을 하위 클래스가 구현하도록 하면 구조적으로 좋은데
# player.handleMsg를 콜백으로 recvLoop에 넘길건데, 이게 player 객체의 컨텍스트가 클로저로 같이 전달이 되는지 확신을 못하겠음.
def handleMsg(st, player, msg):
    """
    recvLoop에 callback으로 넘겨서 recv Thread가 실행하게 될 함수.
    """

    if msg["type"] == MsgType.READY:
        print("recv READY")
    elif msg["type"] == MsgType.START:
        st.my_color = msg["color"]
        st.op_color = 3 - st.my_color    # 1 아니면 2 이므로 3 - my_color로 구할 수 있다.
        print("START : {}".format(st.my_color))

    elif msg["type"] == MsgType.TURN:
        print("\nTURN recv")

        if msg["opponent_put"] is not None:
            # 상대가 놓은 돌을 반영
            point = msg["opponent_put"]
            logger.warning("Opponent put {}".format(str(point)))
            st.putStone(point)
            logger.debug("\n" + str(st))
        
        if msg.get("opponent_status") == OpponentStatus.NOPOINT:
            logger.warning("Opponent NOPOINT")
            st.turnOver()

        st.cnt_available_points = msg["available_points"]
        logger.warning("availables : " + str(st.cnt_available_points))

        player.playTurn(st)

    elif msg["type"] == MsgType.ACCEPT:
        # using msg["opponent_time_limit"]
        logger.debug("ACCEPT")

    elif msg["type"] == MsgType.NOPOINT:
        logger.warning("NOPOINT")
        point = msg["opponent_put"]
        logger.warning("Opponent put {}".format(str(point)))

        st.putStone(point)    # 상대방이 둔 곳을 반영해주고,
        logger.debug("\n" + str(st))
        st.turnOver()         # putStone하면서 내 턴이 되었지만 NOPOINT이므로 바로 turnOver한다.

    elif msg["type"] == MsgType.GAMEOVER:
        logger.warning("GAMEOVER")

        if msg.get("opponent_put") is not None:
            
            i, j = msg["opponent_put"]
            st.putStone((i, j))
            logger.debug("\n" + str(st))
        
        print(msg)
        if msg.get("result") == Result.LOSE:
            print("LOSE")
        elif msg.get("result") == Result.WIN:
            print("WIN")
        else:
            print("DRAW")
        
        return -1

    elif msg["type"] == MsgType.ERROR:
        logger.error(str(msg))

    return 0


class AIPlayer:
    def __init__(self):
        pass

    def playTurn(self, st):
        # 내가 돌을 놓을 차례. 어디디가 놓냐? -> UCT를 호출해서 반환된 좌표에 돌을 놓으면 된다.
        
        with st.board_lock:
            tmp_st = st.clone()    # rendering thread와의 Lock 문제 때문에, 여기서 한 번 clone받아 들어간다.
        m = MCTS.UCT_multi(rootstate = tmp_st, timeout = 1, max_workers = 12)
        # m = MCTS.UCT(rootstate = tmp_st, timeout = 1)
        
        logger.warning("AI choice {}".format(str(m)))
        st.putStone(m)
        logger.debug("\n" + str(st))
        nm.send({
            "type": ClntType.PUT,
            "point": m
        })
        st.cnt_available_points = None

    def clickEventHandler(self, st, i, j):
        print("AI Player!")


class HumanPlayer:
    def __init__(self):
        pass
    
    def playTurn(self, st):
        # 내가 돌을 놓는 것은 clickEventHandler가 처리
        pass

    def clickEventHandler(self, st, i, j):
        if st.my_color is None:
            print("not started")
            return
        elif st.playerJustMoved == st.my_color:
            # 내가 방금 놓은거니까 상대턴.
            print("opponent's turn")
            return

        point = [i, j]
        if point in st.cnt_available_points:    # 원래는 여기서 available인지 검사해야함.
            st.putStone(point)
            nm.send({
                "type": ClntType.PUT,
                "point": point
            })
            st.cnt_available_points = None
        else:
            print("not available point")



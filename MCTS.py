# UCT Monte Carlo Tree Search algorithm
from math import *
import random
import time
from multiprocessing import Pool
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from protocol_enum import Color
from OthelloState import OthelloState, DummyLock


class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.getAvailPoints() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def addChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s


def _UCT(rootstate, timeout, verbose = 0):
    """
    UCT는 win/visit을 바탕으로 노드를 선택해가며 말단 노드까지 내려가서 Expand하는 방식이다.
    따라서 UCT의 이점을 살리려면 multiprocess 환경이라고 하더라도 process들이 내부 상태(node tree)를 유지하고 있어야 한다. 
    그래야 다음 iter 때 UCT를 사용해 노드를 선택할 수 있으니까.
    그러나 multiprocess 환경에서 node tree를 공유하면 비효율적이기 때문에, process가 각자의 내부 상태를 가지도록 해야 한다.
    이런 경우 itermax는 얼마니까 이걸 Queue에 집어넣고 하나씩 process들이 가져가게 하는 것 보다, timeout 동안 알아서 돌아가게 하고
    timeout되면 결과를 취합하는 방식이 더 효율적이다. 실제로 게임에서 timeout이 문제이지 몇 번 반복했냐가 문제는 아니니까.
    """

    rootnode = Node(state = rootstate)

    start_time = time.time()
    while (time.time() - start_time < timeout):
        node = rootnode
        state = rootstate.clone()

        # Select
        # 현재 노드가 leaf(GAMEOVER)가 아니면서, 모든 available points에 한 번 이상 방문한 경우. 말단 노드 중 하나를 UCB1을 이용해 선택하고, 거기서부터 Expand해야하므로.
        # 한 iter가 끝나면 다시 rootnode로 되돌아가므로, 이렇게 해도 어느 한 쪽에 편향되지 않는다.
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.putStone(node.move)

        # Expand
        # 노드 객체는 생성되면서 untiredMoves를 계산해서 가지고 있게된다. GAMEOVER나 NOPOINT가 아니면 untiredMoves가 항상 있음.
        # NOPOINT일 때도 untiredMoves가 비어있게 되므로 leaf node가 되는데, 시뮬레이션만 중단하고 그 시점의 돌 개수를 세어서 승/패를 판단하므로 큰 영향은 없을 것 같음.
        if node.untriedMoves != []:
            m = random.choice(node.untriedMoves)
            state.putStone(m)
            node = node.addChild(m,state)
        # 여기서 랜덤하게 하나의 availble_point를 골라서 expand한 다음, node를 새로 생성한 자식 노드로 변경해준다.(즉 expand되는 노드는 한 iter 당 하나.)
        
        # Rollout(Simulate) - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        # expand된 노드부터(여기서는 state가 expand된 node라고 보면 됨.) AvailPoints를 계산하고 랜덤하게 다음 수를 선택하는 방식으로 끝까지 진행해본다.
        while state.getAvailPoints() != []: # while state is non-terminal
            # putStone하니까 state(board)는 새로 갱신됨. 돌을 놓으면서 시뮬레이션해가는거지...
            state.putStone(random.choice(state.getAvailPoints()))
        
        # 그래서 이 시점에서 state는 GAMEOVER 상태(승, 패가 결정됨) 즉 leaf가 된다.
        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            # state는 게임 종료 상태. node를 거슬러 올라가면서 게임 결과를 update(visit++)해준다. getResult는 내가 이겼냐 상대방이 이겼냐를 playerJustMoved의 관점에서 반환.
            node.update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose == 2): print(rootnode.TreeToString(0))
    elif (verbose == 1): print(rootnode.ChildrenToString())
    
    return rootnode.childNodes


def UCT(rootstate, timeout, verbose = 1):
    child_nodes = _UCT(rootstate, timeout, verbose)
    return sorted(child_nodes, key = lambda c: c.visits)[-1].move # return the move that was most visited

def UCT_multi(rootstate, timeout, max_workers, verbose = 1):
    tmp_st = rootstate.clone()
    tmp_st.board_lock = DummyLock()    # threading.Lock()은 pickle이 불가능해서 에러나기 때문에 바꿔준다.
    processing_results = []
    with ProcessPoolExecutor(max_workers) as e:
        # max worker만큼 작업을 시작.
        futures = [e.submit(_UCT, tmp_st, timeout, False) for _ in range(max_workers)]
        for future in as_completed(futures):
            # 각 process들이 끝나는 대로, result_list에 추가.
            processing_results.append(future.result())

    return assembleMultiResult(processing_results, verbose)


def assembleMultiResult(multi_child_nodes, verbose = 1):
    assembled_result = {}    # move를 key로 하고 (W,V)를 value로 하는 dict
    for child_nodes in multi_child_nodes:
        for node in child_nodes:
            if node.move in assembled_result:
                assembled_result[node.move].wins += node.wins
                assembled_result[node.move].visits += node.visits
            else:
                assembled_result[node.move] = node
    
    if verbose == 1:
        for node in assembled_result.values():
            print(node)
    return sorted(assembled_result.values(), key = lambda x: x.visits)[-1].move


def UCTPlayGame():
    st = OthelloState(8)
    max_workers = 12
    while (st.getAvailPoints() != []):
        print(str(st))
        if st.playerJustMoved == 1:
            m = UCT(rootstate = st, timeout = 2) # play with values for itermax and verbose = True
        else:
            m = UCT_multi(rootstate = st, timeout = 2, max_workers = max_workers)
        print("Best Move: ", m , "\n")
        st.putStone(m)

    if st.GetResult(st.playerJustMoved) == 1.0:
        print("Player " + str(st.playerJustMoved) + " wins!")
    elif st.GetResult(st.playerJustMoved) == 0.0:
        print("Player " + str(3 - st.playerJustMoved) + " wins!")
    else: print("Nobody wins!")

if __name__ == "__main__":
    UCTPlayGame()



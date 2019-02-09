# UCT Monte Carlo Tree Search algorithm
from math import *
import random

import numpy as np

from protocol_enum import Color
from OthelloState import OthelloState


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
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
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


def UCT(rootstate, itermax, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    rootnode = Node(state = rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.clone()

        # Select
        # 현재 노드가 leaf(GAMEOVER)가 아니면서, 모든 available points에 대한 노드가 있는 경우.
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.putStone(node.move)

        # Expand
        # 노드 객체는 생성되면서 untiredMoves를 계산해서 가지고 있게된다. GAMEOVER나 NOPOINT가 아니면 untiredMoves가 항상 있음.
        # NOPOINT일 때도 untiredMoves가 비어있게 되므로 leaf node가 되는데, 시뮬레이션만 중단하고 그 시점의 돌 개수를 세어서 승/패를 판단하므로 큰 영향은 없을 것 같음.
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal) 게임 오버가 아니면
            m = random.choice(node.untriedMoves)    # 랜덤하게 하나 골라서
            state.putStone(m)    # 움직이고, 변경된 state를 node의 Child로 추가.
            node = node.AddChild(m,state) # add child and descend tree
        # 여기서 랜덤하게 하나 골라서 expand한 다음.(즉 expand되는 노드는 한 iter 당 하나.)
        
        # node.untiredMoves == state.getAvailPoints다. 애초에 초기화 할 때 이렇게 초기화함.
        # Rollout(Simulate) - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.getAvailPoints() != []: # while state is non-terminal
            # putStone하니까 state(board)는 새로 갱신됨. 돌을 놓으면서 시뮬레이션해가는거지...
            state.putStone(random.choice(state.getAvailPoints()))
        # expand된 노드부터(여기서는 state가 expand된 node라고 보면 됨.) AvailPoints를 계산하고 랜덤하게 다음 수를 선택하는 방식으로 끝까지 진행해본다.
        
        # 그래서 이 시점에서 state는 GAMEOVER 상태(승, 패가 결정됨) 즉 leaf가 된다.
        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            # getResult는 내가 이겼냐 상대방이 이겼냐를 반환.
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            # node부터 parent로 하나씩 갱신하면서 올라가준다.
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print(rootnode.TreeToString(0))
    else: print(rootnode.ChildrenToString())

    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited

def UCTPlayGame():
    cnt_state = OthelloState(8)
    while (cnt_state.getAvailPoints() != []):
        print(str(cnt_state))
        if cnt_state.playerJustMoved == 1:
            m = UCT(rootstate = cnt_state, itermax = 100, verbose = False) # play with values for itermax and verbose = True
        else:
            # m1 = int(input())
            # m2 = int(input())
            # m = (m1, m2)
            m = UCT(rootstate = cnt_state, itermax = 100, verbose = False)
        print(m)
        print("Best Move: ", m , "\n")
        cnt_state.putStone(m)

    if cnt_state.GetResult(cnt_state.playerJustMoved) == 1.0:
        print("Player " + str(cnt_state.playerJustMoved) + " wins!")
    elif cnt_state.GetResult(cnt_state.playerJustMoved) == 0.0:
        print("Player " + str(3 - cnt_state.playerJustMoved) + " wins!")
    else: print("Nobody wins!")

if __name__ == "__main__":
    UCTPlayGame()



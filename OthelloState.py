from threading import Lock

import numpy as np

from protocol_enum import Color
from processing import getAvailablePosition

class OthelloState:
    def __init__(self, sz = 8):
        assert sz == int(sz) and sz % 2 == 0 # size must be integral and even

        self.playerJustMoved = Color.WHITE # 시작할 때 BLACK 부터 움직여야 하므로.
        self.size = sz
        self.board_lock = Lock()
        # self.board = np.zeros((8,8), dtype=int)
        self.board = []
        for _ in range(sz):
            self.board.append([0]*sz)
        self.board[int(sz/2)][int(sz/2)-1] = self.board[int(sz/2)-1][int(sz/2)] = Color.BLACK
        self.board[int(sz/2)][int(sz/2)] = self.board[int(sz/2)-1][int(sz/2)-1] = Color.WHITE
        self.my_color = None
        self.op_color = None
        self.cnt_available_points = None

    def clone(self):
        """ Create a deep clone of this game state.
        """
        st = OthelloState()
        st.playerJustMoved = self.playerJustMoved
        st.board = [self.board[i][:] for i in range(self.size)]
        st.size = self.size
        return st
        
    def putStone(self, move):
        """ Update a state by carrying out the given move.
            Must update playerToMove.
        """
        (x,y)=(move[0],move[1])
        assert x == int(x) and y == int(y) and self.IsOnBoard(x,y) and self.board[x][y] == 0
        m = self.GetAllSandwichedCounters(x,y)
        self.playerJustMoved = 3 - self.playerJustMoved
        
        with self.board_lock:
            self.board[x][y] = self.playerJustMoved
            for (a,b) in m:
                self.board[a][b] = self.playerJustMoved
    
    def getAvailPoints(self):
        """ Get all possible moves from this state.
        """
        # print([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 0 and self.ExistsSandwichedCounter(x,y)])
        # print(getAvailablePosition(self.board, 3 - self.playerJustMoved))
        return [(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 0 and self.ExistsSandwichedCounter(x,y)]

    def AdjacentToEnemy(self,x,y):
        """ Speeds up getAvailPoints by only considering squares which are adjacent to an enemy-occupied square.
        """
        for (dx,dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)]:
            if self.IsOnBoard(x+dx,y+dy) and self.board[x+dx][y+dy] == self.playerJustMoved:
                return True
        return False
    
    def AdjacentEnemyDirections(self,x,y):
        """ Speeds up getAvailPoints by only considering squares which are adjacent to an enemy-occupied square.
        """
        es = []
        for (dx,dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)]:
            if self.IsOnBoard(x+dx,y+dy) and self.board[x+dx][y+dy] == self.playerJustMoved:
                es.append((dx,dy))
        return es
    
    def ExistsSandwichedCounter(self,x,y):
        """ Does there exist at least one counter which would be flipped if my counter was placed at (x,y)?
        """
        for (dx,dy) in self.AdjacentEnemyDirections(x,y):
            if len(self.SandwichedCounters(x,y,dx,dy)) > 0:
                return True
        return False
    
    def GetAllSandwichedCounters(self, x, y):
        """ Is (x,y) a possible move (i.e. opponent counters are sandwiched between (x,y) and my counter in some direction)?
        """
        sandwiched = []
        for (dx,dy) in self.AdjacentEnemyDirections(x,y):
            sandwiched.extend(self.SandwichedCounters(x,y,dx,dy))
        return sandwiched

    def SandwichedCounters(self, x, y, dx, dy):
        """ Return the coordinates of all opponent counters sandwiched between (x,y) and my counter.
        """
        x += dx
        y += dy
        sandwiched = []
        while self.IsOnBoard(x,y) and self.board[x][y] == self.playerJustMoved:
            sandwiched.append((x,y))
            x += dx
            y += dy
        if self.IsOnBoard(x,y) and self.board[x][y] == 3 - self.playerJustMoved:
            return sandwiched
        else:
            return [] # nothing sandwiched

    def IsOnBoard(self, x, y):
        return x >= 0 and x < self.size and y >= 0 and y < self.size
    
    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        # TODO : 게임 결과가 이것 말고도 더 있지.
        # 내 돌의 수
        jmcount = len([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == playerjm])
        # 상대방 돌의 수
        notjmcount = len([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 3 - playerjm])
        # 내가 이겼냐 상대방이 이겼냐를 리턴.
        if jmcount > notjmcount: return 1.0
        elif notjmcount > jmcount: return 0.0
        else: return 0.5 # draw

    def __repr__(self):
        s= ""
        for r in range(self.size):
            for c in range(self.size):
                s += ".OX"[self.board[r][c]]
            s += "\n"
        return s


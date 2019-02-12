from threading import Lock

# import numpy as np

from protocol_enum import Color
import processing

class OthelloState:
    def __init__(self, sz = 8):
        assert sz == int(sz) and sz % 2 == 0 # size must be integral and even

        # 항상 BLACK부터 시작하므로, WHITE로 설정. 첫 턴의 playerJustMoved가 WHITE이니 첫 턴은 BLACK의 턴이 되어 제대로 게임이 진행된다.
        self.playerJustMoved = Color.WHITE
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
        self.turn_num = 0

    def clone(self):
        """ Create a deep clone of this game state.
        """
        st = OthelloState()
        st.playerJustMoved = self.playerJustMoved
        st.board = [self.board[i][:] for i in range(self.size)]
        st.size = self.size
        st.turn_num = self.turn_num
        st.cnt_available_points = self.cnt_available_points
        return st
        
    def turnOver(self):
        # switch user
        self.playerJustMoved = 3 - self.playerJustMoved    # 1 아니면 2 이기 때문에 3 - 로 반대 색상을 구할 수 있음.
        self.turn_num += 1

    def putStone(self, move):
        self.turnOver()

        with self.board_lock:
            i, j = move
            self.board[i][j] = self.playerJustMoved
            reversed_points = processing.getReversedPosition(self.board, self.playerJustMoved, move[0], move[1])
            
            for i, j in reversed_points:
                self.board[i][j] = self.playerJustMoved


        # (x,y)=(move[0],move[1])
        # assert x == int(x) and y == int(y) and self.IsOnBoard(x,y) and self.board[x][y] == 0
        # m = self.GetAllSandwichedCounters(x,y)
        # self.playerJustMoved = 3 - self.playerJustMoved

        # with self.board_lock:
        #     self.board[x][y] = self.playerJustMoved
        #     for (a,b) in m:
        #         self.board[a][b] = self.playerJustMoved
    
    def getAvailPoints(self):
        # TODO : DEBUG용.
        # r1 = [(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 0 and self.ExistsSandwichedCounter(x,y)]
        # r2 = processing.getAvailablePosition(self.board, 3 - self.playerJustMoved)
        # if (r1 != r2):
        #     print(r1)
        #     print(r2)
        #     raise Exception
        return processing.getAvailablePosition(self.board, 3 - self.playerJustMoved)

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
        # GAMEOVER는 판이 가득 찬 경우, 한 쪽이 전멸하는 경우, 둘 다 놓을 수 없는 경우 세 가지임.
        # 이 세 가지 경우 모두 돌의 개수를 세면 승/패를 판정할 수 있음. 따라서 MCTS 시뮬레이션 할 때는 이렇게 승/패를 계산해도 됨.
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


class DummyLock:
    """
    multiprocess 모듈을 사용할 때 프로세스에서 실행하는 함수에서 어떤 객체를 참조하고, 그 객체의 멤버에 threading.Lock()변수가 포함되어 있으면
    이는 pickle이 불가능하다며 에러가 발생한다. 그래서 프로세스에 넘기기 전에 동일한 인터페이스를 가지는 DummyLock으로 변경해준다.
    """
    def __enter__(self):
        return None

    def __exit__(self, type, value, traceback):
        pass

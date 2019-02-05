"""
class Board를 만들고
안에 np.zeros((8, 8), dtype=int) 하고,
__getitem__을 오버로딩해서 바로 numpy array에 접근하도록 구성하고, 
putStone이나 reverse같은걸 Board 클래스에서 처리해주면 설계상 깔끔하고 구조적으로도 더 낫다.
아니면 class Board(np.ndarray)로 상속받던가.
"""
from threading import Lock
import itertools

import pygame as pg

import protocol_enum as proto
import processing

class Square:
    stone_size = 18
    def __init__(self, rect):
        self.rect  = rect
        self.stone: proto.Color = proto.Color.EMPTY
        self.available = False

    def __eq__(self, other):
        return self.stone == other
    
    def __ne__(self, other):
        return self.stone != other

    def putStone(self, color: proto.Color):
        assert(self.stone is proto.Color.EMPTY)
        self.stone = color


def putStone(color: proto.Color, i, j):
    assert(board[i][j].stone is proto.Color.EMPTY)
    board[i][j].stone = color

def reverseStones(color: proto.Color, i, j):
    point_to_reverse = processing.getReversedPosition(board, color, i, j)
    for i, j in point_to_reverse:
        board[i][j].stone = color

def setAvailablePoints(available_points):
    for i, j in available_points:
        board[i][j].available = True

def clearAvailablePoints():
    for square in itertools.chain(*board):
        square.available = False

# board init
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
board_len = SCREEN_HEIGHT if (SCREEN_HEIGHT < SCREEN_WIDTH) else SCREEN_WIDTH
rect_len = int(board_len / 8)    # 8 * 8 board

board = []    # 2-d array.
for y_pos in range(0, board_len, rect_len):
    square_line = []
    for x_pos in range(0, board_len, rect_len):
        rect = pg.Rect(x_pos, y_pos, rect_len, rect_len)
        square_line.append(Square(rect))
    board.append(square_line)

board[3][3].stone = proto.Color.WHITE
board[3][4].stone = proto.Color.BLACK
board[4][3].stone = proto.Color.BLACK
board[4][4].stone = proto.Color.WHITE

board_lock = Lock()
"""
8*8 othello program!
"""

# 뷰와 관련된 코드는 여기에.

import itertools
import random
import threading

import pygame as pg
# from pygame.locals import *

import protocol_enum as proto
import processing
from board import *
from network import NetworkManager as nm
from logic import *
import g_val as G


pg.init()
screen = pg.display.set_mode((G.SCREEN_WIDTH, G.SCREEN_HEIGHT))
pg.display.set_caption("미치셨습니가 휴먼?")

##################################################################
# client network init

nm.initNetwork(G.HOST, G.PORT)
threading.Thread(target=nm.recvLoop, args=(handleMsg, )).start()

##################################################################
# game start

#Loop until the user clicks the close button.
DONE = False
clock = pg.time.Clock()

while not DONE:
    # This limits the while loop to a max of 10 times per second.
    # Leave this out and we will use all CPU we can.
    clock.tick(30)
    
    # Main Event Loop
    for event in pg.event.get():
        if event.type == pg.QUIT:
            DONE = True
            nm.loop_running = False
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == G.MOUSE_LEFT:
            # pos to array index
            pos = event.pos    # == pg.mouse.get_pos()
            i, j = int(pos[1] / rect_len), int(pos[0] / rect_len)
            if 0 <= i <= 7 and 0 <= j <= 7:
                clickEventHandler(i, j)
            else:
                print("not implemented.")


    # All drawing code happens after the for loop and but
    # inside the main while done==False loop.
    screen.fill(G.GRAY_221)
    board_lock.acquire()
    for square in itertools.chain(*board):
        pg.draw.rect(screen, G.GRAY_150, square.rect, 1)
        if square.stone == proto.Color.BLACK:
            pg.draw.circle(screen, pg.Color("black"), square.rect.center, Square.stone_size)
        elif square.stone == proto.Color.WHITE:
            pg.draw.circle(screen, pg.Color("white"), square.rect.center, Square.stone_size)
        
        if square.available:
            pg.draw.rect(screen, pg.Color("green"), square.rect, 1)
    board_lock.release()

    # Go ahead and update the screen with what we've drawn.
    # This MUST happen after all the other drawing commands.
    pg.display.flip()
  
# Be IDLE friendly
pg.quit()



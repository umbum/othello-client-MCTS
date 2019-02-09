"""
8*8 othello program!
"""

# 뷰와 관련된 코드는 여기에.
import sys
import itertools
import random
import threading

import pygame as pg
# from pygame.locals import *

import protocol_enum as proto
import processing
from network import NetworkManager as nm
from Player import *
import g_val as G
from OthelloState import OthelloState


pg.init()
screen = pg.display.set_mode((G.SCREEN_WIDTH, G.SCREEN_HEIGHT))
pg.display.set_caption("미치셨습니가 휴먼?")
font = pg.font.SysFont("consolas", 36)

##################################################################
# Othello Game board, state init

st = OthelloState(G.BOARD_SIZE)

##################################################################
# client network init

if len(sys.argv) >= 2 and sys.argv[1] == "-p":
    player = HumanPlayer()
else:
    player = AIPlayer()
    pg.display.set_caption("미치셨습니가 휴먼? - AI")

nm.initNetwork(G.HOST, G.PORT)
nm_t = threading.Thread(target=nm.recvLoop, args=(handleMsg, st, player, ))
nm_t.daemon = True
nm_t.start()


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
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == G.MOUSE_LEFT:
            # pos to array index
            pos = event.pos    # == pg.mouse.get_pos()
            i, j = int(pos[1] / G.RECT_LEN), int(pos[0] / G.RECT_LEN)
            if 0 <= i <= 7 and 0 <= j <= 7:
                player.clickEventHandler(st, i, j)
            else:
                print("not implemented.")


    # All drawing code happens after the for loop and but
    # inside the main while done==False loop.
    screen.fill(G.GRAY_221)
    black_count = 0
    white_count = 0
    st.board_lock.acquire()    # timeout 걸면 rendering thread가 멈추지 않도록 할 수 있을듯.
    for i in range(G.BOARD_SIZE):
        for j in range(G.BOARD_SIZE):
            y_pos, x_pos = i * G.RECT_LEN, j * G.RECT_LEN
            pg.draw.rect(screen, G.GRAY_150, (x_pos, y_pos, G.RECT_LEN, G.RECT_LEN), 1)
            if st.board[i][j] == proto.Color.BLACK:
                pg.draw.circle(screen, pg.Color("black"), (x_pos + int(G.RECT_LEN / 2), y_pos + int(G.RECT_LEN / 2)), G.STONE_SIZE)
                black_count += 1
            elif st.board[i][j] == proto.Color.WHITE:
                pg.draw.circle(screen, pg.Color("white"), (x_pos + int(G.RECT_LEN / 2), y_pos + int(G.RECT_LEN / 2)), G.STONE_SIZE)
                white_count += 1
    st.board_lock.release()
    text_b = font.render("O : {}".format(black_count), True, pg.Color("black"))
    text_w = font.render("O : {}".format(white_count), True, pg.Color("white"))
    screen.blit(text_b, (G.BOARD_LEN + 10, 10))
    screen.blit(text_w, (G.BOARD_LEN + 10, 60))

    # hello_msg = font.render("별풍선 감사합니다", True, pg.Color("black"))
    # screen.blit(hello_msg, (G.BOARD_LEN + 10, 150))
    # Go ahead and update the screen with what we've drawn.
    # This MUST happen after all the other drawing commands.
    pg.display.flip()
  
# Be IDLE friendly
nm.loop_running = False
pg.quit()
exit()

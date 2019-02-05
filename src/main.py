import itertools
import random
import threading

import pygame as pg
# from pygame.locals import *

import protocol_enum as proto
import processing
from board import *
from network import NetworkManager as nm

# Initialize the game engine
pg.init()
 
# Define the colors we will use in RGB format
GRAY_221  = (221, 221, 221)
GRAY_150  = (150, 150, 150)
 
# Set the height and width of the screen
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  
pg.display.set_caption("미치셨습니가 휴먼?")

##################################################################
# client network init

HOST = '127.0.0.1'
PORT = 8472
nm.initNetwork(HOST, PORT)

threading.Thread(target=nm.recvLoop).start()

##################################################################
# game start

MOUSE_LEFT  = 1
MOUSE_RIGHT = 3

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
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == MOUSE_LEFT:
            # pos to array index
            pos = event.pos    # == pg.mouse.get_pos()
            i, j = int(pos[1] / rect_len), int(pos[0] / rect_len)
            if 0 <= i <= 7 and 0 <= j <= 7:
                if nm.my_turn:
                    board_lock.acquire()
                    if board[i][j].available == True:
                        clearAvailablePoints()
                        putStone(nm.my_color, i, j)
                        reverseStones(nm.my_color, i, j)
                        nm.send({
                            "type": proto.ClntType.PUT,
                            "point": (i, j)
                        })
                        nm.my_turn = False
                    else:
                        print("not available point")
                    board_lock.release()
                else:
                    print("opponent's turn")
            else:
                print("not implemented.")
    
    if nm.my_turn:
        board_lock.acquire()
        
        
        if board[i][j].available == True:
            clearAvailablePoints()
            putStone(nm.my_color, i, j)
            reverseStones(nm.my_color, i, j)
            nm.send({
                "type": proto.ClntType.PUT,
                "point": (i, j)
            })
            nm.my_turn = False
        else:
            print("not available point")
        board_lock.release()


    
    # All drawing code happens after the for loop and but
    # inside the main while done==False loop.
    screen.fill(GRAY_221)
    board_lock.acquire()
    for square in itertools.chain(*board):
        pg.draw.rect(screen, GRAY_150, square.rect, 1)
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



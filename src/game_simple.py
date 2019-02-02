import itertools

import pygame as pg
# from pygame.locals import *

import protocol_enum as proto

MOUSE_LEFT  = 1
MOUSE_RIGHT = 3

class Square:
    stone_size = 16
    def __init__(self, rect):
        self.rect  = rect
        self.stone_color = proto.Color.EMPTY

    def putStone(self):
        self.stone_color = proto.Color.BLACK
    
    def reverseStone(self):
        pass


# Initialize the game engine
pg.init()
 
# Define the colors we will use in RGB format
GRAY_221  = (221, 221, 221)
GRAY_150  = (150, 150, 150)
 
# Set the height and width of the screen
width = 900
height = 600
screen = pg.display.set_mode((width, height))
  
pg.display.set_caption("미치셨습니가 휴먼?")
  
#Loop until the user clicks the close button.
done = False
clock = pg.time.Clock()
visibility = False

# padding = 10

board_len = height if (height < width) else width
rect_len = int(board_len / 8)    # 8 * 8 board

square_array = []    # 2-d array.


for y_pos in range(0, board_len, rect_len):
    square_line = []
    for x_pos in range(0, board_len, rect_len):
        rect = pg.Rect(x_pos, y_pos, rect_len, rect_len)
        square_line.append(Square(rect))
    square_array.append(square_line)

while not done:
    # This limits the while loop to a max of 10 times per second.
    # Leave this out and we will use all CPU we can.
    clock.tick(30)
     
    # Main Event Loop
    for event in pg.event.get():
        if event.type == pg.QUIT:
            done=True
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == MOUSE_LEFT:
            # pos to array index
            # pos = pg.mouse.get_pos()    이렇게 해도 되지만, 아래처럼.
            pos = event.pos
            i, j = int(pos[1] / rect_len), int(pos[0] / rect_len)
            print(i, j)
            square_array[i][j].putStone()
            # 동시에 여기서 프로세싱이 들어가줘야겠군.
                    

    # All drawing code happens after the for loop and but
    # inside the main while done==False loop.
    screen.fill(GRAY_221)
    
    
    # draw board (rectangles)
    for square in itertools.chain(*square_array):
        pg.draw.rect(screen, GRAY_150, square.rect, 1)
        if square.stone_color == proto.Color.BLACK:
            pg.draw.circle(screen, pg.Color("black"), square.rect.center, Square.stone_size)
        if square.stone_color == proto.Color.WHITE:
            pg.draw.circle(screen, pg.Color("white"), square.rect.center, Square.stone_size)
    

    # Go ahead and update the screen with what we've drawn.
    # This MUST happen after all the other drawing commands.
    pg.display.flip()
  
# Be IDLE friendly
pg.quit()



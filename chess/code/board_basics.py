import cv2
import numpy as np

def get_square_image(row,column,board_img):
    height, width = board_img.shape
    minX =  int(column * width / 8 ) 
    maxX = int((column + 1) * width / 8 )
    minY = int(row * width / 8 )
    maxY = int((row + 1) * width / 8 )
    square = board_img[minY:maxY, minX:maxX]
    square_without_borders = square[3:-3, 3:-3]
    return square_without_borders

def convert_row_column_to_square_name(row,column, is_white_on_bottom):
    if is_white_on_bottom == True:
        number = repr(8 - row)
        letter = str(chr(97 + column))
        return letter+number
    else:
        number = repr(row + 1)
        letter = str(chr(97 + (7 - column)))
        return letter+number

def convert_square_name_to_row_column(square_name,is_white_on_bottom):
    for row in range(8):
        for column in range(8):
            this_square_name = convert_row_column_to_square_name(row,column,is_white_on_bottom)
            if  this_square_name == square_name:
                return row,column
    return 0,0

def get_square_center_from_image_and_move(square_name, is_white_on_bottom , minX,minY,maxX,maxY):
    row,column = convert_square_name_to_row_column(square_name,is_white_on_bottom)
    
    centerX = int(minX + (column + 0.5) *(maxX-minX)/8)
    centerY = int(minY + (row + 0.5) *(maxY-minY)/8)
    return centerX,centerY

def has_square_image_changed(old_square, new_square):
    diff = cv2.absdiff(old_square,new_square)
    if diff.mean() > 8: 
        return True
    else:
        return False

def is_square_empty(square):
    return square.std() < 10 

def is_white_on_bottom(current_chessboard_image):
    m1 = get_square_image(0,0,current_chessboard_image).mean() 
    m2 = get_square_image(7,7,current_chessboard_image).mean() 
    if m1 < m2: 
        return True
    else:
        return False



def get_potential_moves(old_image,new_image,is_white_on_bottom):
    potential_starts = []
    potential_arrivals = []
    for row in range(8):
        for column in range(8):
            old_square = get_square_image(row,column,old_image)
            new_square = get_square_image(row,column,new_image)
            if has_square_image_changed(old_square, new_square):
                square_name = convert_row_column_to_square_name(row,column,is_white_on_bottom)
                square_was_empty = is_square_empty(old_square)
                square_is_empty = is_square_empty(new_square)
                if  square_was_empty == False:
                    potential_starts= np.append(potential_starts,square_name)
                if  square_is_empty== False:
                    potential_arrivals = np.append(potential_arrivals,square_name)
    return potential_starts, potential_arrivals

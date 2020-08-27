import chess 
import chess.uci 
import numpy as np
from board_basics import *
import chessboard_detection
import pyautogui
import cv2
import mss 
import time 


class Board_position:
    def __init__(self,minX,minY,maxX,maxY):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY

    def print_custom(self):
        return ("from " + str(self.minX) + "," + str(self.minY) + " to " + str(self.maxX) + ","+ str(self.maxY))

class Game_state:

    def __init__(self):
        self.we_play_white = True
        self.moves_to_detect_before_use_engine = -1 
        self.expected_move_to_detect = "" 
        self.previous_chessboard_image = [] 
        self.executed_moves = [] 
        self.engine = chess.uci.popen_engine("stockfish")
        self.board = chess.Board() 
        self.board_position_on_screen = []
        self.sct = mss.mss()
    

    def can_image_correspond_to_chessboard(self, move, current_chessboard_image):
        self.board.push(move)
        squares = chess.SquareSet(chess.BB_ALL)
        for square in squares:
            row = chess.square_rank(square)
            column = chess.square_file(square)
            piece = self.board.piece_at(square)
            shouldBeEmpty = (piece == None)
                
            if self.we_play_white == True:
                rowOnImage = 7-row
                columnOnImage = column
            else:
                rowOnImage = row
                columnOnImage = 7-column

            squareImage = get_square_image(rowOnImage,columnOnImage,current_chessboard_image)

            if is_square_empty(squareImage) != shouldBeEmpty:
                self.board.pop()
                #print( "Problem with : ", self.board.uci(move) ," the square ", rowOnImage, columnOnImage, "should ",'be empty' if shouldBeEmpty else 'contain a piece')
                return False
        #print("Accepted move", self.board.uci(move))
        self.board.pop()
        return True


    def get_valid_move(self, potential_starts, potential_arrivals, current_chessboard_image):
        #print("Starts and arrivals:",potential_starts, potential_arrivals)

        valid_move_string = ""
        for start in potential_starts:
            for arrival in potential_arrivals:
                uci_move = start+arrival
                move = chess.Move.from_uci(uci_move)
                if move in self.board.legal_moves:
                    if self.can_image_correspond_to_chessboard(move,current_chessboard_image):
                        valid_move_string = uci_move
                else:
                    uci_move_promoted = uci_move + 'q'
                    promoted_move = chess.Move.from_uci(uci_move_promoted)
                    if promoted_move in self.board.legal_moves:
                        if self.can_image_correspond_to_chessboard(move,current_chessboard_image):
                            valid_move_string = uci_move_promoted
                            #print("There has been a promotion to queen")
                    
        if ("e1" in potential_starts) and ("h1" in potential_starts) and ("f1" in potential_arrivals) and ("g1" in potential_arrivals):
            valid_move_string = "e1g1"

        if ("e1" in potential_starts) and ("a1" in potential_starts) and ("c1" in potential_arrivals) and ("d1" in potential_arrivals):
            valid_move_string = "e1c1"

        if ("e8" in potential_starts) and ("h8" in potential_starts) and ("f8" in potential_arrivals) and ("g8" in potential_arrivals):
            valid_move_string = "e8g8"

        if ("e8" in potential_starts) and ("a8" in potential_starts) and ("c8" in potential_arrivals) and ("d8" in potential_arrivals):
            valid_move_string = "e8c8"
        
        return valid_move_string

    def register_move_if_needed(self):             
        new_board = chessboard_detection.get_chessboard(self)
        potential_starts, potential_arrivals = get_potential_moves(self.previous_chessboard_image,new_board,self.we_play_white)
        valid_move_string1 = self.get_valid_move(potential_starts,potential_arrivals,new_board)
        #print("Valid move string 1:" + valid_move_string1)

        if len(valid_move_string1) > 0:
            time.sleep(0.1)    
            'Check that we were not in the middle of a move animation'
            new_board = chessboard_detection.get_chessboard(self)
            potential_starts, potential_arrivals = get_potential_moves(self.previous_chessboard_image,new_board,self.we_play_white)
            valid_move_string2 = self.get_valid_move(potential_starts,potential_arrivals,new_board)
            #print("Valid move string 2:" + valid_move_string2)
            if valid_move_string2 != valid_move_string1:
                return False, "The move has changed"
            valid_move_UCI = chess.Move.from_uci(valid_move_string1)
            valid_move_registered = self.register_move(valid_move_UCI,new_board) 
            return True, valid_move_string1
        return False, "No move found"
        
        

    def register_move(self,move,board_image):
        if move in self.board.legal_moves:
            #print("Move has been registered")
            self.executed_moves= np.append(self.executed_moves,self.board.san(move))
            self.board.push(move)
            self.moves_to_detect_before_use_engine = self.moves_to_detect_before_use_engine - 1
            self.previous_chessboard_image = board_image
            return True
        else:
            return False

    def get_square_center(self,square_name):
        row,column = convert_square_name_to_row_column(square_name,self.we_play_white)
        position = self.board_position_on_screen
        centerX = int(position.minX + (column + 0.5) *(position.maxX-position.minX)/8)
        centerY = int(position.minY + (row + 0.5) *(position.maxY-position.minY)/8)
        return centerX,centerY

    def play_next_move(self):
        #print("\nUs to play: Calculating next move")
        self.engine.position(self.board)
        engine_process = self.engine.go(movetime=200)
        best_move = engine_process.bestmove
        best_move_string = best_move.uci()

        origin_square = best_move_string[0:2]
        destination_square = best_move_string[2:4]
        
        centerXOrigin, centerYOrigin = self.get_square_center(origin_square)
        centerXDest, centerYDest = self.get_square_center(destination_square)

        pyautogui.moveTo(centerXOrigin, centerYOrigin, 0.01)
        pyautogui.dragTo(centerXOrigin, centerYOrigin + 1, button='left', duration=0.01) 
        pyautogui.dragTo(centerXDest, centerYDest, button='left', duration=0.3)

        if best_move.promotion != None:
            #print("Promoting to a queen")
            cv2.waitKey(100)
            pyautogui.dragTo(centerXDest, centerYDest + 1, button='left', duration=0.1) 

        #print("Done playing move",origin_square,destination_square)
        self.moves_to_detect_before_use_engine = 2
        return


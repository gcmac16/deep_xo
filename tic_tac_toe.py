import pandas as pd
import numpy as np
import math

class ClassicBoard():
    
    def __init__(self, board_id):
        self.board = np.array(np.zeros((3,3)))
        self.board_id = board_id
        
        self.won = False
        self.winner = ''
        self.game_over = False
        
        self.remaining_squares = 9
        
        self._lab2int = {'X':1, 'O':2}
        self._int2lab = {1:'X', 2:'O', 0:'-'}
        
    def play(self, pos, label):
        if self.game_over:
            raise ValueError(f"The game on board {self.board_id} has ended")
        if isinstance(pos, int):
            pos = (math.floor(pos / 3), pos % 3)
        if self.board[pos[0], pos[1]] > 0:
            raise ValueError(f"Position {(pos[0],pos[1])} on board {self.board_id} has already been played")
        if label not in {'X','O'}:
            raise ValueError("Label must be in {'X','O'}")
        
        self.board[pos[0], pos[1]] = self._lab2int[label]
        self._update_state(label)
        
    def _update_state(self, label):
        self.remaining_squares -= 1
        
        label_board = self.board == self._lab2int[label]
        if (np.any(np.sum(label_board, axis=0) == 3) or
            np.any(np.sum(label_board, axis=1) == 3) or
            sum([label_board[i,i] for i in range(3)]) == 3 or
            sum([label_board[i,2-i] for i in range(3)]) == 3):
            # if a player has won, set appropriate flags
            self.won = True
            self.winner = label
            self.game_over = True
            
        if self.remaining_squares == 0:
            print ("Cat Game")
            self.game_over = True
            
    def __str__(self):
        lines = []
        for i in range(3):
            lines.append(' '.join([self._int2lab[num] for num in self.board[i,:]]))
            
        return '\n'.join(lines)
                      
        
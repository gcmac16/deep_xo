import pandas as pd
import numpy as np
import math
import pickle
from operator import itemgetter

class ClassicBoard():
    
    def __init__(self, board_id):
        self.board = np.array(np.zeros((3,3)))
        self.board_id = board_id
        
        self.won = False
        self.winner = ''
        self.game_over = False
        
        self.remaining_squares = set(range(9))
        
        self._lab2int = {'X':1, 'O':2}
        self._int2lab = {1:'X', 2:'O', 0:'-'}
        
        self.history = []
        
    def play(self, pos, label):
        if self.game_over:
            raise ValueError(f"The game on board {self.board_id} has ended")
            
        if isinstance(pos, (int, np.int64)):
            pos_tup = (math.floor(pos / 3), pos % 3)
            pos_int = pos
        if isinstance(pos, tuple):
            pos_tup = pos
            pos_int = 3*pos[0] + pos[1]
            
        if self.board[pos_tup[0], pos_tup[1]] > 0:
            raise ValueError(f"Position {(pos_tup[0],pos_tup[1])} on board {self.board_id} has already been played")
            
        if label not in {'X','O'}:
            raise ValueError("Label must be in {'X','O'}")
        
        self.board[pos_tup[0], pos_tup[1]] = self._lab2int[label]
        self.history.append((pos_tup, self._lab2int[label]))
        
        self._update_state(pos_int, label)
        
    def _update_state(self, pos, label):
        self.remaining_squares.remove(pos)
        
        label_board = self.board == self._lab2int[label]
        if (np.any(np.sum(label_board, axis=0) == 3) or
            np.any(np.sum(label_board, axis=1) == 3) or
            sum([label_board[i,i] for i in range(3)]) == 3 or
            sum([label_board[i,2-i] for i in range(3)]) == 3):
            # if a player has won, set appropriate flags
            self.won = True
            self.winner = label
            self.game_over = True
            
        if len(self.remaining_squares) == 0:
            self.game_over = True
            
    def undo_move(self):
        if len(self.history) == 0:
            return
        
        last_move, last_player = self.history[-1]
        self.history = self.history[:-1]
        self.game_over = False
        self.board[(last_move[0], last_move[1])] = 0
        self.remaining_squares.add(last_move[0]*3 + last_move[1])
    
    def __str__(self):
        lines = []
        for i in range(3):
            lines.append(' '.join([self._int2lab[num] for num in self.board[i,:]]))
            
        return '\n'.join(lines)
                      
class UltimateBoard():
    
    def __init__(self, x_turn=True):
        if not isinstance(x_turn, bool):
            raise ValueError("x_turn must be boolean")
        self.boards = {i:ClassicBoard(i) for i in range(9)}
        self.meta_board = ClassicBoard('meta_board')
        self.game_over = False
        self.won = False
        self.active_boards = set(range(9))
        self.x_turn = x_turn 
        self.history = []
        self.meta_history = []
        self.winner = None
   #     self.model = pickle.load(open('gbm_x_wins','rb'))
        self._int2lab = {1:'X', 2:'O', 0:'-'}
        
    def play(self, board, pos, label):
        if board not in self.active_boards:
            raise ValueError("That board is not in play")
            
        if isinstance(pos, tuple):
            pos = 3*pos[0] + pos[1]
            
        if ((self.x_turn and label != 'X') 
            or (not self.x_turn and label != 'O')):
            raise ValueError("It is the other player's turn")
            
        self.boards[board].play(pos, label)
        self._update_state(board, pos, label)
        
    def _update_state(self, board, pos, label):
        '''
        Update state assuming successful play 00
        '''
        
        b = self.boards[board]
        self.history.append((board, pos, {'X':1, 'O':2}[label]))
        
        if b.game_over:
            if b.won:
                self.meta_board.play(board, label)
            
            if self.boards[pos].game_over:
                self.active_boards = {i for i in range(9) \
                                      if not self.boards[i].game_over}
            else:
                self.active_boards = {pos}
            
        else:
            if self.boards[pos].game_over:
                self.active_boards = {i for i in range(9) \
                                      if not self.boards[i].game_over}
            else:
                self.active_boards = {pos}
                
        if len(self.active_boards) == 0:
            self.winner = 'Cat'
            self.game_over = True
   
        if self.meta_board.game_over:
            if self.meta_board.won:
                self.winner = label
            else:
                self.winner = 'Cat'
                
            self.game_over = True
            self.won = True
        
        self.meta_history.append(self.meta_board.board.flatten())
        self._flip_turn()
        
    def get_history(self):
        big_board = np.zeros(81)
        meta_board = np.zeros(9)
        
        final_res = []
        
        # mv is list of tuples (board (int), pos (int), label (int))
        for i, mv in enumerate(self.history):
            big_board[mv[0]*9 + mv[1]] = mv[2]
            app_list = list(big_board) + list(self.meta_history[i])
            if self.winner is not None:
                app_list.append(self.winner)
            final_res.append(app_list)
            
        return final_res
    
    def undo_move(self):
        if len(self.history) == 0:
            raise ValueError("No moves to undo")
            
        board, cell, player = self.history[-1]
        self.boards[board].undo_move()
        self.history = self.history[:-1]
        
        # need early return for checking first move
        # comes up when playing computer vs. computer
        try:
            last_valid_move = self.history[-1]
        except IndexError:
            self.x_turn = self._int2lab[player] == 'X'
            self.active_boards = set(range(9))
            return
        
        lv_board, lv_cell, lv_player = last_valid_move
        self.x_turn = lv_player == 2 
        
        if self.boards[lv_cell].game_over:
            self.active_boards = {i for i in range(9) \
                                  if not self.boards[i].game_over}
        else:
            self.active_boards = {lv_cell}
        
        last_meta_board = self.meta_history[-1]
        self.meta_history = self.meta_history[:-1]
        
        if list(last_meta_board) != list(self.meta_history[-1]): 
            self.meta_board.undo_move()
            
    def make_move(self, label, kind='model'):
        # TODO: evaluate every move and return the best to play in form of board(int), pos(int)
        mv_value = []
        pred_idx = 0 if label == 'O' else 1
        for brd_id in self.active_boards:
            rm_sqrs = self.boards[brd_id].remaining_squares
            for sq in rm_sqrs:
                self.play(brd_id, sq, label)
                pred = self.model.predict_proba(np.array(self.get_history()[-1]).reshape(1,-1))[0][pred_idx]
                mv_value.append((brd_id, sq, pred))
                self.undo_move()
        
        mv_value = sorted(mv_value, key=itemgetter(2), reverse=True)
        
        idx = 0 if kind == 'model' else np.random.randint(len(mv_value))
        return mv_value[idx]
    
    def _flip_turn(self):
        self.x_turn = not self.x_turn
    
    def __str__(self):
        board_strs = [self.boards[i].__str__() for i in range(9)]
        
        all_rows = []
        for i in range(0,9,3):
            row = board_strs[i:i+3]
            top_rows = ['|'.join(r.split('\n')[i] for r in row) \
                        for i in range(3)]
            all_rows.append('\n'.join(top_rows))
        
        return ('\n' + '-'*17 + '\n').join(all_rows)
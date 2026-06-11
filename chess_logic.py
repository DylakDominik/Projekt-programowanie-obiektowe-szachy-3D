import copy

# klasa figury

class Piece:
    def __init__(self, color, x, y):
        self.color = color  
        self.x = x
        self.y = y
        self.has_moved = False  

    def get_valid_moves(self, board):
        return []

    def __repr__(self):
        return f"{self.color[0].upper()}-{self.__class__.__name__[0]}"

# logika konkretnych figur

class Pawn(Piece):
    def get_valid_moves(self, board):
        moves = []
        direction = 1 if self.color == 'white' else -1
        start_row = 1 if self.color == 'white' else 6
        
        if board.get_piece(self.x, self.y + direction) is None:
            moves.append((self.x, self.y + direction))
            if self.y == start_row and board.get_piece(self.x, self.y + 2 * direction) is None:
                moves.append((self.x, self.y + 2 * direction))
        
        for dx in [-1, 1]:
            target_x = self.x + dx
            target_y = self.y + direction
            if 0 <= target_x < 8 and 0 <= target_y < 8:
                target_piece = board.get_piece(target_x, target_y)
                
                if target_piece is not None and target_piece.color != self.color:
                    moves.append((target_x, target_y))
                
                elif getattr(board, 'en_passant_target', None) == (target_x, target_y):
                    moves.append((target_x, target_y))        
        return moves

class Rook(Piece):
    def get_valid_moves(self, board):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] 
        for dx, dy in directions:
            for step in range(1, 8):
                target_x = self.x + dx * step
                target_y = self.y + dy * step
                if 0 <= target_x < 8 and 0 <= target_y < 8:
                    target_piece = board.get_piece(target_x, target_y)
                    if target_piece is None:
                        moves.append((target_x, target_y))
                    elif target_piece.color != self.color:
                        moves.append((target_x, target_y))
                        break
                    else:
                        break
                else:
                    break
        return moves

class Knight(Piece):
    def get_valid_moves(self, board):
        moves = []
        knight_moves = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
        for dx, dy in knight_moves:
            target_x = self.x + dx
            target_y = self.y + dy
            if 0 <= target_x < 8 and 0 <= target_y < 8:
                target_piece = board.get_piece(target_x, target_y)
                if target_piece is None or target_piece.color != self.color:
                    moves.append((target_x, target_y))
        return moves

class Bishop(Piece):
    def get_valid_moves(self, board):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)] 
        for dx, dy in directions:
            for step in range(1, 8):
                target_x = self.x + dx * step
                target_y = self.y + dy * step
                if 0 <= target_x < 8 and 0 <= target_y < 8:
                    target_piece = board.get_piece(target_x, target_y)
                    if target_piece is None:
                        moves.append((target_x, target_y))
                    elif target_piece.color != self.color:
                        moves.append((target_x, target_y))
                        break
                    else:
                        break
                else:
                    break
        return moves

class Queen(Piece):
    def get_valid_moves(self, board):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in directions:
            for step in range(1, 8):
                target_x = self.x + dx * step
                target_y = self.y + dy * step
                if 0 <= target_x < 8 and 0 <= target_y < 8:
                    target_piece = board.get_piece(target_x, target_y)
                    if target_piece is None:
                        moves.append((target_x, target_y))
                    elif target_piece.color != self.color:
                        moves.append((target_x, target_y))
                        break
                    else:
                        break
                else:
                    break
        return moves

class King(Piece):
    def get_valid_moves(self, board):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in directions:
            target_x = self.x + dx
            target_y = self.y + dy
            if 0 <= target_x < 8 and 0 <= target_y < 8:
                target_piece = board.get_piece(target_x, target_y)
                if target_piece is None or target_piece.color != self.color:
                    moves.append((target_x, target_y))
                    
        if not self.has_moved:
            rook_short = board.get_piece(7, self.y)
            if rook_short is not None and rook_short.__class__.__name__ == 'Rook' and not rook_short.has_moved:
                if board.get_piece(5, self.y) is None and board.get_piece(6, self.y) is None:
                    if not board.is_square_attacked(4, self.y, self.color) and \
                       not board.is_square_attacked(5, self.y, self.color) and \
                       not board.is_square_attacked(6, self.y, self.color):
                        moves.append((6, self.y)) 
                        
            rook_long = board.get_piece(0, self.y)
            if rook_long is not None and rook_long.__class__.__name__ == 'Rook' and not rook_long.has_moved:
                if board.get_piece(1, self.y) is None and board.get_piece(2, self.y) is None and board.get_piece(3, self.y) is None:
                    if not board.is_square_attacked(4, self.y, self.color) and \
                       not board.is_square_attacked(3, self.y, self.color) and \
                       not board.is_square_attacked(2, self.y, self.color):
                        moves.append((2, self.y)) 

        return moves

# szachownica i stan gry

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.current_turn = 'white'
        self.en_passant_target = None 
        
        self.captured_white = []
        self.captured_black = []
        self.history = []
        
        self.setup_board()

    def setup_board(self):
        for x in range(8):
            self.grid[1][x] = Pawn('white', x, 1)
            self.grid[6][x] = Pawn('black', x, 6)
        placement = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for x, piece_class in enumerate(placement):
            self.grid[0][x] = piece_class('white', x, 0)
            self.grid[7][x] = piece_class('black', x, 7)

    def get_piece(self, x, y):
        if 0 <= x < 8 and 0 <= y < 8:
            return self.grid[y][x]
        return None

    # historia ruchów

    def save_state(self):
        snapshot = {
            'grid': copy.deepcopy(self.grid),
            'current_turn': self.current_turn,
            'en_passant_target': self.en_passant_target,
            'captured_white': copy.deepcopy(self.captured_white),
            'captured_black': copy.deepcopy(self.captured_black)
        }
        self.history.append(snapshot)

    def undo_move(self):
        if not self.history:
            return False 
        last_state = self.history.pop()
        self.grid = last_state['grid']
        self.current_turn = last_state['current_turn']
        self.en_passant_target = last_state['en_passant_target']
        self.captured_white = last_state['captured_white']
        self.captured_black = last_state['captured_black']
        return True


    
    # szach i mat
    
    def is_square_attacked(self, x, y, defender_color):
        for row in range(8):
            for col in range(8):
                p = self.grid[row][col]
                if p is not None and p.color != defender_color:
                    if p.__class__.__name__ == 'King':
                        if abs(p.x - x) <= 1 and abs(p.y - y) <= 1:
                            return True
                    elif p.__class__.__name__ == 'Pawn':
                        direction = 1 if p.color == 'white' else -1
                        if p.y + direction == y and abs(p.x - x) == 1:
                            return True
                    else:
                        if (x, y) in p.get_valid_moves(self):
                            return True
        return False

    def is_in_check(self, color):
        king_pos = None
        for y in range(8):
            for x in range(8):
                p = self.grid[y][x]
                if p is not None and p.color == color and p.__class__.__name__ == 'King':
                    king_pos = (x, y)
                    break
            if king_pos: break
        if not king_pos: return False
        return self.is_square_attacked(king_pos[0], king_pos[1], color)

    def get_legal_moves_for_piece(self, piece):
        pseudo_moves = piece.get_valid_moves(self)
        legal_moves = []
        start_x, start_y = piece.x, piece.y
        
        for end_x, end_y in pseudo_moves:
            target_piece = self.grid[end_y][end_x]
            
            is_ep = False
            ep_captured = None
            if piece.__class__.__name__ == 'Pawn' and start_x != end_x and target_piece is None:
                is_ep = True
                ep_captured = self.grid[start_y][end_x]
                self.grid[start_y][end_x] = None

            self.grid[end_y][end_x] = piece
            self.grid[start_y][start_x] = None
            piece.x, piece.y = end_x, end_y
            
            if not self.is_in_check(piece.color):
                legal_moves.append((end_x, end_y))
                
            self.grid[start_y][start_x] = piece
            self.grid[end_y][end_x] = target_piece
            piece.x, piece.y = start_x, start_y
            
            if is_ep:
                self.grid[start_y][end_x] = ep_captured

        return legal_moves

    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False 
        for y in range(8):
            for x in range(8):
                p = self.grid[y][x]
                if p is not None and p.color == color:
                    if len(self.get_legal_moves_for_piece(p)) > 0:
                        return False 
        return True 

    # wykonanie ruchu na planszy

    def move_piece(self, start_x, start_y, end_x, end_y):
        piece = self.get_piece(start_x, start_y)
        if piece is None:
            return False 

        legal_moves = self.get_legal_moves_for_piece(piece)
        
        if (end_x, end_y) in legal_moves:
            self.save_state()
            
            if piece.__class__.__name__ == 'King' and abs(start_x - end_x) == 2:
                if end_x == 6:
                    rook = self.grid[start_y][7]
                    self.grid[start_y][5] = rook
                    self.grid[start_y][7] = None
                    rook.x, rook.y = 5, start_y
                    rook.has_moved = True
                elif end_x == 2:
                    rook = self.grid[start_y][0]
                    self.grid[start_y][3] = rook
                    self.grid[start_y][0] = None
                    rook.x, rook.y = 3, start_y
                    rook.has_moved = True

            next_ep_target = None
            if piece.__class__.__name__ == 'Pawn' and abs(end_y - start_y) == 2:
                direction = 1 if piece.color == 'white' else -1
                next_ep_target = (start_x, start_y + direction)
                
            if piece.__class__.__name__ == 'Pawn' and start_x != end_x and self.grid[end_y][end_x] is None:
                captured_ep = self.grid[start_y][end_x]
                if captured_ep:
                    if captured_ep.color == 'white':
                        self.captured_white.append(captured_ep)
                    else:
                        self.captured_black.append(captured_ep)
                self.grid[start_y][end_x] = None

            target_piece = self.grid[end_y][end_x]
            if target_piece is not None:
                if target_piece.color == 'white':
                    self.captured_white.append(target_piece)
                else:
                    self.captured_black.append(target_piece)
            
            self.grid[end_y][end_x] = piece
            self.grid[start_y][start_x] = None
            piece.x = end_x
            piece.y = end_y
            piece.has_moved = True 
            
            if piece.__class__.__name__ == 'Pawn':
                if piece.color == 'white' and end_y == 7:
                    self.grid[end_y][end_x] = Queen('white', end_x, end_y)
                elif piece.color == 'black' and end_y == 0:
                    self.grid[end_y][end_x] = Queen('black', end_x, end_y)
            
            self.en_passant_target = next_ep_target
            
            if self.current_turn == 'white':
                self.current_turn = 'black'
            else:
                self.current_turn = 'white'
                
            return True
        return False

    # odtwarzanie partii
    
    def get_current_state(self):
        return {
            'grid': copy.deepcopy(self.grid),
            'current_turn': self.current_turn,
            'en_passant_target': self.en_passant_target,
            'captured_white': copy.deepcopy(self.captured_white),
            'captured_black': copy.deepcopy(self.captured_black)
        }

    def load_state(self, state):
        self.grid = copy.deepcopy(state['grid'])
        self.current_turn = state['current_turn']
        self.en_passant_target = state['en_passant_target']
        self.captured_white = copy.deepcopy(state['captured_white'])
        self.captured_black = copy.deepcopy(state['captured_black'])

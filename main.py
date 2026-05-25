import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import os
import math
from chess_logic import Board

MODEL_CONFIG = {
    'pawn':   {'scale': 0.01, 'rot_x': -90},
    'rook':   {'scale': 0.01, 'rot_x': -90},
    'knight': {'scale': 0.01, 'rot_x': -90},
    'bishop': {'scale': 0.01, 'rot_x': -90},
    'queen':  {'scale': 0.01, 'rot_x': -90},
    'king':   {'scale': 0.01, 'rot_x': -90}
}

def get_board_square_from_mouse(mouse_x, mouse_y):
    try:
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        winX = float(mouse_x)
        winY = float(viewport[3] - mouse_y)
        near_p = gluUnProject(winX, winY, 0.0, modelview, projection, viewport)
        far_p = gluUnProject(winX, winY, 1.0, modelview, projection, viewport)
        if not near_p or not far_p: return None
        ray_dir_x = far_p[0] - near_p[0]
        ray_dir_y = far_p[1] - near_p[1]
        ray_dir_z = far_p[2] - near_p[2]
        if ray_dir_y == 0: return None
        t = -near_p[1] / ray_dir_y
        if t < 0: return None
        ix = near_p[0] + t * ray_dir_x
        iz = near_p[2] + t * ray_dir_z
        board_x = int(math.floor(ix + 4))
        board_z = int(math.floor(iz + 4))
        if 0 <= board_x < 8 and 0 <= board_z < 8:
            return (board_x, board_z)
        return None
    except Exception: return None

def load_obj(filename):
    vertices, faces = [], []
    if not os.path.exists(filename): return None
    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.split()
                if not parts: continue
                if parts[0] == 'v':
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == 'f':
                    face = []
                    for v in parts[1:]:
                        w = v.split('/')
                        idx = int(w[0])
                        if idx > 0: idx -= 1
                        elif idx < 0: idx = len(vertices) + idx
                        face.append(idx)
                    faces.append(face)
        return vertices, faces
    except Exception: return None

def create_display_list(vertices, faces):
    model_list = glGenLists(1)
    glNewList(model_list, GL_COMPILE)
    for face in faces:
        if len(face) == 3: glBegin(GL_TRIANGLES)
        elif len(face) == 4: glBegin(GL_QUADS)
        else: glBegin(GL_POLYGON)
        for vertex_index in face:
            if 0 <= vertex_index < len(vertices):
                glVertex3fv(vertices[vertex_index])
        glEnd()
    glEndList()
    return model_list

def draw_board(selected_square=None, valid_moves=None, flash_square=None):
    if valid_moves is None: valid_moves = []
    glBegin(GL_QUADS)
    for z in range(8):
        for x in range(8):
            if flash_square == (x, z): glColor3f(0.8, 0.1, 0.1)
            elif selected_square == (x, z): glColor3f(0.2, 0.8, 0.2)
            elif (x, z) in valid_moves: glColor3f(0.2, 0.5, 1.0) 
            elif (x + z) % 2 == 0: glColor3f(0.9, 0.8, 0.7)
            else: glColor3f(0.4, 0.2, 0.1)
                
            pos_x, pos_z = x - 4, z - 4
            glVertex3f(pos_x, 0, pos_z)
            glVertex3f(pos_x + 1, 0, pos_z)
            glVertex3f(pos_x + 1, 0, pos_z + 1)
            glVertex3f(pos_x, 0, pos_z + 1)
    glEnd()

def draw_pieces(board, models):
    for z in range(8):
        for x in range(8):
            piece = board.get_piece(x, z)
            if piece:
                name = piece.__class__.__name__.lower()
                if piece.color == 'white': glColor3f(0.8, 0.8, 0.8)
                else: glColor3f(0.15, 0.15, 0.15)
                glPushMatrix()
                glTranslatef(x - 3.5, 0, z - 3.5) 
                if models.get(name):
                    config = MODEL_CONFIG.get(name, {'scale': 1.0, 'rot_x': 0})
                    s = config['scale']
                    glScalef(s, s, s)
                    glRotatef(config['rot_x'], 1, 0, 0)
                    glCallList(models[name])
                glPopMatrix()

def main():
    pygame.init()
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    glEnable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    models = {}
    piece_types = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
    for p_type in piece_types:
        obj_data = load_obj(f"{p_type}.obj")
        if obj_data: models[p_type] = create_display_list(obj_data[0], obj_data[1])
        else: models[p_type] = None

    game_board = Board()
    running = True
    
    source_square = None
    valid_moves = []  
    click_pos = None  
    flash_square = None
    flash_timer = 0
    
    pygame.display.set_caption("Szachy 3D - Tura: białe")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_pos = pygame.mouse.get_pos()

        if flash_timer > 0:
            flash_timer -= 1
            if flash_timer == 0: flash_square = None

        glClearColor(0.1, 0.1, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -11.5)
        glRotatef(55, 1, 0, 0)

        if click_pos is not None:
            clicked_square = get_board_square_from_mouse(click_pos[0], click_pos[1])
            click_pos = None
            
            if clicked_square:
                if source_square is None:
                    piece = game_board.get_piece(clicked_square[0], clicked_square[1])
                    if piece:
                        if hasattr(game_board, 'current_turn') and piece.color != game_board.current_turn:
                            flash_square = clicked_square
                            flash_timer = 25
                        else:
                            source_square = clicked_square
                            # Używamy ulepszonej funkcji, żeby podświetlić tylko te bezpieczne dla Króla ruchy
                            valid_moves = game_board.get_legal_moves_for_piece(piece)
                else:
                    if clicked_square == source_square:
                        source_square = None
                        valid_moves = []
                    else:
                        start_x, start_y = source_square
                        end_x, end_y = clicked_square
                        
                        moved = game_board.move_piece(start_x, start_y, end_x, end_y)
                        
                        if moved:
                            obecna_tura = getattr(game_board, 'current_turn', 'nieznana')
                            
                            # --- POTĘŻNA LOGIKA WYŚWIETLANIA STATUSU GRY ---
                            if game_board.is_checkmate(obecna_tura):
                                zwyciezca = "BIAŁE" if obecna_tura == "black" else "CZARNE"
                                pygame.display.set_caption(f"Szachy 3D - !!! SZACH MAT !!! Wygrywają {zwyciezca}")
                                print(f"SZACH MAT! Gratulacje dla: {zwyciezca}!")
                            elif game_board.is_in_check(obecna_tura):
                                pygame.display.set_caption(f"Szachy 3D - Tura: {obecna_tura} (SZACH!)")
                                print(f"SZACH! Gracz {obecna_tura} musi uciekać Królem!")
                            else:
                                pygame.display.set_caption(f"Szachy 3D - Tura: {obecna_tura}")
                                
                        else:
                            flash_square = clicked_square  
                            flash_timer = 25              
                            
                        source_square = None 
                        valid_moves = []
            else:
                source_square = None
                valid_moves = []

        draw_board(source_square, valid_moves, flash_square)
        draw_pieces(game_board, models)
        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()
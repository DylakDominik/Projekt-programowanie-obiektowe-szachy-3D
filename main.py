import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import os
import math
from chess_logic import Board

# ustawienia modeli

MODEL_CONFIG = {
    'pawn':   {'scale': 0.01, 'rot_x': -90},
    'rook':   {'scale': 0.01, 'rot_x': -90},
    'knight': {'scale': 0.01, 'rot_x': -90},
    'bishop': {'scale': 0.01, 'rot_x': -90},
    'queen':  {'scale': 0.01, 'rot_x': -90},
    'king':   {'scale': 0.01, 'rot_x': -90}
}

# tekstury i oświetlenie sceny

def load_texture(filename):
    if not os.path.exists(filename):
        print(f"!!! BŁĄD: Brak pliku tekstury: {filename} !!!")
        return 0
        
    surface = pygame.image.load(filename).convert_alpha()
    surface = pygame.transform.flip(surface, False, True)
    data = pygame.image.tobytes(surface, "RGBA")
    width, height = surface.get_width(), surface.get_height()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return tex_id

def init_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE) 
    
    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 10.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])   
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])   
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])  
    
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0]) 
    glMaterialf(GL_FRONT, GL_SHININESS, 60.0)                 
    glShadeModel(GL_SMOOTH) 

# wykrywanie kliknięć 3D

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



# wczytywanie modeli

def load_obj(filename):
    vertices, texcoords, normals, faces = [], [], [], []
    if not os.path.exists(filename): return None
    with open(filename, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts: continue
            if parts[0] == 'v': vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'vt': texcoords.append([float(parts[1]), float(parts[2])])
            elif parts[0] == 'vn': normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'f':
                face = []
                for v in parts[1:]:
                    w = v.split('/')
                    v_idx = int(w[0]) - 1 if int(w[0]) > 0 else len(vertices) + int(w[0])
                    t_idx = None
                    if len(w) > 1 and w[1] != '': t_idx = int(w[1]) - 1 if int(w[1]) > 0 else len(texcoords) + int(w[1])
                    n_idx = None
                    if len(w) > 2 and w[2] != '': n_idx = int(w[2]) - 1 if int(w[2]) > 0 else len(normals) + int(w[2])
                    face.append((v_idx, t_idx, n_idx))
                faces.append(face)
    return vertices, texcoords, normals, faces

def create_display_list(vertices, texcoords, normals, faces):
    model_list = glGenLists(1)
    glNewList(model_list, GL_COMPILE)
    for face in faces:
        if len(face) == 3: glBegin(GL_TRIANGLES)
        elif len(face) == 4: glBegin(GL_QUADS)
        else: glBegin(GL_POLYGON)
        for v_idx, t_idx, n_idx in face:
            if n_idx is not None and 0 <= n_idx < len(normals): glNormal3fv(normals[n_idx])
            if t_idx is not None and 0 <= t_idx < len(texcoords): glTexCoord2f(texcoords[t_idx][0], texcoords[t_idx][1])
            if 0 <= v_idx < len(vertices): glVertex3fv(vertices[v_idx])
        glEnd()
    glEndList()
    return model_list

# rysowanie planszy i figur

def draw_board(tex_white, tex_black, selected_square=None, valid_moves=None, flash_square=None):
    glEnable(GL_TEXTURE_2D)
    if valid_moves is None: valid_moves = []
    
    for z in range(8):
        for x in range(8):
            if (x + z) % 2 == 0: glBindTexture(GL_TEXTURE_2D, tex_white)
            else: glBindTexture(GL_TEXTURE_2D, tex_black)

            if flash_square == (x, z): glColor3f(1.0, 0.3, 0.3)      
            elif selected_square == (x, z): glColor3f(0.5, 1.0, 0.5) 
            elif (x, z) in valid_moves: glColor3f(0.5, 0.8, 1.0)     
            else: glColor3f(1.0, 1.0, 1.0)                           
                
            pos_x, pos_z = x - 4, z - 4
            glBegin(GL_QUADS)
            glNormal3f(0.0, 1.0, 0.0) 
            glTexCoord2f(0.0, 0.0); glVertex3f(pos_x, 0, pos_z)
            glTexCoord2f(1.0, 0.0); glVertex3f(pos_x + 1, 0, pos_z)
            glTexCoord2f(1.0, 1.0); glVertex3f(pos_x + 1, 0, pos_z + 1)
            glTexCoord2f(0.0, 1.0); glVertex3f(pos_x, 0, pos_z + 1)
            glEnd()

    glBindTexture(GL_TEXTURE_2D, tex_black) 
    glColor3f(0.8, 0.8, 0.8) 
    b = 4.3; h = -0.6 
    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-b, -0.01, -b); glTexCoord2f(8.0, 0.0); glVertex3f(b, -0.01, -b)
    glTexCoord2f(8.0, 8.0); glVertex3f(b, -0.01, b); glTexCoord2f(0.0, 8.0); glVertex3f(-b, -0.01, b)
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-b, h, b); glTexCoord2f(8.0, 0.0); glVertex3f(b, h, b)
    glTexCoord2f(8.0, 1.0); glVertex3f(b, 0, b); glTexCoord2f(0.0, 1.0); glVertex3f(-b, 0, b)
    glNormal3f(0.0, 0.0, -1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(b, h, -b); glTexCoord2f(8.0, 0.0); glVertex3f(-b, h, -b)
    glTexCoord2f(8.0, 1.0); glVertex3f(-b, 0, -b); glTexCoord2f(0.0, 1.0); glVertex3f(b, 0, -b)
    glNormal3f(-1.0, 0.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-b, h, -b); glTexCoord2f(8.0, 0.0); glVertex3f(-b, h, b)
    glTexCoord2f(8.0, 1.0); glVertex3f(-b, 0, b); glTexCoord2f(0.0, 1.0); glVertex3f(-b, 0, -b)
    glNormal3f(1.0, 0.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(b, h, b); glTexCoord2f(8.0, 0.0); glVertex3f(b, h, -b)
    glTexCoord2f(8.0, 1.0); glVertex3f(b, 0, -b); glTexCoord2f(0.0, 1.0); glVertex3f(b, 0, b)
    glEnd()

def draw_pieces(board, models, tex_white, tex_black, anim_start=None, anim_end=None, anim_progress=0.0):
    glEnable(GL_TEXTURE_2D)
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glScalef(0.1, 0.1, 1.0)
    glMatrixMode(GL_MODELVIEW)
    
    def render_model(piece_obj, pos_x, pos_y, pos_z):
        name = piece_obj.__class__.__name__.lower()
        glColor3f(1.0, 1.0, 1.0) 
        if piece_obj.color == 'white': glBindTexture(GL_TEXTURE_2D, tex_white)
        else: glBindTexture(GL_TEXTURE_2D, tex_black)
        glPushMatrix()
        glTranslatef(pos_x, pos_y, pos_z) 
        if models.get(name):
            config = MODEL_CONFIG.get(name, {'scale': 1.0, 'rot_x': 0})
            s = config['scale']; glScalef(s, s, s); glRotatef(config['rot_x'], 1, 0, 0); glCallList(models[name])
        glPopMatrix()

    for z in range(8):
        for x in range(8):
            if anim_end and (x, z) == anim_end: continue
            piece = board.get_piece(x, z)
            if piece: render_model(piece, x - 3.5, 0, z - 3.5)

    if anim_end:
        piece = board.get_piece(anim_end[0], anim_end[1])
        if piece:
            cur_x = anim_start[0] + (anim_end[0] - anim_start[0]) * anim_progress
            cur_z = anim_start[1] + (anim_end[1] - anim_start[1]) * anim_progress
            jump_height = math.sin(anim_progress * math.pi) * 1.5
            render_model(piece, cur_x - 3.5, jump_height, cur_z - 3.5)

    if hasattr(board, 'captured_black') and board.captured_black:
        total_rows_b = (len(board.captured_black) - 1) // 2
        start_z_b = -(total_rows_b * 0.8) / 2 
        for i, piece in enumerate(board.captured_black): 
            render_model(piece, -4.8 - (i % 2) * 0.8, 0, start_z_b + (i // 2) * 0.8)

    if hasattr(board, 'captured_white') and board.captured_white:
        total_rows_w = (len(board.captured_white) - 1) // 2
        start_z_w = -(total_rows_w * 0.8) / 2
        for i, piece in enumerate(board.captured_white): 
            render_model(piece, 4.8 + (i % 2) * 0.8, 0, start_z_w + (i // 2) * 0.8)

    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# główna pętla gry i sterowanie

def main():
    pygame.init()
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    glEnable(GL_DEPTH_TEST) 
    glEnable(GL_TEXTURE_2D)
    init_lighting()
    
    tex_white = load_texture("wood_light.png")
    tex_black = load_texture("wood_dark.png")
    
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluPerspective(45, (display[0] / display[1]), 0.1, 50.0); glMatrixMode(GL_MODELVIEW)

    models = {}
    piece_types = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
    for p_type in piece_types:
        obj_data = load_obj(f"{p_type}.obj")
        if obj_data: models[p_type] = create_display_list(obj_data[0], obj_data[1], obj_data[2], obj_data[3])
        else: models[p_type] = None

    game_board = Board()
    running = True
    
    source_square = None
    valid_moves = []  
    click_pos = None  
    flash_square = None
    flash_timer = 0
    anim_start = None; anim_end = None; anim_progress = 0.0
    
    game_over = False
    replay_mode = False
    replay_history = []
    replay_index = 0
    
    camera_distance = 11.5
    camera_pitch = 55.0  
    camera_yaw = 0.0     
    is_dragging_camera = False
    last_mouse_pos = (0, 0)
    
    pygame.display.set_caption("Szachy 3D - Tura: białe")

    while running:
        if flash_timer > 0:
            flash_timer -= 1
            if flash_timer == 0: flash_square = None
            
        if anim_end is not None:
            anim_progress += 0.08  
            if anim_progress >= 1.0: anim_end = None 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_z or event.key == pygame.K_BACKSPACE) and not replay_mode and anim_end is None:
                    if game_board.undo_move():
                        game_over = False  
                        anim_end = None; source_square = None; valid_moves = []; flash_square = None
                        pygame.display.set_caption(f"Szachy 3D - Tura: {game_board.current_turn}")
                elif event.key == pygame.K_r:
                    game_board = Board()
                    game_over = False; replay_mode = False
                    anim_end = None; source_square = None; valid_moves = []
                    pygame.display.set_caption("Szachy 3D - Nowa gra. Tura: białe")
                elif event.key == pygame.K_p and game_over and not replay_mode:
                    replay_mode = True
                    replay_history = game_board.history + [game_board.get_current_state()]
                    replay_index = 0
                    game_board.load_state(replay_history[replay_index])
                    pygame.display.set_caption(f"=== ODTWARZACZ === Ruch: {replay_index} / {len(replay_history)-1} (Użyj STRZAŁEK)")
                elif replay_mode:
                    if event.key == pygame.K_LEFT:
                        replay_index = max(0, replay_index - 1)
                        game_board.load_state(replay_history[replay_index])
                        pygame.display.set_caption(f"=== ODTWARZACZ === Ruch: {replay_index} / {len(replay_history)-1}")
                    elif event.key == pygame.K_RIGHT:
                        replay_index = min(len(replay_history)-1, replay_index + 1)
                        game_board.load_state(replay_history[replay_index])
                        pygame.display.set_caption(f"=== ODTWARZACZ === Ruch: {replay_index} / {len(replay_history)-1}")
                    elif event.key == pygame.K_ESCAPE:
                        replay_mode = False
                        game_board.load_state(replay_history[-1])
                        pygame.display.set_caption("Szachy 3D - !!! SZACH MAT !!! (R - Restart gry)")
                        
                elif event.key == pygame.K_w or event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                    camera_distance = max(5.0, camera_distance - 1.0)
                elif event.key == pygame.K_s or event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    camera_distance = min(25.0, camera_distance + 1.0)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    if anim_end is None and not game_over and not replay_mode:
                        click_pos = pygame.mouse.get_pos()
                elif event.button == 3: 
                    is_dragging_camera = True
                    last_mouse_pos = pygame.mouse.get_pos()
                elif event.button == 4: 
                    camera_distance = max(5.0, camera_distance - 1.0)
                elif event.button == 5: 
                    camera_distance = min(25.0, camera_distance + 1.0)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    is_dragging_camera = False

            elif event.type == pygame.MOUSEMOTION:
                if is_dragging_camera:
                    current_mouse_pos = pygame.mouse.get_pos()
                    dx = current_mouse_pos[0] - last_mouse_pos[0]
                    dy = current_mouse_pos[1] - last_mouse_pos[1]
                    
                    camera_yaw += dx * 0.3
                    camera_pitch += dy * 0.3
                    camera_pitch = max(10.0, min(85.0, camera_pitch))
                    
                    last_mouse_pos = current_mouse_pos

        glClearColor(0.1, 0.1, 0.15, 1.0); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -camera_distance)
        glRotatef(camera_pitch, 1, 0, 0)
        glRotatef(camera_yaw, 0, 1, 0)

        if click_pos is not None:
            clicked_square = get_board_square_from_mouse(click_pos[0], click_pos[1])
            click_pos = None
            if clicked_square:
                if source_square is None:
                    piece = game_board.get_piece(clicked_square[0], clicked_square[1])
                    if piece:
                        if hasattr(game_board, 'current_turn') and piece.color != game_board.current_turn:
                            flash_square = clicked_square; flash_timer = 25
                        else:
                            source_square = clicked_square; valid_moves = game_board.get_legal_moves_for_piece(piece)
                else:
                    if clicked_square == source_square: source_square = None; valid_moves = []
                    else:
                        start_x, start_y = source_square; end_x, end_y = clicked_square
                        moved = game_board.move_piece(start_x, start_y, end_x, end_y)
                        
                        if moved:
                            anim_start = (start_x, start_y); anim_end = (end_x, end_y); anim_progress = 0.0
                            obecna_tura = getattr(game_board, 'current_turn', 'nieznana')
                            
                            if game_board.is_checkmate(obecna_tura):
                                zwyciezca = "BIAŁE" if obecna_tura == "black" else "CZARNE"
                                pygame.display.set_caption(f"Szachy 3D - !!! SZACH MAT !!! Wygrywają {zwyciezca} (P-Powtórka, R-Restart)")
                                game_over = True 
                            elif game_board.is_in_check(obecna_tura): pygame.display.set_caption(f"Szachy 3D - Tura: {obecna_tura} (SZACH!)")
                            else: pygame.display.set_caption(f"Szachy 3D - Tura: {obecna_tura}")
                        else:
                            flash_square = clicked_square; flash_timer = 25              
                        source_square = None; valid_moves = []
            else:
                source_square = None; valid_moves = []

        draw_board(tex_white, tex_black, source_square, valid_moves, flash_square)
        draw_pieces(game_board, models, tex_white, tex_black, anim_start, anim_end, anim_progress)
        pygame.display.flip(); pygame.time.wait(10)

if __name__ == "__main__":
    main()

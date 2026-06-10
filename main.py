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

# --- NOWOŚĆ: Funkcja ustawiająca oświetlenie ---
def init_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    # BARDZO WAŻNE: Naprawia odbijanie światła przy skalowanych modelach (scale: 0.01)
    glEnable(GL_NORMALIZE) 
    
    # Pozycja żarówki (z góry, lekko z boku i z tyłu)
    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 10.0, 1.0])
    
    # Rodzaje światła
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])   # Lekkie oświetlenie cieni
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])   # Główne światło padające
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])  # Mocny biały błysk (odblask)
    
    # Pozwalamy, żeby kolory (glColor3f) działały z oświetleniem
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    
    # Ustawiamy połysk materiału dla figur (efekt polerowanego drewna)
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0]) # Siła odblasku
    glMaterialf(GL_FRONT, GL_SHININESS, 60.0)                 # Ostrość odblasku
    
    glShadeModel(GL_SMOOTH) # Płynne cieniowanie krawędzi

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

# --- ZAKTUALIZOWANO: Parser czyta teraz wektory normalne ('vn') potrzebne do cieni ---
def load_obj(filename):
    vertices, texcoords, normals, faces = [], [], [], []
    if not os.path.exists(filename): 
        print(f"BRAK PLIKU: {filename}")
        return None
    
    with open(filename, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts: continue
            
            if parts[0] == 'v':
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'vt':
                texcoords.append([float(parts[1]), float(parts[2])])
            elif parts[0] == 'vn': # Wczytywanie wektorów oświetlenia
                normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'f':
                face = []
                for v in parts[1:]:
                    w = v.split('/')
                    
                    v_idx = int(w[0]) - 1 if int(w[0]) > 0 else len(vertices) + int(w[0])
                    
                    t_idx = None
                    if len(w) > 1 and w[1] != '':
                        t_idx = int(w[1]) - 1 if int(w[1]) > 0 else len(texcoords) + int(w[1])
                        
                    n_idx = None
                    if len(w) > 2 and w[2] != '':
                        n_idx = int(w[2]) - 1 if int(w[2]) > 0 else len(normals) + int(w[2])
                        
                    face.append((v_idx, t_idx, n_idx))
                faces.append(face)
                
    print(f"SUKCES: {filename} wczytany! Wierzchołki: {len(vertices)}, Ściany: {len(faces)}")
    return vertices, texcoords, normals, faces

def create_display_list(vertices, texcoords, normals, faces):
    model_list = glGenLists(1)
    glNewList(model_list, GL_COMPILE)
    for face in faces:
        if len(face) == 3: glBegin(GL_TRIANGLES)
        elif len(face) == 4: glBegin(GL_QUADS)
        else: glBegin(GL_POLYGON)
        
        for v_idx, t_idx, n_idx in face:
            # Informujemy OpenGL o wektorze oświetlenia przed narysowaniem punktu
            if n_idx is not None and 0 <= n_idx < len(normals):
                glNormal3fv(normals[n_idx])
                
            if t_idx is not None and 0 <= t_idx < len(texcoords):
                glTexCoord2f(texcoords[t_idx][0], texcoords[t_idx][1])
                
            if 0 <= v_idx < len(vertices):
                glVertex3fv(vertices[v_idx])
        glEnd()
    glEndList()
    return model_list

def draw_board(selected_square=None, valid_moves=None, flash_square=None):
    glDisable(GL_TEXTURE_2D)
    if valid_moves is None: valid_moves = []
    
    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0) # Informujemy światło, że płaska szachownica patrzy prosto w górę
    
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

def draw_pieces(board, models, tex_white, tex_black):
    glEnable(GL_TEXTURE_2D)
    
    # Skalowanie tekstury drewna (żeby słoje były ładne)
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    zoom_factor = 0.1  
    glScalef(zoom_factor, zoom_factor, 1.0)
    glMatrixMode(GL_MODELVIEW)
    
    for z in range(8):
        for x in range(8):
            piece = board.get_piece(x, z)
            if piece:
                name = piece.__class__.__name__.lower()
                
                glColor3f(1.0, 1.0, 1.0) 
                if piece.color == 'white': 
                    glBindTexture(GL_TEXTURE_2D, tex_white)
                else: 
                    glBindTexture(GL_TEXTURE_2D, tex_black)
                    
                glPushMatrix()
                glTranslatef(x - 3.5, 0, z - 3.5) 
                if models.get(name):
                    config = MODEL_CONFIG.get(name, {'scale': 1.0, 'rot_x': 0})
                    s = config['scale']
                    glScalef(s, s, s)
                    glRotatef(config['rot_x'], 1, 0, 0)
                    glCallList(models[name])
                glPopMatrix()

    # Sprzątanie po skalowaniu tekstury
    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def main():
    pygame.init()
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    glEnable(GL_DEPTH_TEST) 
    glEnable(GL_TEXTURE_2D)
    
    # Włączamy cienie i błyski
    init_lighting()
    
    tex_white = load_texture("wood_light.png")
    tex_black = load_texture("wood_dark.png")
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    models = {}
    piece_types = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
    for p_type in piece_types:
        obj_data = load_obj(f"{p_type}.obj")
        # Zwracamy teraz 4 wartości z parsera (wierzchołki, tekstury, wektory normalne, ściany)
        if obj_data: models[p_type] = create_display_list(obj_data[0], obj_data[1], obj_data[2], obj_data[3])
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
        draw_pieces(game_board, models, tex_white, tex_black)
        
        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()

import pygame
import random
import sys
import time


#  SETTINGS  

ROWS  = 8 # 0-7
COLS  = 8 # 0-7
MINES = 8
CELL  = 52          # size of each cell in pixels

# Window layout
TOP_BAR = 70        # height of the top info bar
MARGIN  = 15        # space around the grid

WIN_W = COLS * CELL + MARGIN * 2  # windows width size
WIN_H = ROWS * CELL + MARGIN * 2 + TOP_BAR # windows height size

# ══════════════════════════════════════════════════════
#  COLORS in RGB
# ══════════════════════════════════════════════════════
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GRAY_LIGHT = (220, 220, 220)   # unrevealed cell
GRAY_MID   = (180, 180, 180)   # border / background
GRAY_DARK  = (120, 120, 120)   # shadow
GRAY_OPEN  = (200, 200, 200)   # revealed cell
RED        = (220,  50,  50)   # mine explosion
GREEN      = (50,  180,  50)   # win color
YELLOW     = (255, 210,  50)   # flag
BLUE_BAR   = (40,   80, 140)   # top bar

# Number colors (1-8) num inside the cell = mines around the cell
NUM_COLOR = {
    1: (30,  80, 220),
    2: (30, 140,  50),
    3: (210,  40,  40),
    4: (20,   20, 150),
    5: (150,  20,  20),
    6: (20,  140, 140),
    7: (80,   80,  80),
    8: (140, 140, 140),
}


# ══════════════════════════════════════════════════════
#  GAME LOGIC
# ══════════════════════════════════════════════════════
class Minesweeper:
    """
    Handles all game logic.
    board[r][c] = -1 means mine, 0-8 means number of adjacent mines.
    """

    def __init__(self):
        self.reset() 

    def reset(self):
        # 2D grids for the game state
        self.board    = [[0] * COLS for _ in range(ROWS)]   # -1=mine, 0-8=count
        self.revealed = [[False] * COLS for _ in range(ROWS)] 
        self.flagged  = [[False] * COLS for _ in range(ROWS)]

        self.mines_set  = set()    # set of (r, c) with mines  ,, using set for search faster
        self.started    = False    # becomes True after first click
        self.game_over  = False
        self.victory    = False
        self.start_time = None # for record time
        self.end_time   = None
        self.flag_count = 0

    # ── Place mines (called on first click so first click is always safe) ──
    def place_mines(self, first_r, first_c):
        # Avoid placing mine on or around first click
        safe_zone = {
            (first_r + dr, first_c + dc) 
            for dr in [-1, 0, 1]   
            for dc in [-1, 0, 1]
        }

        all_cells = [
            (r, c)
            for r in range(ROWS)
            for c in range(COLS)
            if (r, c) not in safe_zone
        ]

        chosen = random.sample(all_cells, MINES)  # choose cells for mines = num of mines
        for r, c in chosen:
            self.mines_set.add((r, c))
            self.board[r][c] = -1

        # Fill in numbers
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] != -1:
                    self.board[r][c] = self._count_adjacent_mines(r, c) 

        self.started    = True
        self.start_time = time.time()

    def _count_adjacent_mines(self, r, c): # sum the num in the cell
        count = 0
        for dr in [-1, 0, 1]:   # squar 3*3 around first click is safe (8 cell )
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc # new row , new cols
                if 0 <= nr < ROWS and 0 <= nc < COLS: # ensure that the ncell in the board
                    if self.board[nr][nc] == -1:
                        count += 1
        return count

    def _neighbors(self, r, c): # for open safe cell recursion
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and (dr, dc) != (0, 0): # the cell itself (0,0) ignore it 
                    yield nr, nc 
    # ── Reveal a cell 
    def reveal(self, r, c):
        if self.game_over:
            return
        if self.revealed[r][c] or self.flagged[r][c]:
            return

        # First click: place mines now
        if not self.started:
            self.place_mines(r, c)

        # Hit a mine
        if self.board[r][c] == -1:
            self.revealed[r][c] = True
            self.game_over = True
            self.victory   = False
            self.end_time  = time.time()
            return

        # Use BFS to open the cell (and flood-fill if it's a zero)
        queue = [(r, c)] # using q for first reveal cell   (BFS algo)
        while queue:
            cr, cc = queue.pop(0)  
            if self.revealed[cr][cc]:  # current row , current col
                continue
            self.revealed[cr][cc] = True
            # If cell is blank (0), auto-open all neighbors
            if self.board[cr][cc] == 0:
                for nr, nc in self._neighbors(cr, cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        queue.append((nr, nc))

        self._check_win()

    # ── Flag / unflag a cell 
    def toggle_flag(self, r, c):
        if self.game_over or self.revealed[r][c]:
            return
        if self.flagged[r][c]:
            self.flagged[r][c] = False
            self.flag_count -= 1
        else:
            self.flagged[r][c] = True
            self.flag_count += 1

    # ── Chord: middle-click or double-click on a number 
    def chord(self, r, c):
        if not self.revealed[r][c] or self.board[r][c] <= 0:
            return
        flags_nearby = sum(
            1 for nr, nc in self._neighbors(r, c)
            if self.flagged[nr][nc]
        )
        if flags_nearby == self.board[r][c]:
            for nr, nc in self._neighbors(r, c):
                if not self.flagged[nr][nc] and not self.revealed[nr][nc]:
                    self.reveal(nr, nc)

    # ── Check if the player won 
    def _check_win(self):
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return   # still unrevealed safe cells
        self.game_over = True
        self.victory   = True
        self.end_time  = time.time()

    # ── Getters for UI display
    @property
    def mines_left(self):
        return MINES - self.flag_count

    @property
    def seconds(self):
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time else time.time()
        return int(end - self.start_time)



#  DRAWING

class Renderer:

    def __init__(self, screen):
        self.screen   = screen
        self.font_big = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_sm  = pygame.font.SysFont("Arial", 13)

    # ── Return pixel rect for cell (r, c) 
    def cell_rect(self, r, c):
        x = MARGIN + c * CELL
        y = MARGIN + TOP_BAR + r * CELL
        return pygame.Rect(x, y, CELL, CELL)

    # ── Main draw call
    def draw(self, game, hover, pressing):
        self.screen.fill(GRAY_MID)
        self._draw_top_bar(game)
        self._draw_grid(game, hover, pressing)
        self._draw_message(game)
        pygame.display.flip()

    # ── Top bar: mine counter, smiley, timer
    def _draw_top_bar(self, game):
        bar = pygame.Rect(0, 0, WIN_W, TOP_BAR)
        pygame.draw.rect(self.screen, BLUE_BAR, bar)

        # Mine counter
        mine_txt = self.font_big.render(f"💣 {game.mines_left:02d}", True, WHITE)
        self.screen.blit(mine_txt, (18, TOP_BAR // 2 - mine_txt.get_height() // 2))

        # Timer
        time_txt = self.font_big.render(f"⏱ {min(game.seconds, 999):03d}", True, WHITE)
        self.screen.blit(time_txt, (WIN_W - time_txt.get_width() - 18,
                                     TOP_BAR // 2 - time_txt.get_height() // 2))

        # Smiley reset button (center)
        face = "😎" if game.victory else ("💀" if game.game_over else "🙂")
        face_txt = pygame.font.SysFont("Segoe UI Emoji", 28).render(face, True, WHITE)
        fx = WIN_W // 2 - face_txt.get_width() // 2
        fy = TOP_BAR // 2 - face_txt.get_height() // 2
        self.screen.blit(face_txt, (fx, fy))

        # Save button area for click detection
        self.reset_rect = pygame.Rect(WIN_W // 2 - 22, fy - 2, 44, 40)

        # Hint text
        hint = self.font_sm.render("R = Reset  |  Right-click = Flag  |  Click face to restart", True, (180, 200, 230))
        self.screen.blit(hint, (WIN_W // 2 - hint.get_width() // 2, TOP_BAR - 17))

    # ── Draw all cells 
    def _draw_grid(self, game, hover, pressing):
        for r in range(ROWS):
            for c in range(COLS):
                rect = self.cell_rect(r, c)
                self._draw_cell(game, r, c, rect, hover, pressing)

    def _draw_cell(self, game, r, c, rect, hover, pressing):
        is_hover    = (hover == (r, c)) and not game.game_over
        is_pressing = (pressing == (r, c)) and not game.game_over

        if game.revealed[r][c]:
            val = game.board[r][c]

            # Background
            if val == -1:
                bg = RED          # exploded mine
            else:
                bg = GRAY_OPEN
            pygame.draw.rect(self.screen, bg, rect)
            pygame.draw.rect(self.screen, GRAY_DARK, rect, 1)

            # Content
            if val == -1:
                self._draw_text(rect, "💣", 22, BLACK)
            elif val > 0:
                t = self.font_big.render(str(val), True, NUM_COLOR[val])
                self.screen.blit(t, t.get_rect(center=rect.center))

        else:
            # Show un-flagged mines after losing
            if game.game_over and not game.victory and (r, c) in game.mines_set and not game.flagged[r][c]:
                pygame.draw.rect(self.screen, (230, 180, 180), rect)
                pygame.draw.rect(self.screen, GRAY_DARK, rect, 1)
                self._draw_text(rect, "💣", 22, BLACK)
                return

            # Choose cell color
            if is_pressing:
                bg = GRAY_OPEN
            elif is_hover:
                bg = (235, 235, 235)
            else:
                bg = GRAY_LIGHT

            pygame.draw.rect(self.screen, bg, rect)

            # Simple 3D border (raised look)
            b = 3
            pygame.draw.rect(self.screen, WHITE,     (rect.x,         rect.y,         rect.w, b))
            pygame.draw.rect(self.screen, WHITE,     (rect.x,         rect.y,         b, rect.h))
            pygame.draw.rect(self.screen, GRAY_DARK, (rect.x,         rect.y+rect.h-b, rect.w, b))
            pygame.draw.rect(self.screen, GRAY_DARK, (rect.x+rect.w-b, rect.y,        b, rect.h))

            # Flag
            if game.flagged[r][c]:
                self._draw_text(rect, "🚩", 20, RED)
                # Mark wrong flags on loss
                if game.game_over and not game.victory and (r, c) not in game.mines_set:
                    pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 3)
                    pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 3)

    def _draw_text(self, rect, text, size, color):
        f = pygame.font.SysFont("Segoe UI Emoji", size)
        t = f.render(text, True, color)
        self.screen.blit(t, t.get_rect(center=rect.center))

    # ── Win / Lose overlay message 
    def _draw_message(self, game):
        if not game.game_over:
            return

        if game.victory:
            msg   = f"  You Win! 🎉  Time: {game.seconds}s  "
            color = (30, 160, 30)
        else:
            msg   = "  Game Over! 💥  Press R to retry  "
            color = (180, 30, 30)

        box = pygame.Surface((WIN_W, 40), pygame.SRCALPHA)
        box.fill((*color, 210))
        self.screen.blit(box, (0, TOP_BAR + ROWS * CELL // 2 - 20 + MARGIN))

        f = pygame.font.SysFont("Arial", 20, bold=True)
        t = f.render(msg, True, WHITE)
        self.screen.blit(t, t.get_rect(center=(WIN_W // 2,
                          TOP_BAR + ROWS * CELL // 2 + MARGIN)))



#  MAIN LOOP

def get_cell(mx, my):
    """Convert mouse position to (row, col), or None if outside grid."""
    c = (mx - MARGIN) // CELL
    r = (my - MARGIN - TOP_BAR) // CELL
    if 0 <= r < ROWS and 0 <= c < COLS:
        return (r, c)
    return None


def main():
    pygame.init()
    screen   = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("💣 Minesweeper")

    game     = Minesweeper()
    renderer = Renderer(screen)

    hover    = None   # cell under mouse
    pressing = None   # cell being left-clicked
    clock    = pygame.time.Clock()

    while True:
        clock.tick(30)

        # Handle events 
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Reset with R key
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game = Minesweeper()
                pressing = None

            # Track mouse movement for hover
            if event.type == pygame.MOUSEMOTION:
                hover = get_cell(*event.pos)

            # Mouse press
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Click on smiley face = reset
                if hasattr(renderer, 'reset_rect') and renderer.reset_rect.collidepoint(mx, my):
                    game = Minesweeper()
                    pressing = None
                    continue

                cell = get_cell(mx, my)
                if cell is None:
                    continue

                if event.button == 1:           # left click
                    pressing = cell
                elif event.button == 3:         # right click = flag
                    game.toggle_flag(*cell)

            # Mouse release
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and pressing:
                    cell = get_cell(*event.pos)
                    if cell == pressing:          # only if still on same cell
                        r, c = pressing
                        if game.revealed[r][c]:
                            game.chord(r, c)      # chord on revealed number
                        else:
                            game.reveal(r, c)     # reveal hidden cell
                    pressing = None

        # ── Draw everything 
        renderer.draw(game, hover, pressing)
        clock.tick(30)


if __name__ == "__main__":
    main()
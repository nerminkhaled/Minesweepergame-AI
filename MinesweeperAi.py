import pygame
import random
import sys
import time
from collections import deque

#  SETTINGS
ROWS  = 8
COLS  = 8
MINES = 8
CELL  = 52

TOP_BAR = 90
MARGIN  = 15
BTN_BAR = 50   # bottom button bar

WIN_W = COLS * CELL + MARGIN * 2
WIN_H = ROWS * CELL + MARGIN * 2 + TOP_BAR + BTN_BAR

#  COLORS

WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0)
GRAY_LIGHT   = (220, 220, 220)
GRAY_MID     = (180, 180, 180)
GRAY_DARK    = (120, 120, 120)
GRAY_OPEN    = (200, 200, 200)
RED          = (220,  50,  50)
GREEN        = ( 50, 180,  50)
YELLOW       = (255, 210,  50)
BLUE_BAR     = ( 40,  80, 140)
AI_HIGHLIGHT = ( 80, 200, 120)   # green — certain safe move
AI_FLAG_CLR  = (255, 120,  50)   # orange — certain mine flagged by AI
AI_GUESS_CLR = (255, 230,  80)   # yellow — probabilistic guess
MINIMAX_CLR  = (180,  80, 220)   # purple — minimax-informed choice
BTN_MANUAL   = ( 70, 130, 200)
BTN_AI       = ( 50, 160,  90)
BTN_RESET    = (160,  60,  60)
BTN_STEP     = (200, 150,  30)

NUM_COLOR = {
    1: (30,  80, 220), 2: (30, 140, 50),  3: (210, 40, 40),
    4: (20,  20, 150), 5: (150, 20, 20),  6: (20, 140, 140),
    7: (80,  80,  80), 8: (140, 140, 140),
}



#   GAME LOGIC  

class Minesweeper:
    """Core game logic. board[r][c] = -1 mine, 0-8 neighbor count."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board    = [[0]*COLS for _ in range(ROWS)]
        self.revealed = [[False]*COLS for _ in range(ROWS)]
        self.flagged  = [[False]*COLS for _ in range(ROWS)]
        self.mines_set  = set()
        self.started    = False
        self.game_over  = False
        self.victory    = False
        self.start_time = None
        self.end_time   = None
        self.flag_count = 0

    def place_mines(self, first_r, first_c):
        safe = {
            (first_r+dr, first_c+dc) 
            for dr in (-1,0,1) 
            for dc in (-1,0,1)
        }
        pool = [         # all cells
            (r,c) for r in range(ROWS) 
            for c in range(COLS) 
            if (r,c) not in safe] 
        
        for r,c in random.sample(pool, MINES): # choose cells for mines = num of mines
            self.mines_set.add((r,c))
            self.board[r][c] = -1
            
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] != -1:
                    self.board[r][c] = self._count_adj(r,c) # calc num of mines around the cell
                    
        self.started    = True
        self.start_time = time.time()

    def _count_adj(self, r, c):   # calc num of mines around the cell
        return sum(1 for nr,nc in self._neighbors(r,c) if self.board[nr][nc]==-1)

    def _neighbors(self, r, c):
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                nr,nc = r+dr, c+dc
                if 0<=nr<ROWS and 0<=nc<COLS and (dr,dc)!=(0,0): # the cell itself (0,0) ignore it 
                    yield nr,nc  # return the values value by value not a list (yields) 

    # ── BFS flood-fill reveal (Uninformed Search #1) ── Reveal a cell and auto-expand if blank (0)
    def reveal(self, r, c):
        if self.game_over or self.revealed[r][c] or self.flagged[r][c]:
            return
        if not self.started: # First click: place mines now
            self.place_mines(r, c)
        if self.board[r][c] == -1: # Hit a mine
            self.revealed[r][c] = True
            self.game_over = True
            self.end_time  = time.time()
            return
        # BFS
        queue = deque([(r,c)])
        while queue:
            cr,cc = queue.popleft()
            if self.revealed[cr][cc]:
                continue
            self.revealed[cr][cc] = True
            if self.board[cr][cc] == 0:    # If cell is blank (0), auto-open all neighbors
                for nr,nc in self._neighbors(cr,cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        queue.append((nr,nc))
                        
        self._check_win()
        
# ── Flag / unflag a cell
    def toggle_flag(self, r, c):
        if self.game_over or self.revealed[r][c]:
            return
        if self.flagged[r][c]:
            self.flagged[r][c] = False; self.flag_count -= 1
        else:
            self.flagged[r][c] = True;  self.flag_count += 1
            
            
# ── Chord: middle-click or double-click on a number 

    def chord(self, r, c):
        if not self.revealed[r][c] or self.board[r][c] <= 0:
            return
        if sum(1 for nr,nc in self._neighbors(r,c) if self.flagged[nr][nc]) == self.board[r][c]:
            for nr,nc in self._neighbors(r,c):
                if not self.flagged[nr][nc] and not self.revealed[nr][nc]:
                    self.reveal(nr,nc)
                    
# ── Check if the player won 
    def _check_win(self):
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return
        self.game_over = True
        self.victory   = True
        self.end_time  = time.time()

# ── Getters 

    @property
    def mines_left(self):
        return MINES - self.flag_count

    @property
    def seconds(self):
        if self.start_time is None: return 0
        return int((self.end_time or time.time()) - self.start_time)



#   CSP — Sentence-based constraint propagation

class Sentence:
    """
    A CSP constraint: `cells` is a frozenset of (r,c) that together
    contain exactly `count` mines.
    """
    def __init__(self, cells, count):
        self.cells = frozenset(cells) # the group of cells
        self.count = count    # how many are mines

    def known_mines(self):
        return set(self.cells) if self.count == len(self.cells) else set()

    def known_safes(self):
        return set(self.cells) if self.count == 0 else set()

    def subtract(self, other):
        """Return new Sentence with `other` removed if `other ⊂ self`."""
        if other.cells <= self.cells and other.cells != self.cells:
            return Sentence(self.cells - other.cells, self.count - other.count)
        return None

    def __eq__(self, o):
        return isinstance(o, Sentence) and self.cells==o.cells and self.count==o.count

    def __repr__(self):
        return f"Sentence({set(self.cells)}, {self.count})"



#   HEURISTIC — mine-probability estimation

def estimate_probabilities(sentences, unrevealed, flagged_set):
    """
    Heuristic: for every unrevealed, un-flagged cell compute the
    average fraction of sentences that include it.

    Returns dict {(r,c): probability} for frontier cells.
    Lower = safer.
    """
    prob = {}
    counts = {}
    for s in sentences:
        if len(s.cells) == 0:
            continue
        p = s.count / len(s.cells)
        for cell in s.cells:
            if cell not in flagged_set and cell in unrevealed:
                prob[cell]   = prob.get(cell, 0.0) + p
                counts[cell] = counts.get(cell, 0) + 1
    # average
    for cell in prob:
        prob[cell] /= counts[cell]
    return prob



#   ADVERSARIAL SEARCH — Minimax risk evaluator

def minimax_risk(game, cell, depth=2):
    """
    Minimax: treat the agent as MAX (wants to survive)
    and the "board" as MIN (tries to maximise risk).

    We simulate a shallow minimax over the two possible
    outcomes of clicking `cell`:
      - safe  → agent gains +1 per newly-revealed neighbor
      - mine  → agent loses everything (-MINES)

    Returns a risk score ∈ [0, 1] (lower = safer choice).
    """
    r, c = cell
    if not game.started:
        # Before mines are placed every cell is equally risky
        return 1 / (ROWS * COLS)

    def max_val(board_sim, revealed_sim, flagged_sim, d):
        """Agent maximises: returns best expected safe-reveals count."""
        if d == 0:
            return 0
        unrevealed = {(rr,cc) for rr in range(ROWS) for cc in range(COLS)
                      if not revealed_sim[rr][cc] and not flagged_sim[rr][cc]}
        if not unrevealed:
            return 0
        best = -1e9
        # Agent picks a cell to explore (sample a few for efficiency)
        candidates = list(unrevealed)[:6]
        for nr, nc in candidates:
            val = min_val(board_sim, revealed_sim, flagged_sim, nr, nc, d-1)
            if val > best:
                best = val
        return best

    def min_val(board_sim, revealed_sim, flagged_sim, nr, nc, d):
        """Board tries to be adversarial: returns worst (min) outcome."""
        if board_sim[nr][nc] == -1:
            return -MINES           # mine → catastrophic
        # safe reveal → reward = 1 + future
        new_rev = [row[:] for row in revealed_sim]
        new_rev[nr][nc] = True
        gain = 1 + max_val(board_sim, new_rev, flagged_sim, d)
        return gain

    # Evaluate our target cell
    score = min_val(game.board, game.revealed, game.flagged, r, c, depth)
    # Normalise to [0,1] risk: lower score → higher risk
    max_score = ROWS * COLS
    risk = max(0.0, min(1.0, 1.0 - (score + MINES) / (max_score + MINES)))
    return risk


#   AI AGENT  (Model-Based Reflex Agent)

class MinesweeperAgent:
    """
    Model-Based Reflex Agent.

    Internal state:
      - knowledge : list of Sentence constraints (CSP)
      - safe_moves: cells guaranteed safe by CSP
      - mine_moves: cells guaranteed to be mines by CSP
      - last_action: description of most recent decision
      - last_type  : 'csp_safe' | 'csp_flag' | 'heuristic' | 'minimax' | 'random'
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.knowledge  = []
        self.safe_moves = set()
        self.mine_moves = set()
        self.known_mines_confirmed = set()
        self.known_safes_confirmed = set()
        self.last_action = "Agent ready."
        self.last_type   = None
        self.stats = {"csp":0, "heuristic":0, "minimax":0, "random":0, "flags":0}

    #  Perception: update knowledge base from revealed board
    def update_knowledge(self, game):
        unrevealed = {(r,c) for r in range(ROWS) for c in range(COLS)
                      if not game.revealed[r][c]}
        flagged_set = {(r,c) for r in range(ROWS) for c in range(COLS)
                       if game.flagged[r][c]}

        # Add new sentences from newly revealed numbered cells
        for r in range(ROWS):
            for c in range(COLS):
                if not game.revealed[r][c] or game.board[r][c] <= 0:
                    continue
                neighbors = list(game._neighbors(r,c))
                unknown_neighbors = [
                    (nr,nc) for nr,nc in neighbors
                    if not game.revealed[nr][nc]
                ]
                flagged_neighbors = [(nr,nc) for nr,nc in unknown_neighbors
                                     if game.flagged[nr][nc]]
                hidden_neighbors  = [(nr,nc) for nr,nc in unknown_neighbors
                                     if not game.flagged[nr][nc]]

                mines_left = game.board[r][c] - len(flagged_neighbors)
                if hidden_neighbors and mines_left >= 0:
                    s = Sentence(hidden_neighbors, mines_left)
                    if s not in self.knowledge:
                        self.knowledge.append(s)

        # CSP inference loop
        changed = True
        while changed:
            changed = False

            new_mines = set()
            new_safes = set()
            for s in self.knowledge:
                new_mines |= s.known_mines()
                new_safes |= s.known_safes()

            for cell in new_mines - self.known_mines_confirmed:
                self.known_mines_confirmed.add(cell)
                self.mine_moves.add(cell)
                changed = True
            for cell in new_safes - self.known_safes_confirmed:
                self.known_safes_confirmed.add(cell)
                self.safe_moves.add(cell)
                changed = True

            # Subset rule: A ⊂ B → (B-A) = (B.count - A.count)
            new_sentences = []
            for i, s1 in enumerate(self.knowledge):
                for s2 in self.knowledge[i+1:]:
                    derived = s1.subtract(s2)
                    if derived and derived not in self.knowledge and derived not in new_sentences:
                        new_sentences.append(derived)
                        changed = True
                    derived2 = s2.subtract(s1)
                    if derived2 and derived2 not in self.knowledge and derived2 not in new_sentences:
                        new_sentences.append(derived2)
                        changed = True
            self.knowledge.extend(new_sentences)

        # Remove sentences with empty cell sets
        self.knowledge = [s for s in self.knowledge if len(s.cells) > 0]

        # Remove confirmed cells from safe/mine queues if already acted on
        self.safe_moves -= {(r,c) for r in range(ROWS) for c in range(COLS)
                            if game.revealed[r][c] or game.flagged[r][c]}
        self.mine_moves -= {(r,c) for r in range(ROWS) for c in range(COLS)
                            if game.flagged[r][c]}

    #Action: decide and execute next move 
    def act(self, game):
        if game.game_over:
            return

        self.update_knowledge(game)

        # Phase 1: Flag known mines (CSP certain) 
        for cell in list(self.mine_moves):
            r, c = cell
            if not game.flagged[r][c] and not game.revealed[r][c]:
                game.toggle_flag(r, c)
                self.mine_moves.discard(cell)
                self.last_action = f"CSP: flagged mine at {cell}"
                self.last_type   = "csp_flag"
                self.stats["flags"] += 1
                return

        # Phase 2: Reveal certain safe cells (CSP) 
        for cell in list(self.safe_moves):
            r, c = cell
            if not game.revealed[r][c] and not game.flagged[r][c]:
                game.reveal(r, c)
                self.safe_moves.discard(cell)
                self.last_action = f"CSP: safe reveal at {cell}"
                self.last_type   = "csp_safe"
                self.stats["csp"] += 1
                return

        #  Phase 3: First click or all unknown → pick corner/center 
        if not game.started:
            r, c = ROWS//2, COLS//2
            game.reveal(r, c)
            self.last_action = f"Uninformed start: center {(r,c)}"
            self.last_type   = "random"
            return

        #  Phase 4: Heuristic probability + Minimax tiebreaker 
        unrevealed = [(r,c) for r in range(ROWS) for c in range(COLS)
                      if not game.revealed[r][c] and not game.flagged[r][c]]
        if not unrevealed:
            return

        flagged_set = {(r,c) for r in range(ROWS) for c in range(COLS)
                       if game.flagged[r][c]}

        probs = estimate_probabilities(self.knowledge, set(unrevealed), flagged_set)

        if probs:
            # Among cells with lowest probability, use minimax to break ties
            min_p = min(probs.values())
            candidates = [cell for cell, p in probs.items() if p <= min_p + 0.05]

            # Minimax risk evaluation for each candidate
            risks = {cell: minimax_risk(game, cell) for cell in candidates}
            best  = min(risks, key=risks.get)

            if risks[best] < 0.35:
                self.last_type = "heuristic"
                self.stats["heuristic"] += 1
                self.last_action = f"Heuristic: reveal {best} (p={probs.get(best,0):.2f})"
            else:
                self.last_type = "minimax"
                self.stats["minimax"] += 1
                self.last_action = f"Minimax: safest guess {best} (risk={risks[best]:.2f})"
            game.reveal(*best)
        else:
            # Phase 5: Random uninformed fallback (BFS over unknowns) 
            # BFS from border cells inward to find least constrained cell
            border  = set()
            for r in range(ROWS):
                for c in range(COLS):
                    if game.revealed[r][c] and game.board[r][c] > 0:
                        for nr,nc in game._neighbors(r,c):
                            if not game.revealed[nr][nc] and not game.flagged[nr][nc]:
                                border.add((nr,nc))
            interior = set(unrevealed) - border
            pool = list(interior) if interior else unrevealed
            choice = random.choice(pool)
            game.reveal(*choice)
            self.last_action = f"Random fallback: {choice}"
            self.last_type   = "random"
            self.stats["random"] += 1


#  RENDERING

class Renderer:

    def __init__(self, screen):
        self.screen    = screen
        self.font_big  = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_med  = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_sm   = pygame.font.SysFont("Arial", 12)
        self.reset_rect = None

    def cell_rect(self, r, c):
        x = MARGIN + c*CELL
        y = MARGIN + TOP_BAR + r*CELL
        return pygame.Rect(x, y, CELL, CELL)

    def draw(self, game, agent, mode, hover, pressing, ai_overlay):
        self.screen.fill(GRAY_MID)
        self._draw_top_bar(game, mode, agent)
        self._draw_grid(game, agent, hover, pressing, ai_overlay)
        self._draw_message(game)
        self._draw_buttons(mode)
        pygame.display.flip()

    def _draw_top_bar(self, game, mode, agent):
        pygame.draw.rect(self.screen, BLUE_BAR, (0, 0, WIN_W, TOP_BAR))

        # Mine counter
        mine_txt = self.font_big.render(f"💣 {game.mines_left:02d}", True, WHITE)
        self.screen.blit(mine_txt, (10, 8))

        # Timer
        time_txt = self.font_big.render(f"⏱ {min(game.seconds,999):03d}", True, WHITE)
        self.screen.blit(time_txt, (WIN_W - time_txt.get_width() - 10, 8))

        # Mode label
        mode_lbl = self.font_med.render(f"{'🤖 AI MODE' if mode=='ai' else '🎮 MANUAL'}", True,
                                        AI_HIGHLIGHT if mode=='ai' else (200,200,255))
        self.screen.blit(mode_lbl, (WIN_W//2 - mode_lbl.get_width()//2, 8))

        # Face reset
        face = "😎" if game.victory else ("💀" if game.game_over else "🙂")
        face_s = pygame.font.SysFont("Segoe UI Emoji", 26).render(face, True, WHITE)
        fx = WIN_W//2 - face_s.get_width()//2
        fy = 30
        self.screen.blit(face_s, (fx, fy))
        self.reset_rect = pygame.Rect(fx-4, fy-2, face_s.get_width()+8, face_s.get_height()+4)

        # AI status line
        if mode == 'ai' and agent:
            color_map = {"csp_safe": AI_HIGHLIGHT, "csp_flag": AI_FLAG_CLR,
                         "heuristic": AI_GUESS_CLR, "minimax": MINIMAX_CLR,
                         "random": (200,200,200)}
            clr = color_map.get(agent.last_type, WHITE)
            msg = self.font_sm.render(agent.last_action[:60], True, clr)
            self.screen.blit(msg, (6, TOP_BAR - 18))

            # stats
            st = agent.stats
            stats_txt = self.font_sm.render(
                f"CSP:{st['csp']}  Heur:{st['heuristic']}  MM:{st['minimax']}  Rnd:{st['random']}  Flags:{st['flags']}",
                True, (180,210,255))
            self.screen.blit(stats_txt, (WIN_W//2 - stats_txt.get_width()//2, TOP_BAR - 18))
        else:
            hint = self.font_sm.render("R=Reset  Right-click=Flag  Space=AI Step  A=Auto  M=Manual", True, (180,200,230))
            self.screen.blit(hint, (WIN_W//2 - hint.get_width()//2, TOP_BAR - 16))

    def _draw_grid(self, game, agent, hover, pressing, ai_overlay):
        for r in range(ROWS):
            for c in range(COLS):
                rect = self.cell_rect(r, c)
                self._draw_cell(game, r, c, rect, hover, pressing, ai_overlay)

    def _draw_cell(self, game, r, c, rect, hover, pressing, ai_overlay):
        is_hover    = (hover == (r,c)) and not game.game_over
        is_pressing = (pressing == (r,c)) and not game.game_over

        if game.revealed[r][c]:
            val = game.board[r][c]
            bg  = RED if val == -1 else GRAY_OPEN
            pygame.draw.rect(self.screen, bg, rect)
            pygame.draw.rect(self.screen, GRAY_DARK, rect, 1)
            if val == -1:
                self._icon(rect, "💣", 22)
            elif val > 0:
                t = self.font_big.render(str(val), True, NUM_COLOR[val])
                self.screen.blit(t, t.get_rect(center=rect.center))
        else:
            if game.game_over and not game.victory and (r,c) in game.mines_set and not game.flagged[r][c]:
                pygame.draw.rect(self.screen, (230,180,180), rect)
                pygame.draw.rect(self.screen, GRAY_DARK, rect, 1)
                self._icon(rect, "💣", 22)
                return

            # AI overlay tint
            overlay = ai_overlay.get((r,c))
            if overlay:
                bg = overlay
            elif is_pressing:
                bg = GRAY_OPEN
            elif is_hover:
                bg = (235,235,235)
            else:
                bg = GRAY_LIGHT

            pygame.draw.rect(self.screen, bg, rect)

            b = 3
            pygame.draw.rect(self.screen, WHITE,     (rect.x,            rect.y,             rect.w, b))
            pygame.draw.rect(self.screen, WHITE,     (rect.x,            rect.y,             b, rect.h))
            pygame.draw.rect(self.screen, GRAY_DARK, (rect.x,            rect.y+rect.h-b,    rect.w, b))
            pygame.draw.rect(self.screen, GRAY_DARK, (rect.x+rect.w-b,   rect.y,             b, rect.h))

            if game.flagged[r][c]:
                self._icon(rect, "🚩", 20)
                if game.game_over and not game.victory and (r,c) not in game.mines_set:
                    pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 3)
                    pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 3)

    def _icon(self, rect, text, size):
        f = pygame.font.SysFont("Segoe UI Emoji", size)
        t = f.render(text, True, BLACK)
        self.screen.blit(t, t.get_rect(center=rect.center))

    def _draw_message(self, game):
        if not game.game_over:
            return
        msg   = f"  You Win! 🎉  {game.seconds}s  " if game.victory else "  Game Over! 💥  Press R  "
        color = (30,160,30) if game.victory else (180,30,30)
        box   = pygame.Surface((WIN_W, 40), pygame.SRCALPHA)
        box.fill((*color, 210))
        self.screen.blit(box, (0, TOP_BAR + ROWS*CELL//2 - 20 + MARGIN))
        f = pygame.font.SysFont("Arial", 20, bold=True)
        t = f.render(msg, True, WHITE)
        self.screen.blit(t, t.get_rect(center=(WIN_W//2, TOP_BAR + ROWS*CELL//2 + MARGIN)))

    def _draw_buttons(self, mode):
        y = TOP_BAR + ROWS*CELL + MARGIN*2
        bw = WIN_W // 4 - 4
        buttons = [
            ("Manual (M)",  BTN_MANUAL, 2),
            ("AI Auto (A)", BTN_AI,     bw+6),
            ("AI Step (SP)",BTN_STEP,   (bw+6)*2),
            ("Reset (R)",   BTN_RESET,  (bw+6)*3),
        ]
        for label, color, x in buttons:
            rect = pygame.Rect(x, y+4, bw, BTN_BAR-8)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            txt = self.font_sm.render(label, True, WHITE)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def button_at(self, mx, my):
        y = TOP_BAR + ROWS*CELL + MARGIN*2
        bw = WIN_W // 4 - 4
        for label, _, x in [("manual", None, 2), ("ai_auto", None, bw+6),
                              ("ai_step", None, (bw+6)*2), ("reset", None, (bw+6)*3)]:
            if pygame.Rect(x, y+4, bw, BTN_BAR-8).collidepoint(mx, my):
                return label
        return None


#  HELPER: build AI overlay colours

def build_ai_overlay(game, agent):
    """
    Show the agent's internal belief state as cell tints:
      green  → CSP-confirmed safe
      orange → CSP-confirmed mine
      yellow → heuristic low-probability
    """
    overlay = {}
    if agent is None:
        return overlay

    flagged_set  = {(r,c) for r in range(ROWS) for c in range(COLS) if game.flagged[r][c]}
    unrevealed   = {(r,c) for r in range(ROWS) for c in range(COLS)
                    if not game.revealed[r][c] and not game.flagged[r][c]}
    probs        = estimate_probabilities(agent.knowledge, unrevealed, flagged_set)

    for cell in agent.safe_moves:
        if not game.revealed[cell[0]][cell[1]]:
            overlay[cell] = AI_HIGHLIGHT
    for cell in agent.mine_moves:
        if not game.revealed[cell[0]][cell[1]] and not game.flagged[cell[0]][cell[1]]:
            overlay[cell] = AI_FLAG_CLR
    for cell, p in probs.items():
        if cell not in overlay:
            t = max(0, min(1, p))
            overlay[cell] = (int(255*t), int(230*(1-t)), 80)
    return overlay


#  INPUT HELPERS

def get_cell(mx, my):
    c = (mx - MARGIN) // CELL
    r = (my - MARGIN - TOP_BAR) // CELL
    if 0 <= r < ROWS and 0 <= c < COLS:
        return (r, c)
    return None


#  MAIN LOOP

def main():
    pygame.init()
    screen   = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("💣 Minesweeper + AI Agent")

    game     = Minesweeper()
    agent    = MinesweeperAgent()
    renderer = Renderer(screen)

    mode         = "manual"   # "manual" or "ai"
    ai_auto      = False      # auto-step AI every interval
    ai_timer     = 0
    AI_INTERVAL  = 400        # ms between AI steps

    hover    = None
    pressing = None
    clock    = pygame.time.Clock()

    while True:
        dt = clock.tick(60)

        # AI auto-step
        if mode == "ai" and ai_auto and not game.game_over:
            ai_timer += dt
            if ai_timer >= AI_INTERVAL:
                ai_timer = 0
                agent.act(game)

        # Build overlay for rendering
        ai_overlay = build_ai_overlay(game, agent) if mode == "ai" else {}

        #  Events 
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game = Minesweeper(); agent = MinesweeperAgent(); pressing = None
                elif event.key == pygame.K_m:
                    mode = "manual"; ai_auto = False
                elif event.key == pygame.K_a:
                    mode = "ai"; ai_auto = True; ai_timer = 0
                elif event.key == pygame.K_SPACE:
                    mode = "ai"; ai_auto = False
                    if not game.game_over:
                        agent.act(game)

            if event.type == pygame.MOUSEMOTION:
                hover = get_cell(*event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Reset face
                if renderer.reset_rect and renderer.reset_rect.collidepoint(mx, my):
                    game = Minesweeper(); agent = MinesweeperAgent(); pressing = None; continue

                # Button bar
                btn = renderer.button_at(mx, my)
                if btn == "manual":
                    mode = "manual"; ai_auto = False; continue
                elif btn == "ai_auto":
                    mode = "ai"; ai_auto = True; ai_timer = 0; continue
                elif btn == "ai_step":
                    mode = "ai"; ai_auto = False
                    if not game.game_over: agent.act(game)
                    continue
                elif btn == "reset":
                    game = Minesweeper(); agent = MinesweeperAgent(); pressing = None; continue

                # Grid clicks (manual mode only)
                if mode == "manual":
                    cell = get_cell(mx, my)
                    if cell is None: continue
                    if event.button == 1:
                        pressing = cell
                    elif event.button == 3:
                        game.toggle_flag(*cell)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and pressing and mode == "manual":
                    cell = get_cell(*event.pos)
                    if cell == pressing:
                        r, c = pressing
                        if game.revealed[r][c]:
                            game.chord(r, c)
                        else:
                            game.reveal(r, c)
                    pressing = None

        renderer.draw(game, agent, mode, hover, pressing, ai_overlay)


if __name__ == "__main__":
    main()

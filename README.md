
Minesweeper with AI Agent
Implements: Agents, Uninformed Search (BFS), Heuristics, CSP, Adversarial Search (Minimax)
Modes:
  - Manual Mode  : Classic player-controlled game
  - AI Mode      : Agent solves the board autonomously, step by step

 Model-Based Reflex Agent.

    Internal state:
      - knowledge : list of Sentence constraints (CSP)
      - safe_moves: cells guaranteed safe by CSP
      - mine_moves: cells guaranteed to be mines by CSP
      - last_action: description of most recent decision
      - last_type  : 'csp_safe' | 'csp_flag' | 'heuristic' | 'minimax' | 'random'
    

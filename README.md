# 💣 Minesweeper AI
 
A fully playable Minesweeper game built in Python with an autonomous AI agent that can solve the board step by step. The application supports two modes: **Manual Mode** where the user plays normally, and **AI Mode** where the agent takes full control and solves the board using CSP, heuristics, and adversarial search.
 
---
 
## 📸 Preview
 
> *Manual Mode — play yourself | AI Mode — watch the agent solve it*
 
---
 
## 🎮 Features
 
- **Dual-Mode Gameplay** — switch between playing yourself or watching the AI
- **AI Solver** with 5 decision layers (CSP → Heuristic → Minimax → Random)
- **Real-time AI visualization** — see what the agent is thinking after each move
- **Live stats panel** — tracks how many moves came from each strategy
- **Safe first click** — mines are placed after the first click, never on it
- **BFS flood fill** — blank regions auto-expand just like the classic game
- **Flag system** — right-click to mark suspected mines
- **Timer + Mine counter** in the top bar
- Fully reset-able at any time with `R` or the 🙂 button
---
 
## 🧠 AI Architecture
 
The AI is a **Model-Based Reflex Agent** — it maintains an internal knowledge base that grows with every revealed cell and uses it to reason about hidden mine positions.
 
### Decision Hierarchy (in priority order)
 
| Priority | Strategy | Description |
|----------|-----------|-------------|
| 1 | **CSP — Flag Mines** | Logically proven mines are flagged immediately |
| 2 | **CSP — Safe Reveal** | Logically proven safe cells are revealed with 100% certainty |
| 3 | **Opening Move** | First click targets the center of the board |
| 4 | **Heuristic + Minimax** | Probability estimation + 2-step lookahead for forced guesses |
| 5 | **Random Fallback** | Interior cells preferred when no constraint information exists |
 

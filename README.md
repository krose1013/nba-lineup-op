# NBA 5-Man Lineup Optimizer

**Author:** Kylah Rose  
**Live Demo:** (https://nba-lineup-op-4eiwe4sefhpwfgz6zhpn7a.streamlit.app/)  
**Repository:** [github.com/krose1013/nba-lineup-op](https://github.com/krose1013/nba-lineup-op)  

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?style=flat&logo=scipy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)

---

## Project Overview

The **NBA 5-Man Lineup Optimizer** is an interactive web-based analytics dashboard designed to help basketball analysts and front-office personnel build optimal 5-player lineups. Using **Mixed-Integer Linear Programming (MILP)** powered by `scipy.optimize.milp`, the application maximizes overall lineup scoring potential while enforcing roster size rules, minimum performance floors, player locks, and positional balance.

Data is dynamically ingested from the official NBA API for players with at least 5 games played, processed through custom rating algorithms, stored in an optimized local SQLite database (`nba_rosters.db`), and deployed live on Streamlit Cloud.



## Key Features

- **Automated NBA Data Ingestion:** Fetches per-game player statistics and official team rosters for the **2025–26 NBA season** (filtering for `GP ≥ 5`).
- **Composite Playmaking Index:** Utilizes a custom formula that balances high assist volume against turnover penalty to evaluate true playmaking efficiency.
- **MILP Optimization Engine:** Solves complex combinatorial decisions instantly, finding mathematically proven optimal 5-player groups under user-defined constraints and core-player locks.
- **Interactive Streamlit Interface:** Features slider controls for performance thresholds, player locking options, instant team filtering, and real-time KPI metric visualizations.
- **Database Caching:** Uses `@st.cache_data` on SQLite queries to eliminate redundant database hits and ensure instant dashboard responsiveness.


## Mathematical Formulation

### 1. Objective Function
The optimizer selects a 5-player combination from a given team roster $N$ to maximize total lineup shooting output:

$$\text{Maximize } Z = \sum_{i \in N} \text{Shooting}_i \cdot x_i$$

Where:
- $x_i \in \{0, 1\}$ is a binary decision variable indicating whether player $i$ is selected ($1$) or not ($0$).
- For user-locked players $L \subset N$, $x_j = 1 \quad \forall j \in L$.
- $\text{Shooting}_i$ is the normalized 1–10 rating assigned to player $i$.



### 2. Constraint Matrix

The decision variables are subjected to the following mathematical constraints:

1. **Exact Roster Size Constraint:** Lineups must contain exactly 5 players:
   $$\sum_{i \in N} x_i = 5$$

2. **Rebounding Floor Constraint:** Combined rebounding rating must meet or exceed the user threshold ($T_{\text{reb}}$):
   $$\sum_{i \in N} \text{Rebounding}_i \cdot x_i \ge T_{\text{reb}}$$

3. **Playmaking Floor Constraint:** Combined playmaking rating must meet or exceed the user threshold ($T_{\text{play}}$):
   $$\sum_{i \in N} \text{Playmaking}_i \cdot x_i \ge T_{\text{play}}$$

4. **Positional Flexibility Constraints:** Ensures basic positional coverage across available player eligibility:
   $$\sum_{i \in \text{Guards}} x_i \ge 1, \quad \sum_{i \in \text{Forwards}} x_i \ge 1, \quad \sum_{i \in \text{Centers}} x_i \ge 1$$



### 3.Composite Playmaking Index

To prevent rewarding players with inflated assist counts resulting from high turnover rates, playmaking ratings are computed using a weighted efficiency index:

$$\text{Playmaking Index} = \text{APG} \times \left( \frac{\text{AST}}{\text{AST} + \text{TOV}} \right)$$

*Note: Raw statistics are normalized onto a 1–10 scale across qualified league players using Min-Max scaling.*


## System Architecture

```text
nba-lineup-op/
├── database.py         # Ingests NBA API stats & builds SQLite schema
├── lineup.py           # Streamlit UI dashboard & MILP optimization logic
├── nba_rosters.db      # SQLite database storing scaled 2025-26 player metrics
└── requirements.txt    # Production dependencies (streamlit, pandas, scipy, nba_api)

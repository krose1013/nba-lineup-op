import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from scipy.optimize import LinearConstraint, milp, Bounds

st.set_page_config(page_title="NBA Roster Optimizer", layout="wide")
st.title("NBA 5-Man Lineup Optimizer")

# SQL DATA RETRIEVAL
def get_all_teams():
    conn = sqlite3.connect("nba_rosters.db")
    df = pd.read_sql_query("SELECT DISTINCT team_name FROM players ORDER BY team_name ASC", conn)
    conn.close()
    return df['team_name'].tolist()

def get_team_roster(team_name):
    conn = sqlite3.connect("nba_rosters.db")
    query = """
    SELECT player_name, position, ppg, rpg, apg, topg, shooting, rebounding, playmaking 
    FROM players 
    WHERE team_name = ?
    """
    df = pd.read_sql_query(query, conn, params=(team_name,))
    conn.close()
    return df

#SIDEBAR CONTROLS
st.sidebar.header("1. Select Franchise")
all_teams = get_all_teams()
selected_team = st.sidebar.selectbox("Choose Team:", all_teams)

roster_df = get_team_roster(selected_team)

st.sidebar.header("2. Player Locks")
locked_players = st.sidebar.multiselect(
    "Lock Players into Lineup (Max 5):",
    options=roster_df['player_name'].tolist(),
    max_selections=5
)

st.sidebar.header("3. Optimization Thresholds")
min_rebound = st.sidebar.slider("Min Combined Rebound Rating (1-10 Scale)", 10, 45, 20)
min_playmaking = st.sidebar.slider("Min Combined Playmaking Rating (1-10 Scale)", 10, 45, 20)

#DISPLAY ROSTER
st.subheader(f"Current Roster & Statistics: {selected_team}")

display_roster = roster_df.rename(columns={
    'player_name': 'Player',
    'position': 'Pos',
    'ppg': 'PPG',
    'rpg': 'RPG',
    'apg': 'APG',
    'topg': 'TOV',
    'shooting': 'Scoring Rating',
    'rebounding': 'Rebound Rating',
    'playmaking': 'Playmaking Rating'
})

st.dataframe(display_roster, use_container_width=True)

#OPTIMIZATION ALGORITHM
if st.button("Generate Optimal Lineup", type="primary"):
    num_players = len(roster_df)
    
    # Objective: Maximize Shooting Rating (-1 * shooting)
    c = -roster_df['shooting'].values
    
    # Core Constraints
    rule_total_5 = np.ones(num_players)
    rule_rebound = roster_df['rebounding'].values
    rule_playmaking = roster_df['playmaking'].values
    
    constraints_list = [rule_total_5, rule_rebound, rule_playmaking]
    lower_bounds = [5, min_rebound, min_playmaking]
    upper_bounds = [5, np.inf, np.inf]
    
    # User-Locked Players
    for locked in locked_players:
        lock_rule = np.where(roster_df['player_name'] == locked, 1, 0)
        constraints_list.append(lock_rule)
        lower_bounds.append(1)
        upper_bounds.append(1)
        
    constraints_matrix = np.vstack(constraints_list)
    constraints = LinearConstraint(constraints_matrix, lb=lower_bounds, ub=upper_bounds)
    
    integrality = np.ones(num_players)
    bounds = Bounds(0, 1)
    
    res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)
    
    if res.success:
        selected_indices = np.where(res.x > 0.5)[0]
        optimal_lineup = roster_df.iloc[selected_indices]
        
        st.success("Optimal 5-Man Unit Found!")
        
        # Display Combined Averages
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Projected PPG", f"{optimal_lineup['ppg'].sum():.1f}")
        col2.metric("Projected RPG", f"{optimal_lineup['rpg'].sum():.1f}")
        col3.metric("Projected APG", f"{optimal_lineup['apg'].sum():.1f}")
        col4.metric("Projected TOV", f"{optimal_lineup['topg'].sum():.1f}")
        
        lineup_display = optimal_lineup.rename(columns={
            'player_name': 'Player',
            'position': 'Pos',
            'ppg': 'PPG',
            'rpg': 'RPG',
            'apg': 'APG',
            'topg': 'TOV',
            'shooting': 'Scoring Rating',
            'rebounding': 'Rebound Rating',
            'playmaking': 'Playmaking Rating'
        })
        
        st.subheader("Recommended Lineup:")
        st.dataframe(lineup_display, use_container_width=True)
    else:
        st.error("No valid lineup meets all constraints! Relax slider thresholds or adjust locked players.")
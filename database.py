import sqlite3
import pandas as pd
import numpy as np
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster, leaguedashplayerstats

def scale_to_rating(series, min_rating=1, max_rating=10):
    """Converts a Pandas Series of raw stats into an integer rating from 1 to 10."""
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(5, index=series.index)
    scaled = min_rating + (max_rating - min_rating) * ((series - s_min) / (s_max - s_min))
    return scaled.round().clip(min_rating, max_rating).astype(int)

def build_nba_database():
    print("1. Fetching per-game statistics and turnovers from NBA API...")
    
    stats_endpoint = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='PerGame')
    stats_df = stats_endpoint.get_data_frames()[0]
    stats_df = stats_df[stats_df['GP'] >= 5].copy()

    # --- COMPOSITE PLAYMAKING INDEX ---
    # Formula: APG * (AST / (AST + TOV))
    # Protect against division by zero if AST + TOV == 0
    ast_tov_sum = stats_df['AST'] + stats_df['TOV']
    ast_ratio = np.where(ast_tov_sum > 0, stats_df['AST'] / ast_tov_sum, 0)
    stats_df['playmaking_index'] = stats_df['AST'] * ast_ratio

    # Calculate 1-10 Scaled Ratings
    stats_df['shooting_rating'] = scale_to_rating(stats_df['PTS'])
    stats_df['rebounding_rating'] = scale_to_rating(stats_df['REB'])
    stats_df['playmaking_rating'] = scale_to_rating(stats_df['playmaking_index'])

    print("2. Connecting to SQLite and building schema...")
    conn = sqlite3.connect("nba_rosters.db")
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS players")
    cursor.execute("""
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY,
        team_id INTEGER,
        team_name TEXT,
        player_name TEXT,
        position TEXT,
        ppg REAL,
        rpg REAL,
        apg REAL,
        topg REAL,
        shooting INTEGER,
        rebounding INTEGER,
        playmaking INTEGER
    )
    """)
    
    all_teams = teams.get_teams()
    all_players = []
    
    for team in all_teams:
        team_id = team['id']
        team_name = team['full_name']
        print(f"Processing roster: {team_name}")
        
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            
            for _, row in roster.iterrows():
                p_id = int(row['PLAYER_ID'])
                p_name = str(row['PLAYER'])
                pos = str(row['POSITION']) if row['POSITION'] else 'G'
                
                player_stat = stats_df[stats_df['PLAYER_ID'] == p_id]
                
                if not player_stat.empty:
                    ppg = round(float(player_stat['PTS'].values[0]), 1)
                    rpg = round(float(player_stat['REB'].values[0]), 1)
                    apg = round(float(player_stat['AST'].values[0]), 1)
                    topg = round(float(player_stat['TOV'].values[0]), 1)
                    
                    shooting = int(player_stat['shooting_rating'].values[0])
                    rebounding = int(player_stat['rebounding_rating'].values[0])
                    playmaking = int(player_stat['playmaking_rating'].values[0])
                else:
                    ppg, rpg, apg, topg = 0.0, 0.0, 0.0, 0.0
                    shooting, rebounding, playmaking = 1, 1, 1
                
                all_players.append((
                    p_id, int(team_id), team_name, p_name, pos,
                    ppg, rpg, apg, topg, shooting, rebounding, playmaking
                ))
        except Exception as e:
            print(f"Error fetching {team_name}: {e}")
            
    cursor.executemany("""
    INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_players)
    
    conn.commit()
    conn.close()
    print("SQL Database successfully updated with Composite Playmaking Ratings!")

if __name__ == "__main__":
    build_nba_database()
from nba_api.stats.endpoints import (
    playercareerstats,
    commonplayerinfo,
    leaguedashteamstats,
    teamgamelog,
    teaminfocommon,
    teamestimatedmetrics
)
from nba_api.stats.library.parameters import (
    PerModeDetailed,
    MeasureTypeDetailedDefense
)
from nba_api.stats.static import players, teams
import time
from config import API_DELAY
from thefuzz import process

headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nba.com/',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

def find_player(name: str):
    """Find a player by name, returns the first match or None."""
    all_players = players.get_active_players()
    names = [p["full_name"] for p in all_players]

    match, score = process.extractOne(name, names)

    if score < 60:
        return None

    return next(p for p in all_players if p["full_name"] == match)


def find_team(name: str):
    """Find a team by name using fuzzy matching"""
    all_teams = teams.get_teams()

    # Search across full name, nickname, and abbr
    by_full = {t["full_name"]: t for t in all_teams}
    by_nickname = {t["nickname"]: t for t in all_teams}
    by_abbr = {t["abbreviation"]: t for t in all_teams}
    combined = {**by_full, **by_nickname, **by_abbr}

    match, score = process.extractOne(name, combined.keys())

    if score < 60:
        return None
    
    print(f"Found team: {match}")
    
    return combined[match]


def get_player_stats(player_id: int) -> dict:
    """Get current season stats and per 36 stats for a player."""
    time.sleep(API_DELAY)  # Avoid rate limiting
    career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=10, headers=headers)
    df = career.get_data_frames()[0]

    if df.empty:
        return None

    # Get most recent season
    latest = df.iloc[-1]

    gp = latest["GP"]
    min_per_game = latest["MIN"] / gp if gp > 0 else 0

    stats = {
        "season": latest["SEASON_ID"],
        "team": latest["TEAM_ABBREVIATION"],
        "gp": int(gp),
        "mpg": round(min_per_game, 1),
        "ppg": round(latest["PTS"] / gp, 1) if gp > 0 else 0,
        "rpg": round(latest["REB"] / gp, 1) if gp > 0 else 0,
        "apg": round(latest["AST"] / gp, 1) if gp > 0 else 0,
        "spg": round(latest["STL"] / gp, 1) if gp > 0 else 0,
        "bpg": round(latest["BLK"] / gp, 1) if gp > 0 else 0,
        "fg_pct": round(latest["FG_PCT"] * 100, 1) if latest["FG_PCT"] else 0,
        "fg3_pct": round(latest["FG3_PCT"] * 100, 1) if latest["FG3_PCT"] else 0,
        "ft_pct": round(latest["FT_PCT"] * 100, 1) if latest["FT_PCT"] else 0,
    }

    # Per 36 stats
    total_min = latest["MIN"]
    if total_min > 0:
        factor = 36 / (total_min / gp) if gp > 0 else 0
        stats["per36"] = {
            "pts": round(stats["ppg"] * factor, 1),
            "reb": round(stats["rpg"] * factor, 1),
            "ast": round(stats["apg"] * factor, 1),
            "stl": round(stats["spg"] * factor, 1),
            "blk": round(stats["bpg"] * factor, 1),
        }
    else:
        stats["per36"] = None

    return stats


def get_team_stats(team_id: int) -> dict:
    try:
        """Get team net rating for the season and last 10 games."""
        time.sleep(API_DELAY)

        # Season net rating
        print("Fetching season stats...")
        league_stats = with_retry(lambda: leaguedashteamstats.LeagueDashTeamStats(timeout=10, headers=headers))
        df = league_stats.get_data_frames()[0]
        team_row = df[df["TEAM_ID"] == team_id]

        if team_row.empty:
            return None

        team_row = team_row.iloc[0]

        # Last 10 games
        print("Fetching last 10 games...")
        time.sleep(API_DELAY)
        last10 = with_retry(lambda: leaguedashteamstats.LeagueDashTeamStats(per_mode_detailed=PerModeDetailed.per_100_possessions, measure_type_detailed_defense=MeasureTypeDetailedDefense.advanced, last_n_games=10, timeout=10, headers=headers))
        df_last10 = last10.get_data_frames()[0]
        last10_row = df_last10[df_last10["TEAM_ID"] == team_id]
        last10_row = last10_row.iloc[0] if not last10_row.empty else None

        stats = {
            "name": team_row["TEAM_NAME"],
            "wins": int(team_row["W"]),
            "losses": int(team_row["L"]),
            "last10": {
                "wins": int(last10_row["W"]) if last10_row is not None else "N/A",
                "losses": int(last10_row["L"]) if last10_row is not None else "N/A",
                "net_rating": round(float(last10_row["NET_RATING"]), 1) if last10_row is not None else "N/A",
            },
        }

        # Upcoming schedule (last 5 games from game log as a proxy)
        print("Fetching game log...")
        time.sleep(API_DELAY)
        game_log = with_retry(lambda: teamgamelog.TeamGameLog(team_id=team_id, timeout=10, headers=headers))
        games_df = game_log.get_data_frames()[0]
        recent_games = []
        for _, game in games_df.head(5).iterrows():
            recent_games.append({
                "date": game["GAME_DATE"],
                "matchup": game["MATCHUP"],
                "result": game["WL"],
                "pts": int(game["PTS"]),
            })
        stats["recent_games"] = recent_games
        
        print("Done!")
        print(f"{stats}")

        return stats
    except Exception as e:
        print(f"API error: {e}")
        return None

def with_retry(fn, retries=3, delay=1):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    return None
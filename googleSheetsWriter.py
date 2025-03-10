import gspread
from oauth2client.service_account import ServiceAccountCredentials
import dashboard_dataScraper as t
import os

data = t.main()
next_game = data[0]
opp_record = data[1]
stars = data[2]
last_five = data[3]
last_vs_grind = data[4]
standings = data[5]

creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
creds_dict = json.loads(creds_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )

#scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Users\thech\Desktop\BeerLeagueStats\dashboard\python-project-431722-a3a0c9fb2d39.json", scope)
client = gspread.authorize(creds)

# --- Next Game Info --- #
opponentData = client.open("GrindersDashboard").worksheet("Opponent")
opponent_data = [
    ["Opponent Name", "GP", "W", "L", "OTL", "SOL", "PTS", "GF", "GA", "PIM", "Date", "Time", "Rink"],
    [next_game["opponent_name"],
    int(opp_record[1]), #GP
    int(opp_record[2]), #W
    int(opp_record[3]), #L
    int(opp_record[4]), #OTL
    int(opp_record[5]), #SOL
    int(opp_record[6]), #PTS
    int(opp_record[7]), #GF
    int(opp_record[8]), #GA
    int(opp_record[9]), #PIM
    next_game["date"],
    next_game["time"],
    next_game["rink"]]
    ]

opponentData.update(values=opponent_data, range_name="A1")

# --- Top Performers --- #
topPerf = client.open("GrindersDashboard").worksheet("TopPerformers")
players = []
for s in stars:
    stats = []
    stats.append(f"#{s['JerseyNumber']} {s['PlayerName']}")
    stats.append(int(s['G']))
    stats.append(int(s['A']))
    stats.append(int(s['PTS']))
    players.append(stats)

topPerf_data = [["Player Name", "G", "A", "PTS"]]
for p in players:
    topPerf_data.append(p)

topPerf.update(values=topPerf_data, range_name="B1")
topPerf.sort((4, "des"))
topPerf.update(values=[["Rank"], [1], [2], [3]], range_name="A1")

# --- Recent Games + Last vs Grind --- #
games = client.open("GrindersDashboard").worksheet("Recent Games")
#print(last_vs_grind)
games_data = [["Opponent","Opponent_Score","Team Name","Team Score","extra_time","game_id","opponent_players", "vs_grind"]]
for g in last_five:
    stats = []
    stats.append(g["opponent_name"])
    stats.append(int(g["opponent_score"]))
    stats.append(g["team_name"])
    stats.append(int(g["team_score"]))
    stats.append(g["extra_time"])
    stats.append(int(g["game_id"]))
    stats.append(int(g["opponent_players"]))
    games_data.append(stats)

games_data.append([last_vs_grind["opponent_name"]
    ,int(last_vs_grind["opponent_score"])
    ,last_vs_grind["team_name"]
    ,int(last_vs_grind["team_score"])
    ,last_vs_grind["extra_time"]
    ,int(last_vs_grind["game_id"])
    ,int(last_vs_grind["opponent_players"])
    , "Y"]
    )
games.update(values=games_data, range_name="C1")
games.update(values=[["Rank", "Result"], [1], [2], [3], [4], [5], [6]], range_name="A1")
formulas = [[f'=IF(D{i}>F{i}, "W", IF(ISBLANK(G{i}), "L", G{i}&"L"))'] for i in range(2, 8)]
games.update(range_name="B2:B7", values=formulas, raw=False)

# --- Standings --- #
stanSheet = client.open("GrindersDashboard").worksheet("Standings")
standings_data = [["Team","PTS","GP","W","L","OTL","SOL", "GF", "GA", "PIM", "matchup_ind"]]
for s in standings:
    x = []
    x.append(s["team_name"]),
    x.append(int(s["PTS"])),
    x.append(int(s["GP"])),
    x.append(int(s["W"])),
    x.append(int(s["L"])),
    x.append(int(s["OTL"])),
    x.append(int(s["SOL"])),
    x.append(int(s["GF"])),
    x.append(int(s["GA"])),
    x.append(int(s["PIM"])),
    x.append(s["matchup_ind"])
    standings_data.append(x)
stanSheet.update(values=standings_data, range_name="A1")

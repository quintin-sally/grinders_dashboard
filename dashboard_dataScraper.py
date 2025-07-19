import requests, re
from bs4 import BeautifulSoup

# Function to scrape season IDs (excluding "NYE")
def get_season_ids(main_url):
    response = requests.get(main_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    season_ids = []
    
    select_element = soup.find('select', {'name': 'SeasonsMenu'})
    if select_element:
        for option in select_element.find_all('option'):
            season_id = option.get('value')
            season_name = option.text.strip()
            if season_id and "NYE" not in season_name:
                season_ids.append((season_id, season_name))
    
    return season_ids

# Function to scrape division IDs that match "B1"
def get_division_ids_for_season(season_id):
    season_url = f"https://pointstreak.com/players/players-leagues.html?leagueid=1060&seasonid={season_id}"
    response = requests.get(season_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    divisions = []
    for a_tag in soup.find_all('a', class_='division'):
        href = a_tag.get('href')
        division_name = a_tag.text.strip()
        if 'divisionid=' in href:
            division_id = href.split('divisionid=')[1].split('&')[0]
            if any(level in division_name for level in ["B1"]): #update here to add additional divisions
                divisions.append((division_id, division_name))
    
    return divisions

# Function to scrape team names, team IDs, and additional 9 stats from division standings page
def get_teams_and_stats(season_id, division_id):
    division_standings_url_base = "https://pointstreak.com/players/players-division-standings.html?divisionid={divisionid}&seasonid={seasonid}"
    division_standings_url = division_standings_url_base.format(divisionid=division_id, seasonid=season_id) 
    #print(division_standings_url)
    response = requests.get(division_standings_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    standings_table = soup.find_all('table')  # find all tables on the page
    tables = soup.find_all('table')
    teams_data = []
    seen_team_ids = set()  # Set to keep track of processed team IDs
    
    for t in tables:
        rows = t.find_all('tr')
        for r in rows:
            cols = r.find_all('td')
            team_link = cols[0].find('a', href=True)
            if team_link and 'teamid=' in team_link['href']:
            # Extract team ID and team name
                team_id = team_link['href'].split('teamid=')[1].split('&')[0]
                if team_id in seen_team_ids:
                    continue  # Skip if team ID has already been processed
                team_name = team_link.text.strip()
                try:
                    check = cols[11]
                    # Extract the next 9 <td> elements for stats
                    team_stats = {
                        'team_id': team_id,
                        'team_name': team_name,
                        'GP': cols[1].text.strip(),
                        'W': cols[2].text.strip(),
                        'L': cols[3].text.strip(),
                        'OTL': cols[4].text.strip(),
                        'SOL': cols[5].text.strip(),
                        'PTS': cols[6].text.strip(),
                        'GF': cols[7].text.strip(),
                        'GA': cols[8].text.strip(),
                        'PIM': cols[9].text.strip(),
                        }
                except IndexError:
                    # Extract the next 9 <td> elements for stats
                    team_stats = {
                        'team_id': team_id,
                        'team_name': team_name,
                        'GP': cols[1].text.strip(),
                        'W': cols[2].text.strip(),
                        'L': cols[3].text.strip(),
                        'OTL':  0 ,
                        'SOL':  0 ,
                        'PTS': cols[4].text.strip() ,
                        'GF': cols[5].text.strip() ,
                        'GA': cols[6].text.strip() ,
                        'PIM': cols[7].text.strip(),
                        }
                teams_data.append(team_stats)
                seen_team_ids.add(team_id)  # Mark this team ID as processed
    return teams_data

def data_pending_check(td_tags):
    for t in td_tags:
        text = t.get_text(strip=True)
        if text == "data pending":
            return True
        if text == "I.C.Green":
            return True
        if text == "I.C.Blue":
            return True
        if text == "I.C.Red":
            return True
    return False
# New function to scrape Game IDs for a particular division and season
def get_next_game(season_id, division_id, grinders_id):
    division_schedule_url_base = "https://pointstreak.com/players/players-division-schedule.html?divisionid={divisionid}&seasonid={seasonid}"
    division_schedule_url = division_schedule_url_base.format(divisionid=division_id, seasonid=season_id)
    response = requests.get(division_schedule_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    home_tag = soup.find('td', string=re.compile(r"Home", re.IGNORECASE))
    schedule = home_tag.find_parent('table')
    rows = schedule.find_all('tr')
    for idx, r in enumerate(rows):
        if idx != 0 and idx != len(rows) - 1:
            td_tags = r.find_all('td')
            if data_pending_check(td_tags) == True:
                info = []
                teamIds = []
                for t in td_tags:
                    content = t.get_text(strip=True)
                    info.append(content)
                    if t.find('a', href = True):
                        a_tag = t.find('a')
                        if 'teamid' in a_tag['href']:
                            href = a_tag['href']
                            teamIds.append(href.split("teamid=")[1].split("&")[0])
                if "Grinders" in info:
                    if teamIds[0] == grinders_id:
                        home_id = grinders_id
                        away_id = teamIds[1]
                        opponent_id = teamIds[1]
                    else:
                        home_id = teamIds[0]
                        opponent_id = teamIds[0]
                        away_id = grinders_id
                    # Update date format for full month name
                    date_parts = info[2].split(", ")
                    # day_of_week = date_parts[0]
                    date_rest = date_parts[1].split(" ")
                    month = date_rest[0].replace("Jan", '1').replace("Feb", '2').replace("Mar", '3').replace("Apr", '4').replace("May", '5').replace("Jun", '6').replace("Jul", '7').replace("Aug", '8').replace("Sep", '9').replace("Oct", '10').replace("Nov", '11').replace("Dec", '12') # Handle short month names
                    formatted_date = f"{month}/{date_rest[1]}"
                    info[2] = formatted_date                       
                    next_game = {
                        "home_id": home_id,
                        "home": info[0],
                        "away_id": away_id,
                        "away": info[1],
                        "date": info[2],
                        "time": info[3],
                        "rink": info[4]
                        }
                    break
    return next_game


# Function to scrape team record and additional 9 stats from division standings page
def get_team_record(season_id, division_id, grinders_id, opponent_id):
    division_standings_url_base = "https://pointstreak.com/players/players-division-standings.html?divisionid={divisionid}&seasonid={seasonid}"
    division_standings_url = division_standings_url_base.format(divisionid=division_id, seasonid=season_id) 
    response = requests.get(division_standings_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table')
    teams_data = []
    seen_team_ids = set()  # Set to keep track of processed team IDs
    
    for t in tables:
        rows = t.find_all('tr')
        for r in rows:
            cols = r.find_all('td')
            team_link = cols[0].find('a', href=True)
            if team_link and 'teamid=' in team_link['href']:
            # Extract team ID and team name
                team_id = team_link['href'].split('teamid=')[1].split('&')[0]
                matchup_ind = "N"
                if team_id == grinders_id or team_id == opponent_id:
                    matchup_ind = "Y"
                if team_id in seen_team_ids:
                    continue  # Skip if team ID has already been processed
                team_name = team_link.text.strip()

                try:
                    check = cols[11]
                    # Extract the next 9 <td> elements for stats
                    team_stats = {
                        'team_id': team_id,
                        'team_name': team_name,
                        'GP': cols[1].text.strip(),
                        'W': cols[2].text.strip(),
                        'L': cols[3].text.strip(),
                        'OTL': cols[4].text.strip(),
                        'SOL': cols[5].text.strip(),
                        'PTS': cols[6].text.strip(),
                        'GF': cols[7].text.strip(),
                        'GA': cols[8].text.strip(),
                        'PIM': cols[9].text.strip(),
                        'matchup_ind': matchup_ind
                        }
                except IndexError:
                    # Extract the next 9 <td> elements for stats
                    team_stats = {
                        'team_id': team_id,
                        'team_name': team_name,
                        'GP': cols[1].text.strip(),
                        'W': cols[2].text.strip(),
                        'L': cols[3].text.strip(),
                        'OTL':  0 ,
                        'SOL':  0 ,
                        'PTS': cols[4].text.strip() ,
                        'GF': cols[5].text.strip() ,
                        'GA': cols[6].text.strip() ,
                        'PIM': cols[7].text.strip(),
                        'matchup_ind': matchup_ind
                        }
                teams_data.append(team_stats)
                seen_team_ids.add(team_id)  # Mark this team ID as processed
    return teams_data


def find_table(game_id, pattern, soup):
    #url = box_score_url_base.format(gameid=game_id)
    #response = requests.get(url)
    #soup = BeautifulSoup(response.content, 'html.parser')
    table_td = soup.find('td', string=re.compile(pattern, re.IGNORECASE))

    if table_td:
        return table_td.find_parent('table')
    
    return None

def get_game_info(opponent_id, season_id):
    team_schedule_url_base = "https://pointstreak.com/players/players-team-schedule.html?teamid={teamid}&seasonid={seasonid}"
    team_schedule_url = team_schedule_url_base.format(teamid=opponent_id, seasonid=season_id) 
    response = requests.get(team_schedule_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the <td> tag containing "Player Stats"
    schedule_td = soup.find('td', string=re.compile(r"Team Schedule", re.IGNORECASE))
    # Find the next table object for the starting point of the loop
    schedule = schedule_td.find_next('table')
    rows = schedule.find_all('tr')
    games = []
    for idx, r in enumerate(rows):
        if idx != 0 and idx != len(rows) - 1:
            td_tags = r.find_all('td')
            if data_pending_check(td_tags) == True:
                continue
            else:
                info = []
                for t in td_tags:
                   if t.find('a', string='final'):
                        f = t.find('a', string='final')
                        href = f.get('href')
                        game_id = href.split('gameid=')[1]
                        info.append(game_id)
                   if t.find('a', string='forfeit'):
                        f = t.find('a', string='forfeit')
                        href = f.get('href')
                        game_id = href.split('gameid=')[1]
                        info.append(game_id)
                   if t.find('a') and t.find('b') and not t.find('b', string = 'SO') and not t.find('b', string = 'OT'):
                        a_tag = t.find('a') #the team
                        href = a_tag.get('href')
                        teamId = href.split("teamid=")[1].split("&")[0]
                        teamName = a_tag.get_text(strip=True)
                        info.append(teamId)
                        info.append(teamName)#a_tag.get_text(strip=True))
                        b_tag = t.find('b') # the score
                        info.append(b_tag.get_text(strip=True))
                   else:
                        content = t.get_text(strip=True)
                        info.append(content)
                
                #print(info)
                opponent_team_flag = "H" if info[0] == opponent_id else "A"
                game_info = {
                    "opponent_id": info[0] if info[0] == opponent_id else info[3],
                    "opponent_name": info[1] if info[0] == opponent_id else info[4],
                    "opponent_score" : info[2] if info[0] == opponent_id else info[5],
                    "team_id": info[3] if info[0] == opponent_id else info[0],
                    "team_name": info[4] if info[0] == opponent_id else info[1],
                    "team_score": info[5] if info[0] == opponent_id else info[2],
                    "extra_time": info[9].replace("final", "").replace("forfeit", "").strip(),
                    "game_id": info[8]
                    }
                games.append(game_info) 

    if len(games) >= 5:
        for g in games:
            box_score_url_base = "https://pointstreak.com/players/players-boxscore.html?gameid={gameid}"
            url = box_score_url_base.format(gameid=game_id)
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rosters = find_table(game_id, "players", soup)
            tables = rosters.find_all('table') 
            lineups = tables[2:]
            home_players =  0
            away_players = 0
            for idx, l in enumerate(lineups):
                if idx == 0:
                    player_tags = l.find_all('a')
                    home_players = len(player_tags)
                if idx > 0:
                    player_tags = l.find_all('a')
                    away_players = len(player_tags)
            g['opponent_players'] = home_players if opponent_team_flag == "H" else away_players 
            
    return games

def get_top_performers(teamID, seasonID):
    # Construct the URL using the provided teamID and seasonID
    url = f"https://pointstreak.com/players/players-team-roster.html?teamid={teamID}&seasonid={seasonID}"
    
    # Send an HTTP request to fetch the HTML content
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None
    
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')
    
    # Find the <td> tag containing "Player Stats"
    player_stats_td = soup.find('td', string=re.compile(r"Player Stats", re.IGNORECASE))
    
    # Find the next table object for the starting point of the loop
    player_table = player_stats_td.find_next('table')

    # Go to the next table
    skipped_table = player_table.find_next('table')

    # and then go to the NEXT table for the goalie Stats
    goalie_stats_table = skipped_table.find_next('table')
    
    # Initialize dictionaries to store the data
    player_stats = []
    goalie_stats = []

    # If the "Player Stats" table is found
    if player_stats_td:

        # go to the next TR and add it to a list until the TR = the goalie stats TR
        r = False
        cnt = 0
        next_tr = player_table.find_next('tr')
        while r == False or cnt < 50:
            cnt += 1
            next_tr = next_tr.find_next('tr')
            link_check = next_tr.find('a')
            l = link_check['href'].split('playerid=')[1].split('&')[0].replace(" ", "")
            if l=="":
                r = True
                break
            cols = next_tr.find_all('td')
            playerID = next_tr.find('a')
            player_stats.append({
                'seasonID': seasonID,
                'teamID': teamID,
                'JerseyNumber': cols[0].get_text(strip=True),
                'playerId': playerID['href'].split('playerid=')[1].split('&')[0],
                'PlayerName': cols[1].get_text(strip=True),
                'GP': cols[2].get_text(strip=True),
                'G': cols[3].get_text(strip=True),
                'A': cols[4].get_text(strip=True),
                'PTS': cols[5].get_text(strip=True),
                'PIM': cols[6].get_text(strip=True),
                'PP': cols[7].get_text(strip=True),
                'SH': cols[8].get_text(strip=True)
                #'GWG': cols[9].get_text(strip=True)
                })

    # If the "Goalie Stats" table is found
    if goalie_stats_table:
        # Pass the TR rows into the a lit for iterating through
        goalie_rows = goalie_stats_table.find_all('tr')[1:]  #Skip the header row
        
        for row in goalie_rows:
            cols = row.find_all('td')
            g = cols[1].find('a')
            try:
                c = cols[11]
                goalie_stats.append({
                    'seasonID': seasonID,
                    'teamID': teamID,
                    'JerseyNumber': cols[0].get_text(strip=True),
                    'GoalieID': g['href'].split('playerid=')[1].split('&')[0],
                    'GoalieName': cols[1].get_text(strip=True),
                    'GP': cols[2].get_text(strip=True),
                    'MIN': cols[3].get_text(strip=True),
                    'W': cols[4].get_text(strip=True),
                    'L': cols[5].get_text(strip=True),
                    'T': cols[6].get_text(strip=True),
                    'SO': cols[7].get_text(strip=True),
                    'GA': cols[8].get_text(strip=True),
                    'GAA': cols[9].get_text(strip=True),
                    'SV': cols[10].get_text(strip=True),
                    'SVpercentage': cols[11].get_text(strip=True)
                    })
            except IndexError:
                goalie_stats.append({
                    'seasonID': seasonID,
                    'teamID': teamID,
                    'JerseyNumber': cols[0].get_text(strip=True),
                    'GoalieID': g['href'].split('playerid=')[1].split('&')[0],
                    'GoalieName': cols[1].get_text(strip=True),
                    'GP': cols[2].get_text(strip=True),
                    'MIN': cols[3].get_text(strip=True),
                    'W': cols[4].get_text(strip=True),
                    'L': cols[5].get_text(strip=True),
                    'T': 0,
                    'SO': cols[6].get_text(strip=True),
                    'GA': cols[7].get_text(strip=True),
                    'GAA': cols[8].get_text(strip=True),
                    'SV': cols[9].get_text(strip=True),
                    'SVpercentage': cols[10].get_text(strip=True)
                    })

    # Return a dictionary containing both player stats and goalie stats
    return {
        'Player Stats': player_stats,
        'Goalie Stats': goalie_stats
    }


def main(): 
    main_url = "https://pointstreak.com/players/players-leagues.html?leagueid=1060"
    grinders_id = 0
    season_ids = get_season_ids(main_url) #pulls all the season_ids from the dropdown menu #Sample: [(20179, 'Summer 2020'),(20533, 'ICAHL Summer 2021'),(20320, 'ICAHL Winter 20/21')]
    s = []
    for i in season_ids:
        s.append(int(i[0]))
    curr_season = max(s)
    division = get_division_ids_for_season(curr_season)[0][0]
    teams_stats = get_teams_and_stats(curr_season, division)
    
    if teams_stats:
        for t in teams_stats:
            if t['team_name'] == "Grinders":
                grinders_id = t['team_id']
    next_game = get_next_game(curr_season, division, grinders_id)
    if next_game['home_id'] == grinders_id:
        opponent_id = next_game['away_id']
        opponent_name = next_game['away']
    else:
        opponent_id = next_game['home_id']
        opponent_name = next_game['home']
    standings = get_team_record(curr_season, division, grinders_id, opponent_id)
    opp_record = []
    for t in standings:
        if t['team_id'] == opponent_id:
            opp_record.append(t['team_name']),
            opp_record.append(t['GP']),
            opp_record.append(t['W']),
            opp_record.append(t['L']),
            opp_record.append(t['OTL']),
            opp_record.append(t['SOL']),
            opp_record.append(t['PTS']),
            opp_record.append(t['GF']),
            opp_record.append(t['GA']),
            opp_record.append(t['PIM'])
            next_game["opponent_name"] = opp_record[0]

    game_info = get_game_info(opponent_id, curr_season)
    last_five = game_info[-5:]
    last_vs_grind = None
    for g in game_info:
        if g['team_id'] == grinders_id:
            last_vs_grind = g
    ## if the last game was from the previous season, we need to get the last game from the previous season
    if last_vs_grind is None:
        prior_season = sorted(s)[-2]  # Get the previous seasonID
        prior_division = get_division_ids_for_season(prior_season)[0][0] #pull the division ID for the previous season
        prior_teams_stats = get_teams_and_stats(prior_season, prior_division) #get the list of teams and IDs from previous season
        prior_opponent_id = None
        prior_grinders_id = None
        for t in prior_teams_stats: #looping through teams to get the previous season's ID for Grinders and their opponent
            if prior_opponent_id and prior_grinders_id is not None:
                break
            if t['team_name'].lower() == opponent_name.lower():
                prior_opponent_id = t['team_id']
            if t['team_name'].lower() == 'grinders':
                prior_grinders_id = t['team_id']
        if prior_opponent_id: #if we find a match pull the opponent's games info
            game_info_prior = get_game_info(prior_opponent_id, prior_season)
            # Find the games against the grinders and then find the most recent game (max game_id).
            games_with_grinders = [g for g in game_info_prior if g['team_id'] == prior_grinders_id]
            if games_with_grinders:
                last_vs_grind = max(games_with_grinders, key=lambda x: int(x['game_id']))
    # Set default if still None
    if last_vs_grind is None:
        last_vs_grind = {
            "opponent_id": 0,
            "opponent_name": opponent_name,
            "opponent_score": 0,
            "team_id": 0,
            "team_name": "Grinders",
            "team_score": 0,
            "extra_time": 0,
            "game_id": 0,
            "opponent_players": 0
        }
    players = get_top_performers(opponent_id, curr_season)
    stars = players['Player Stats'][:3]
    
    output = [next_game, opp_record, stars, last_five, last_vs_grind, standings]
    return output
    # #Output
    # print("Grinders next game is against: ", next_game["opponent_name"])
    # print(f"Scheduled for {next_game['date']} at {next_game['time']} on {next_game['rink']}")
    # print("Opp Record: ",opp_record)
    # print("Top Performers: ")
    # for s in stars:
        # print(f"#{s['JerseyNumber']} {s['PlayerName']} G:{s['G']} A:{s['A']} PTS: {s['PTS']}")
    # for g in last_five:
        # print(g)
    # print("last vs Grind: ", last_vs_grind)

    # print(" - - - Current Standings - - -")
    # for s in standings:
        # print(s['team_name'], s['PTS'])
    # print(" - - - Current Standings - - -")

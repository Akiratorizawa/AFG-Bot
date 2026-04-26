import discord
from services.errors import InvalidDivisionError, InvalidOperationError, InvalidJSONError
import requests
import json
import os
import sqlite3

def stats(attachment: discord.Attachment, operation: str, division: str, walkons: str):
    # Opening original JSON in .txt form from FF, a string object by convention
    if division.lower() not in ['d1', 'd2']:
        raise InvalidDivisionError(f"{division} is not a valid division. Input either D1 or D2.")

    if operation not in ['+', '-']:
        raise InvalidOperationError(f"{operation} is not a valid operation. Please choose either to record or delete stats.")
    
    division = division.lower()  

    try:                                                
        attachment = requests.get(attachment.url)
        content = attachment.text

    except:
        raise InvalidJSONError("Error reading file. Please try again.")

    # 1. Get the directory of THIS file (afg_bot/services)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Go up one level to reach the 'afg_bot' folder
    # This is now your BASE PATH hardcoded to the project root
    BASE_PATH = os.path.abspath(os.path.join(current_dir, ".."))

    # 3. Define your sub-folders relative to the BASE_PATH
    DB_FOLDER = os.path.join(BASE_PATH, "app", "databases")

    # List with scores at index 0 and stats at index 1
    json_parts = content.split(" /// ")
    
    # Initializing walks to be None by default
    walks = None

    # Making a list of walkons if ever walkons exists
    if walkons is not None:
        walkon_players = walkons.split(",")
        walks = []

        for i in range(len(walkon_players)):
            walks.append(walkon_players[i].strip())

    # List of scores, home team at index 0, away team at index 1
    scores = json_parts[0].split(' - ')

    try:
        # The two scores from the game
        home_score = scores[0]
        away_score = scores[1]

        # Initializing the stats from the game
        temp_stats = json_parts[1]
    
    except:
        raise InvalidJSONError("Invalid JSON. Please input a JSON from FF's \'Copy JSON\' Feature.")
    
    else:
        for i in range(len(scores)):
            scores[i] = int(scores[i])

        scores.sort(reverse=True)

    try:
        game_stats = json.loads(temp_stats)

    except:
        raise InvalidJSONError("Invalid JSON. Please input a JSON from FF's \'Copy JSON\' Feature.")

    final_stats = {}
    teams = []
    username = None
    mvp = None
    winner = None
    loser = None

    with sqlite3.connect(os.path.join(DB_FOLDER, f's24_{division}.db')) as connection:
        # Getting stats from the game_stats JSON | Done :D
        for player in game_stats:
            if walks is None or game_stats[player]['other']['name'] not in walks:
                try:
                    if winner is None or loser is None:
                        temp = None

                        if round(game_stats[player]['other']['w']) == 1:
                            temp = game_stats[player]['other']['team'].split(" ")
                            if len(temp) == 3:
                                winner = temp[0] + " " +  temp[1]
                            else:
                                winner = temp[0]

                        elif game_stats[player]['other']['w'] == 0:
                            temp = game_stats[player]['other']['team'].split(" ")
                            if len(temp) == 3:
                                loser = temp[0] + " " + temp[1]
                            else:
                                loser = temp[0]

                    # Getting team and player
                    team = game_stats[player]['other']['team']
                    team_tmp = team.split(" ")

                    if len(team_tmp) == 3:
                        team = team_tmp[0] + " " + team_tmp[1]
                    else:
                        team = team_tmp[0]

                    if team not in teams and team not in ['nil', None]:
                        teams.append(team)
                        
                    username = game_stats[player]['other']['name']

                    # QB stats | DONE :D
                    qb_stats = game_stats[player]['qb']

                    throws = qb_stats['comp'] + qb_stats['inc']
                    completions = qb_stats['comp']
                    incompletions = qb_stats['inc']
                    tds_thrown = qb_stats['td']
                    ints_thrown = qb_stats['int']
                    sacks_taken = qb_stats['sack']
                    yards = qb_stats['yds']

                    # Runner stats | DONE :D
                    rb_stats = game_stats[player]['rb']

                    run_attempts = rb_stats['att']
                    run_yards  = rb_stats['yds']
                    run_tds = rb_stats['td']

                    # Kicker stats | DONE :D
                    kicker_stats = game_stats[player]['k']

                    kick_attempts = kicker_stats['att']
                    kicks_made = kicker_stats['good']
                    kicks_missed = kicker_stats['att'] - kicker_stats['good']

                    # WR stats | DONE :D
                    wr_stats = game_stats[player]['wr']

                    wr_yards = wr_stats['yds']
                    wr_targets = wr_stats['tgt']
                    wr_ints_allowed = wr_stats['int_allow']
                    catches = wr_stats['catch']
                    wr_tds = wr_stats['td']
                    yards_after_catch = wr_stats['yac']

                    # DB stats | DONE :D
                    db_stats = game_stats[player]['db']

                    db_ints = db_stats['int']
                    db_targets = db_stats['tgt']
                    swats = db_stats['defl']
                    db_tds = db_stats['td']
                    catches_allowed = db_stats['catch_allow']
                    yards_allowed = db_stats['yds_allow']
                    tds_allowed = db_stats['td_allow']

                    # Defender Stats | DONE :D
                    defender_stats = game_stats[player]['def']

                    tackles = defender_stats['tack']
                    sacks = defender_stats['sack']
                    safeties = defender_stats['safe']

                    if game_stats[player]['other']['mvp'] == 1:
                        mvp = username

                    
                    # Adding all stats to DB after assigning everything for safety
                    cursor = connection.cursor()

                    cursor.execute(f"INSERT INTO defender_stats VALUES(?, ?, ?, ?, 1) ON CONFLICT(username) DO UPDATE SET tackles = tackles {operation} ?, sacks = sacks {operation} ?, safeties = safeties {operation} ?, active = 1", 
                                (username, tackles, sacks, safeties, 
                                    tackles, sacks, safeties))

                    cursor.execute(f"INSERT INTO qb_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, 1) ON CONFLICT(username) DO UPDATE SET throws = throws {operation} ?, completions = completions {operation} ?, incompletions = incompletions {operation} ?, touchdowns = touchdowns {operation} ?, interceptions = interceptions {operation} ?, sacks_taken = sacks_taken {operation} ?, yards = yards {operation} ?, active = 1",
                                (username, throws, completions, incompletions, tds_thrown, ints_thrown, sacks_taken, yards, 
                                    throws, completions, incompletions, tds_thrown, ints_thrown, sacks_taken, yards))

                    cursor.execute(f"INSERT INTO db_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, 1) ON CONFLICT(username) DO UPDATE SET interceptions = interceptions {operation} ?, targets = targets {operation} ?, swats = swats {operation} ?, touchdowns = touchdowns {operation} ?, catches_allowed = catches_allowed {operation} ?, yards_allowed = yards_allowed {operation} ?, tds_allowed = tds_allowed {operation} ?, active = 1",
                                (username, db_ints, db_targets, swats, db_tds, catches_allowed, yards_allowed, tds_allowed, 
                                db_ints, db_targets, swats, db_tds, catches_allowed, yards_allowed, tds_allowed))
                    
                    cursor.execute(f"INSERT INTO wr_stats VALUES(?, ?, ?, ?, ?, ?, ?, 1) ON CONFLICT(username) DO UPDATE SET yards = yards {operation} ?, targets = targets {operation} ?, ints_allowed = ints_allowed {operation} ?, catches = catches {operation} ?, touchdowns = touchdowns {operation} ?, yards_after_catch = yards_after_catch {operation} ?, active = 1",
                                (username, wr_yards, wr_targets, wr_ints_allowed, catches, wr_tds, yards_after_catch, 
                                    wr_yards, wr_targets, wr_ints_allowed, catches, wr_tds, yards_after_catch))

                    cursor.execute(f"INSERT INTO kicker_stats VALUES(?, ?, ?, ?, 1) ON CONFLICT(username) DO UPDATE SET attempts = attempts {operation} ?, kicks_made = kicks_made {operation} ?, kicks_missed = kicks_missed {operation} ?, active = 1", 
                                    (username, kick_attempts, kicks_made, kicks_missed, 
                                    kick_attempts, kicks_made, kicks_missed))

                    cursor.execute(f"INSERT INTO rb_stats VALUES(?, ?, ?, ?, 1) ON CONFLICT(username) DO UPDATE SET attempts = attempts {operation} ?, yards = yards {operation} ?, touchdowns = touchdowns {operation} ?, active = 1", 
                                (username, run_attempts, run_yards, run_tds, 
                                    run_attempts, run_yards, run_tds))

                except KeyError:
                    raise KeyError("There is an abrupt cut, or a missing stat in the JSON you have passed. Stats were not recorded.")
        
        connection.commit()
        
    score = f"{scores[0]} - {scores[1]}"
    
    disclaimer = ''

    if division.lower() == 'd1':
        division = 'Division 1'
    
    else:
        division = 'Division 2'
    
    if mvp is None:
        mvp = 'None (Pressed Copy JSON too early...)'
    
    if winner in ['nil', None]:
        winner = "No Team"
        disclaimer = "Winner is labeled as no team due to technical difficulties, a disclaimer will be put under this message."

    if operation == '+':
        operation = 'recorded'
        print("Statistics recorded successfully.")
    
    else:
        operation = 'deleted'
        print("Statistics deleted successfully.")
    
    if walkons:
        disclaimer = f"Walkons: {walkons}\n" + disclaimer
    
    photo_url = 'https://tr.rbxcdn.com/180DAY-4318e112c0ca37c50a31c33f40f3d59f/768/432/Image/Webp/noFilter'

    embed = discord.Embed(
            title=f"<:AFG:1457997553533714589> AFG S24 {division} Game Report (STATS {operation.upper()})",
            description=f"## 🏈 {teams[0]} vs. {teams[1]}\n\n## 📝 Score: {score}\n\n### 🏆 Winner: {winner}\n\n### 👑 MVP: {mvp}\n\n\nStatistics {operation}.",
            color=0xe42229
        )
    
    embed.set_footer(text=f"{disclaimer}")    
    embed.set_image(url='https://tr.rbxcdn.com/180DAY-4318e112c0ca37c50a31c33f40f3d59f/768/432/Image/Webp/noFilter')
        
    return embed

    # Feb 18, 2026 -  5:21 P.M., offline stat database setup complete

    # Error Legend
    # 0 = success
    # 1 = not a valid json
    # 2 = missing stat
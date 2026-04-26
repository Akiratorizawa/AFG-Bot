import discord
from datetime import datetime
import os
import hashlib
import json
import requests
from services.errors import InvalidDivisionError, InvalidOperationError, InvalidJSONError
import sqlite3

def log(yes_or_no: bool, attachment: discord.Attachment, winner: discord.Role, loser: discord.Role, division: str, description: str, walkons: str):
    if yes_or_no == True:
        print("Logging game...")
        
        # Opening original JSON in .txt form from FF, a string object by convention
        if division.lower() not in ['d1', 'd2']:
            raise InvalidDivisionError(f"{division} is not a valid division. Input either D1 or D2.")
        
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

        # List of scores, home team at index 0, away team at index 1
        scores = json_parts[0].split(' - ')

        # Initializing walks to be None by default
        walks = []

        # Making a list of walkons if ever walkons exists
        if walkons is not None:
            walkon_players = walkons.split(",")
            walks = []

            for i in range(len(walkon_players)):
                walks.append(walkon_players[i].strip())

        try:
            # The two scores from the game
            home_score = scores[0]
            away_score = scores[1]

            # Initializing the stats from the game
            temp_stats = json_parts[1]
        
        except:
            raise InvalidJSONError("Invalid JSON. Please input a JSON from FF's \'Copy JSON\' feature.")
        
        else:
            for i in range(len(scores)):
                scores[i] = int(scores[i])

            scores.sort(reverse=True)

        try:
            game_stats = json.loads(temp_stats)
            game_hash = generate_game_id(content)

            # Get the current date and time object
            now = datetime.now()

            # Format the datetime object into a specific string format
            formatted_date = now.strftime("%m/%d/%Y")

            winner_name, loser_name = winner.name.replace(" ", "").lower(), loser.name.replace(" ", "").lower()

        except:
            return 1

        with sqlite3.connect(os.path.join(DB_FOLDER, f's24_{division.lower()}_logs.db')) as connection:
            cursor = connection.cursor()

            check = cursor.execute('SELECT * FROM qb_stats WHERE game_hash = ?', (game_hash,))

            if check.fetchone() is not None:
                print("Game stats log terminated as game has already been previously logged.")
                return
            
            # Getting stats from the game_stats JSON | Done :D
            for player in game_stats:
                try:
                    username = game_stats[player]['other']['name']

                    if username in walks:
                        walkon_status = 1
                    
                    else:
                        walkon_status = 0

                    team = game_stats[player]['other']['team']
                        

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
                    cursor.execute(f"INSERT INTO defender_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                (username, tackles, sacks, safeties, game_hash, walkon_status, formatted_date, winner_name, loser_name, f'{scores[0]} - {scores[1]}', description, division, team))

                    cursor.execute(f"INSERT INTO qb_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (username, throws, completions, incompletions, tds_thrown, ints_thrown, sacks_taken, yards, game_hash, walkon_status, formatted_date, winner_name, loser_name, f'{scores[0]} - {scores[1]}', description, division, team))

                    cursor.execute(f"INSERT INTO db_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (username, db_ints, db_targets, swats, db_tds, catches_allowed, yards_allowed, tds_allowed, game_hash, walkon_status, formatted_date, winner_name, loser_name, f'{scores[0]} - {scores[1]}', description, division, team))
                    
                    cursor.execute(f"INSERT INTO wr_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (username, wr_yards, wr_targets, wr_ints_allowed, catches, wr_tds, yards_after_catch, game_hash, walkon_status, formatted_date, winner_name, loser_name, f'{scores[0]} - {scores[1]}', description, division, team))

                    cursor.execute(f"INSERT INTO kicker_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                    (username, kick_attempts, kicks_made, kicks_missed, game_hash, walkon_status, formatted_date, winner_name, loser_name, f'{scores[0]} - {scores[1]}', description, division, team))

                    cursor.execute(f"INSERT INTO rb_stats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                (username, run_attempts, run_yards, run_tds, game_hash, walkon_status, formatted_date, winner_name, loser_name, f'{scores[0]} - {scores[1]}', description, division, team))

                except KeyError:
                    raise KeyError("There is an abrupt cut, or a missing stat in the JSON you have passed. Stats for this game were not logged.")
            
            connection.commit()

    print('Game successfully logged.')

def generate_game_id(content):
    # Use SHA-256 to create a unique string based on the JSON text
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
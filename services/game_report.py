import discord
from discord.ext.commands import Context
from discord.utils import get
from services.errors import InvalidDivisionError, InvalidJSONError
import json
from inspect import cleandoc
import requests
import time

def report(ctx, attachment: discord.Attachment, winner: discord.Role, loser: discord.Role, division: str, description: str, walkons: str):
    print("Processing game...")
    
    # Opening original JSON in .txt form from FF, a string object by convention
    if division.lower() not in ['d1', 'd2']:
        raise InvalidDivisionError(f"{division} is not a valid division. Input either D1 or D2.")
    
    try:                                                
        attachment = requests.get(attachment.url)
        content = attachment.text

    except:
        raise InvalidJSONError("Error reading file. Please try again.")
    
    # List with scores at index 0 and stats at index 1
    json_parts = content.split(" /// ")

    # List of scores, home team at index 0, away team at index 1
    scores = json_parts[0].split(' - ')

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

    except:
        return 1
    
    best_qb = {}
    best_wr = {}
    best_db = {}

    for index, player in enumerate(game_stats):
        username = game_stats[player]['other']['name']
        
        if index == 0:
            # Best passer
            best_qb['display'] = game_stats[player]['other']['display']
            best_qb['username'] = username
            best_qb['stats'] = game_stats[player]['qb']

            # Best WR
            if game_stats[player]['wr']['tgt'] > 0:
                best_wr['display'] = game_stats[player]['other']['display']
                best_wr['username'] = username
                best_wr['stats'] = game_stats[player]['wr']
                best_wr['grade'] = calculate_wr_grade(game_stats[player]['wr'])

            # Best DB
            best_db['display'] = game_stats[player]['other']['display']
            best_db['username'] = username
            best_db['stats'] = game_stats[player]['db']

        else:
            # Best passer sorting
            if game_stats[player]['qb']['rtng'] > best_qb['stats']['rtng']:
                best_qb['display'] = game_stats[player]['other']['display']
                best_qb['username'] = username
                best_qb['stats'] = game_stats[player]['qb']
            
            # Best WR sorting
            wr_grade = calculate_wr_grade(game_stats[player]['wr'])

            if not best_wr and game_stats[player]['wr']['tgt'] > 0:
                best_wr['display'] = game_stats[player]['other']['display']
                best_wr['username'] = username
                best_wr['stats'] = game_stats[player]['wr']
                best_wr['grade'] = calculate_wr_grade(game_stats[player]['wr'])

            elif 'grade' in best_wr and wr_grade > best_wr['grade']:
                best_wr['display'] = game_stats[player]['other']['display']
                best_wr['username'] = username
                best_wr['stats'] = game_stats[player]['wr']
                best_wr['grade'] = wr_grade
            
            elif 'grade' in best_wr and wr_grade == best_wr['grade']:
                if game_stats[player]['wr']['tgt'] > 0 and (game_stats[player]['wr']['yds'] / game_stats[player]['wr']['tgt']) > (best_wr['stats']['yds'] / best_wr['stats']['tgt']):
                    best_wr['display'] = game_stats[player]['other']['display']
                    best_wr['username'] = username
                    best_wr['stats'] = game_stats[player]['wr']
                    best_wr['grade'] = wr_grade

            # Best DB sorting
            current_db_stats = game_stats[player]['db']
            # 1. Check if they have more Interceptions
            if current_db_stats['int'] > best_db['stats']['int']:
                is_better = True

            # 2. If Interceptions are TIED, check for more Swats (Deflections)
            elif current_db_stats['int'] == best_db['stats']['int']:
                if current_db_stats['defl'] > best_db['stats']['defl']:
                    is_better = True
                    
                # 3. If Swats are also TIED, check for fewer Catches Allowed
                elif current_db_stats['defl'] == best_db['stats']['defl']:
                    if current_db_stats['catch_allow'] < best_db['stats']['catch_allow']:
                        is_better = True
                    else:
                        is_better = False
                else:
                    is_better = False
            else:
                is_better = False

            # Update the best_db if the current player won the tiebreaker
            if is_better:
                best_db['display'] = game_stats[player]['other']['display']
                best_db['username'] = username
                best_db['stats'] = current_db_stats

    winner_name, loser_name = winner.name.replace(" ", "").lower(), loser.name.replace(" ", "").lower()
    winner_emoji, loser_emoji = get(ctx.guild.emojis, name=winner_name), get(ctx.guild.emojis, name=loser_name)
    
    if division.lower() == 'd1':
        div = 'Division 1'
    
    else:
        div = 'Division 2'

    title_embed = discord.Embed(
        title=f"<:AFG:1457997553533714589> AFG S24 {div} Game Report",
        description=f"""
        ## {winner_emoji} {winner.mention} {scores[0]} - {scores[1]} {loser.mention} {loser_emoji}
        """,
        color=0xe42229
    )

    title_embed.set_thumbnail(url=winner_emoji.url)
    title_embed.set_footer(text=f"Walkons: {walkons}\n{description}")

    qb_field = cleandoc(f"""```ansi
                    \u001b[1;32mQB Rating:         {best_qb['stats']['rtng']}
                    Yards:             {best_qb['stats']['yds']}
                    Completions:       {best_qb['stats']['comp']}/{best_qb['stats']['comp'] + best_qb['stats']['inc']}
                    Touchdowns:        {best_qb['stats']['td']}
                    \u001b[1;31mInterceptions:     {best_qb['stats']['int']}\u001b[0m
                    ```""")

    if best_qb['display'] == 'Error':
        qb_description = best_qb['username']
    else:
        qb_description = f'{best_qb['display']} ({best_qb['username']})'

    qb_embed = discord.Embed(
        title="",
        description=f"""
        ##  🏈 Best QB
        ## {qb_description}
        """,
        color=0xe42229
    )
    
    max_retries = 5

    for _ in range(max_retries):
        qb_pic = get_player_avatar(best_qb['username'])
        if qb_pic is not None:
            break

    qb_embed.set_thumbnail(url=qb_pic)

    if best_wr['display'] == 'Error':
        wr_description = best_wr['username']
    else:
        wr_description = f'{best_wr['display']} ({best_wr['username']})'

    wr_embed = discord.Embed(
        title="",
        description=f"""
        ## 🧤 Best WR
        ## {wr_description}
        """,
        color=0xe42229
    )

    for _ in range(max_retries):
        wr_pic = get_player_avatar(best_wr['username'])
        if wr_pic is not None:
            break

    wr_embed.set_thumbnail(url=wr_pic)

    if best_db['display'] == 'Error':
        db_description = best_db['username']
    else:
        db_description = f'{best_db['display']} ({best_db['username']})'

    db_embed = discord.Embed(
        title="",
        description=f"""
        ## 🛡️ Best DB
        ## {db_description}
        """,
        color=0xe42229
    )

    for _ in range(max_retries):
        db_pic = get_player_avatar(best_db['username'])
        if db_pic is not None:
            break

    db_embed.set_thumbnail(url=db_pic)

    wr_field = cleandoc(f"""```ansi
                        \u001b[1;32mWR Rating:         {best_wr['stats']['rtng']}
                        Yards:             {best_wr['stats']['yds']}
                        YAC:               {best_wr['stats']['yac']}
                        Catches:           {best_wr['stats']['catch']}/{best_wr['stats']['tgt']}
                        Catch Rate:        {round((best_wr['stats']['catch'] / (best_wr['stats']['tgt'])) * 100, 2)}%
                        Touchdowns:        {best_wr['stats']['td']}\u001b[0m
                        ```""")
    

    db_field = cleandoc(f"""```ansi
                        \u001b[1;32mDB Rating:          {best_db['stats']['rtng']}
                        Interceptions:      {best_db['stats']['int']}
                        Targets:            {best_db['stats']['tgt']}
                        Swats:              {best_db['stats']['defl']}
                        \u001b[1;31mCatches Allowed:    {best_db['stats']['catch_allow']}
                        \u001b[1;32mTouchdowns:         {best_db['stats']['td']}\u001b[0m
                        ```""")
    

    qb_embed.add_field(name="QB Stats", value=qb_field, inline=False)
    wr_embed.add_field(name="WR Stats", value=wr_field, inline=False)
    db_embed.add_field(name="WR Stats", value=db_field, inline=False)

    print('Game successfully processed.')
    
    return {
        'title_embed': title_embed,
        'qb_embed': qb_embed,
        'wr_embed': wr_embed,
        'db_embed': db_embed
    }

def calculate_wr_grade(stats):
    # Avoid DivisionByZero if targets are 0
    if stats['tgt'] == 0:
        return 0
    
    catch_rate = (stats['catch'] / stats['tgt']) * 100
    
    # Weighted calculation
    score = (stats['yds'] * 0.1) + \
            (stats['catch'] * 0.5) + \
            (stats['td'] * 6) + \
            (catch_rate * 0.2)
            
    return round(score, 2)


def get_player_avatar(username, max_retries=5):
    # Get user ID
    user_api = "https://users.roblox.com/v1/usernames/users"
    try:
        user_res = requests.post(user_api, json={"usernames": [username], "excludeBannedUsers": True})
        user_data = user_res.json().get('data')
        if not user_data:
            print(f"User data for {username} returned null.")
            return None
        user_id = user_data[0]['id']
    except:
        print(f"Request for user data failed. ({username})")
        return None

    thumb_url = (
        f"https://thumbnails.roblox.com/v1/users/avatar-headshot?"
        f"userIds={user_id}&size=420x420&format=Png&isCircular=false"
    )

    for attempt in range(max_retries):
        try:
            res = requests.get(thumb_url)
            if res.status_code == 200:
                data = res.json()["data"][0]

                # ✅ CRITICAL FIX
                if data["state"] == "Completed" and data["imageUrl"]:
                    # ✅ cache buster for Discord
                    return data["imageUrl"] + f"?cb={int(time.time())}"

        except:
            pass

        time.sleep(0.5 * (attempt + 1))  # shorter + smoother backoff

    return None
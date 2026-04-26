import discord
from services.errors import ArgumentError
from services.game_report import get_player_avatar
import os
import sqlite3

def view_stats(username: str, stat_category: str, division: str):
    # 1. Get the directory of THIS file (afg_bot/utility)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Go up one level to reach the 'afg_bot' folder
    # This is now your BASE PATH hardcoded to the project root
    BASE_PATH = os.path.abspath(os.path.join(current_dir, ".."))

    # 3. Define your sub-folders relative to the BASE_PATH
    DB_FOLDER = os.path.join(BASE_PATH, "app", "databases")

    division = division.lower()

    with sqlite3.connect(f'{DB_FOLDER}/s24_{division}.db') as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM qb_stats WHERE username = ?", (username,))

        if cursor.fetchone() is None:
            raise ArgumentError(f"The player you requested to view stats is not in the {division.upper()} statsheet. You likely mistyped the username, or that player has not yet played a {division} game.")

        cursor.execute(f"SELECT * FROM {stat_category}_stats WHERE username = ?", (username,))
        
        headers = [description[0] for description in cursor.description]

        stats = dict(zip(headers, cursor.fetchone()))

    if division == 'd1':
        division = 'Division 1'
    
    else:
        division = 'Division 2'
    
    if stat_category.lower() in ['defender', 'kicker']:
        stat_category = stat_category.capitalize()

    else:
        stat_category = stat_category.upper()

    embed = discord.Embed(
        title=f'<:AFG:1457997553533714589> AFG {division} S24 Player Statistics',
        description=f""" # {username}
                    ## 🏈 {stat_category} Stats
                    """,
        color=0xe42229
    )
    
    field = ''

    labels = [
        f"{key.replace('_', ' ').capitalize()}:"
        for key in stats.keys()
        if key not in ['active', 'username']
    ]

    max_label_length = max(len(label) for label in labels)

    for key, value in stats.items():
        if key not in ['active', 'username']:
            label = f"{key.replace('_', ' ').capitalize()}:"
            field += f"{label:<{max_label_length}}  {value}\n"
        
    embed.add_field(name='', value=f'```{field}```')

    max_retries = 5
    for _ in range(max_retries):
        player_pic = get_player_avatar(username)
        if player_pic is not None:
            break

    embed.set_thumbnail(url=player_pic)

    return embed

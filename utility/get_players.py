import sqlite3
import discord
from discord.commands import Option, OptionChoice
import os

def get_players(input):
    # 1. Get the directory of THIS file (afg_bot/services)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Go up one level to reach the 'afg_bot' folder
    # This is now your BASE PATH hardcoded to the project root
    BASE_PATH = os.path.abspath(os.path.join(current_dir, ".."))

    # 3. Define your sub-folders relative to the BASE_PATH
    DB_FOLDER = os.path.join(BASE_PATH, "app", "databases")

    with sqlite3.connect(os.path.join(DB_FOLDER, 's24_d1.db')) as connection:
        cursor = connection.cursor()
        
        input = f"{input}%"
        rows = cursor.execute("SELECT username FROM qb_stats WHERE active = 1 AND username LIKE ? LIMIT 25", (input,))

        usernames = [row[0] for row in rows]

        options = [OptionChoice(name=user, value=user) for user in usernames]

        return options
        
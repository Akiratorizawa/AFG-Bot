from datetime import datetime
import discord

def initialize():
    on_time = datetime.now().time()
    formatted_time = datetime.now().strftime("%m/%d/%Y, %H:%M")

    # Set custom status: 'Custom Status Message'
    # You can also add an emoji using the emoji parameter
    activity = discord.CustomActivity(name="AFG's own custom bot.", emoji="😃")

    print(f'Bot initialized - {formatted_time}')
    print('Logged in. ')
    print('')

    return activity
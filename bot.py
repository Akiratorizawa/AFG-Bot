import discord
from discord.commands import Option, OptionChoice
from discord.ui import Button, View
from discord.utils import get
from dotenv import load_dotenv
from utility.initialization import initialize
from utility.get_players import get_players
from services.log_game import log
from services.stream import stream
from services.stats import stats
from services.game_report import report, get_player_avatar
from services.transfer_stats import transfer
from services.view_stats import view_stats
import os

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True # Required for receiving messages
bot = discord.Bot(intents=intents)

# DEFINITIONS
statsheet_link = 'https://therapist-somehow-facilitate-dos.trycloudflare.com/'
valid_stat_operations = [
    OptionChoice(name='Record Stats', value="+"),
    OptionChoice(name='Delete Stats', value="-")
]
valid_divisions = [
    OptionChoice(name='Division 1', value='D1'),
    OptionChoice(name='Division 2', value='D2')
]
valid_stat_category = [
    OptionChoice(name='QB', value='qb'),
    OptionChoice(name='WR', value='wr'),
    OptionChoice(name='DB', value='db'),
    OptionChoice(name='RB', value='rb'),
    OptionChoice(name='Defender', value='defender'),
    OptionChoice(name='Kicker', value='kicker')
]
yes_or_no = [
    OptionChoice(name='Yes', value=True),
    OptionChoice(name='No', value=False)
]

async def username_autocomplete(ctx: discord.AutocompleteContext):
    input = ctx.value

    results = get_players(input)

    return results


# Bot initialization
@bot.event
async def on_ready():
    activity = initialize()
    await bot.change_presence(activity=activity)


# Bot details command
@bot.command(description="Gives details about the bot.", guild_ids=[1473474628268720321, 1455099949896302655])
async def details(ctx):
    embed = discord.Embed(
        title="Details about the AFG Bot",
        description="Written by Random 😃\n\nFront-end:\n• HTML, CSS, JavaScript\n• Jinja\n\nBack-end:\n• Flask\n• Python (Pycord)\n• SQL via sqlite3",
        color=0xe42229
    )
    max_retries = 5

    for _ in range(max_retries):
        avatar = get_player_avatar('lolrandomnames')
        if avatar is not None:
            break
        
    embed.set_thumbnail(url=avatar)
    await ctx.respond(embed=embed)


# Statsheet command
@bot.command(description="Gives current link to AFG Statsheet.", guild_ids=[1473474628268720321, 1455099949896302655])
async def statsheet(ctx):
    await ctx.respond(f'Statsheet: {statsheet_link}', ephemeral=True)
    

# Ping command
@bot.command(description="Sends the bot's latency.", guild_ids=[1473474628268720321, 1455099949896302655]) # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency:.3f} milliseconds!")


# Stat record/delete command
@bot.command(description="Records/delete game statistics using FF\'s \'Copy JSON\' Feature.", guild_ids=[1473474628268720321, 1455099949896302655])
async def report_stats(ctx, operation: Option(str, "What operation do you want to perform?", choices=valid_stat_operations), attachment: discord.Attachment, log_individual_stats: Option(bool, "Will you log individual stats for this game?", choices=yes_or_no), winner: discord.Role, loser: discord.Role, division: Option(str, "What division was this game played in?", choices=valid_divisions), 
                      game_description: str, walkons: Option(str, "The usernames of people who walked on seperated by commas", required=False)): 

    await ctx.defer()

    try:
        recorded_embed = stats(attachment, operation, division, walkons)
        await ctx.respond(embed=recorded_embed)

    except Exception as e:
        print(e)
        await ctx.respond(e)
    
    try:
        embeds = report(ctx, attachment, winner, loser, division, game_description, walkons)
        log(log_individual_stats, attachment, winner, loser, division, game_description, walkons)

    except Exception as e:
        await ctx.respond(e)
    
    else:
        if operation == "+":
            if division == 'D1':
                channel = await bot.fetch_channel(1463831777473990821)
            
            else:
                channel = await bot.fetch_channel(1463835706198720660)


            await channel.send(embed=embeds['title_embed'])
            await channel.send(embed=embeds['qb_embed'])
            await channel.send(embed=embeds['wr_embed'])
            await channel.send(embed=embeds['db_embed'])

            await ctx.respond("Game successfully reported and individual stats logged.", ephemeral=True)

        else:
            await ctx.respond("Game stats successfully deleted.", ephemeral=True)


# Stat transfer command
@bot.command(description="Transfers one players statistics to another.", guild_ids=[1473474628268720321, 1455099949896302655])
async def transfer_stats(ctx, old_acc: str, new_acc: str, division: Option(str, "What division are you transferring stats in?", choices=valid_divisions)):

    try:
        transfer_status = transfer(old_acc, new_acc, division)
    
    except Exception as e:
        await ctx.respond(e)

    else:
        await ctx.respond(f"{division.upper()} Stats successfully transferred from {old_acc} to {new_acc}.")


# Stat view command command
@bot.command(description="Shows the stats for a single player of your choice.", guild_ids=[1473474628268720321, 1455099949896302655])
async def stat_view(ctx, username: Option(str, "Which player's stats do you want to see?", autocomplete=username_autocomplete), category: Option(str, "Which stats should I find?", choices=valid_stat_category), 
                    division: Option(str, "Which division stats should I find for this player?", choices=valid_divisions)):

    await ctx.defer()

    try:
        embed = view_stats(username, category, division)
        await ctx.respond(embed=embed)
    except Exception as e:
        await ctx.respond(e)



# Stream announcement command
@bot.command(description="Posts an announcement for a game stream.", guild_ids=[1473474628268720321, 1455099949896302655])
async def stream_announcement(ctx, team1: discord.Role, team2: discord.Role, streamer: discord.User, stream_link: str):

    await ctx.defer()

    stream_embed = stream(ctx, team1, team2, streamer, stream_link)

    await ctx.send("@here")
    await ctx.respond(embed=stream_embed['embed'], view=stream_embed['view'])



bot.run(discord_token)

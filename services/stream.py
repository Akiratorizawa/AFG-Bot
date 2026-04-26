import discord
from discord.ext.commands import Context
from discord.utils import get
from discord.ui import Button, View
from services.errors import InvalidDivisionError, ArgumentError, URLError

def stream(ctx, team1: discord.Role, team2: discord.Role, streamer: discord.User, stream_link: str):
    if not (stream_link.startswith("http://") or stream_link.startswith("https://")):
        raise URLError("Invalid link. Please input a stream link that begins with http:// or https://.")

    else:
        team1_name, team2_name = team1.name.replace(" ", "").lower(), team2.name.replace(" ", "").lower()
        emoji1, emoji2 = get(ctx.guild.emojis, name=team1_name), get(ctx.guild.emojis, name=team2_name)

        embed = discord.Embed(
            title=f"<:AFG:1457997553533714589> AFG S24 Game Stream",
            description=f"## {emoji1} {team1.mention}\n\n## vs.\n\n## {emoji2} {team2.mention}\n\n\n### 📸 Streamer: {streamer.mention}",
            color=0xe42229
        )

        embed.set_image(url='https://tr.rbxcdn.com/180DAY-4318e112c0ca37c50a31c33f40f3d59f/768/432/Image/Webp/noFilter')

        try:
            button = Button(
                label="🏈 Click to watch the stream!",
                url=f'{stream_link}',
                style=discord.ButtonStyle.link
            )

        except:
            raise URLError("Invalid link. Please input a valid, openable link.")
        
        else:
            view = View()
            view.add_item(button)
        
            return {
                'embed': embed,
                'view': view
            }
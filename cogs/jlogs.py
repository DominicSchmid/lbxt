import json
import sqlite3
from datetime import datetime
from textwrap import dedent
from typing import Optional

import discord
from discord import Embed, Member
from discord.ext import commands

import justlogs as jl
# When everybody leaves the cinema set a 5 minute timeout after which the watchparty will be closed.


class JustLogs(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(name='logs', aliases=['l'])
    async def logs(self, ctx, twitch_username):
        """Display information about you or another user"""
        CHANNELS = jl.get_tracked_channels()
        logs = jl.get_log_list([twitch_username])
        for user, channels in sorted(logs.items()):
            if(channels):
                print(f"{user} ({len(channels)}): {channels}")

        embed = Embed(title=twitch_username, description=f'{twitch_username} is active in the following channels:',
                      color=discord.Colour.red(), timestamp=datetime.utcnow())
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')

        for channel in channels:
            embed.add_field(name=channel, value=f'[{channel}](https://twitch.tv/{channel})', inline=True)

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(JustLogs(client))
    print('JustLogs loaded')

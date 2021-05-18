import os
import sys
import resources as res
from datetime import datetime

import discord
from discord import Embed
from discord.ext import commands, tasks
from typing import Optional

import lbxd_scraper as lbxd

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True, voice_states=True)
client = commands.Bot(command_prefix=res.CMD_PREFIX, intents=intents, case_insensitive=True)  # Use dot to make commands

cogs = []  # stores all .py files

""" TODO's
- add an info command that shows eg your cinema channel, how many linked users, how many movies watched together idk
- todo random chance to get emojis in your message?? idk lmao im out of ideas i havent slept in 3 days
"""


@client.event
async def on_ready():  # When bot has all information, bot goes into ready state
    change_status.start()
    print(f'{client.user} is ready.')


def load_cogs(cogs):
    for filename in cogs:
        try:
            # [:-3] removes last 3 chars, .py, so it imports cogs.example
            client.load_extension(f'cogs.{filename[:-3]}')
        except Exception as e:
            print(f'Failed to load extension {filename}', file=sys.stderr)
            print(e)


def unload_cogs(cogs):
    for filename in cogs:
        try:
            # [:-3] removes last 3 chars, .py, so it imports cogs.example
            client.unload_extension(f'cogs.{filename[:-3]}')
        except Exception as e:
            print(f'Failed to unload extension {filename}', file=sys.stderr)
            print(e)


@client.command()
@commands.has_guild_permissions(administrator=True)
async def reload(ctx, extension=None):
    """<Administrator> reloads bot dependencies without restarting the core."""
    if extension:
        client.reload_extension(f'cogs.{extension}')
    else:
        print('Reloading all cogs...')
        unload_cogs(cogs)
        load_cogs(cogs)


@client.command()
async def ping(ctx):  # First parameter of function must be the context
    """Replies 'Pong!' and shows your delay to the bot"""
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')


@client.command(name='random', aliases=['ran'])
async def random(ctx):  # First parameter of function must be the context
    """Returns a random movie for you to watch

    Currently picks a random movie from this list:
    https://letterboxd.com/tobiasandersen2/list/random-movie-roulette/
    as this bot has no API access and needs to scrape the pages"""
    movie = lbxd.get_random_movie_from_page('tobiasandersen2', 'random-movie-roulette')  # Should be like 90 something

    if movie:
        embed = Embed(title=getattr(movie, 'name'), url=getattr(movie, 'link'), description=getattr(movie, 'release_year'),
                      color=discord.Colour.green(), timestamp=datetime.utcnow())
        embed.set_thumbnail(url=getattr(movie, 'img'))
        embed.set_footer(icon_url=res.LBXD_LOGO, text=f'on Letterboxd.com')  # {ctx.author.name}')
        await ctx.send(f'{ctx.author.mention} I think you will like this movie:', embed=embed)
    else:
        await ctx.send(f'Oops! This looks like an issue on our end. Please try again.')


@tasks.loop(seconds=30)  # Update status every 30 seconds
async def change_status():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f'.help - {len(client.guilds)} servers'))


@client.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True)  # Only run if user has delete permissions
async def clear(ctx, amount: Optional[int]):
    """Delete a given amount of messages or purge entire channel"""
    await ctx.channel.purge(limit=amount)  # +1 because the delete command also counts as message
    if amount is None:
        amount = 'all'
    await ctx.send(f'Successfully deleted **{amount}** messages!', delete_after=5)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        cogs.append(filename)
load_cogs(cogs)  # Load all cogs. No arg specified -> refresh from folder

token = os.getenv('DISCORD_TOKEN')
if not token:
    with open(res.DISCORD_TOKEN) as f:
        token = f.read()

client.run(token)
print('Bot started!')

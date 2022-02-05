import os
import sys
import resources as res
from datetime import datetime

import discord
from discord import Embed
from discord.ext import commands, tasks
from typing import Optional

import lbxd_scraper as lbxd
from postgres_helper import setup_db, delete_cinemas

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True, voice_states=True)
client = commands.Bot(command_prefix=res.CMD_PREFIX, intents=intents, case_insensitive=True)  # Use dot to make commands

cogs = []  # stores all .py files

""" TODO's
- add an info command that shows eg your cinema channel, how many linked users, how many movies watched together idk
- Search movies by name and maaaaaybe genre
- Maybe:
"""


@client.event
async def on_ready():  # When bot has all information, bot goes into ready state
    change_status.start()
    print(f'{client.user} is ready.')
    setup_db()


@client.event
# The client got banned. The client got kicked. The client left the guild. The client or the guild owner deleted the guild.
async def on_guild_remove(ctx):
    print(f"The client was removed from Guild {ctx.message.guild.name} ({ctx.guild.id})")
    print("Removing Cinema links...")
    delete_cinemas(ctx.guild.id)


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
async def lbxthelp(ctx):  # First parameter of function must be the context
    """Provides a sexier help interface :)"""
    embed = Embed(color=discord.Colour.green())
    embed.set_author(
        name='Letterboxd Bot', icon_url=res.LBXD_LOGO)
    embed.set_footer(
        text='Made by Domski#1087. Send a PM for help', icon_url='https://i.imgur.com/vahlwre.jpg')
    embed.set_thumbnail(url=res.LBXD_LOGO_WIDE)
    embed.description = '[GitHub](https://github.com/DominicSchmid/lbxt) | Explanation:\n() are optional parameters\n| are aliases for the same command\n* are Administrator commands'
    pref = res.CMD_PREFIX
    embed.add_field(name=f"{pref}link <lbxd user>",
                    value="Link this discord account with the given Letterboxd account", inline=False)
    embed.add_field(name=f"{pref}unlink", value="Unlink your Letterboxd account", inline=False)
    embed.add_field(name=f"{pref}whois|who (<user>)", value="Shows information about a given user", inline=False)
    embed.add_field(name=f"{pref}watchlist|wl (<user>)",
                    value="Show information about a user's Letterboxd watchlist (LBXD link needs to be set)", inline=False)
    embed.add_field(name=f"{pref}watchlist|wl compare|cmp <user> (<user2>, <user3>, ...)",
                    value="Compares all given user's watchlists and returns a new list with movies that are on all the lists", inline=False)
    embed.add_field(name=f"{pref}random", value="Selects a random movie for you to watch", inline=False)
    embed.add_field(name=f"{pref}ping", value="Replise 'Pong!' and shows your delay to the bot", inline=False)
    embed.add_field(name=f"{pref}cinema|cine", value="Shows information about this server's cinema", inline=False)
    embed.add_field(name=f"* {pref}cinema|cine set <text channel> <voice channel>",
                    value="Create a new cinema for this server", inline=False)
    embed.add_field(name=f"* {pref}cinema|cine unset", value="Remove this server's cinema", inline=False)
    embed.add_field(name=f"* {pref}clear (<amount>)",
                    value="Deletes a given amount of messages from a channel (or purges the whole channel)", inline=False)
    """Replies 'Pong!' and shows your delay to the bot"""
    await ctx.send(embed=embed)


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
    await ctx.send('Picking a really special movie for you.. Give me a sec', delete_after=5)
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
    # TODO if i change prefix i should change this
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f'.lbxthelp - {len(client.guilds)} servers'))


@client.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True)  # Only run if user has delete permissions
async def clear(ctx, amount=10):
    """Delete a given amount of messages or purge entire channel"""
    if isinstance(amount, int) and amount > 0:
        await ctx.channel.purge(limit=amount)  # +1 because the delete command also counts as message
        if amount is None:
            amount = 'all'
        await ctx.send(f'Successfully deleted **{amount}** messages!', delete_after=5)


# SETUP BOT

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        cogs.append(filename)
load_cogs(cogs)  # Load all cogs. No arg specified -> refresh from folder

token = os.getenv('DISCORD_TOKEN')
if not token:
    with open(res.DISCORD_TOKEN) as f:  # ENV not found, opens txt file for discord token (locally)
        token = f.read()
    if not token:
        print("!!!CRITICAL ERROR: Environment Variable DISCORD_TOKEN not found")

res.DATABASE_URL = os.getenv('DATABASE_URL')
if not res.DATABASE_URL:
    print("!!!CRITICAL ERROR: Environment Variable DATABASE_URL not found")
    exit()
    """with open(res.DISCORD_TOKEN) as f:
        token = f.read()"""

client.run(token)
print('Bot started!')

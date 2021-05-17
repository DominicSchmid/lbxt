import os
import sys
import resources as res

import discord
from discord.ext import commands, tasks
from typing import Optional

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True, voice_states=True)
client = commands.Bot(command_prefix=res.CMD_PREFIX, intents=intents, case_insensitive=True)  # Use dot to make commands

cogs = []  # stores all .py files

""" TODO's
- add an info command that shows eg your cinema channel, how many linked users, how many movies watched together idk
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
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')


@tasks.loop(seconds=30)  # Update status every 30 seconds
async def change_status():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f'.help - {len(client.guilds)} servers'))


@client.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True)  # Only run if user has delete permissions
async def clear(ctx, amount: Optional[int]):
    """Delete a given amount of messages or purge entire channel"""
    await ctx.channel.purge(limit=amount)  # +1 because the delete command also counts as message
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

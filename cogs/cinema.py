import discord
import resources as res
from discord import Embed
from discord.ext import commands
from typing import Optional
import random

import db


class Cinema(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Detects who's currently in the cinema voice channel"""
        cinema = db.fetch_cinemas(member.guild.id)
        if cinema:
            description = None
            cinema_channel = self.client.get_channel(int(cinema[1]))  # Get cinema obj from int ID
            # Muting also calls this, so check for after=before

            if random.random() < 0.4:  # 40% chance to get eastegg
                eastereggs = ["Consider joining 🙂",
                              "(again)", "They're probably rewatching ⭐⚔️", "Quick! Run!", "So?", "💉💎", "👦🏻👓⚡", "❌🗣️", "Time to throw PogChamp"]
            else:
                eastereggs = [""]

            if after.channel == cinema_channel and before.channel != cinema_channel:
                # TODO send PM telling user if a watchparty has already been started and if not how to make one
                cinema_watchers = len(after.channel.members) - 1
                if cinema_watchers > 0:
                    # TODO send into cinema channel
                    description = f'**{member.name}** just joined the cinema with {cinema_watchers} other(s)! {random.choice(eastereggs)}'
                else:
                    description = f'**{member.name}** just joined the cinema! {random.choice(eastereggs)}'
            elif after.channel != cinema_channel and before.channel == cinema_channel:
                cinema_watchers = len(before.channel.members)
                if cinema_watchers == 1:
                    description = f'**{member.name}** just left the cinema. Now {before.channel.members[0].mention} is all alone! 😭'
                else:
                    description = f'**{member.name}** just left the cinema! 😢'

            text = self.get_cinema_text_channel(member.guild.id)  # Get the server's cinema channel
            if text and description:
                print(description)
                await text.send(description)

    @commands.group(name='cinema', aliases=['cine'], invoke_without_command=True)
    async def cinema(self, ctx):
        """Shows this server's cinema channels or a tutorial"""
        cinema = db.fetch_cinemas(ctx.guild.id)
        if cinema:
            cinema_text_name = self.client.get_channel(int(cinema[0]))
            cinema_voice_name = self.client.get_channel(int(cinema[1]))
            if cinema_text_name and cinema_voice_name:
                embed = Embed(title=f'{ctx.guild.name} Cinema',
                              color=discord.Colour.green())
                embed.add_field(name='Text Channel', value=f'#{cinema_text_name}')
                embed.add_field(name='Voice Channel', value=cinema_voice_name)
                embed.set_thumbnail(url=res.LBXD_LOGO)
            else:
                # This means a channel was deleted while the bot wasn away, so it will remove cinemas
                db.delete_cinemas(ctx.guild.id)
                embed = get_cinema_creation_help_easy("You haven't set up a cinema yet.")
        else:
            embed = get_cinema_creation_help_easy("You haven't set up a cinema yet.")

        await ctx.send(embed=embed)

    @cinema.command(name='set')
    async def set_cinema_channel(self, ctx, text_channel: discord.TextChannel, voice_channel: discord.VoiceChannel):
        """Select text and voice channel for watchparties"""

        if not ctx.message.author.guild_permissions.administrator:
            return

        result = db.execute('SELECT * FROM cinemas WHERE server_id = ?', (ctx.guild.id,))

        if result:
            sql = ('UPDATE cinemas SET text_id = ?, voice_id = ? WHERE server_id = ?')
            val = (text_channel.id, voice_channel.id, ctx.guild.id)
            db.execute(sql, val)
        else:
            sql = ('INSERT INTO cinemas(server_id, text_id, voice_id) VALUES (?,?,?)')
            val = (ctx.guild.id, text_channel.id, voice_channel.id)
            db.execute(sql, val)

        embed = Embed(title=f'{ctx.message.guild.name} has a new cinema!', description='Join the voice channel during watchparties and use the text channel to play around with me!',
                      color=discord.Colour.green())
        embed.add_field(name='Text Channel', value=f'#{text_channel.name}')
        embed.add_field(name='Voice Channel', value=voice_channel.name)
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @cinema.command(name='unset')
    async def unset_cinema_channels(self, ctx, message=None):
        """Remove cinema channel binding"""

        if not ctx.message.author.guild_permissions.administrator:
            return

        cinema = db.fetch_cinemas(ctx.guild.id)

        if cinema:
            db.delete_cinemas(ctx.guild.id)
            text = self.client.get_channel(int(cinema[0]))
            voice = self.client.get_channel(int(cinema[1]))
            if text and voice:
                description = f'Successfully unlinked **#{text}** and **{voice}** cinema channels for {ctx.message.guild.name}'
            else:
                description = f'Successfully unlinked the cinema channels for **{ctx.message.guild.name}**'
        else:
            description = "You haven't set up any cinema channels yet.\nNo changes have been made."

        if message:
            description = message

        embed = Embed(title='Cinema', description=description,
                      color=discord.Colour.red())
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @cinema.command(name='idset')
    async def cinema_idset(self, ctx):
        """Shows how to set up cinema using IDs instead of names"""
        embed = Embed(title='Advanced Cinema Help', description="**Here's how you can always set up a cinema:**",
                      color=discord.Colour.green())
        embed.add_field(name='**1:**', value="Go to your settings and under 'Advanced' enable 'Developer Mode'")
        embed.add_field(name='**2:**', value="Right-click on your desired cinema **text** channel")
        embed.add_field(name='**3:**', value="At the bottom, click 'Copy ID'")
        embed.add_field(name='**4:**', value="Do the same for your desired **voice** channel'")
        embed.add_field(
            name='**5:**', value=f"Paste these numbers into `{res.CMD_PREFIX}cinema set <text channel> <voice channel>` and you're *Done!*")
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @set_cinema_channel.error
    async def set_cinema_channel_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):  # If ANY command gives this error at any point, this command runs
            embed = get_cinema_creation_help_easy(
                'Please specify both a text channel and voice channel for your cinema!')
            await ctx.send(embed=embed)
        else:
            embed = get_cinema_creation_help_easy(error)
            await ctx.send(embed=embed)

    # Optional:
    # So if your bot leaves a guild, the guild is removed from the dict

    @commands.Cog.listener()
    async def on_guild_remove(self, ctx):  # TODO idk if this works
        self.unset_cinema_channels(ctx)

    @commands.Cog.listener()
    # So long because if text is deleted need to send to system channel
    async def on_guild_channel_delete(self, channel):
        cinema = db.fetch_cinemas(channel.id)
        if cinema:
            if int(cinema[0]) == int(channel.id):
                await channel.guild.system_channel.send(f'Hey! The cinema text channel **#{channel.name}** ({channel.id}) was just deleted. Removed link.')
                print(f'Cinema text channel {channel.id} in {channel.guild.id} was just deleted')
            elif int(cinema[1]) == int(channel.id):
                text = self.client.get_channel(int(cinema[0]))
                await text.send(f'Hey! The cinema voice channel **{channel.name}** ({channel.id}) was just deleted. Removed link.')
                print(f'Cinema voice channel {channel.id} in {channel.guild.id} was just deleted')
            db.delete_cinemas(channel.id)

    @commands.Cog.listener()
    # So long because if text is deleted need to send to system channel
    async def on_private_channel_delete(self, channel):
        cinema = db.fetch_cinemas(channel.id)
        if cinema:
            if int(cinema[0]) == int(channel.id):
                await channel.guild.system_channel.send(f'Hey! The private cinema text channel **#{channel.name}** ({channel.id}) was just deleted. Removed link.')
                print(f'Private cinema text channel {channel.id} in {channel.guild.id} was just deleted')
            elif int(cinema[1]) == int(channel.id):
                text = self.client.get_channel(int(cinema[0]))
                await text.send(f'Hey! The private cinema voice channel **{channel.name}** ({channel.id}) was just deleted. Removed link.')
                print(f'Private cinema voice channel {channel.id} in {channel.guild.id} was just deleted')
            db.delete_cinemas(channel.id)

    def get_cinema_text_channel(self, server_id):
        """Returns the ID of the cinema text channel of a given contex or None if there isn't one"""
        cinema = db.fetch_cinemas(server_id)
        return self.client.get_channel(int(cinema[0])) if cinema else None


def get_cinema_creation_help_easy(message: str) -> Embed:
    embed = Embed(title='Cinema Help', description=f"""**{message}**
            To set up a cinema channel, write ```{res.CMD_PREFIX}cinema set <text channel> <voice channel>``` (case sensitive)
            If this does not work, use `{res.CMD_PREFIX}cinema idset` to show a more advanced guide that always works.""",
                  color=discord.Colour.green())
    embed.set_thumbnail(url=res.LBXD_LOGO)

    return embed


def setup(client):
    client.add_cog(Cinema(client))
    print('Cinema is loaded')

import sqlite3
from datetime import datetime

import discord
import resources as res
from discord import Embed
from discord.ext import commands


class Cinema(commands.Cog):

    cinema_watchers = []

    def __init__(self, client):
        self.client = client

    def fetch_cinema(self, ctx):
        """Returns the Cinema ID for the given server or None if there isn't one"""
        db = sqlite3.connect(res.DB_NAME)
        cursor = db.cursor()
        sql = 'SELECT * FROM cinemas WHERE server_id = ?'
        cursor.execute(sql, (ctx.guild.id,))
        result = cursor.fetchone()

        db.commit()
        cursor.close()
        db.close()

       # If channel found in DB but not on Server, return Null
        return result[1] if result else None

    def delete_cinema_from_db(self, channel_id):
        """Takes a channel ID that will be used to delete a cinema link from the database"""
        db = sqlite3.connect(res.DB_NAME)
        cursor = db.cursor()
        cursor.execute('DELETE FROM cinemas WHERE channel_id = ?', (channel_id,))
        db.commit()
        cursor.close()
        db.close()

    def get_cinema_creation_help_easy(self, message: str) -> Embed:
        embed = Embed(title='Cinema Help', description=f"""**{message}**
            To set up a cinema channel, write ```{res.CMD_PREFIX}cinema set <channel>``` where `<channel>` is the desired **voice** channel (case sensitive)
            If this does not work, use `{res.CMD_PREFIX}cinema idset` to show a more advanced guide that always works.""",
                      color=discord.Colour.green())
        embed.set_thumbnail(url=res.LBXD_LOGO)

        return embed

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Detects who's currently in the cinema voice channel."""
        cinema = self.fetch_cinema(member)
        if cinema:
            cinema_channel = self.client.get_channel(int(cinema))  # Get cinema obj from int ID
            # Muting also calls this, so check for after=before
            if after.channel == cinema_channel and before.channel != cinema_channel:
                # TODO send PM telling user if a watchparty has already been started and if not how to make one
                if self.cinema_watchers:
                    print(f'{member} just joined the cinema with {len(self.cinema_watchers)} other(s)!')
                else:
                    print(f'{member} just joined the cinema!')
                self.cinema_watchers.append(member)
            elif after.channel != cinema_channel and before.channel == cinema_channel:
                print(f'{member} just left the cinema!')
                if member in self.cinema_watchers:
                    self.cinema_watchers.remove(member)

    @commands.group(name='cinema', aliases=['cine', 'c'], invoke_without_command=True)
    async def cinema(self, ctx):
        """Show cinema channel. <help cinema> to learn how"""
        cinema = self.fetch_cinema(ctx)
        if cinema:
            cinema_name = self.client.get_channel(int(cinema))
            if cinema_name:
                embed = Embed(title='Cinema', description=f'{self.client.get_channel(int(cinema))} is the cinema for {ctx.message.guild.name}',
                              color=discord.Colour.green())
                embed.set_thumbnail(url=res.LBXD_LOGO)
            else:
                self.delete_cinema_from_db(cinema)
                embed = self.get_cinema_creation_help_easy("You haven't set up a cinema yet.")
        else:
            embed = self.get_cinema_creation_help_easy("You haven't set up a cinema yet.")

        await ctx.send(embed=embed)

    @cinema.command(name='set')
    async def set_cinema_channel(self, ctx, channel: discord.VoiceChannel):
        """Select voice channel for watchparties"""

        db = sqlite3.connect(res.DB_NAME)
        cursor = db.cursor()
        sql = 'SELECT * FROM cinemas WHERE server_id = ?'
        cursor.execute(sql, (ctx.guild.id,))
        result = cursor.fetchone()

        if result:
            sql = ('UPDATE cinemas SET channel_id = ? WHERE server_id = ?')
            val = (channel.id, ctx.guild.id)
            cursor.execute(sql, val)
        else:
            sql = ('INSERT INTO cinemas(server_id, channel_id) VALUES (?,?)')
            val = (ctx.guild.id, channel.id)
            cursor.execute(sql, val)

        db.commit()
        cursor.close()
        db.close()

        embed = Embed(title='Cinema', description=f'**{channel.name}** is the new cinema for **{ctx.message.guild.name}**',
                      color=discord.Colour.green(), timestamp=datetime.utcnow())
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @cinema.command(name='unset')
    async def unset_cinema_channel(self, ctx):
        """Remove cinema channel binding"""
        cinema = self.fetch_cinema(ctx)

        if cinema:
            self.delete_cinema_from_db(cinema)
            cinema_name = self.client.get_channel(int(cinema))
            if cinema_name:
                description = f'**{self.client.get_channel(int(cinema))}** is no longer the cinema for {ctx.message.guild.name}'
            else:
                description = f'Successfully unlinked the cinema associated with **{ctx.message.guild.name}**'
        else:
            description = 'You haven\'t set a cinema channel yet.\nNo changes have been made.'

        embed = Embed(title='Cinema', description=description,
                      color=discord.Colour.red())

        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @cinema.command(name='idset')
    async def cinema_idset(self, ctx):
        embed = Embed(title='Advanced Cinema Help', description="**Here's how you can always set up a cinema:**",
                      color=discord.Colour.green())
        embed.add_field(name='**1:**', value="Go to your settings and under 'Advanced' enable 'Developer Mode'")
        embed.add_field(name='**2:**', value="Right-click on your desired cinema voice channel")
        embed.add_field(name='**3:**', value="At the bottom, click 'Copy ID'")
        embed.add_field(
            name='**4:**', value=f"Paste this number after into `{res.CMD_PREFIX}cinema set <Channel ID>` and you're *Done!*")
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @set_cinema_channel.error
    async def set_cinema_channel_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):  # If ANY command gives this error at any point, this command runs
            embed = self.get_cinema_creation_help_easy('Please specify a voice channel as your cinema!')
            await ctx.send(embed=embed)
        else:
            await ctx.send(error)

    # Optional:
    # So if your bot leaves a guild, the guild is removed from the dict

    @commands.Cog.listener()
    async def on_guild_remove(self, ctx):  # TODO idk if this works
        self.unset_cinema_channel(ctx)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        cinema = self.fetch_cinema(channel)
        if cinema and int(cinema) == channel.id:
            print(f'Cinema channel {channel.id} in {channel.guild.id} was just deleted')
            self.delete_cinema_from_db(channel.id)

    @commands.Cog.listener()
    async def on_private_channel_delete(self, channel):
        cinema = self.fetch_cinema(channel)
        if cinema and int(cinema) == channel.id:
            print(f'Cinema channel {channel.id} in {channel.guild.id} was just deleted')
            self.delete_cinema_from_db(channel.id)


def setup(client):
    client.add_cog(Cinema(client))
    print('Cinema is loaded')

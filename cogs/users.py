import sys
from datetime import datetime
from textwrap import dedent
from typing import Optional

import discord
import resources as res
from discord import Embed, Member
from discord.ext import commands
from sqlite3 import OperationalError

import db
from db import fetch_user
from lbxd_scraper import get_watchlist_size


class Users(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def get_user_lbxd(client, ctx, user):
        """Tries to return a tuple (disc_id, lbxd_id) for a given search value. Both can be None"""
        if isinstance(user, Member):  # If user is a member, fetch his lbxd_id (can be None) from db
            lbxd_id = fetch_user(user.id)
        else:  # isinstance(user, str):
            try:  # to convert given user (eg. username)
                user = await commands.MemberConverter().convert(ctx, str(user))
                lbxd_id = fetch_user(user.id)
            except commands.BadArgument:  # If conversion doesnt work, expect a LBXD_ID username
                lbxd_id = user
                user = fetch_user(lbxd_id)  # Get associated discord account from DB. If there isnt one -> None
                if user:
                    user = client.get_user(int(user))  # Convert ID from DB into a Member instance
        return (user, lbxd_id)

    @commands.command(name='whois', aliases=['userinfo', 'ui', 'who'])
    # Optional is like Union[Member, None]. If member can be converted to type member it will, otherwise None
    async def whois(self, ctx, target: Optional[Member]):
        """Display information about you or another user"""
        target = target or ctx.author  # If no member was specified, user author of command

        embed = Embed(title=target.name, description=target.mention,
                      color=discord.Colour.red(), timestamp=datetime.utcnow())
        embed.set_thumbnail(url=target.avatar_url)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')

        embed.add_field(name="ID", value=target.id, inline=True)
        lbxd_id = db.fetch_user(target.id)
        if lbxd_id:
            embed.add_field(name="Letterboxd", value=f'[{lbxd_id}]({res.LBXD_URL}/{lbxd_id})', inline=True)
            wl_size = get_watchlist_size(lbxd_id)  # Limit to 1 so only one request happens
            if wl_size != -1:  # If user exists
                embed.add_field(name="Watchlist",
                                value=f'[{wl_size} movies]({res.LBXD_URL}/{lbxd_id}/watchlist)', inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='link', pass_context=True)
    async def link_user(self, ctx, lbxd_user):
        """
        Links your Discord account to the specified Letterboxd account
        Only works if the given Letterboxd account it hasn't already been linked to another account
        """

        """WAS LIKE THIS WHEN CHECKING PERMISSIONS
        async def link_user(self, ctx, disc_user: Optional[commands.MemberConverter], lbxd_user):
        if ctx.message.author.guild_permissions.administrator:
        if ctx.author.name == lbxd_user:
            await ctx.send(dedent(f'''
                Oh no {ctx.message.author.mention}! Are you *sure* your name on Discord and Letterboxd are the same?
                If so, please quickly reply with 'yes' to this message.'''))
            ##############

            def check(m):
                return m.channel == ctx.channel and m.author.id == ctx.author.id

            try:
                message = await self.client.wait_for('message', check=check, timeout=5)
                if message.content != 'yes':
                    return
            except asyncio.TimeoutError:
                return"""

        member_uid = str(ctx.author.id)  # Get numerical User ID
        # First, check if user is already in db
        d_id = db.execute('SELECT * FROM users WHERE disc_id = ?', (member_uid,))
        # First, check if lbxd is already in db but on another account
        l_id = db.execute('SELECT * FROM users WHERE lbxd_id = ?', (lbxd_user,))

        show_link = True  # Show new link by default

        if d_id is None and l_id is None:  # Add new user since both dont exist
            sql = ('INSERT INTO users(disc_id, lbxd_id) VALUES (?,?)')
            val = (member_uid, lbxd_user)
            db.execute(sql, val)
            desc = 'Linked successfully!'
        elif d_id is not None and l_id is None:  # Update user since user exists but lbxd is new
            sql = ('UPDATE users SET lbxd_id = ? WHERE disc_id = ?')
            val = (lbxd_user, member_uid)
            db.execute(sql, val)
            desc = f'Successfully changed from [{d_id[1]}](https://letterboxd.com/{d_id[1]}) to:'
        # lbxd name already exists for another user, check if this user is you (no changes) or not (illegal)
        else:
            if l_id == d_id:  # If you entered your account
                desc = f'You have already linked those accounts. No changes have been made.'
            else:
                desc = f'Hey {ctx.author.mention}! [{lbxd_user}](https://letterboxd.com/{lbxd_user}) is already linked to another account.\nPlease contact an administrator if you think this is an error.'
                show_link = False

        embed = Embed(description=desc, color=discord.Colour.green())
        if show_link:
            embed.add_field(name=ctx.author, value=f'[{lbxd_user}](https://letterboxd.com/{lbxd_user})', inline=True)
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @commands.command(name='unlink', pass_context=True)
    async def unlink_user(self, ctx):
        """Unlink the Letterboxd account associated with your Discord account"""
        member_uid = str(ctx.author.id)  # Get numerical User ID
        result = db.execute('SELECT * FROM users WHERE disc_id = ?', (member_uid,))

        if result:  # First, check if user even exists in DB
            db.execute('DELETE FROM users WHERE disc_id = ?', (member_uid,))
            description = 'Unlinked successfully!'
        else:
            description = 'Your account has not been linked yet.\nNo changes have been made.'
            result = ["", ""]

        embed = Embed(description=description, color=discord.Colour.red())
        embed.add_field(name=ctx.author, value=f'[{result[1]}](https://letterboxd.com/{result[1]})', inline=True)
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @commands.command(name='users', aliases=['linklist', 'list'], pass_context=True)
    async def link_list(self, ctx):
        """Display all Discord accounts and their linked Letterboxd accounts"""
        if ctx.author.guild_permissions.administrator:  # Only admins can list all connections
            # TODO maybe need to replace this with api_call ctx.guild.fetch_members(limit=None)
            results = db.fetch_links_from_userlist(ctx.guild.members)
            # results = db.fetch_users()  # TODO probably should join with guild db to only show users on this server

            if results is None:
                embed = Embed(description=f'There are **no** linked user accounts so far!',
                              color=discord.Colour.red(), timestamp=datetime.utcnow())

            elif len(results) < 40 and len(results) > 0:  # Max 40 fields to embed
                embed = Embed(title=f'{ctx.guild.name}\'s user list', description=f'Found **{len(results)}** users with linked accounts',
                              color=discord.Colour.green(), timestamp=datetime.utcnow())
                embed.set_thumbnail(url=res.LBXD_LOGO)
                embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')

                for r in results:
                    user = self.client.get_user(int(r[0]))
                    if user:
                        embed.add_field(name=user.name, value=f'[{r[1]}](https://letterboxd.com/{r[1]})')
            else:
                embed = Embed(description=f'There are **{len(results)}** linked user accounts on this server!',
                              color=discord.Colour.green(), timestamp=datetime.utcnow())

            await ctx.send(embed=embed)

    @link_user.error
    async def link_user_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):  # If ANY command gives this error at any point, this command runs
            # First, check if user is already in db
            result = db.execute('SELECT * FROM users WHERE disc_id = ?', (str(ctx.author.id),))  # Get numerical User ID

            if result:
                embed = Embed(title='Linked accounts', color=discord.Colour.green())
                embed.add_field(name=ctx.author,
                                value=f'[{result[1]}](https://letterboxd.com/{result[1]})', inline=True)
                embed.set_thumbnail(url=res.LBXD_LOGO)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f'Oh no {ctx.author.mention}! If you want to link your own account you need to provide your Letterboxd name: `{res.CMD_PREFIX}link <lbxd account>`')
        elif isinstance(error, OperationalError):
            await ctx.send('There was an unexpected backend error on our side. Please try again.', file=sys.stderr)
            print(error, )
        else:
            await ctx.send(error)


def setup(client):
    client.add_cog(Users(client))
    print('Users loaded')

import sqlite3
import sys
from datetime import datetime
from textwrap import dedent
from typing import Optional

import discord
import resources as res
from discord import Embed, Member
from discord.ext import commands


class Users(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(name='whois', aliases=['userinfo', 'ui', 'who'])
    # Optional is like Union[Member, None]. If member can be converted to type member it will, otherwise None
    async def whois(self, ctx, target: Optional[Member]):
        target = target or ctx.author  # If no member was specified, user author of command

        embed = Embed(title=target.name, description=target.mention,
                      color=discord.Colour.red(), timestamp=datetime.utcnow())
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.set_thumbnail(url=target.avatar_url)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')
        await ctx.send(embed=embed)

    @commands.command(name='link', pass_context=True)
    async def link_user(self, ctx, lbxd_user):
        """
        Links your Discord account to the specified Letterboxd account.
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
        db = sqlite3.connect(res.DB_NAME)
        cursor = db.cursor()
        sql = 'SELECT * FROM users WHERE disc_id = ?'
        cursor.execute(sql, (member_uid,))
        d_id = cursor.fetchone()  # First, check if user is already in db

        sql = 'SELECT * FROM users WHERE lbxd_id = ?'
        cursor.execute(sql, (lbxd_user,))
        l_id = cursor.fetchone()  # First, check if lbxd is already in db but on another account

        show_link = True  # Show new link by default

        # embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')

        if d_id is None and l_id is None:  # Add new user since both dont exist
            sql = ('INSERT INTO users(disc_id, lbxd_id) VALUES (?,?)')
            val = (member_uid, lbxd_user)
            cursor.execute(sql, val)
            desc = 'Linked successfully!'
        elif d_id is not None and l_id is None:  # Update user since user exists but lbxd is new
            sql = ('UPDATE users SET lbxd_id = ? WHERE disc_id = ?')
            val = (lbxd_user, member_uid)
            cursor.execute(sql, val)
            desc = f'Successfully changed from [{d_id[1]}](https://letterboxd.com/{d_id[1]}) to:'
        # lbxd name already exists for another user, check if this user is you (no changes) or not (illegal)
        else:
            if l_id == d_id:  # If you entered your account
                desc = f'You have already linked those accounts. No changes have been made.'
            else:
                desc = f'Hey {ctx.author.mention}! [{lbxd_user}](https://letterboxd.com/{lbxd_user}) is already linked to another account.\nPlease contact an administrator if you think this is an error.'
                show_link = False

        db.commit()
        cursor.close()
        db.close()

        embed = Embed(description=desc, color=discord.Colour.green())
        if show_link:
            embed.add_field(name=ctx.author, value=f'[{lbxd_user}](https://letterboxd.com/{lbxd_user})', inline=True)
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @commands.command(name='unlink', pass_context=True)
    async def unlink_user(self, ctx):
        """Unlink the Letterboxd account associated with your Discord account."""
        member_uid = str(ctx.author.id)  # Get numerical User ID
        db = sqlite3.connect(res.DB_NAME)
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE disc_id = ?', (member_uid,))
        result = cursor.fetchone()

        if result:  # First, check if user even exists in DB
            cursor.execute('DELETE FROM users WHERE disc_id = ?', (member_uid,))
            description = 'Unlinked successfully!'
        else:
            description = 'Your account has not been linked yet.\nNo changes have been made.'
            result = ["", ""]

        db.commit()
        cursor.close()
        db.close()

        embed = Embed(description=description, color=discord.Colour.red())
        embed.add_field(name=ctx.author, value=f'[{result[1]}](https://letterboxd.com/{result[1]})', inline=True)
        embed.set_thumbnail(url=res.LBXD_LOGO)
        await ctx.send(embed=embed)

    @commands.command(name='users', aliases=['linklist', 'list'], pass_context=True)
    async def link_list(self, ctx):
        """Display all Discord accounts and their linked Letterboxd accounts."""
        if ctx.author.guild_permissions.administrator:  # Only admins can list all connections
            db = sqlite3.connect(res.DB_NAME)
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users')
            results = cursor.fetchall()

            if results is None:
                await ctx.send('There are no linked user accounts yet!')
            else:
                embed = Embed(title='User list', description=f'Found {len(results)} users with linked accounts',
                              color=discord.Colour.green(), timestamp=datetime.utcnow())
                embed.set_thumbnail(url=res.LBXD_LOGO)
                embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')

                for r in results:
                    user = self.client.get_user(int(r[0]))
                    if user:
                        embed.add_field(name=user.name, value=f'[{r[1]}](https://letterboxd.com/{r[1]})')
                await ctx.send(embed=embed)

    @link_user.error
    async def link_user_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):  # If ANY command gives this error at any point, this command runs
            db = sqlite3.connect(res.DB_NAME)
            cursor = db.cursor()
            cursor.execute('SELECT * FROM users WHERE disc_id = ?', (str(ctx.author.id),))  # Get numerical User ID
            result = cursor.fetchone()  # First, check if user is already in db

            db.commit()
            cursor.close()
            db.close()

            if result:
                embed = Embed(title='Linked accounts', color=discord.Colour.green())
                embed.add_field(name=ctx.author,
                                value=f'[{result[1]}](https://letterboxd.com/{result[1]})', inline=True)
                embed.set_thumbnail(url=res.LBXD_LOGO)
                await ctx.send(embed=embed)
            else:
                await ctx.send(dedent(f'''
                Oh no {ctx.author.mention}! If you want to link your own account you need to provide your Letterboxd name:
                ```{res.CMD_PREFIX}link <yourLBXDuser>```'''))

        elif isinstance(error, sqlite3.OperationalError):
            await ctx.send('There was an unexpected backend error on our side. Please try again.', file=sys.stderr)
            print(error, )
        else:
            await ctx.send(error)


def setup(client):
    client.add_cog(Users(client))
    print('Users loaded')

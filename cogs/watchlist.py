import discord
import lbxd_scraper
import resources as res
from db import fetch_user
from discord import Embed, Member
from discord.ext import commands
import concurrent.futures


class Watchlist(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.preview_amount = 5

    async def get_user_lbxd(self, ctx, user):
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
                    user = self.client.get_user(int(user))  # Convert ID from DB into a Member instance
        return (user, lbxd_id)

    # todo make getlist command, opt limit parameter that shows imgs until like 10, list until like 50 and info otherwise

    @commands.group(name='watchlist', aliases=['wl'], invoke_without_command=True)
    async def watchlist(self, ctx, user=None):
        """Shows your watchlist

        Add a number after the command to show a specific amount of movies
        <= 5: With images  -> number saved in self.preview_amount
        <= 50: List without images
        > 50: General info"""

        # This is really fucking weird and definitely wrong but IDK what I'm doing man

        user = user or ctx.author
        values = await self.get_user_lbxd(ctx, user)

        user = values[0]  # Either a user Object or None
        lbxd_id = values[1]  # String containing lbxd name

        if lbxd_id:
            if user:
                await ctx.send(f'Loading watchlist for {user.mention}. Give me a few seconds 😘')
            else:
                await ctx.send(f'Loading watchlist for **{lbxd_id}**. Give me a few seconds 😘')

            result = lbxd_scraper.get_watchlist(lbxd_id, self.preview_amount)
            wl_size = result[0]
            watchlist = result[1]
            if wl_size > 0:
                # LIMIT. This is the amount of movies that will be loaded
                # Limit to 5 because only they will be displayed
                for movie in watchlist:  # Show preview of 5 movies
                    embed = Embed(title=getattr(movie, 'name'), url=getattr(movie, 'link'), description=getattr(movie, 'release_year'),
                                  color=discord.Colour.green())
                    embed.set_thumbnail(url=getattr(movie, 'img'))
                    await ctx.send(embed=embed)

                if wl_size > 5:  # show 'and x more ...' (link)
                    embed = Embed(title=f'and {wl_size - self.preview_amount} more...', url=f'{res.LBXD_URL}/{lbxd_id}/watchlist',
                                  color=discord.Colour.green())
                    embed.set_footer(icon_url=res.LBXD_LOGO,
                                     text=f'on Letterboxd.com ')  # {ctx.author.name}')
            else:
                if user:
                    embed = Embed(title=f"**{user.name}'s** watchlist", description=f'Hey {user.mention}, your watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?',
                                  color=discord.Colour.green())
                else:
                    embed = Embed(title=f"**{lbxd_id}'s** watchlist", description=f'{lbxd_id}\'s watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?',
                                  color=discord.Colour.green())

        else:
            if user:
                embed = Embed(title="Watchlist", description=f"{user.mention} hasn't linked their accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them",
                              color=discord.Colour.green())
            else:
                embed = Embed(title="Watchlist Error", description=f"There was an error processing '{lbxd_id}'.\nType ```{res.CMD_PREFIX}help link``` for help",
                              color=discord.Colour.green())

        await ctx.send(embed=embed)

    @watchlist.command(name='compare', aliases=['cmp'])
    async def compare(self, ctx, a, b=None):
        """Compare two users watchlists
        If only one person is given it compares the authors watchlist with that persons"""
        b = b or ctx.author
        values = await self.get_user_lbxd(ctx, b)
        bu = values[0]  # Either a Member object or None
        bl = values[1]  # String containing lbxd name or None

        values = await self.get_user_lbxd(ctx, a)
        au = values[0]  # Either a Member object or None
        al = values[1]  # String containing lbxd name or None

        print(f'Comparing {au} ({al}) to {bu} ({bl})')

        description = None

        if not bl and bu:  # LBXD Account for B not found, User exists -> Need to link
            description = f"{bu.mention} hasn't linked their accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them"
        if not al and au:
            description = f"{au.mention} hasn't linked their accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them"

        if description:  # description was set to something so an error occurred
            embed = Embed(
                title="Watchlist", description=description, color=discord.Colour.red())
            return await ctx.send(embed=embed)

        if al and bl:  # Two lbxd accounts were given (or at least strings)
            if al.lower() == bl.lower():  # Comparing to yourself is illegal
                embed = Embed(
                    title="Watchlist", description=f"**Bruh** you can't compare yourself to yourself, has nobody ever told you that?", color=discord.Colour.red())
                return await ctx.send(embed=embed)
            # Check if both accounts exist on lbxd
            a_watchlist_size = lbxd_scraper.get_watchlist_size(al)
            b_watchlist_size = lbxd_scraper.get_watchlist_size(bl)

            description = None
            if a_watchlist_size == -1:
                description = f"No Letterboxd account found for **{al}**!"

            if b_watchlist_size == -1:
                description = f"No Letterboxd account found for **{bl}**!"

            if a_watchlist_size == 0:
                user = au.mention if au else al  # Mention the user if their accounts are linked
                description = f"**{user}**'s watchlist is empty... Don't make work for no reason 😭"

            if b_watchlist_size == 0:
                user = bu.mention if bu else bl
                description = f"**{user}**'s watchlist is empty... Don't make work for no reason 😭"

            if description:  # description was set to something so an error occurred
                embed = Embed(
                    title="Watchlist", description=description, color=discord.Colour.red())
                return await ctx.send(embed=embed)

            # TODO maybe run this in the background while the user replies with yes to 'show all X moveis'? Idk
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []  # TODO Make this a loop and add variable amount of args to command to compare X amount of wlists
                futures.append(executor.submit(lbxd_scraper.get_watchlist, al))
                futures.append(executor.submit(lbxd_scraper.get_watchlist, bl))

            watchlists = [f.result() for f in futures]  # Wait for all the movies to be loaded

            # -1 = Acc does not exist, 0 = empty watchlist, > 0 contains wl
        print(f'WLA: {watchlists[0][0]}')
        print(f'WLB: {watchlists[1][0]}')

        """if lbxd_id:
            if user:
                await ctx.send(f'Loading watchlist for {user.mention}. This may take a few seconds...')
            else:
                await ctx.send(f'Loading watchlist for {lbxd_id}. This may take a few seconds...')

            result = lbxd_scraper.get_watchlist(lbxd_id, self.preview_amount)
            wl_size = result[0]
            watchlist = result[1]

            if wl_size > 0:
                # LIMIT. This is the amount of movies that will be loaded
                # Limit to 5 because only they will be displayed
                for movie in watchlist:  # Show preview of 5 movies
                    embed = Embed(title=getattr(movie, 'name'), url=getattr(movie, 'link'), description=getattr(movie, 'release_year'),
                                  color=discord.Colour.green())
                    embed.set_thumbnail(url=getattr(movie, 'img'))
                    await ctx.send(embed=embed)

                if wl_size > 5:  # show 'and x more ...' (link)
                    embed = Embed(title=f'and {wl_size - self.preview_amount} more...', url=f'{res.LBXD_URL}/{lbxd_id}/watchlist',
                                  color=discord.Colour.green())
                    embed.set_footer(icon_url=res.LBXD_LOGO,
                                     text=f'on Letterboxd.com ')  # {ctx.author.name}')
            else:
                if user:
                    embed = Embed(title=f"**{user.name}'s** watchlist", description=f'Hey {user.mention}, your watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?',
                                  color=discord.Colour.green())
                else:
                    embed = Embed(title=f"**{lbxd_id}'s** watchlist", description=f'{lbxd_id}\'s watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?',
                                  color=discord.Colour.green())

        else:
            if user:
                embed = Embed(title="Watchlist", description=f"{user.mention} hasn't linked their accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them",
                              color=discord.Colour.green())
            else:
                embed = Embed(title="Watchlist Error", description=f"There was an error processing '{lbxd_id}'.\nType ```{res.CMD_PREFIX}help link``` for help",
                              color=discord.Colour.green())"""

        # await ctx.send(embed=embed)

    @compare.error
    async def compare_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):  # If ANY command gives this error at any point, this command runs
            await ctx.send('Error: You need to specify at least one other User to compare your watchlist with')  # TODO


def setup(client):
    client.add_cog(Watchlist(client))
    print('Watchlist loaded')

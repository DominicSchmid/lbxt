import concurrent.futures
import random
from datetime import datetime

import discord
import lbxd_scraper
import resources as res
from discord import Embed, Member
from discord.ext import commands
from resources import Movielist

from cogs.users import Users


class Watchlist(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.preview_amount = 5

    # todo make getlist command, opt limit parameter that shows imgs until like 10, list until like 50 and info otherwise

    @commands.group(name='watchlist', aliases=['wl'], invoke_without_command=True)
    async def watchlist(self, ctx, user=None):
        """Shows a user's watchlist"""

        """TODO? Add a number after the command to show a specific amount of movies
        <= 5: With images  -> number saved in self.preview_amount
        <= 50: List without images
        > 50: General info"""

        user = user or ctx.author
        values = await Users.get_user_lbxd(self.client, ctx, user)
        user = values[0]  # Either a user Object or None
        lbxd_id = values[1]  # String containing lbxd name

        if lbxd_id:
            if user:
                await ctx.send(f'Loading watchlist for {user.mention}. Give me a few seconds 😘', delete_after=15)
            else:
                await ctx.send(f'Loading watchlist for **{lbxd_id}**. Give me a few seconds 😘', delete_after=15)

            movielist = lbxd_scraper.get_watchlist(lbxd_id, self.preview_amount)

            if not movielist:  # Account does not exists
                embed = Embed(title="Watchlist Error", description=f"The Letterboxd account **{lbxd_id}** doesn't exist.\nLearn to type yo",
                              color=discord.Colour.red())
                return await ctx.send(embed=embed)

            wl_size = movielist.length()
            watchlist = movielist.get_movies()
            if wl_size > 0:
                # LIMIT. This is the amount of movies that will be loaded
                # Limit to 5 because only they will be displayed
                for movie in watchlist:  # Show preview of 5 movies
                    embed = Embed(title=getattr(movie, 'name'), url=getattr(movie, 'link'), description=getattr(movie, 'release_year'),
                                  color=discord.Colour.green())
                    embed.set_thumbnail(url=getattr(movie, 'img'))
                    await ctx.send(embed=embed)

                if wl_size >= self.preview_amount:  # show 'and x more ...' (link)
                    original_watchlist_size = lbxd_scraper.get_watchlist_size(lbxd_id)
                    embed = Embed(title=f'and {original_watchlist_size - self.preview_amount} more...', url=f'{res.LBXD_URL}/{lbxd_id}/watchlist',
                                  color=discord.Colour.green())
                    embed.set_footer(icon_url=res.LBXD_LOGO,
                                     text=f'on Letterboxd.com ')  # {ctx.author.name}')
                    await ctx.send(embed=embed)
                return
            else:
                if user:
                    embed = Embed(title=f"{user.name}'s watchlist", description=f'Hey {user.mention}, your watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?',
                                  color=discord.Colour.red())
                else:
                    embed = Embed(title=f"{lbxd_id}'s watchlist", description=f"*{lbxd_id}'s* watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?",
                                  color=discord.Colour.red())

        else:
            if user:
                embed = Embed(title="Watchlist", description=f"{user.mention} hasn't linked their accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them",
                              color=discord.Colour.red())
            else:
                embed = Embed(title="Watchlist Error", description=f"There was an error processing **{lbxd_id}**.\nMake sure you enter a Discord account or a Letterboxd account that exists",
                              color=discord.Colour.red())

        await ctx.send(embed=embed)

    @watchlist.command(name='compare', aliases=['cmp'])
    async def compare(self, ctx, *others):
        """If one person specified, compare your linked account with them. Otherwise compare all specified (WITHOUT you)"""
        if len(others) == 0:  # Illegal
            return await ctx.send(f"Error: {ctx.author.mention} you're going to have to tell me who to compare your watchlist to. **Try this:** ```{res.CMD_PREFIX}wl cmp <another lbxd account>```")

        users = []  # create list from *others tuple

        if len(others) == 1:  # Compare author with person specified in others
            values = await Users.get_user_lbxd(self.client, ctx, ctx.author)
            lbxd = values[1]  # String containing lbxd name or Non""e
            if not lbxd:  # LBXD Account for B not found, User exists -> Need to link
                embed = Embed(
                    title="Watchlist", description=f"{ctx.author.mention} you haven't linked your account yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link it", color=discord.Colour.red())
                return await ctx.send(embed=embed)
            users.append((ctx.author, lbxd))

        # Check all others for errors
        for other in others:
            values = await Users.get_user_lbxd(self.client, ctx, other)
            user = values[0]  # Either a Member object or None
            lbxd = values[1]  # String containing lbxd name or Non""e

            if user and not lbxd:  # LBXD Account for B not found, User exists -> Need to link
                embed = Embed(
                    title="Watchlist", description=f"{user.mention} hasn't linked their accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them", color=discord.Colour.red())
                return await ctx.send(embed=embed)

            if lbxd.lower() in [name[1].lower() for name in users]:  # Comparing to yourself is illegal (even once)
                embed = Embed(
                    title="Watchlist", description=f"**Bruh** you can't compare yourself to yourself, has nobody ever told you that?", color=discord.Colour.red())
                return await ctx.send(embed=embed)
            users.append((user, lbxd))

        await ctx.send(f'Loading watchlists... Give me a few seconds 😘 (a lot.. like.. 10 or 15)', delete_after=20)

        futures = []
        # Check if accounts exist on lbxd
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for u in users:
                user = u[0]  # Either a Member object or None
                lbxd = u[1]  # String containing lbxd name or Non""e

                watchlist_size = lbxd_scraper.get_watchlist_size(lbxd)

                description = None
                if watchlist_size == -1:
                    description = f"No Letterboxd account found for **{lbxd}**!"

                if watchlist_size == 0:
                    user = user.mention if user else lbxd  # Mention the user if their accounts are linked
                    description = f"**{user}**'s watchlist is empty... Don't make work for no reason 😭"

                if description:  # description was set to something so an error occurred
                    embed = Embed(
                        title="Watchlist", description=description, color=discord.Colour.red())
                    return await ctx.send(embed=embed)

                # TODO maybe run this in the background while the user replies with yes to 'show all X moveis'? Idk
                futures.append(executor.submit(lbxd_scraper.get_watchlist, lbxd))

        # Wait for all the movies to be loaded
        watchlists = [f.result() for f in futures]

        # -1 = Acc does not exist, 0 = empty watchlist, > 0 contains wl
        #common_movies = res.Movielist(watchlists[0]).get_common_movies([watchlists[1]])
        common_movies = Movielist.common_movies(watchlists)

        if common_movies.length() == 0:  # no commons found
            embed = Embed(title=f'There are no movies that are on all {len(users)} lists 😞', description='Add more movies to [your watchlist](https://letterboxd.com/watchlist)',
                          color=discord.Colour.green())
            embed.set_thumbnail(url=res.LBXD_LOGO)
        else:
            image = random.choice(common_movies.get_movies()).img
            description = ""
            for movie in common_movies.get_movies():
                if len(description) > 2000:  # Description max length = 2048
                    description = "\n\nand more... This was definitely enough!"  # EZ Clap 5 to spare
                description += str(movie) + "\n"

            embed = Embed(title=f'There are **{common_movies.length()}** movies on everyones watchlist! 🙌', description=description,
                          color=discord.Colour.green(), timestamp=datetime.utcnow())
            embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author.name}')
            if image:
                embed.set_thumbnail(url=image)
            else:
                embed.set_thumbnail(url=res.LBXD_LOGO)
            # TODO Reply 'yes' to this to get a file with all of them or 'random <amount>' to get a random one from the list
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Watchlist(client))
    print('Watchlist loaded')

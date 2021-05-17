from typing import Optional

import discord
import lbxd_scraper
import resources as res
from db import fetch_user
from discord import Embed, Member
from discord.ext import commands


class Watchlist(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.preview_amount = 5

    # todo make getlist command, opt limit parameter that shows imgs until like 10, list until like 50 and info otherwise
    @commands.group(name='watchlist', aliases=['wl'], invoke_without_command=True)
    async def watchlist(self, ctx, user=None):
        """Shows your watchlist

        Add a number after the command to show a specific amount of movies
        <= 5: With images  -> number saved in self.preview_amount
        <= 50: List without images
        > 50: General info"""

        # This is really fucking weird and definitely wrong but IDK what I'm doing man

        if user:  # User provided
            if isinstance(user, Member):  # If user is a member, fetch his lbxd_id (can be None) from db
                lbxd_id = fetch_user(user.id)
            else:  # isinstance(user, str):
                try:  # to convert given user (eg. username)
                    user = await commands.MemberConverter().convert(ctx, str(user))
                    lbxd_id = fetch_user(user.id)
                except commands.BadArgument:  # If conversion doesnt work, expect a LBXD_ID username
                    lbxd_id = user
                    user = fetch_user(lbxd_id)  # Get associated discord account from DB. If there isnt one -> None
        else:  # User wasn't provided, use command author
            user = ctx.author
            lbxd_id = fetch_user(user.id)

        if lbxd_id:
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
                              color=discord.Colour.green())

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Watchlist(client))
    print('Watchlist loaded')

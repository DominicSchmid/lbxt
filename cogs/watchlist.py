import discord
import lbxd_scraper
import resources as res
from discord import Embed, Member
from discord.ext import commands

from db import fetch_user


class Watchlist(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.preview_amount = 5

        # todo make getlist command, opt limit parameter that shows imgs until like 10, list until like 50 and info otherwise
    @commands.group(name='wl', aliases=['watchlist'], invoke_without_command=True)
    async def watchlist(self, ctx):
        """Shows your watchlist

        Add a number after the command to show a specific amount of movies 
        <= 5: With images  -> number saved in self.preview_amount
        <= 50: List without images
        > 50: General info"""
        lbxd_id = fetch_user(ctx.author.id)
        if lbxd_id:
            # TODO make a different command to load like all of them
            await ctx.send(f'Loading watchlist for {ctx.author.mention}. This may take a few seconds...')

            wl_size = lbxd_scraper.get_watchlist_size(lbxd_id)
            if wl_size > 0:
                # LIMIT. This is the amount of movies that will be loaded
                # Limit to 5 because only they will be displayed
                watchlist = lbxd_scraper.get_watchlist(lbxd_id, self.preview_amount)

                for movie in watchlist:  # Show preview of 5 movies
                    description = getattr(movie, 'release_year')
                    embed = Embed(title=getattr(movie, 'name'), url=getattr(movie, 'link'), description=description,
                                  color=discord.Colour.green())
                    embed.set_thumbnail(url=getattr(movie, 'img'))
                    await ctx.send(embed=embed)

                if wl_size > 5:  # show 'and x more ...' (link)
                    embed = Embed(title=f'and {wl_size - self.preview_amount} more...', url=f'{res.LBXD_URL}/{lbxd_id}/watchlist',
                                  color=discord.Colour.green())
                    embed.set_footer(icon_url=res.LBXD_LOGO,
                                     text=f'on Letterboxd.com ')  # {ctx.author.name}')
            else:
                description = ''
                embed = Embed(title='Watchlist', description=f'Hey {ctx.author.mention}, your watchlist seems to be empty!\nWould you like to [add some movies]({res.LBXD_URL}/{lbxd_id}/watchlist)?',
                              color=discord.Colour.green())
        else:
            embed = Embed(title='Watchlist', description=f"Hey {ctx.author.mention}, you haven't linked your accounts yet!\nType ```{res.CMD_PREFIX}link <lbxd account>``` to link them",
                          color=discord.Colour.green())

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Watchlist(client))
    print('Watchlist loaded')

import discord
import lbxd_scraper
import resources as res
from discord import Embed, Member
from discord.ext import commands

import db


class Movielist(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.preview_amount = 5

        # todo make getlist command, opt limit parameter that shows imgs until like 10, list until like 50 and info otherwise


def setup(client):
    client.add_cog(Movielist(client))
    print('Movielist loaded')

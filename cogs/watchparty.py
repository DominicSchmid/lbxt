import json
import sqlite3
from datetime import datetime
from textwrap import dedent
from typing import Optional

import discord
from discord import Embed, Member
from discord.ext import commands

# When everybody leaves the cinema set a 5 minute timeout after which the watchparty will be closed.


class Watchparty(commands.Cog):

    def __init__(self, client):
        self.client = client


def setup(client):
    client.add_cog(Watchparty(client))
    print('Watchparty loaded')

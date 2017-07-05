import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from cogs.utils import checks


class ReeeAction:
    """custom cog for a configureable suggestion box"""

    __author__ = "sigttou"
    __version__ = "0.0.1"

    def __init__(self, bot):
        self.bot = bot
        self.channel = "#shitpostingaeiou"

    async def on_message(self, message):
        if(not message.content.contains("REEE"))
            return
        if(message.channel != self.channel)
            self.bot.say(self.channel)

def setup(bot):
    n = ReeeAction(bot)
    bot.add_cog(n)

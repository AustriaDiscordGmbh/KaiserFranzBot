import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from cogs.utils import checks


class Quote:
    """Simple quote cog"""

    __author__ = "pitikay"
    __version__ = "0.1"

    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "💾":
            await self.add_quote(reaction.message)

    async def add_quote(self, message):
        await self.bot.send_message(message.channel,
            "'{}' - {}".format(message.content, message.author.name))

def setup(bot):
    bot.add_cog(Quote(bot))

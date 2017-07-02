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

    @client.event
    async def on_reaction_add(reaction, user):
        if reaction.emoji.name == ":sweat_drops:":
            m = reaction.message
            await self.add_quote(m)

    def add_quote(message):
        await client.send_message(message.channel, '"' + message.content + '" - ' + message.author)

    def setup(bot):
        n = Quote(bot)
        bot.add_cog(n)

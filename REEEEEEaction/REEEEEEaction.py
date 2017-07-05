import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils import checks


class ReeeAction:
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        if(not "reee" in message.content.lower()):
            return
        shit = discord.utils.find(lambda m: str(c.name) == "shitpostingaeiou", message.server.channels)
        if(shit != message.channel):
            self.bot.say(shit.mention)

def setup(bot):
    bot.add_cog(ReeeAction(bot))

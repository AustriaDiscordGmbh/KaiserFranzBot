import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils import checks


class ReeeAction:
    def __init__(self, bot):
        self.bot = bot
        self.channel = "#shitpostingaeiou"

    async def on_message(self, message):
        if(not "reee" in message.content.to_lower())
            return
        if(message.channel != self.channel)
            self.bot.say(self.channel)

def setup(bot):
    bot.add_cog(ReeeAction(bot))

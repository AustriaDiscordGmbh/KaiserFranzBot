import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils import checks
import re


class RedditLinker:
    subRegex = re.compile(r"r\/([a-zA-Z0-9_]*)($|\s)")

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        if(not message.server):
            return
        if(message.author.bot):
            return
        
        matches = self.subRegex.findall(message.content)

        linkMessage = ""
        for match in matches:
            linkMessage += "https://reddit.com/r/" + match[0] + "\n"

        if linkMessage != "":
            await self.bot.send_message(message.channel, linkMessage)




def setup(bot):
    bot.add_cog(RedditLinker(bot))

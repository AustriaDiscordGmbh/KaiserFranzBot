import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils import checks
import re


class RedditLinker:
    subRegex = re.compile(r"(^|\s)[\/]?r\/([a-zA-Z0-9_]+)(?=($|\s))")
    subBlacklist = ["austria", "de", "aeiou", "europe"]

    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        if(not message.server or message.author.bot):
            return
        
        matches = self.subRegex.findall(message.content)

        links = ["https://reddit.com/r/" + match[1] for match in matches if match[1].lower() not in [x.lower() for x in self.subBlacklist]]
        if len(links):
            await self.bot.send_message(message.channel, "\n".join(links))




def setup(bot):
    bot.add_cog(RedditLinker(bot))

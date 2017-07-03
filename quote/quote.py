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
            await self.add_quote(reaction.message, user)

    async def add_quote(self, message, user):
        author = message.author
        content = message.clean_content
        timestamp = message.timestamp.strftime('%Y-%m-%d %H:%M')
        avatar = author.avatar_url if author.avatar \
            else author.default_avatar_url

        em = discord.Embed(description=content,
                           color=discord.Color.purple())
        em.set_author(name='Quote from {}'.format(author.name),
                      icon_url=avatar)
        em.set_footer(text='Quote made at {} UTC by {}'.format(timestamp, user))
        await self.bot.send_message(message.channel, embed=em)

def setup(bot):
    bot.add_cog(Quote(bot))

import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from cogs.utils import checks
import json

class Quote:
    """Simple quote cog"""

    __author__ = "pitikay"
    __version__ = "0.1"

    def __init__(self, bot):
        with open('quotes.json') as data:
            self.quotes = json.load(data)
        if not self.quotes:
            self.quotes = []
        self.bot = bot

    def __del__(self):
        store_quotes()

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "💾" and reaction.count == 1:
            await self.add_quote(reaction.message, user)

    async def add_quote(self, message, user):
        quote = quote_from_message(message, user)
        self.quotes.append(quote)
        store_quotes()
        send_quote_to_channel(quote, message.channel)

    async def send_quote_to_channel(self, quote, channel):
        em = gen_embed(quote)
        await self.bot.send_message(channel, embed=em)

    def gen_embed(self, quote):
        author = quote.get("author")
        content = quote.get("content")
        timestamp = quote.get("time")
        avatar = quote.get("avatar_url")
        adder = quote.get("adder")
        em = discord.Embed(description=content,
                           color=discord.Color.purple())
        em.set_author(name='Quote from {}'.format(author.name),
                      icon_url=avatar)
        em.set_footer(text='Quote made at {} UTC by {}'.format(timestamp, adder))
        return em
        timestamp = message.timestamp.strftime('%Y-%m-%d %H:%M')
        avatar = author.avatar_url if author.avatar \
            else author.default_avatar_url

    def quote_from_message(self, message, user):
        quote = {}
        quote["author"] = message.author
        quote["adder"] = user.name
        quote["content"] = message.clean_content
        quote["time"] = message.timestamp.strftime('%Y-%m-%d %H:%M')
        quote["avatar"] = author.avatar_url if author.avatar \
            else author.default_avatar_url
        return quote

    def store_quotes(self):
        with open('quotes.json') as out:
            json.dump(self.quotes, out)


def setup(bot):
    bot.add_cog(Quote(bot))

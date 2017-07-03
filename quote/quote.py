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
        self.bot = bot

        try:
            with open('quotes.json', 'r') as f:
                self.quotes = json.load(f)
        except FileNotFoundError:
            self.quotes = []

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "💾" and reaction.count == 1:
            await self.add_quote(reaction.message, user)

    async def add_quote(self, message, user):
        quote = self.quote_from_message(message, user)
        self.quotes.append(quote)
        self.store_quotes()
        self.send_quote_to_channel(quote, message.channel)

    async def send_quote_to_channel(self, quote, channel):
        em = self.gen_embed(quote)
        await self.bot.send_message(channel, embed=em)

    @commands.command(name="quote", pass_context=True)
    async def get_quote(self, ctx):
        await self.send_quote_to_channel(get_random_quote)

    def gen_embed(self, quote):
        author = quote.get("author")
        content = quote.get("content")
        timestamp = quote.get("time")
        avatar = quote.get("avatar_url")
        adder = quote.get("adder")
        quote_id = quote.get("id")
        em = discord.Embed(description=content,
                           color=discord.Color.purple())
        em.set_author(name='Quote from {}'.format(author.name),
                      icon_url=avatar)
        em.set_footer(text='Quote {} made at {} UTC by {}'.format(quote_id, timestamp, adder))
        return em

    def quote_from_message(self, message, user):
        quote = {}
        quote["author"] = message.author
        quote["adder"] = user.name
        quote["content"] = message.clean_content
        quote["id"] = str(message.id)
        quote["time"] = message.timestamp.strftime('%Y-%m-%d %H:%M')
        quote["avatar"] = author.avatar_url if author.avatar \
            else author.default_avatar_url
        return quote

    def get_random_quote(self):
        return random.choice(self.quotes)

    def delete_quote(self, qid):
        for q in self.quotes:
            if q.get("id") == str(qid):
                self.quotes.remove(q)
                break
        self.store_quotes()

    def store_quotes(self):
        with open('quotes.json', 'w') as out:
            json.dump(self.quotes, out)


def setup(bot):
    bot.add_cog(Quote(bot))

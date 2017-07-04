import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from cogs.utils import checks
import json
import random

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
            self.quotes = {}

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "💾" and reaction.count == 1:
            await self.add_quote(reaction.message, user)

    async def add_quote(self, message, user):
        quote = self.quote_from_message(message, user)
        if(not quote["content"]):
            await self.bot.say(message.channel, "Empty quotes are not allowed!")
            return
        aid = quote["aid"]
        qid = quote["qid"]
        if(not self.quotes.get(aid)):
            self.quotes[aid] = {}
        if(self.quotes[aid].get(qid)):
            await self.bot.say(message.channel, "This message was already added!")
            return

        self.quotes[aid][qid] = quote
        self.store_quotes()
        await self.send_quote_to_channel(quote, message.channel)

    async def send_quote_to_channel(self, quote, channel):
        em = self.gen_embed(quote)
        await self.bot.send_message(channel, embed=em)

    @commands.command(name="quote", pass_context=True)
    async def get_quote(self, ctx):
        author = random.choice(self.quotes.keys)
        entry = random.choice(self.quotes[author].keys)
        await self.send_quote_to_channel(self.quotes[author][entry], ctx.message.channel)

    def gen_embed(self, quote):
        author = quote.get("author")
        content = quote.get("content")
        timestamp = quote.get("time")
        avatar = quote.get("avatar")
        adder = quote.get("adder")
        quote_id = quote.get("qid")
        em = discord.Embed(description=content,
                           color=discord.Color.purple())
        em.set_author(name='Quote from {}'.format(author),
                      icon_url=avatar)
        em.set_footer(text='Quote {} added at {} UTC by {}'.format(quote_id, timestamp, adder))
        return em

    def quote_from_message(self, message, user):
        quote = {}
        quote["author"] = message.author.name
        quote["aid"] = message.author.id
        quote["adder"] = user.name
        quote["content"] = message.clean_content
        quote["qid"] = str(message.id)
        quote["time"] = message.timestamp.strftime('%Y-%m-%d %H:%M')
        author = message.author
        quote["avatar"] = author.avatar_url if author.avatar \
            else author.default_avatar_url
        return quote

    def delete_quote(self, qid, channel):
        found = False
        for author in self.quotes.keys:
            for q in self.quotes[author]:
                if q.get("qid") == str(qid):
                    self.quotes.remove(q)
                    found = True
                    break
            if(found):
                break
        if(found):
            self.bot.send_message(channel, "Deleted quote!")
        else:
            self.bot.send_message(channel, "Quote not found!")
        self.store_quotes()

    def store_quotes(self):
        with open('quotes.json', 'w') as out:
            json.dump(self.quotes, out)


def setup(bot):
    bot.add_cog(Quote(bot))

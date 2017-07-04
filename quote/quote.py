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
            await self.bot.send_message(message.channel, "Empty quotes are not allowed!")
            return
        aid = quote["aid"]
        qid = quote["qid"]
        if(not self.quotes.get(aid)):
            self.quotes[aid] = {}
        if(self.quotes[aid].get(qid)):
            await self.bot.send_message(message.channel, "This message was already added!")
            return

        self.quotes[aid][qid] = quote
        self.store_quotes()
        await self.send_quote_to_channel(quote, message.channel)

    async def send_quote_to_channel(self, quote, channel):
        em = self.gen_embed(quote, channel)
        await self.bot.send_message(channel, embed=em)

    @commands.command(name="quote", pass_context=True)
    async def get_quote(self, ctx):
        if(not self.quotes):
            await self.bot.send_message(ctx.message.channel, "No quotes available!")
            return
        if(ctx.message.mentions):
            author = random.choice(ctx.message.mentions).id
            if(not self.quotes.get(author)):
                await self.bot.send_message(ctx.message.channel, "No quotes from this author")
                return
        else:
            author = random.choice(list(self.quotes.keys()))
        if(self.quotes[author].keys()):
            entry = random.choice(list(self.quotes[author].keys()))
            await self.send_quote_to_channel(self.quotes[author][entry], ctx.message.channel)
        else:
            await self.bot.send_message(ctx.message.channel, "No quotes available!")

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(name="delquote", pass_context=True)
    async def del_quote(self, ctx):
        message = ctx.message
        channel = message.channel
        qid = int(message.clean_content.replace("!delquote ", "", 1))
        found = False
        for author in self.quotes.keys():
            for q in self.quotes[author].keys():
                if q == str(qid):
                    self.quotes[author].pop(q)
                    if(not self.quotes[author].keys()):
                        self.quotes.pop(author)
                    found = True
                    break
            if(found):
                break
        if(found):
            await self.bot.send_message(channel, "Deleted quote!")
        else:
            await self.bot.send_message(channel, "Quote not found!")
        self.store_quotes()

    def gen_embed(self, quote, channel):
        member = discord.utils.find(lambda m: str(m.id) == quote.get("aid"), channel.server.members)
        if(member):
            author = member.display_name
        else:
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
        quote["author"] = message.author.display_name
        quote["aid"] = message.author.id
        quote["adder"] = user.name
        quote["content"] = message.clean_content
        quote["qid"] = str(message.id)
        quote["time"] = message.timestamp.strftime('%Y-%m-%d %H:%M')
        author = message.author
        quote["avatar"] = author.avatar_url if author.avatar \
            else author.default_avatar_url
        return quote

    def store_quotes(self):
        with open('quotes.json', 'w') as out:
            json.dump(self.quotes, out)


def setup(bot):
    bot.add_cog(Quote(bot))

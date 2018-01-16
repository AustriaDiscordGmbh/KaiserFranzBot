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
        if reaction.emoji == u"\U0001F5D1": 
            if reaction.count == 5:
                await self.votedel_quote(reaction.message)
            elif user.server_permissions.manage_roles:
                await self.votedel_quote(reaction.message)

    async def add_quote(self, message, user):
        image = False
        if(not message.clean_content):
            if(message.attachments and message.attachments[0].get("width")):
                image = True
            else:
                await self.bot.send_message(message.channel, "Heast, leere Zitate gehn net!")
                return

        quote = self.quote_from_message(message, user, image)
        aid = quote["aid"]
        qid = quote["qid"]
        if(not self.quotes.get(aid)):
            self.quotes[aid] = {}
        if(self.quotes[aid].get(qid)):
            await self.bot.send_message(message.channel, "Oida des hob i scho gspeichert!")
            return

        self.quotes[aid][qid] = quote
        self.store_quotes()
        await self.send_quote_to_channel(quote, message.channel)


    async def votedel_quote(self, message):
        if(not message.embeds):
            return
        footer = message.embeds[0].get("footer")
        if(not footer or not footer.get("text")):
            return
        if(not (len(footer["text"].split()) > 1)):
            return
        qid = footer["text"].split()[1]
        if(not qid.isdigit()):
            return

        await self.del_quote_by_id(qid, message.channel)

    async def send_quote_to_channel(self, quote, channel):
        em = self.gen_embed(quote, channel)
        await self.bot.send_message(channel, embed=em)

    @commands.command(name="quote", pass_context=True)
    async def get_quote(self, ctx):
        if(not self.quotes):
            await self.bot.send_message(ctx.message.channel, "I hob no kane Zitate gspeichert.")
            return

        authorId = ctx.message.clean_content.replace("!quote", "", 1).strip()

        print(authorId)

        if(ctx.message.mentions):
            author = random.choice(ctx.message.mentions).id

            if(not self.quotes.get(author)):
                await self.bot.send_message(ctx.message.channel, "Der hot no nix deppates gsogt.")
                return
        elif authorId != "":
            if authorId in self.quotes:
                author = authorId
            else:
                # search quotes for passed id
                for userId in self.quotes:
                    for quote in self.quotes[userId].values():
                        if quote.qid == authorId:
                            await self.send_quote_to_channel(quote, ctx.message.channel)
                            return

                author = None
                for userId in self.quotes:
                    if authorId.lower() == list(self.quotes[userId].values())[0]["author"].lower():
                        author = userId
                        break
                
                if author is None:
                    await self.bot.send_message(ctx.message.channel, "I hob niemand mit dem Namen gfundn.")
                    return
        else:
            author = random.choice(list(self.quotes.keys()))

        if(self.quotes[author].keys()):
            entry = random.choice(list(self.quotes[author].keys()))
            await self.send_quote_to_channel(self.quotes[author][entry], ctx.message.channel)
        else:
            await self.bot.send_message(ctx.message.channel, "I hob no kane Zitate gspeichert.")

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(name="delquote", pass_context=True)
    async def del_quote(self, ctx):
        message = ctx.message
        channel = message.channel
        qid = int(message.clean_content.replace("!delquote ", "", 1))
        await self.del_quote_by_id(qid, channel)

    async def del_quote_by_id(self, qid, channel):
        for author in self.quotes.keys():
            for q in self.quotes[author].keys():
                if q == str(qid):
                    self.quotes[author].pop(q)
                    if(not self.quotes[author].keys()):
                        self.quotes.pop(author)
                    await self.bot.send_message(channel, "Zitat is glöscht!")
                    self.store_quotes()
                    return
        await self.bot.send_message(channel, "Ka Zitat gfunden!")

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
        if(quote.get("content")):
            em = discord.Embed(description=content,
                               color=discord.Color.purple())
        else:
            em = discord.Embed(color=discord.Color.purple())
        if(quote.get("image")):
            em.set_image(url=quote["image"])

        em.set_author(name='Zitat von {}'.format(author),
                      icon_url=avatar)
        em.set_footer(text='Zitat {} hinzugfügt am {} UTC von {}'.format(quote_id, timestamp, adder))
        return em

    def quote_from_message(self, message, user, image=False):
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
        if(image):
            quote["image"] = message.attachments[0]["url"]
        return quote

    def store_quotes(self):
        with open('quotes.json', 'w') as out:
            json.dump(self.quotes, out)


def setup(bot):
    bot.add_cog(Quote(bot))

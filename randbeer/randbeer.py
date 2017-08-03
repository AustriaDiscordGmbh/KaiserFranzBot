import os
import asyncio  # noqa: F401
import discord
import json
import random
from urllib.request import urlopen
from discord.ext import commands


API_KEY = "YOUR_KEY_HERE"
BASE_URL = "https://pixabay.com/api/"
SEARCH = "beer"
URL = BASE_URL + "?key=" + API_KEY + "&q=" + SEARCH

class RandBeer:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="beer", pass_context=True)
    async def post_beer(self, ctx):
        message = ctx.message
        f = urlopen(URL)
        data = json.load(f)
        f.close()
        print(data)
        #results = data['responseData']['results']
        #url = results[random.randint(0, len(results) - 1)]['url']
        await self.bot.send_message(message.channel, url)

def setup(bot):
    bot.add_cog(RandBeer(bot))

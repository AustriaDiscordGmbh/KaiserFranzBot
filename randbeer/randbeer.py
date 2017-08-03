import asyncio  # noqa: F401
import discord
import random
from requests import get
from discord.ext import commands


class RandBeer:
    def __init__(self, bot):
        self.url = "https://pixabay.com/api/"
        self.search = "beer"
        self.api_key = "YOUR_API_KEY_HERE"
        self.bot = bot

    @commands.command(name="beer", pass_context=True)
    async def post_beer(self, ctx):
        message = ctx.message
        payload = {'key': self.api_key, 'q': self.search, 'per_page': '200'}
        reply = get(self.url, params=payload).json()
        results = reply["hits"]
        url = results[random.randint(0, len(results) - 1)]["webformatURL"]
        await self.bot.send_message(message.channel, url)


def setup(bot):
    bot.add_cog(RandBeer(bot))

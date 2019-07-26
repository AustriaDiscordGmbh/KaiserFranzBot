from redbot.core import commands
import discord
from datetime import datetime


class Suggest(commands.Cog):
    """My suggest"""
    def __init__(self, bot):
        self.bot = bot
        self.suggestchan = 330390950301925378
        # self.suggestchan = 603891211673272350

    async def make_embed(self, data):
        e = discord.Embed(color=0x7289DA, description=data)
        e.set_author(name=f"Suggestion:")
        e.timestamp = datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f")
        return e

    @commands.command()
    async def suggest(self, ctx, *, content):
        e = await self.make_embed(content)
        chan = self.bot.get_channel(self.suggestchan)
        m = await chan.send(embed=e)
        await m.add_reaction(u"\U00002B06")
        await m.add_reaction(u"\U00002B07")

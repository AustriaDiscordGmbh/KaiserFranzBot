import discord
from redbot.core import commands

class ORFcog(commands.Cog):
    """ORF cog"""

    async def _manage_pins(self, message: discord.Message):
        pins = await message.channel.pins()
        try:
            for pin in pins:
                if message.author.id == pin.author.id:
                    await pin.unpin()
            await message.pin()
        except discord.Forbidden:
            await message.channel.send("Ich benötige die 'Manage Messages' Berechtigung, um die Nachricht zu pinnen")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        if author.bot and author.name == "ORF LIVE-SPEZIAL HEUTE":
            await self._manage_pins(message)

from redbot.core import commands
import discord


class ModMode(commands.Cog):
    """
    Enables or disables mod role colour
    """

    def __init__(self, bot):
        """
        Inits bot and checkpot
        """
        self.bot = bot

    @commands.command(name="modmode")
    async def modmode(self, ctx, *, arg=None):
        """
        enables or disables modmode
        arg either on or off
        """
        server = ctx.guild
        role = discord.utils.get(server.roles, name="Mods")
        if arg == "off":
            await role.edit(colour=discord.Colour(0))
            await ctx.send("Mod colour disabled.")
        else:
            await role.edit(colour=discord.Colour(0xB92615))
            await ctx.send("Mods are now visible.")

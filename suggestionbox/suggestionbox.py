import os
import asyncio  # noqa: F401
import discord
import logging
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from cogs.utils import checks


class SuggestionBox:
    """custom cog for a configureable suggestion box"""

    __author__ = "mikeshardmind"
    __version__ = "1.2"

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/suggestionbox/settings.json')
        for s in self.settings:
            self.settings[s]['usercache'] = []

    def save_json(self):
        dataIO.save_json("data/suggestionbox/settings.json", self.settings)

    @commands.group(name="setsuggest", pass_context=True, no_pm=True)
    async def setsuggest(self, ctx):
        """configuration settings"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    def initial_config(self, server_id):
        """makes an entry for the server, defaults to turned off"""

        if server_id not in self.settings:
            self.settings[server_id] = {'inactive': True,
                                        'output': [],
                                        'cleanup': False,
                                        'usercache': [],
                                        'multiout': False
                                        }
            self.save_json()

    @checks.admin_or_permissions(Manage_server=True)
    @setsuggest.command(name="fixcache", pass_context=True, no_pm=True)
    async def fix_cache(self, ctx):
        """use this if the bot gets stuck not recording your response"""
        self.initial_config(ctx.message.server.id)
        self.settings[server.id]['usercache'] = []
        self.save_json()

    @checks.admin_or_permissions(Manage_server=True)
    @setsuggest.command(name="output", pass_context=True, no_pm=True)
    async def setoutput(self, ctx, chan=None):
        """sets the output channel(s) by id"""
        server = ctx.message.server
        if server.id not in self.settings:
            self.initial_config(server.id)

        if chan in self.settings[server.id]['output']:
            return await self.bot.say("Die Ausgabe is scho in dem Kanal")
        for channel in server.channels:
            if str(chan) == str(channel.id):
                if self.settings[server.id]['multiout']:
                    self.settings[server.id]['output'].append(chan)
                    self.save_json()
                    return await self.bot.say("Ausgabe is jetzt a in dem Kanal")
                else:
                    self.settings[server.id]['output'] = [chan]
                    self.save_json()
                    return await self.bot.say("Ausgabe is jetzt in dem Kanal")

        await self.bot.say("I hob kan Kanal mit der id gfundn.")

    @checks.admin_or_permissions(Manage_server=True)
    @setsuggest.command(name="toggleactive", pass_context=True, no_pm=True)
    async def suggest_toggle(self, ctx):
        """Toggles whether the suggestion box is enabled or not"""
        server = ctx.message.server
        if server.id not in self.settings:
            self.initial_config(server.id)
        self.settings[server.id]['inactive'] = \
            not self.settings[server.id]['inactive']
        self.save_json()
        if self.settings[server.id]['inactive']:
            await self.bot.say("Vorschläge san jetzt ausgscholtn.")
        else:
            await self.bot.say("Vorschläge san jetzt eingscholtn.")

    @commands.command(name="suggest", pass_context=True)
    async def makesuggestion(self, ctx):
        "make a suggestion by following the prompts"
        author = ctx.message.author
        server = ctx.message.server

        if server.id not in self.settings:
            return await self.bot.say("I hob kane Einstellungen für Vorschläge auf dem Server.")
        if self.settings[server.id]['inactive']:
            return await self.bot.say("Im Moment kannst auf dem Server kane Vorschläge einreichen.")
        if author.id in self.settings[server.id]['usercache']:
            return await self.bot.say("Moch amal dein vorigen Vorschlag fertig.")
        message = ctx.message
        await self.send_suggest(message, server)


    async def send_suggest(self, message, server):
        author = message.author
        suggestion = message.clean_content.replace("!suggest ", "", 1)
        if(suggestion == "!suggest" or not suggestion):
            return await self.bot.say("A leerer vorschlag bringt kam wos")
        timestamp = message.timestamp.strftime('%Y-%m-%d %H:%M')
        avatar = author.avatar_url if author.avatar \
            else author.default_avatar_url

        em = discord.Embed(description=suggestion,
                           color=discord.Color.purple())
        em.set_author(name='Vorschlag von {}'.format(author.display_name),
                      icon_url=avatar)
        em.set_footer(text='Vorschlag eingreicht um {} UTC'.format(timestamp))

        for output in self.settings[server.id]['output']:
            where = server.get_channel(output)
            if where is not None:
                message = await self.bot.send_message(where, embed=em)
                await self.bot.add_reaction(message, u"\U0001F44D")
                await self.bot.add_reaction(message, u"\U0001F44E")
        self.save_json()


def check_folder():
    f = 'data/suggestionbox'
    if not os.path.exists(f):
        os.makedirs(f)


def check_file():
    f = 'data/suggestionbox/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = SuggestionBox(bot)
    bot.add_cog(n)

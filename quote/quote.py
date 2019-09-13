# Partly stolen from https://github.com/Painezor/Toonbot/blob/master/ext/quotes.py
import discord
import sqlite3
import asyncio
from redbot.core import commands
from datetime import datetime


class Quote(commands.Cog):
    """My quote"""
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('quotes.db')
        self.c = self.conn.cursor()

    def __unload(self):
        self.conn.close()

    def __reload(self):
        self.conn.close()
        self.conn = sqlite3.connect('quotes.db')
        self.c = self.conn.cursor()

    async def make_embed(self, data):
        # [id,author,content,channelid,timestamp,submitterid]
        author = discord.utils.get(self.bot.get_all_members(), id=data[1])
        channel = self.bot.get_channel(data[3])
        submitter = discord.utils.get(self.bot.get_all_members(), id=data[5])
        submittern = submitter.display_name if submitter else "deleted user"
        submitteravi = submitter.avatar_url if submitter else ""

        e = discord.Embed(color=0x7289DA, description=data[2])
        e.set_author(name=f"Quote #{data[0]}",
                     icon_url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")

        if author:
            e.set_thumbnail(url=author.avatar_url)
            e.title = f"{author.display_name} in #{channel}"
        else:
            e.set_thumbnail(url="https://discordapp.com/assets/2c21aeda16de354ba5334551a883b481.png")
            e.title = f"Deleted user in #{channel}"

        e.set_footer(text=f"Added by {submittern}", icon_url=submitteravi)
        e.timestamp = datetime.strptime(data[4], "%Y-%m-%d %H:%M:%S.%f")
        return e

    @commands.group(invoke_without_command=True, aliases=["quotes"])
    async def quote(self, ctx, *, member: discord.Member = None):
        """ Show random quote (optionally from specific user). Use ".help quote" to view subcommands. """
        if ctx.invoked_subcommand is None:
            if member:  # If member provided, show random quote from member.
                self.c.execute(f"SELECT rowid, * FROM quotes WHERE userid = {member.id} ORDER BY RANDOM()")
                x = self.c.fetchone()
                if not x:
                    return await ctx.send(f"No quotes found from user {member.mention}")
            else:  # Display a random quote.
                self.c.execute("SELECT rowid, * FROM quotes ORDER BY RANDOM()")
                x = self.c.fetchone()
                if not x:
                    return await ctx.send("Quote DB appears to be empty.")
                else:
                    await ctx.send("Displaying random quote:")
        e = await self.make_embed(x)
        await ctx.send(embed=e)

    @quote.command()
    async def search(self, ctx, *, qry):
        with ctx.typing():
            m = await ctx.send('Searching...')
            localconn = sqlite3.connect('quotes.db')
            lc = localconn.cursor()
            lc.execute(f"SELECT rowid, * FROM quotes WHERE quotetext LIKE (?)", (f'%{qry}%',))
            x = lc.fetchall()
            lc.close()
            localconn.close()

        numquotes = len(x)
        embeds = []
        for i in x:
            y = await self.make_embed(i)
            embeds.append(y)

        # Do we need to paginate?
        if numquotes == 0:
            return await m.edit(content=f'No quotes matching {qry} found.')

        if numquotes == 1:
            return await m.edit(content=f"{ctx.author.mention}: 1 quote found", embed=embeds[0])
        else:
            await m.edit(content=f"{ctx.author.mention}: {numquotes} quotes found", embed=embeds[0])
        # Paginate then.
        page = 0
        if numquotes > 2:
            await m.add_reaction("⏮")  # first
        if numquotes > 1:
            await m.add_reaction("◀")  # prev
        if numquotes > 1:
            await m.add_reaction("▶")  # next
        if numquotes > 2:
            await m.add_reaction("⏭")  # last

        def check(reaction, user):
            if reaction.message.id == m.id and user == ctx.author:
                e = str(reaction.emoji)
                return e.startswith(('⏮', '◀', '▶', '⏭'))

        # Reaction Logic Loop.
        while True:
            try:
                res = await self.bot.wait_for("reaction_add", check=check, timeout=30)
            except asyncio.TimeoutError:
                await m.clear_reactions()
                break
            res = res[0]
            if res.emoji == "⏮":  # first
                page = 1
                await m.remove_reaction("⏮", ctx.message.author)
            elif res.emoji == "◀":  # prev
                await m.remove_reaction("◀", ctx.message.author)
                if page > 1:
                    page = page - 1
            elif res.emoji == "▶":  # next
                await m.remove_reaction("▶", ctx.message.author)
                if page < numquotes:
                    page = page + 1
            elif res.emoji == "⏭":  # last
                page = numquotes
                await m.remove_reaction("⏭", ctx.message.author)
            await m.edit(embed=embeds[page - 1])

    @quote.command()
    @commands.is_owner()
    async def export(self, ctx):
        self.c.execute("SELECT rowid, * from quotes")
        x = self.c.fetchall()
        with open("out.txt", "wb") as fp:
            fp.write("\n".join([f"#{i[0]} @ {i[4]}: <{i[1]}> {i[2]} (Added by: {i[3]})" for i in x]).encode('utf8'))
        await ctx.send("Quotes exported. THIS IS NOT FOR BACKUP REASONS!", file=discord.File("out.txt", "quotes.txt"))

    @quote.command(aliases=["id", "fetch"])
    async def get(self, ctx, number):
        """ Get a quote by it's QuoteID number """
        if not number.isdigit():
            return
        self.c.execute(f"SELECT rowid, * FROM quotes WHERE rowid = {number}")
        x = self.c.fetchone()
        if x is None:
            return await ctx.send(f"Quote {number} does not exist.")
        e = await self.make_embed(x)
        await ctx.send(embed=e)

    @quote.command(invoke_without_command=True)
    async def add(self, ctx, target):
        """ Add a quote, either by message ID or grabs the last message a user sent """
        if ctx.message.mentions:
            messages = await ctx.history(limit=123).flatten()
            user = ctx.message.mentions[0]
            if ctx.message.author == user:
                return await ctx.send("You can't quote yourself.")
            m = discord.utils.get(messages, channel=ctx.channel, author=user)
        elif target.isdigit():
            try:
                m = await ctx.channel.fetch_message(int(target))
            except discord.errors.NotFound:
                return await ctx.send('Message not found. Are you sure that\'s a valid ID?')
        if not m:
            return await ctx.send(f":no_entry_sign: Could not find message with id {target}")

        return await self.add_to_db(m, ctx.author, ctx)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "💾" and reaction.count == 1:
            return await self.add_to_db(reaction.message, user, reaction.message.channel)

    async def add_to_db(self, message, adder, recv):
        m = message
        if m.author.id == adder.id:
            return await recv.send("You can't quote yourself you virgin.")
        n = await recv.send("Attempting to add quote to db...")
        insert_tuple = (m.author.id, m.clean_content, m.channel.id, m.created_at, adder.id)
        self.c.execute("INSERT INTO quotes VALUES (?,?,?,?,?)", insert_tuple)
        self.conn.commit()
        self.c.execute("SELECT rowid, * FROM quotes ORDER BY rowid DESC")
        x = self.c.fetchone()
        e = await self.make_embed(x)
        await n.edit(content=":white_check_mark: Successfully added to database", embed=e)

    @quote.command()
    async def last(self, ctx, arg: discord.Member = None):
        """ Gets the last saved message (optionally from user) """
        if not arg:
            self.c.execute("SELECT rowid, * FROM quotes ORDER BY rowid DESC")
            x = self.c.fetchone()
            if not x:
                await ctx.send("No quotes found.")
                return
        else:
            self.c.execute(f"SELECT rowid, * FROM quotes WHERE userid = {arg.id} ORDER BY rowid DESC")
            x = self.c.fetchone()
            if not x:
                await ctx.send(f"No quotes found for user {arg.mention}.")
                return
        e = await self.make_embed(x)
        await ctx.send(embed=e)

    @quote.command(name="del")
    @commands.has_permissions(manage_messages=True)
    async def _del(self, ctx, id):
        """ Delete quote by quote ID """
        if not id.isdigit():
            await ctx.send("That doesn't look like a valid ID")
        else:
            self.c.execute(f"SELECT rowid, * FROM quotes WHERE rowid = {id}")
            x = self.c.fetchone()
            if not x:
                return await ctx.send(f"No quote found with ID #{id}")
            e = await self.make_embed(x)
            m = await ctx.send("Delete this quote?", embed=e)
            await m.add_reaction("👍")
            await m.add_reaction("👎")

            def check(reaction, user):
                if reaction.message.id == m.id and user == ctx.author:
                    e = str(reaction.emoji)
                    return e.startswith(("👍", "👎"))
            try:
                res = await self.bot.wait_for("reaction_add", check=check, timeout=30)
            except asyncio.TimeoutError:
                return await ctx.send("Response timed out after 30 seconds, quote not deleted", delete_after=30)
            res = res[0]
            if res.emoji.startswith("👎"):
                await ctx.send("OK, quote not deleted", delete_after=20)
            elif res.emoji.startswith("👍"):
                self.c.execute(f"DELETE FROM quotes WHERE rowid = {id}")
                await ctx.send(f"Quote #{id} has been deleted.")
                await m.delete()
                await ctx.message.delete()
                self.conn.commit()

    @quote.command()
    async def stats(self, ctx, arg: discord.Member = None):
        """ See how many times you've been quoted, and how many quotes you've added"""
        if not arg:
            arg = ctx.author
        self.c.execute(f"SELECT COUNT(*) FROM quotes WHERE quoterid = {arg.id}")
        y = self.c.fetchone()[0]
        self.c.execute(f"SELECT COUNT(*) FROM quotes WHERE userid = {arg.id}")
        x = self.c.fetchone()[0]
        await ctx.send(f"{arg.mention} has been quoted {x} times, and has added {y} quotes")

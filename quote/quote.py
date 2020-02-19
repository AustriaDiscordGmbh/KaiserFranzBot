# this all started with a little fork from toonbot's quotes.py:
# https://github.com/Painezor/Toonbot/blob/master/ext/quotes.py
from .config import QUOTE_ARCHIVE_CHAN_ID, QUOTE_DB_FILE
from redbot.core import commands
from datetime import datetime
from pathlib import Path
import discord
import io
import json
import sqlite3
import re
# https://pypi.org/project/disputils/
import disputils
# https://pypi.org/project/aiohttp/
import aiohttp


class Quote(commands.Cog):
    """
    Allows you to quote whatever a user says and posts on discord.
    Supports attachments and embeds.
    Simple search and regex is included.
    Attachments are stored to the database and kept for archiving.
    """

    def __init__(self, bot):
        """
        Loads bot from config, inits database and sets regex function
        """
        self.bot = bot

        self.deleted_avatar_url = "https://emojipedia-us.s3.dualstack."
        self.deleted_avatar_url += "us-west-1."
        self.deleted_avatar_url += "amazonaws.com/thumbs/120/microsoft/209/"
        self.deleted_avatar_url += "skull_1f480.png"

        if not QUOTE_ARCHIVE_CHAN_ID and QUOTE_DB_FILE:
            raise ValueError("Please set values in config.py.")
        if not Path(QUOTE_DB_FILE).is_file():
            raise ValueError("Database file does not exist.")

        self.archive_chan_id = QUOTE_ARCHIVE_CHAN_ID
        self.db_file = QUOTE_DB_FILE
        self.conn = sqlite3.connect(self.db_file)
        self.conn.create_function('regexp', 2,
                                  lambda x, y: 1 if re.search(x, y)
                                  else 0)

    def cog_unload(self):
        """
        Closes database connection
        """
        self.conn.close()

    @commands.group(invoke_without_command=True, aliases=["quotes"])
    async def quote(self, ctx, *, member: discord.Member = None):
        """
        Show random quote (optionally from specific user)
        """
        if not ctx.invoked_subcommand:
            cur = self.conn.cursor()
            if member:
                sql = '''SELECT id FROM quotes WHERE author_id=? ORDER BY
                         RANDOM() LIMIT 1;'''
                cur.execute(sql, (member.id,))
            else:
                sql = '''SELECT id FROM quotes ORDER BY RANDOM() LIMIT 1;'''
                cur.execute(sql)
        ans = cur.fetchone()
        if not ans:
            return await ctx.send(":person_shrugging: No quote available.")
        return await self.get(ctx, str(ans[0]))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        1 disk emoji is storing the message
        5 wastebasked emoji is deleting the quote
        """
        # 1x floppy disk = add quote
        if reaction.emoji == "\U0001F4BE" and reaction.count == 1:
            return await self.add_quote(reaction.message, user)

        # 5x wastebasket = delete quote
        if reaction.emoji == "\U0001F5D1\U0000FE0F":
            if (reaction.count == 5 or
               user.permissions_in(reaction.message.channel).manage_messages):
                return await self.check_and_delete_quote(reaction.message)

    @quote.command()
    async def add(self, ctx, target):
        """
        Stores given target to database
        target can either be a msg id or a user mention
        user mention will quote the last thing said by him
        """
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            messages = await ctx.history(limit=123).flatten()
            msg = discord.utils.get(messages, channel=ctx.channel, author=user)
        elif target.isdigit():
            try:
                msg = await ctx.channel.fetch_message(int(target))
            except discord.errors.NotFound:
                return await ctx.send(":confused: Sure that's a valid id?")
        else:
            return await ctx.send(":confused: Can't work with this.")
        await self.add_quote(msg, ctx.author)

    @quote.command("get", aliases=["id", "fetch"])
    async def cmd_get(self, ctx, number):
        """
        Command to get quote by id and send it to channel
        """
        return await self.get(ctx, number)

    @quote.command()
    async def search(self, ctx, *, qry):
        """
        Shows messages matching given qry
        """
        qry = '%' + qry + '%'
        sql = '''SELECT id FROM quotes WHERE content LIKE (?)'''
        await self.search_general(ctx, sql, qry)

    @quote.command()
    async def regex(self, ctx, regex):
        """
        Search with regex
        """
        sql = '''SELECT id FROM quotes WHERE content REGEXP (?)'''
        await self.search_general(ctx, sql, regex)

    @quote.command()
    async def user(self, ctx, arg: discord.Member = None):
        """
        Get all quotes from oneself or given user
        """
        if not arg:
            arg = ctx.author
        sql = '''SELECT id FROM quotes WHERE author_id=?'''
        await self.search_general(ctx, sql, arg.id)

    @quote.command()
    async def adder(self, ctx, arg: discord.Member = None):
        """
        Get all quotes added from oneself or given user
        """
        if not arg:
            arg = ctx.author
        sql = '''SELECT id FROM quotes WHERE adder_id=?'''
        await self.search_general(ctx, sql, arg.id)

    @quote.command()
    @commands.is_owner()
    async def export(self, ctx):
        """
        Uploads database and sends it to owner.
        """
        await ctx.send(":card_box: Quote database, have fun.",
                       file=discord.File(self.db_file, "quote.db"))

    @quote.command()
    async def last(self, ctx, arg: discord.Member = None):
        """
        Show last added quote, optionally by given user
        """
        cur = self.conn.cursor()
        if arg:
            sql = '''SELECT id FROM quotes WHERE author_id=? ORDER BY id DESC
                  '''
            cur.execute(sql, (arg.id,))
        else:
            sql = '''SELECT id FROM quotes ORDER BY id DESC'''
            cur.execute(sql)
        last_id = cur.fetchone()
        cur.close()
        if not last_id:
            return await ctx.send(":person_shrugging: No quote available.")
        await self.get(ctx, str(last_id[0]))

    @quote.command("delete", aliases=["del"])
    @commands.has_permissions(manage_messages=True)
    async def cmd_delete(self, ctx, qid):
        """
        Asks and deletes given quote id
        """
        if not qid.isdigit():
            return await ctx.send(":rage: That's not a valid quote id")
        ask = disputils.BotConfirmation(ctx, 0x7289DA)

        await self.get(ctx, qid)
        if not self.get_msg_id_from_quote_id(qid):
            return
        await ask.confirm("Delete Quote #" + qid + "?")
        if ask.confirmed:
            self.delete_quote(qid)
            await ask.update("Quote #" + qid + " deleted.")
        else:
            await ask.update("Fair, nothing happend.")

    @quote.command(aliases=["stat"])
    async def stats(self, ctx, arg: discord.Member = None):
        """
        See stats about quotes for oneself or given user
        """
        if not arg:
            arg = ctx.author

        sql = '''SELECT COUNT (*) FROM quotes WHERE author_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (arg.id,))
        cnt_quoted = cur.fetchone()[0]
        cur.close()

        sql = '''SELECT COUNT (*) FROM quotes WHERE adder_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (arg.id,))
        cnt_added = cur.fetchone()[0]
        cur.close()

        ans = ":pencil: "
        ans += arg.mention + " has been quoted " + str(cnt_quoted) + " times, "
        ans += "and has added " + str(cnt_added) + " quotes."
        await ctx.send(ans)

    async def get(self, ctx, number):
        """
        Get quote by id and send it to channel
        """
        if not number.isdigit():
            return
        quote_id = int(number)

        info = self.load_msg(quote_id)
        if not info:
            return await ctx.send(":rage: Quote #" + number +
                                  " does not exist.")
        embeds = self.load_embeds(info["msg_id"])
        attachments = await self.load_attachments(info["msg_id"])

        e = self.make_embed(info, embeds, attachments)
        await ctx.send(embed=e)
        for embed in embeds:
            await ctx.send(embed=discord.Embed.from_dict(embed))

    async def store_attachments(self, msg):
        """
        Stores attachments to database + archives them on local disk
        returns: list of attachment tuples (filename, urls, is_image)
        """
        ret = []
        for att in msg.attachments:
            sql = '''INSERT INTO attachments
                     (msg_id, content, filename, url, is_image)
                     VALUES(?, ?, ?, ?, ?)'''
            cur = self.conn.cursor()
            is_image = 0
            if att.height:
                is_image = 1
            async with aiohttp.ClientSession() as cs:
                async with cs.get(att.url) as r:
                    cur.execute(sql, (msg.id, await r.read(),
                                      att.filename, att.url, is_image))
            self.conn.commit()
            cur.close()
            ret.append((att.filename, att.url, is_image))
        return ret

    async def load_attachments(self, msg_id):
        """
        Retrieves attachments stored for msg_id.
        Reuploads attachment to archive chan, in case unavailable
        returns: list of attachment tuples (filename, url, is_image)
        """
        sql = '''SELECT id, filename, url, is_image
                 FROM attachments WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))

        ret = []
        for entry in cur.fetchall():
            att_id = entry[0]
            filename = entry[1]
            url = entry[2]
            is_image = entry[3]
            # check if still available:
            async with aiohttp.ClientSession() as cs:
                async with cs.head(url) as r:
                    if r.status != 200:
                        url = await self.archive_attachment(att_id)
            ret.append((filename, url, is_image))
        cur.close()
        return ret

    async def archive_attachment(self, att_id):
        """
        Pushes the attachment content to the archive channel
        returns: new attachment url
        """
        sql = '''SELECT filename, content FROM attachments WHERE id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (att_id, ))
        ans = cur.fetchall()
        content = ans[0][1]
        filename = ans[0][0]
        archive = self.bot.get_channel(self.archive_chan_id)
        rehost = await archive.send(
                file=discord.File(io.BytesIO(content), filename))
        url = rehost.attachments[0].url
        cur.close()

        sql = '''UPDATE attachments SET url=? WHERE id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (url, att_id))
        self.conn.commit()
        cur.close()

        # if this is archived again, but missing anyway, delete entry
        sql = '''DELETE FROM archive_att WHERE att_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (att_id,))
        self.conn.commit()
        cur.close()

        sql = '''INSERT INTO archive_att(att_id, archive_msg_id)
                 VALUES(?, ?)'''
        cur = self.conn.cursor()
        cur.execute(sql, (att_id, rehost.id))
        self.conn.commit()
        cur.close()

        return url

    def delete_attachments(self, msg_id):
        """
        Deletes all attachment information for given msg_id
        also removes archives
        """
        sql = '''SELECT id FROM attachments WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))
        for entry in cur.fetchall():
            att_id = entry[0]
            sql = '''DELETE FROM archive_att WHERE att_id=?'''
            cur = self.conn.cursor()
            cur.execute(sql, (att_id,))
            self.conn.commit()
            cur.close()

        sql = '''DELETE FROM attachments WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))
        self.conn.commit()
        cur.close()

    def store_embeds(self, msg):
        """
        Stores given embeds to database
        returns: list of embed dicts
        """
        ret = []
        for embed in msg.embeds:
            d = dict(embed.to_dict())
            ret.append(d)
            sql = '''INSERT INTO embeds(msg_id, content)
                     VALUES(?, ?)'''
            cur = self.conn.cursor()
            cur.execute(sql, (msg.id, json.dumps(d)))
            self.conn.commit()
            cur.close()
        return ret

    def load_embeds(self, msg_id):
        """
        Retrieves embeds stored for msg_id.
        returns: list of embed dicts
        """
        sql = '''SELECT content FROM embeds WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))
        ret = []
        for entry in cur.fetchall():
            d = json.loads(entry[0])
            ret.append(d)
        cur.close()
        return ret

    def delete_embeds(self, msg_id):
        """
        Deletes stored embed information for given message id
        """
        sql = '''DELETE FROM embeds WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))
        self.conn.commit()
        cur.close()

    def store_msg(self, msg, adder):
        """
        Stores all data needed to build a quote from a msg added by adder
        returns: id of the quote
        """
        ans = self.get_quote_id_from_msg_id(msg.id)
        if ans:
            # already quoted, just give them the info
            return ans
        sql = '''INSERT INTO quotes(msg_id, chan_id, author_id, author_name,
                 adder_id, jump_url, timestamp, content)
                 VALUES(?, ?, ?, ?, ?, ?, ?, ?)'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg.id, msg.channel.id, msg.author.id,
                          msg.author.display_name, adder.id, msg.jump_url,
                          msg.created_at, msg.clean_content))
        self.conn.commit()
        cur.close()
        return self.get_quote_id_from_msg_id(msg.id)

    def load_msg(self, quote_id):
        """
        Loads message from database with the given quote_id
        returns: dict with all msg information.
        """
        sql = '''SELECT * FROM quotes WHERE id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (quote_id,))
        ans = cur.fetchone()
        ret = {}
        if not ans:
            return ret
        ret["quote_id"] = ans[0]
        ret["msg_id"] = ans[1]
        ret["chan_id"] = ans[2]
        ret["author_id"] = ans[3]
        ret["author_name"] = ans[4]
        ret["adder_id"] = ans[5]
        ret["jump_url"] = ans[6]
        ret["timestamp"] = ans[7]
        ret["content"] = ans[8]
        return ret

    def delete_msg(self, msg_id):
        """
        Deletes message from database with the given msg_id
        """
        sql = '''DELETE FROM quotes WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))
        self.conn.commit()
        cur.close()

    def get_quote_id_from_msg_id(self, msg_id):
        """
        Retrieve quote id for given msg id
        returns quote id or None
        """
        sql = '''SELECT id FROM quotes WHERE msg_id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (msg_id,))
        ans = cur.fetchone()
        return ans[0] if ans else None

    def get_msg_id_from_quote_id(self, quote_id):
        """
        Retrievie msg id for given quote id
        returns message id or None
        """
        sql = '''SELECT msg_id FROM quotes WHERE id=?'''
        cur = self.conn.cursor()
        cur.execute(sql, (quote_id,))
        ans = cur.fetchone()
        return ans[0] if ans else None

    def make_embed(self, info, embeds=[], attachments=[]):
        """
        create embed form msg info
        returns discord embed representing the quote
        """
        author = self.bot.get_user(info["author_id"])
        channel = self.bot.get_channel(info["chan_id"])
        submitter = self.bot.get_user(info["adder_id"])

        e = discord.Embed(color=0x7289DA, description="")
        if not author:
            current_name = "Deleted user"
            avatar_url = self.deleted_avatar_url
        else:
            current_name = discord.utils.get(self.bot.get_all_members(),
                                             id=author.id).display_name
            avatar_url = author.avatar_url

        if current_name == info["author_name"]:
            author_info = current_name
        else:
            author_info = current_name + ", said as "
            author_info += info["author_name"] + ","

        if not channel:
            channel = "unknown-channel"
        e.set_author(
            name=author_info + " in #" + str(channel),
            icon_url=avatar_url)

        e.description += "**__[Quote #"
        e.description += str(info["quote_id"]) + "]("
        e.description += info['jump_url'] + ")__**\n"

        if attachments:
            att_set = False
            img_set = False
            for entry in attachments:
                filename = entry[0]
                url = entry[1]
                is_image = entry[2]
                if (not img_set) and is_image:
                    img_set = True
                    e.set_image(url=url)
                else:
                    if not att_set:
                        e.add_field(name="Message had other attachment(s):",
                                    value="_ _", inline=False)
                        att_set = True
                    e.add_field(name=filename + ": " + url, value="_ _",
                                inline=False)
        if embeds:
            e.add_field(name="Message had embed(s), see below.", value="_ _")

        e.description += info["content"]
        footer = "Added by "
        if submitter:
            footer += discord.utils.get(self.bot.get_all_members(),
                                        id=submitter.id).display_name
            sub_avatar_url = submitter.avatar_url
        else:
            footer += "deleted user"
            sub_avatar_url = self.deleted_avatar_url
        e.set_footer(text=footer,
                     icon_url=sub_avatar_url)

        e.timestamp = datetime.strptime(info["timestamp"],
                                        "%Y-%m-%d %H:%M:%S.%f")
        return e

    async def add_quote(self, msg, adder):
        """
        Acutally stores quote
        """
        ctx = msg.channel
        if msg.author.id == adder.id:
            return await ctx.send(":shushing_face: Can't quote yourself!")
        if self.get_quote_id_from_msg_id(msg.id):
            return

        ans = await ctx.send(":file_cabinet: Attempting to add quote to db...")
        self.store_embeds(msg)
        await self.store_attachments(msg)
        quote_id = self.store_msg(msg, adder)

        await self.get(ctx, str(quote_id))
        await ans.edit(content=(
            ":white_check_mark: Quote added successfully."))

    def delete_quote(self, quote_id):
        """
        Actually deletes quote and all the stored data related to it.
        """
        msg_id = self.get_msg_id_from_quote_id(quote_id)
        self.delete_attachments(msg_id)
        self.delete_embeds(msg_id)
        self.delete_msg(msg_id)

    async def check_and_delete_quote(self, msg):
        """
        Verifies the to be deleted msg is a quote triggers delete after
        """
        ctx = msg.channel
        if not len(msg.embeds) == 1:
            return
        try:
            qid = int(msg.embeds[0].description.split('#')[1].split(']')[0])
        except ValueError:
            return await ctx.send(":confused: Something went wrong, eh?")
        self.delete_quote(qid)
        await msg.edit(content=(":wastebasket: Quote deleted successfully."))

    async def search_general(self, ctx, sql, arg):
        """
        executes given sql with 1 given arg
        creates pages for resulting quote ids
        """
        cur = self.conn.cursor()
        try:
            cur.execute(sql, (arg,))
        except sqlite3.OperationalError:
            cur.close()
            return await ctx.send(":thinking: Nothing found.")

        quotes = []
        for entry in cur.fetchall():
            quote_id = entry[0]
            info = self.load_msg(quote_id)
            embeds = self.load_embeds(info["msg_id"])
            attachments = await self.load_attachments(info["msg_id"])
            quotes.append(self.make_embed(info, embeds, attachments))
        cur.close()

        if not quotes:
            return await ctx.send(":thinking: Nothing found.")
        pag = disputils.BotEmbedPaginator(ctx, quotes)
        await pag.run()

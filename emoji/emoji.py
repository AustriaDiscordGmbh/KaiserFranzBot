import discord
import re
import emoji
import os
import sqlite3
import traceback
import logging
from discord.ext import commands
from functools import reduce

DATA = "data/emoji/"
DATABASE = DATA + "emoji.db"

log = logging.getLogger("red.emoji")

def extract_emojis(txt, emoji_list):
    """
    Extract all the emoji from a string, returning a tuple of strings
    emoji_list: custom per-server emojis (discord.Server.emojis)
    """
    # extract normal unicode emoji
    emojis = list(c for c in txt if c in emoji.UNICODE_EMOJI)

    # extract IDs of custom emoji
    emojis += list(re.findall("<:[a-zA-Z]+:[0-9]+>", txt))

    return tuple(emojis)

class Emoji:
    """Logs emoji usage and gives nice statistics"""

    def __init__(self, bot):
        self.bot = bot

        if not os.path.exists(DATA):
            os.makedirs(DATA)

        self.db = sqlite3.connect(DATABASE)

        if self.db is not None:
            self.dbc = self.db.cursor()
            self.dbc.execute(
                """CREATE TABLE IF NOT EXISTS messages (
                    row_id integer PRIMARY KEY AUTOINCREMENT,
                    server_id text NOT NULL,
                    channel_id text NOT NULL,
                    user_id text NOT NULL,
                    message_id text NOT NULL,
                    date text NOT NULL,
                    emoji text NOT NULL
                );"""
            )
        else:
            raise Exception("Couldn't connect to database")

    async def on_message(self, message):
        """Grab all messages that contain emojis and log them"""

        if (not message.server):
            return

        emoji_names = extract_emojis(message.content, message.server.emojis)

        if emoji_names:
            try:
                # create query for each emoji
                queries = list(map(
                        lambda e: (
                            message.server.id,
                            message.channel.id,
                            message.author.id,
                            message.id,
                            message.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
                            e
                        ),
                        emoji_names
                    ))

                self.dbc.executemany("INSERT INTO messages (server_id, channel_id, user_id, message_id, date, emoji) VALUES (?,?,?,?,?,?)", queries)
                self.db.commit()
            except Exception:
                log.error(traceback.format_exc())

    @commands.command(pass_context=True)
    async def emoji(self, ctx):
        """List rankings for emojis/users/channels
        Supply zero or one of each (user, channel, emoji)"""

        # query format
        # example: 3 emoji are given
        #   SELECT
        #       user_id,
        #       COUNT(user_id)
        #   FROM messages WHERE
        #       server_id = ?
        #       AND emoji IN (?, ?, ?)
        #   GROUP BY user_id
        #   ODER BY COUNT(user_id)
        #   LIMIT 3
        # same query will be repeated with channel_id instead of user_id

        pretty_columns = {
            "channel_id": "channels",
            "user_id": "users",
            "emoji": "emojis"
        }

        # dict of lists at first, then reduced to dict of string/None
        criteria = {}
        criteria["user_id"] = ctx.message.mentions
        criteria["channel_id"] = ctx.message.channel_mentions
        for role in ctx.message.role_mentions:
            criteria["user_id"] += filter(
                lambda y: role in y.roles and y not in criteria["user_id"],
                ctx.message.server.members
            )

        criteria["emoji"] = extract_emojis(ctx.message.content, ctx.message.server.emojis)

        # remove channel and user mentions
        rest = re.sub("<[@#][0-9]+>", " ", ctx.message.content[7:])
        # remove emojis
        rest = reduce(lambda s, e: s.replace(e, " "), criteria["emoji"], rest)

        debug = "debug" in rest

        # input validation
        for c, x in criteria.items():
            if len(x) == 0:
                criteria[c] = None

        # build WHERE clauses for each given criterium,
        # prepare embed header
        query_select_cols = "SELECT {}, COUNT({})"
        query = " FROM messages WHERE server_id = ?"
        query_data = [ctx.message.server.id]

        em_header_target = ""
        for c, v in criteria.items():
            if v:
                if c in ("user_id", "channel_id"):
                    query_data += map(lambda x: x.id, v)
                elif c == "emoji":
                    query_data += v

                query += " AND %s IN (%s)" % (c, ",".join(list("?" * len(v))))

        em = discord.Embed()
        if debug:
            em.description = str(criteria)

        # query database, populate embed
        for c, x in criteria.items():
            if not x:
                tmp_query = query_select_cols.format(c, c) + query + " GROUP BY %s ORDER BY COUNT(%s) DESC LIMIT 3" % (c, c)
                log.debug("query:")
                log.debug(tmp_query)
                log.debug(query_data)

                results = self.dbc.execute(tmp_query, query_data).fetchall()
                log.debug("result:")
                log.debug(results)

                if not results:
                    return await self.bot.say("No data available.")

                em_values = ""
                for i, row in enumerate(results):
                    server = ctx.message.server
                    result_id = row[0]
                    if c == "user_id":
                        result_id = discord.utils.find(lambda v: v.id == result_id, server.members).mention
                    elif c == "channel_id":
                        result_id = discord.utils.find(lambda v: v.id == result_id, server.channels).mention

                    em_values += "%d. %s (%dx)\n" % (i+1, result_id, row[1])

                em.add_field(name="Top " + pretty_columns[c] + em_header_target, value=em_values, inline=False)

        if not em.fields:
            # doesn't matter what we SELECT, we're counting everything
            results = self.dbc.execute(query_select_cols.format("emoji", "emoji") + query, query_data).fetchone()
            em.add_field(name="Amount", value=results[1])

        await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(Emoji(bot))

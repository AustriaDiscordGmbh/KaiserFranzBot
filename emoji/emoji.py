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
    emoji_list: custom per-server emojis (Server.emojis)
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
                print(traceback.format_exc())

    @commands.command(pass_context=True)
    async def emoji(self, ctx):
        """list rankings for emojis/users/channels. Supply zero or one of each mentions, channels, and/or emojis"""

        pretty_columns = {
            "channel_id": "channels",
            "user_id": "users",
            "emoji": "emojis"
        }

        criteria = {}
        criteria["user_id"] = ctx.message.mentions
        criteria["channel_id"] = ctx.message.channel_mentions
        criteria["emoji"] = extract_emojis(ctx.message.content, ctx.message.server.emojis)

        # input validation
        for c, x in criteria.items():
            l = len(x)
            if l > 1:
                return await self.bot.say("Error: %s specified more than once" % pretty_columns[c])
            if l == 1:
                criteria[c] = x[0]
            elif l == 0:
                criteria[c] = None

        # build WHERE clauses for each given criterium,
        # prepare embed header
        query_select_cols = "SELECT {}, COUNT({})"
        query = " FROM messages WHERE server_id = ?"
        query_data = [ctx.message.server.id]

        em_header_target = ""
        for c, x in criteria.items():
            if x:
                if c == "user_id":
                    em_header_target += " for @%s" % x.name
                    query_data.append(x.id)
                elif c == "channel_id":
                    em_header_target += " in #%s" % x.name
                    query_data.append(x.id)
                elif c == "emoji":
                    em_header_target += " with %s" % x
                    query_data.append(x)

                query += " AND %s = ?" % c

        em = discord.Embed()

        # query database, populate embed
        for c, x in criteria.items():
            if not x:
                tmp_query = query_select_cols.format(c, c) + query + " GROUP BY %s ORDER BY COUNT(%s) DESC" % (c, c)
                log.debug("query:")
                log.debug(tmp_query)
                log.debug(query_data)

                results = self.dbc.execute(tmp_query, query_data).fetchall()
                log.debug("result:")
                log.debug(results)

                em_values = ""
                for i in range(0,3):
                    if len(results) > i:
                        server = ctx.message.server
                        result_id = results[i][0]
                        if c == "user_id":
                            result_id = discord.utils.find(lambda v: v.id == result_id, server.members).mention
                        elif c == "channel_id":
                            result_id = discord.utils.find(lambda v: v.id == result_id, server.channels).mention

                        em_values += "%d. %s (%dx)\n" % (i+1, result_id, results[i][1])

                em.add_field(name="Top " + pretty_columns[c] + em_header_target, value=em_values, inline=False)

        if not em.fields:
            tmp_query = query_select_cols.format("emoji", "emoji") + query
            results = self.dbc.execute(tmp_query, query_data).fetchone()
            em.add_field(name="Amount", value=results[1])

        await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(Emoji(bot))

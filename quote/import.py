#!/usr/bin/env python3
# import version 2 quote db to version 3 - as if we would track version numbers
import sys
import sqlite3


def main(old_db_file, new_db_file):
    print("Loading from " + old_db_file + " to " + new_db_file + ".")
    old_jump_url = "https://canary.discordapp.com/channels/"
    old_jump_url += "297910194841583616/297910194841583616/678519154503974912"
    old_author_name = "old quote"

    old_conn = sqlite3.connect(old_db_file)
    old_cur = old_conn.cursor()
    new_conn = sqlite3.connect(new_db_file)

    sql = '''SELECT rowid, * FROM quotes ORDER BY rowid ASC'''
    old_cur.execute(sql)

    # this is ugly as fuck, but legacy code is supposed to be like that
    old_msg_id = 100000
    for entry in old_cur.fetchall():
        author_id = entry[1]
        content = entry[2]
        chan_id = entry[3]
        timestamp = entry[4]
        adder_id = entry[5]
        sql = '''INSERT INTO quotes(msg_id, chan_id, author_id, author_name,
                 adder_id, jump_url, timestamp, content)
                 VALUES(?, ?, ?, ?, ?, ?, ?, ?)'''
        new_cur = new_conn.cursor()
        new_cur.execute(sql, (old_msg_id, chan_id, author_id, old_author_name,
                              adder_id, old_jump_url, timestamp, content))
        new_conn.commit()
        new_cur.close()
        old_msg_id += 1
    old_cur.close()
    new_conn.close()
    old_conn.close()
    print("Loading done.")


if __name__ == "__main__":
    if not len(sys.argv) == 3:
        print(sys.argv[0] + " <old_db> <new_db>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

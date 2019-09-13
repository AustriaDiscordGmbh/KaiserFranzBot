#!/usr/bin/env python3
# EMERGENCY SOLUTION FOR IMPORTING EXPORT TXT DO NOT FUCKING USE IT FOR BACKUPS
import sqlite3
import sys
import parse


print("loading from: " + sys.argv[1])
print("EMERGENCY SOLUTION FOR IMPORTING EXPORT TXT DO NOT FUCKING USE IT FOR BACKUPS")

with open(sys.argv[1]) as f:
    content = f.read()

quotes = []
for e in content.split("#")[1:]:
    if not e.split()[0].isdigit():
        print("Problem with:")
        print(e)
        sys.exit()
    quotes.append(e)

conn = sqlite3.connect('importquotes.db')
c = conn.cursor()
# quote layout: <id> @ <timestamp>: <FROM_USER> <TEXT> (Added by: <ADD_USER>)
# db layout: #{i[0]} @ {i[4]}: <{i[1]}> {i[2]} (Added by: {i[3]})
for q in quotes:
    r = parse.parse("{qid} @ {ts}: <{fuid}> {text} (Added by: {quid})", q)
    if not r:
        print(q)
        sys.exit()
    insert_tuple = (r['qid'], r['fuid'], r['text'], r['quid'], r['ts'])
    c.execute("INSERT INTO quotes VALUES (?,?,?,?,?)", insert_tuple)
    conn.commit()

conn.close()
print("Import done")

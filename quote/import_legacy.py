import json
import sqlite3

conn = sqlite3.connect('importquotes.db')
c = conn.cursor()

old_quotes = json.load(open('old_quotes.json'))

quote_list = []

for l1 in old_quotes:
    for l2 in old_quotes[l1]:
        quote_list += [old_quotes[l1][l2]]

for q in quote_list:
    if q["content"]:
        q["time"] += ':00.0'
        insert_tuple = (int(q['aid']), q['content'], 297910194841583616, q['time'], 505003247803826177)
        c.execute("INSERT INTO quotes VALUES (?,?,?,?,?)", insert_tuple)
        conn.commit()

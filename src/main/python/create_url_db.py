#!/usr/bin/env python
# pip install psycopg2

import sys
import psycopg2
import psycopg2.extensions

conn = psycopg2.connect(host = sys.argv[1], user = sys.argv[2], password = sys.argv[3], database = sys.argv[4])
conn.set_client_encoding('UTF-8')
cur = conn.cursor()

cur.execute("select * from information_schema.tables where table_schema = 'public' and table_name=%s", ('urls',))
if cur.rowcount == 0:
    cur.execute("""
        CREATE TABLE urls (
            url TEXT PRIMARY KEY,
            started TIMESTAMP,
            completed TIMESTAMP,
            final_url TEXT,
            status_code INTEGER,
            status_message TEXT,
            error TEXT,
            archive TEXT,
            file TEXT
        );
    """)
    cur.execute("""
        CREATE INDEX urls_started_idx on urls(started);
        CREATE INDEX urls_url_idx on urls(url);
    """)
    conn.commit()

existing = set()
cur.arraysize = 500
cur.execute("SELECT url FROM urls;")

while True:
    rows = cur.fetchmany(500)
    if not rows:
        break
    for row in rows:
        existing.add(row[0])

print("Discovered %s existing urls" % len(existing))

added = 0
for line in open('../../../urls.txt'):
    url = line.strip()
    if url not in existing:
        added += 1
        cur.execute("INSERT into urls VALUES(%s)", (url,))
        if added % 1000 == 0:
            print('adding url %d' % added)
            conn.commit()

conn.commit()

print("Added %d new urls " % added)

conn.set_isolation_level(0)
cur.execute('vacuum analyze;')


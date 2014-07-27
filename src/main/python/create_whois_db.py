#!/usr/bin/env python
# pip install psycopg2

import sys
import psycopg2
import psycopg2.extensions

conn = psycopg2.connect(host = sys.argv[1], user = sys.argv[2], password = sys.argv[3], database = sys.argv[4])
conn.set_client_encoding('UTF-8')
cur = conn.cursor()

cur.execute("select * from information_schema.tables where table_schema = 'public' and table_name=%s", ('domains',))
if cur.rowcount == 0:
    cur.execute("""
        CREATE TABLE domains (
            domain text PRIMARY KEY,
            started TIMESTAMP,
            completed TIMESTAMP,
            status VARCHAR,
            server TEXT,
            error TEXT,
            message TEXT
        );
    """)
    cur.execute("""
        CREATE INDEX domains_started_idx on domains(started);
        CREATE INDEX domains_domain_idx on domains(domain);
    """)
    conn.commit()

existing = set()
cur.arraysize = 500
cur.execute("SELECT domain FROM domains;")

while True:
    rows = cur.fetchmany(500)
    if not rows:
        break
    for row in rows:
        existing.add(row[0])

print("Discovered %s existing domains" % len(existing))

added = 0
for line in open('../../../domains.txt'):
    domain = line.strip()
    if domain not in existing:
        added += 1
        cur.execute("INSERT into domains VALUES(%s)", (domain,))
        if added % 1000 == 0:
            print('adding domain %d' % added)
            conn.commit()

conn.commit()

print("Added %d new domains " % added)

conn.set_isolation_level(0)
cur.execute('vacuum analyze;')


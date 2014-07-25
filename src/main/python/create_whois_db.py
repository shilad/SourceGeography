#!/usr/bin/env python
# pip install psycopg2

import sys
import psycopg2

conn = psycopg2.connect(database = sys.argv[1], user = sys.argv[2], host = sys.argv[3])
cur = conn.cursor()

cur.execute("select * from information_schema.tables where table_name=%s", ('domains',))
if cur.rowcount == 0:
    cur.execute("""
        CREATE TABLE domains (
            domain text PRIMARY KEY,
            started TIMESTAMP,
            completed TIMESTAMP,
            status VARCHAR,
            error TEXT,
            message TEXT
        );
    """)
    cur.execute("""
        CREATE INDEX domains_started_idx on domains(started);
        CREATE INDEX domains_domain_idx on domains(domain);
        VACUUM ANALYZE;
    """)
    conn.commit()

added = 0
for line in open('../../../domains.txt'):
    domain = line.strip()
    cur.execute("SELECT domain FROM domains where domain = %s", (domain,))
    if cur.rowcount == 0:
        added += 1
        cur.execute("INSERT into domains VALUES(%s)", (domain,))
        if added % 1000 == 0:
            print('adding domain %d' % added)

conn.commit()

print("Added %d new domains " % added)


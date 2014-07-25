#!/usr/bin/env python

import sys
import psycopg2
import time
import traceback
import pythonwhois

SLEEP_TIME = 1



conn = psycopg2.connect(database = sys.argv[1], user = sys.argv[2], host = sys.argv[3])
cur = conn.cursor()

for i in range(1000):
    cur.execute("""
        BEGIN ISOLATION LEVEL SERIALIZABLE;
        UPDATE domains
        SET    started = 'now()'
        WHERE  domain = (SELECT domain FROM domains WHERE started IS NULL LIMIT 1)
        RETURNING domain
    """)
    conn.commit()
    domain = cur.fetchone()[0]
    print('processing %s' % domain)
    try:
        result = pythonwhois.net.get_whois_raw(domain)
        cur.execute("""
            UPDATE domains
            SET completed = 'now()', status = 'C', message = %s
            WHERE domain = %s
        """, (result, domain))
    except:
        traceback.print_exc()
        cur.execute("""
            UPDATE domains
            SET completed = 'now()', status = 'E', error = %s
            WHERE domain = %s
        """, (traceback.format_exc(), domain))

    conn.commit()

    time.sleep(SLEEP_TIME)
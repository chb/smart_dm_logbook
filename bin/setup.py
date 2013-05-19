#!/usr/bin/env python
#
# create the sqlite3 database and tables
import os
import sys
base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/..')

import settings
import sqlite3

conn = sqlite3.connect('./data/'+settings.REQ_DB_FILENAME)
c = conn.cursor()
c.execute('drop table requests')
c.execute('''create table requests (
    date text,
    external_id text,
    smart_record_id text,
    friendly_name text,
    person_id text,
    hv_record_id text
)''')

conn.commit()
conn.close()

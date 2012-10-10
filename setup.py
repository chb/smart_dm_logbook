# create the sqlite3 database and tables

import settings
import sqlite3

conn = sqlite3.connect('./data/'+settings.REQ_DB_FILENAME)
c = conn.cursor()
c.execute('''create table requests
                (external_id text,
                 smart_record_id text,
                 friendly_name text,
                 person_id text,
                 hv_record_id text)''')

conn.commit()
conn.close()

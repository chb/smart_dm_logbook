#!/usr/bin/env python
#
# Arjun Sanyal (arjun.sanyal@childrens.harvard.edu)
#
# A utility script to poll the Microsoft HealtVault API for
# authorized connection requests. See
# http://msdn.microsoft.com/en-us/library/jj551258.aspx for details.
#
# The script finds the returned "external_id" i.e. the random request_id
# sent with the auth request and updates that row with the person and record
# ids.
#
# NOTE: must be called from the top-level directory!

import os
import sys
base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/../healthvault/healthvault')
sys.path.append(base+'/..')

import healthvault
import settings
import sqlite3

DEBUG = True

if __name__ == "__main__":
    print "\n# Getting Authed requests from HealtVault:"
    hv_conn = healthvault.HVConn()
    reqs = hv_conn.getAuthorizedConnectRequests()
    for req in reqs:
        person_id = req[0]
        hv_record_id = req[1]
        external_id = req[2]  # the random request_id we provided

        if DEBUG:
            print 'person_id: ' + person_id
            print 'hv_record_id: ' + hv_record_id
            print 'external_id: ' + external_id + '\n'

        # update the db with the person and record ids
        conn = sqlite3.connect(
            settings.REQ_DB_DIR + '/' + settings.REQ_DB_FILENAME
        )
        c = conn.cursor()
        s = 'update requests set person_id = ?, hv_record_id = ? where external_id = ?'
        c.execute(s, (person_id, hv_record_id, external_id))
        conn.commit()

    # show the smart id to hv id mappings
    s = ('select smart_record_id, hv_record_id, person_id from requests')
    res = c.execute(s)
    rows = res.fetchall()
    print '\n# Stored Mappings (smart_record_id = hv_record_id + person_id):'
    for row in rows:
        print row[0] + ' = ' + row[1] + ' + ' + row[2]

    print '\n'
    conn.close()

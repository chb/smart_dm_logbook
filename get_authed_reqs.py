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

import os
import sys
base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/healthvault/healthvault')
import healthvault

DEBUG = True

if __name__ == "__main__":
    hv_conn = healthvault.HVConn()
    reqs = hv_conn.getAuthorizedConnectRequests()
    for req in reqs:
        person_id = req[0]
        record_id = req[1]
        external_id = req[2]  # the random request_id we provided

        if DEBUG:
            print '>>> person_id: ' + person_id
            print '>>> record_id: ' + record_id
            print '>>> external_id: ' + external_id

        # update the db with the person and record ids

    print """\nDone.."""

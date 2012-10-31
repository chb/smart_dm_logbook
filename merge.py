"""
SMART HealthVault Merge App

Arjun Sanyal <arjun.sanyal@childrens.harvard.edu>

"""

import os
import sys
base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/healthvault/healthvault')

import datetime
import healthvault
import json
import pdb
import random
import settings
from smart_client import oauth
from smart_client.smart import SmartClient
import sqlite3
import urllib
import web

DEBUG_EMAIL = 'arjun@arjun.nu'

SMART_SERVER_OAUTH = {
    'consumer_key': None,  # will fill this in later
    'consumer_secret': 'smartapp-secret'
}

SMART_SERVER_PARAMS = {
    'api_base': None  # will fill this in later
}

# fixme: maybe use one class??
urls = (
    '/smartapp/index.html', 'Merge',
    '/getGlucoseMeasurements', 'GetGlucoseMeasurements',
    '/getA1cs', 'GetA1cs',
)

def _get_smart_client(smart_oauth_header):
    """Convenience function to initialize a new SmartClient"""
    try:
        smart_oauth_header = urllib.unquote(smart_oauth_header)
    except:
        return "Couldn't find a parameter to match the name 'oauth_header'"

    oa_params = oauth.parse_header(smart_oauth_header)

    # This is how we know...
    # 1. what container we're talking to
    try:
        SMART_SERVER_PARAMS['api_base'] = oa_params['smart_container_api_base']
    except:
        return "Couldn't find 'smart_contianer_api_base' in %s" % smart_oauth_header

    # 2. what our app ID is
    try:
        SMART_SERVER_OAUTH['consumer_key'] = oa_params['smart_app_id']
    except:
        return "Couldn't find 'smart_app_id' in %s" % smart_oauth_header

    # (For demo purposes, we're assuming a hard-coded consumer secret, but
    #  in real life we'd look this up in some config or DB now...)
    resource_tokens = {
        'oauth_token': oa_params['smart_oauth_token'],
        'oauth_token_secret': oa_params['smart_oauth_token_secret']
    }

    ret = SmartClient(
        SMART_SERVER_OAUTH['consumer_key'],
        SMART_SERVER_PARAMS,
        SMART_SERVER_OAUTH,
        resource_tokens
    )

    ret.record_id = oa_params['smart_record_id']
    return ret

class Merge:

    def _get_hv_ids(self, smart_record_id):
        conn = sqlite3.connect(settings.REQ_DB_DIR + '/' + settings.REQ_DB_FILENAME)
        c = conn.cursor()
        s = 'select person_id, hv_record_id from requests where smart_record_id = ? limit 1'
        res = c.execute(s, (smart_record_id, ))
        row = res.fetchone()
        conn.commit()
        conn.close()
        if row:
            return {'person_id': row[0], 'record_id': row[1]}
        else:
            return None

    def _create_connection_request(self, smart_record_id):
        # TODO: should we use a combination of smart container
        # id and record_id here? what to use for container id?
        # Use a random external_id for now
        external_id = random.randint(1,9999999999)
        # TODO: get these
        friendly_name = 'Connection Request #' + str(external_id)
        secret_q = 'Your favorite color?'
        secret_a = 'gray'  # spaces retained but case insensitive, single word best

        hv_conn = healthvault.HVConn()
        hv_id_code = hv_conn.createConnectRequest(
            external_id,
            friendly_name,
            secret_q,
            secret_a
        )

        if hv_id_code:
            conn = sqlite3.connect( settings.REQ_DB_DIR + '/' + settings.REQ_DB_FILENAME)
            c = conn.cursor()
            s = 'insert into requests values (?, ?, ?, ?, ?, ?)'
            now = datetime.datetime.now().isoformat()
            c.execute(s, (now, external_id, smart_record_id, friendly_name, '', ''))
            conn.commit()
            conn.close()

        return hv_id_code

    def _get_hv_req_url(self, hv_id_code):
        # just display code don't send email, could also print out
        # url = 'https://shellhostname/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKYZ-QNMN-VHRX-ZGNR-GZNH'
        return settings.HV_SHELL_URL + \
            "/redirect.aspx?target=CONNECT&targetqs=packageid%3d" + \
            hv_id_code

    def _send_hv_req_email(self):
        pass

    def GET(self):
        client = _get_smart_client(web.input().oauth_header)
        header = """
        <!DOCTYPE html>
        <html>
        <head>
            <script
                src="http://sample-apps.smartplatforms.org/framework/smart/scripts/smart-api-client.js"></script>
        </head>
        <body>
        """
        footer = """</body></html>"""

        hv_ids = self._get_hv_ids(client.record_id)
        if hv_ids:
            # show something
            hv_conn = healthvault.HVConn(offline_person_id=hv_ids['person_id'])
            main = web.template.frender('static/app/main.html')
            # fixme: rename! using it for person_id
            wctoken = hv_ids['person_id']
            name = hv_conn.person.name
            oauth_header = web.input().oauth_header
            return main(wctoken, name, oauth_header)
        else:
            hv_id_code = self._create_connection_request(client.record_id)
            url = self._get_hv_req_url(hv_id_code)
            # https://account.healthvault-ppe.com/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKKR-XKMX-TRTZ-XPGH-CNZQ
            # ? or https://account.healthvault-ppe.com/patientconnect.aspx?action=GetQuestion
            return header + '<p>Your id code is: ' +hv_id_code \
                + '</p><p>Click <a target="_blank" href="' + url + \
                '">here</a> to authorize this app to connect to your HealthVault account</p>' \
                + footer

class GetGlucoseMeasurements:
    def GET(self):
        person_id = web.input().wctoken
        hvconn = healthvault.HVConn(offline_person_id=person_id)
        hvconn.getGlucoseMeasurements()
        res = hvconn.person.glucoses
        web.header('Content-Type', 'application/json')
        return json.dumps(res)

class GetA1cs:
    def GET(self):
        client = _get_smart_client(web.input().oauth_header)
        #labs = client.get_lab_results()
        #pdb.set_trace()
        # mock
        res = [["2012-09-30T10:00:00", 6]]
        web.header('Content-Type', 'application/json')
        return json.dumps(res)

# start up web.py
app = web.application(urls, globals())
web.config.debug = True
if __name__ == "__main__":
    app.run()
else:
    application = app.wsgifunc()

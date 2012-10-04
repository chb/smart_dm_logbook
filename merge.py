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
import pdb
import random
import settings
from smart_client import oauth
from smart_client.smart import SmartClient
import urllib
import web

DEBUG_EMAIL = 'arjun@arjun.nu'

# configuration
SMART_SERVER_OAUTH = {
    'consumer_key': None,  # will fill this in later
    'consumer_secret': 'smartapp-secret'
}

SMART_SERVER_PARAMS = {
    'api_base': None  # will fill this in later
}
urls = ('/smartapp/index.html', 'Merge')

# the main responder class
class Merge:
    def _get_smart_client(self, smart_oauth_header):
        """Convenience function to initialize a new SmartClient"""
        try:
            smart_oauth_header = urllib.unquote(smart_oauth_header)
        except:
            return "Couldn't find a parameter to match the name 'oauth_header'"

        # Pull out OAuth params from the header
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

    def _create_connection_request(self):
        req_id = random.randint(1,9999999999)  # the app's id for this request
        friendly_name = 'My Fun Connection Request'
        secret_q = 'Your favorite color?'
        secret_a = 'gray'  # spaces retained but case insensitive, single word best
        hv_req_id = None  # the hv id

        hv_conn = healthvault.HVConn()
        return hv_conn.createConnectRequest(
            req_id,
            friendly_name,
            secret_q,
            secret_a
        )

    def _get_hv_req_url(self, hv_req_id):
        # just display code don't send email, could also print out
        # url = 'https://shellhostname/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKYZ-QNMN-VHRX-ZGNR-GZNH'
        return settings.HV_SHELL_URL + \
            "/redirect.aspx?target=CONNECT&targetqs=packageid%3d" + \
            hv_req_id

    def _send_hv_req_email(self):
        pass

    def GET(self):
        client = self._get_smart_client(web.input().oauth_header)

        # keep a mapping between:
        # (smart-container, record ID) <--> (HV Record ID) and maintain
        # HV tokens are necessary for sustained access
        header = """
        <!DOCTYPE html>
        <html>
        <head>
            <script
                src="http://sample-apps.smartplatforms.org/framework/smart/scripts/smart-api-client.js"></script>
        </head>
        <body>
        """

        footer = """
        </body>
        </html>
        """

        # AKS: testing create a connection request
        hv_req_id = self._create_connection_request()
        url = self._get_hv_req_url(hv_req_id)
        # https://account.healthvault-ppe.com/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKTR-HVMJ-HHFR-XRZQ-GFQV
        return header+'Click <a href="'+url+'">here</a> to authorize this app to connect to your HealthVault account'+footer


# start up web.py
app = web.application(urls, globals())
web.config.debug = True
if __name__ == "__main__":
    app.run()
else:
    application = app.wsgifunc()

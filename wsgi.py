"""
SMART Merge App

Arjun Sanyal <arjun.sanyal@childrens.harvard.edu>

FIXME
- don't use global functions
- in _get_smart_client use proper exceptions, not just string returns

"""

import os
import sys
base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/healthvault/healthvault')
import healthvault

import datetime
import flask
import json
import logging
import pdb
import platform
import random
import settings
from   smart_client import oauth
from   smart_client.smart import SmartClient
import sqlite3
import urllib

logging.basicConfig(level=logging.DEBUG)

# Note: using ./app for both the templates and static files
# AF needs "application" here - DRY!
application = app = flask.Flask(
    'wsgi',
    static_folder='app',
    static_url_path='/static',
    template_folder='app'
)
app.debug = True

# Are we running on AppFog? (imprecise) - DRY!
AF_PLATFORM = 'Linux-3.2.0-23-virtual-x86_64-with-Ubuntu-12.04-precise'
if platform.platform() == AF_PLATFORM:
    AF_P = True
    SERVER_NAME = 'smart-hv-merge.aws.af.cm'
    app.config['SERVER_NAME'] = SERVER_NAME
    PORT=80
else:
    AF_P = False
    PORT=8000

######################################################################

SMART_SERVER_OAUTH = {
    'consumer_key': None,  # will fill this in later
    'consumer_secret': 'smartapp-secret'
}

SMART_SERVER_PARAMS = {
    'api_base': None  # will fill this in later
}

def _get_smart_client(smart_oauth_header):
    if smart_oauth_header == '':
        return "No smart_oauth_header"

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

######################################################################

def _get_hv_ids(smart_record_id):
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

def _create_connection_request(smart_record_id):
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

def _get_hv_req_url(hv_id_code):
    # just display code don't send email, could also print out
    # url = 'https://shellhostname/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKYZ-QNMN-VHRX-ZGNR-GZNH'
    return settings.HV_SHELL_URL + \
        "/redirect.aspx?target=CONNECT&targetqs=packageid%3d" + \
        hv_id_code

def _send_hv_req_email():
    pass

######################################################################

@app.route('/smartapp/index.html')
def index():
    client = _get_smart_client(flask.request.args.get('oauth_header', ''))
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

    hv_ids = _get_hv_ids(client.record_id)

    #logging.debug('person_id: %s, record_id %s', hv_ids['person_id'], hv_ids['record_id'])

    if hv_ids:
        # show something
        hvconn = healthvault.HVConn(offline_person_id=hv_ids['person_id'])

        ## FIXME: rename! using it for person_id
        wctoken = hv_ids['person_id']

        return flask.render_template(
            'main.html',
            wctoken=wctoken,
            name=hvconn.person.name,
            person_id=hvconn.person.person_id,
            selected_record_id=hvconn.person.selected_record_id,
            auth_token=hvconn._auth_token,
            shared_secret=hvconn._shared_secret
        )
    else:
        hv_id_code = _create_connection_request(client.record_id)
        url = _get_hv_req_url(hv_id_code)
        # https://account.healthvault-ppe.com/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKKR-XKMX-TRTZ-XPGH-CNZQ
        # ? or https://account.healthvault-ppe.com/patientconnect.aspx?action=GetQuestion
        return header + '<p>Your id code is: ' +hv_id_code \
            + '</p><p>Click <a target="_blank" href="' + url + \
            '">here</a> to authorize this app to connect to your HealthVault account</p>' \
            + footer

@app.route('/getGlucoseMeasurements')
def getGlucoseMeasurements():
    g = flask.request.args.get

    #import pdb; pdb.set_trace();

    hvconn = healthvault.HVConn(user_auth_token=g('wctoken'),
        record_id=g('record_id'),
        auth_token=g('auth_token'),
        shared_secret=g('shared_secret'),
        get_person_info_p=False)
    hvconn.getGlucoseMeasurements()

    # don't use flask's builtin jsonify function... it creates
    # one big dict not an array for these
    resp = flask.make_response()
    resp.data = json.dumps(hvconn.person.glucoses)

    if False:
        resp.data = json.dumps([["2013-02-03T21:31:00", 10.0],
            ["2013-02-03T20:46:00", 8.0], ["2013-01-08T16:43:00", 6.0],
            ["2012-10-16T12:23:00", 10.0], ["2012-10-14T13:25:00", 4.0],
            ["2012-10-13T17:13:00", 9.5], ["2012-10-13T17:13:00", 10.0],
            ["2012-10-13T17:13:00", 8.5], ["2012-10-13T17:05:00", 9.0],
            ["2012-10-24T15:00:00", 10.0], ["2012-10-24T07:00:00", 6.6],
            ["2012-10-23T18:45:00", 6.5], ["2012-10-23T08:30:00", 7.0],
            ["2012-10-22T19:30:00", 7.9], ["2012-10-22T08:30:00", 6.5],
            ["2012-10-21T20:00:00", 6.6], ["2012-10-21T06:00:00", 6.6],
            ["2012-10-20T20:00:00", 8.1], ["2012-10-20T07:00:00", 8.1],
            ["2012-10-19T10:00:00", 5.5]])

    resp.mimetype = 'application/json'
    return resp

@app.route('/getA1cs')
def getA1cs():
    g = flask.request.args.get
    #hvconn = healthvault.HVConn(user_auth_token=g('wctoken'),
        #record_id=g('record_id'),
        #auth_token=g('auth_token'),
        #shared_secret=g('shared_secret'),
        #get_person_info_p=False)
    #hvconn.getGlucoseMeasurements()
    # don't use flask's builtin jsonify function... it creates
    # one big dict not an array for these
    resp = flask.make_response()
    # labs = client.get_lab_results()
    # mock
    a1c = [["2012-09-30T10:00:00", 7]]
    resp.data = json.dumps(a1c)
    resp.mimetype = 'application/json'
    return resp

# Start Flask and run on port 80 for consistency with AF
if __name__ == '__main__':
    app.run(port=PORT)


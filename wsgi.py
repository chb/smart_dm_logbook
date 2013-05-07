"""
SMART Diabetes Logbook: Clinician App

Arjun Sanyal <arjun.sanyal@childrens.harvard.edu>

TODO:
- don't use global functions
- in _get_smart_client use proper exceptions, not just string returns

"""

import datetime
import flask
import json
import logging
import os
import platform
import random
import settings
from smart_client import oauth
from smart_client.smart import SmartClient
import sqlite3
import sys
import urllib

base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/healthvault/healthvault')
import healthvault

if settings.DEBUG:
    app.debug = True
    logging.basicConfig(level=logging.DEBUG)
else:
    app.debug = False
    logging.basicConfig(level=logging.INFO)


# Note: using ./app for both the templates and static files
application = app = flask.Flask(  # some PaaS need "application" here
    'wsgi',
    static_folder='app',
    static_url_path='/static',
    template_folder='app'
)


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
        return "Couldn't find 'smart_contianer_api_base' in %s" % \
            smart_oauth_header

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
    conn = sqlite3.connect(
        settings.REQ_DB_DIR + '/' + settings.REQ_DB_FILENAME
    )
    c = conn.cursor()
    s = ('select person_id, hv_record_id '
         'from requests '
         'where smart_record_id = ? limit 1')
    res = c.execute(s, (smart_record_id, ))
    row = res.fetchone()
    conn.commit()
    conn.close()
    if row:
        return {'person_id': row[0], 'record_id': row[1]}
    else:
        return None


def _create_connection_request(smart_record_id):
    # The requests table is defined as:
    # (datetime,
    #  random_external_id,
    #  smart_record_id,
    #  friendly_name,
    #  hv_person_id,
    #  hv_record_id)

    # TODO: should we use a combination of smart container
    # id and record_id here? what to use for container id?
    # Use a random external_id for now
    external_id = random.randint(1, 9999999999)
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
        conn = sqlite3.connect(
            settings.REQ_DB_DIR +
            '/' +
            settings.REQ_DB_FILENAME
        )
        c = conn.cursor()
        s = 'insert into requests values (?, ?, ?, ?, ?, ?)'
        now = datetime.datetime.now().isoformat()
        c.execute(
            s,
            (now, external_id, smart_record_id, friendly_name, '', '')
        )
        conn.commit()
        conn.close()

    return hv_id_code


def _get_hv_req_url(hv_id_code):
    # just display code don't send email, could also print out
    # https://shell/redirect.aspx?target=CONNECT&targetqs=packageid%3dXYZ
    return (settings.HV_SHELL_URL +
            "/redirect.aspx?target=CONNECT&targetqs=packageid%3d" +
            hv_id_code)


def _send_hv_req_email():
    pass

######################################################################


@app.route('/smartapp/index.html')
def index():
    oauth_header = flask.request.args.get('oauth_header', '')
    client = _get_smart_client(oauth_header)
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

    #logging.debug('person_id: %s, record_id %s',
        #hv_ids['person_id'],
        #hv_ids['record_id'])

    if hv_ids:
        # show something
        hvconn = healthvault.HVConn(offline_person_id=hv_ids['person_id'])

        return flask.render_template(
            'main.html',
            name=hvconn.person.name,
            person_id=hvconn.person.person_id,
            selected_record_id=hvconn.person.selected_record_id,
            auth_token=hvconn._auth_token,
            shared_secret=hvconn._shared_secret,
            oauth_header=oauth_header
        )
    else:
        hv_id_code = _create_connection_request(client.record_id)
        url = _get_hv_req_url(hv_id_code)
        # https://account.healthvault-ppe.com/redirect.aspx?target=CONNECT&targetqs=packageid%3dJKKR-XKMX-TRTZ-XPGH-CNZQ
        # ? or https://account.healthvault-ppe.com/patientconnect.aspx?action=GetQuestion
        return (header + '<p>Your id code is: ' + hv_id_code +
                '</p><p>Click <a target="_blank" href="' + url +
                '">here</a> to authorize this app to connect to' +
                'your HealthVault account</p>' + footer)


@app.route('/getGlucoseMeasurements')
def getGlucoseMeasurements():
    g = flask.request.args.get

    # doing offline calls here, need offline_person_id
    hvconn = healthvault.HVConn(
        offline_person_id=g('person_id'),
        record_id=g('selected_record_id'),
        auth_token=g('auth_token'),
        shared_secret=g('shared_secret'),
        get_person_info_p=False
    )

    hvconn.getGlucoseMeasurements()
    # don't use flask's jsonify; it creates a big dict but we want array
    resp = flask.make_response()
    resp.data = json.dumps(hvconn.person.glucoses)
    resp.mimetype = 'application/json'
    return resp


@app.route('/getA1cs')
def getA1cs():
    # from the SMART container
    g = flask.request.args.get
    #client = _get_smart_client(g('oauth_header'))
    #labs = client.get_lab_results()
    a1cs = [["2013-02-03T21:31:00", 8.6]]

    # don't use flask's jsonify; it creates a big dict but we want array
    resp = flask.make_response()
    resp.data = json.dumps(a1cs)
    resp.mimetype = 'application/json'
    return resp


# Start Flask
if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT)

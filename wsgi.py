"""
SMART Diabetes Logbook: Clinician App

Arjun Sanyal <arjun.sanyal@childrens.harvard.edu>

TODO:
- FIXME: Get the connection request secret question and answer from user
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
from smart_client.client import SMARTClient
import sqlite3
import sys
import urllib

base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base+'/healthvault/healthvault')
import healthvault

###########################################################################
# Configuration
###########################################################################
# SMART Container OAuth Endpoint Configuration
_ENDPOINT = {
    "url": "http://sandbox-api-v06.smartplatforms.org",
    "name": "SMART Sandbox API v0.6",
    "app_id": "diabetes-logbook@apps.smartplatforms.org",
    "consumer_key": "diabetes-logbook@apps.smartplatforms.org",
    "consumer_secret": "smartapp-secret"
}

# Other Configuration (you shouldn't need to change this)
logging.basicConfig(level=logging.DEBUG)  # cf. .INFO; default is WARNING
application = app = flask.Flask(  # some PaaS need "application" here
    'wsgi',
    static_folder='app',
    static_url_path='/static',
    template_folder='app'
)

app.debug = True
app.secret_key = 'smartDMlogbookRULEZ!!!'  # only for encrypting the session


###########################################################################
# SMARTClient and OAuth Helper Functions
###########################################################################
def _init_smart_client(record_id=None):
    """ Returns the SMART client, configured accordingly. """
    try:
        client = SMARTClient(_ENDPOINT.get('app_id'),
                             _ENDPOINT.get('url'),
                             _ENDPOINT)
    except Exception as e:
        logging.critical('Could not init SMARTClient: %s' % e)
        flask.abort(500)
        return

    # initial client setup doesn't require record_id
    client.record_id = record_id
    return client


def _test_acc_token(client):
    """ Tests access token by trying to fetch a records basic demographics """
    try:
        demo = client.get_demographics()
        status = demo.response.get('status')
        if '200' == status:
            return True
        else:
            logging.warning('get_demographics returned non-200 status: ' +
                            demo.response.get('status'))
            return False
    except Exception as e:
        return False


def _request_token_for_record(client):
    """ Requests a request token for a given record_id """
    flask.session['acc_token'] = None
    flask.session['req_token'] = None
    logging.debug("Requesting token for %s on %s" % (
        flask.session['record_id'],
        flask.session['api_base'])
    )
    try:
        flask.session['req_token'] = client.fetch_request_token()
    except Exception as e:
        logging.critical('Could not fetch_request_token: %s' % e)
        flask.abort(500)


def _exchange_token(verifier):
    """ Exchanges verifier for an acc_token and stores it in the session """
    record_id = flask.session['record_id']
    req_token = flask.session['req_token']
    assert record_id and req_token

    client = _init_smart_client(record_id)
    client.update_token(req_token)

    try:
        acc_token = client.exchange_token(verifier)
    except Exception as e:
        logging.critical("Token exchange failed: %s" % e)
        flask.abort(500)

    # success, store it!
    logging.debug("Exchanged req_token for acc_token: %s" % acc_token)
    flask.session['acc_token'] = acc_token


###########################################################################
# HealthVault Helper Functions
###########################################################################
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
    """
        The requests table is defined as:
        (datetime,
         random_external_id,
         smart_record_id,
         friendly_name,
         hv_person_id,
         hv_record_id)
    """
    external_id = random.randint(1, 9999999999)
    friendly_name = 'Connection Request ' + str(external_id)
    secret_q = 'Your favorite color?'
    secret_a = 'gray'  # spaces retained but case insensitive, single word best

    hv_conn = healthvault.HVConn()
    assert hv_conn

    hv_id_code = hv_conn.createConnectRequest(
        external_id,
        friendly_name,
        secret_q,
        secret_a
    )
    assert hv_id_code

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


###########################################################################
# App URLs
###########################################################################

@app.route('/smartapp/index.html')
def index():
    api_base = flask.session['api_base'] = _ENDPOINT.get('url')
    current_record_id = flask.session.get('record_id')
    args_record_id = flask.request.args.get('record_id')

    logging.debug('current_record_id: ' + str(current_record_id))
    logging.debug('args_record_id: ' + str(args_record_id))

    if not args_record_id:
        # no record id in the req, clear session and redir to record selection
        flask.session['acc_token'] = None
        flask.session['req_token'] = None
        client = _init_smart_client()  # just init to get launch_url
        assert client.launch_url, "No launch_url found in client. Aborting."
        logging.debug('Redirecting to app launch_url: ' + client.launch_url)
        return flask.redirect(client.launch_url)

    # set the correct, new record_id and clear the session if required
    if current_record_id != args_record_id:
        record_id = flask.session['record_id'] = args_record_id
        flask.session['acc_token'] = None
        flask.session['req_token'] = None
    else:
        record_id = current_record_id

    logging.debug('record_id: ' + record_id)

    client = _init_smart_client(record_id)

    acc_token = flask.session.get('acc_token')

    logging.debug('acc_token is: ' + str(acc_token))

    if not acc_token:
        _request_token_for_record(client)
        logging.debug("Redirecting to authorize url")
        return flask.redirect(client.auth_redirect_url)
    else:
        client.update_token(flask.session['acc_token'])

    assert _test_acc_token(client)

    ### OAuth dance is complete, get to work! ###

    # attempt to get the person_id and hv_record_id from the database
    hv_ids = _get_hv_ids(client.record_id)

    logging.debug('hv person_id: %s, hv record_id %s',
                  hv_ids['person_id'],
                  hv_ids['record_id'])

    if hv_ids:
        # if we have hv ids, init the connection to HV
        hvconn = healthvault.HVConn(offline_person_id=hv_ids['person_id'])
        assert hvconn.person.name

        return flask.render_template(
            'main.html',
            name=hvconn.person.name,
            person_id=hvconn.person.person_id,
            selected_record_id=hvconn.person.selected_record_id,
            auth_token=hvconn._auth_token,
            shared_secret=hvconn._shared_secret
        )
    else:
        # no record of this smart_reccord in the db, create a connection req
        hv_id_code = _create_connection_request(client.record_id)
        assert hv_id_code
        return flask.render_template(
            'showcode.html',
            hv_id_code=hv_id_code,
            url=_get_hv_req_url(hv_id_code)
        )


@app.route('/smartapp/authorize')
def authorize():
    """ Extract the oauth_verifier and exchange it for an access token. """
    new_oauth_token = flask.request.args.get('oauth_token')
    req_token = flask.session['req_token']
    api_base = flask.session['api_base']
    record_id = flask.session['record_id']
    assert new_oauth_token == req_token.get('oauth_token')
    assert api_base and record_id

    _exchange_token(flask.request.args.get('oauth_verifier'))
    return flask.redirect('/smartapp/index.html?api_base=%s&record_id=%s' %
                          (api_base, record_id))


@app.route('/getGlucoseMeasurements')
def getGlucoseMeasurements():
    g = flask.request.args.get

    # doing offline calls here, need offline_person_id
    hvconn = healthvault.HVConn(
        offline_person_id=g('person_id'),
        auth_token=g('auth_token'),
        shared_secret=g('shared_secret'),
        record_id=g('selected_record_id'),
        get_person_info_p=False
    )
    assert hvconn

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
    #labs = client.get_lab_results()
    a1cs = [["2013-02-03T21:31:00", 8.6]]

    # don't use flask's jsonify; it creates a big dict but we want array
    resp = flask.make_response()
    resp.data = json.dumps(a1cs)
    resp.mimetype = 'application/json'
    return resp


###########################################################################

if __name__ == '__main__':
    app.run(port=8000)

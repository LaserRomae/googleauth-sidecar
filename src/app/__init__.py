# Future imports
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# External imports
import os
import sys
import json
import requests
import urllib.request

# Internal imports
from flask import Flask, abort, current_app, session, request, redirect, url_for, Response
from flask_cors import CORS
from rauth import OAuth2Service

# Creates a new Flask app and sets the SECRET_KEY
app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeeee_meeeee'

# Instanciates Flask-Cors for the current Flask app
CORS(app)

# Google OAuth2 credentials initialization
try:
    GOOGLE_LOGIN_CLIENT_ID = os.environ['CLIENT_ID']
    GOOGLE_LOGIN_CLIENT_SECRET = os.environ['CLIENT_SECRET']
except KeyError as e:
    print("KeyError occurred: Missing %s key." % (e, ))
    sys.exit(-1)

OAUTH_CREDENTIALS = {
    'google': {
        'id': GOOGLE_LOGIN_CLIENT_ID,
        'secret': GOOGLE_LOGIN_CLIENT_SECRET
    }
}

try:
    app.config['OAUTH_CREDENTIALS'] = OAUTH_CREDENTIALS
except KeyError as e:
    print("KeyError occurred: Missing %s key.")
    sys.exit(-1)

# Internal backend where every request is redirected to
INTERNAL_BACKEND = os.environ['INTERNAL_BACKEND']


# This function is used to "autoreply" on every incoming OPTIONS request
@app.before_request
def option_autoreply():
    # Always replies 200 on OPTIONS request

    if request.method == 'OPTIONS':
        # Creates a default options response
        resp = app.make_default_options_response()

        headers = None
        # Save ACCESS_CONTROL_REQUEST_HEADERS header
        # if it's present in the current request
        if 'ACCESS_CONTROL_REQUEST_HEADERS' in request.headers:
            headers = request.headers['ACCESS_CONTROL_REQUEST_HEADERS']

        # Get the default response headers
        h = resp.headers

        # Allow the origin which made the XHR
        h['Access-Control-Allow-Origin'] = '*'
        # Allow for 10 seconds
        h['Access-Control-Max-Age'] = '10'
        # Allow the actual method
        if 'Access-Control-Request-Method' in request.headers:
            h['Access-Control-Allow-Methods'] = request.headers['Access-Control-Request-Method']
        else:
            resp.status_code = 400
            return resp

        # Add Access-Control-Allow-Headers based on the
        # request ACCESS_CONTROL_REQUEST_HEADERS header
        if headers is not None:
            h['Access-Control-Allow-Headers'] = headers

        # Returns the options response
        return resp


# This function sets the origin for GET, POST, PUT, DELETE requests
@app.after_request
def set_allow_origin(resp):

    # Get the input response headers
    h = resp.headers

    # Allow cross-domain for other HTTP Verbs
    if request.method != 'OPTIONS' and 'Origin' in request.headers:
        h['Access-Control-Allow-Origin'] = '*'

    # Returns the correct response
    return resp


# OAuthSignIn base class that can be used with multiple OAuth providers
class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        # Sets the provider name
        self.provider_name = provider_name
        # Gets the credentials - consumer_id and consumer_secret
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    # Not used by this class but implemented in subclasses
    def authorize(self):
        pass
    
    # Not used by this class but implemented in subclasses
    def callback(self):
        pass

    # Returns the generated url for the oauth2callback route defined below
    @staticmethod
    def get_callback_url():
        # Remove _scheme='https' if the route is on http
        # Remove _external=True if the route is internal
        return url_for('oauth2callback', _external=True, _scheme='https')

    # Returns the provider from the given provider_name
    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


# OAuthSignIn implementation for Google OAuth2
class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        # Gets the Google open-id configuration and loads it in a dictionary
        googleinfo = urllib.request.urlopen('https://accounts.google.com/.well-known/openid-configuration')
        google_params = json.load(googleinfo)
        # Instanciates the OAuth2Service using the previously loaded Google parameters
        self.service = OAuth2Service(
                name='google',
                client_id=self.consumer_id,
                client_secret=self.consumer_secret,
                authorize_url=google_params.get('authorization_endpoint'),
                base_url=google_params.get('userinfo_endpoint'),
                access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url(),
            offline=True),
            )

    def callback(self):
        if 'code' not in request.args:
            return None, None

        def new_decoder(payload):
            return json.loads(payload.decode("UTF-8"))

        oauth_session = self.service.get_auth_session(
                data={'code': request.args['code'],
                      'grant_type': 'authorization_code',
                      'redirect_uri': self.get_callback_url()
                     },
                decoder=new_decoder
        )
        me = oauth_session.get('').json()
        return "", me


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    if 'user' not in session:
        return redirect(url_for('oauth2authorize',
                        _external=True, _scheme='https'))

    url = INTERNAL_BACKEND + '{0}'.format(path)
    r = None
    params = None
    body = request.get_json() if request.get_json() is not None else {}
    headers = {}
    headers.update({"X-Remote-User": session['user']['email']})
    
    if request.args:
        params = request.args
    if request.headers:
        headers.update(request.headers)
        
    if path:
        if path == 'oauth2authorize' or path == 'oauth2callback':
            return redirect(url_for(path, _external=True, _scheme='https'))
        else:
            if request.method == 'GET':
                r = requests.get(url, headers=headers, params=params)
            elif request.method == 'POST':
                r = requests.post(url, headers=headers, data=body, params=params)
            elif request.method == 'PUT':
                r = requests.put(url, headers=headers, data=body, params=params)
            elif request.method == 'DELETE':
                r = requests.delete(url, headers=headers, data=body, params=params)
    else:
        r = requests.get(url, headers=headers, params=params)

    return Response(r.content, status=r.status_code, content_type=r.headers['content-type'])


@app.route('/oauth2authorize')
def oauth2authorize():
    oauth = OAuthSignIn.get_provider('google')
    return oauth.authorize()


@app.route('/oauth2callback')
def oauth2callback():
    oauth = OAuthSignIn.get_provider('google')
    _, me = oauth.callback()
    if me is None:
        return abort(404)
    session['user'] = me
    return redirect(url_for('catch_all'))

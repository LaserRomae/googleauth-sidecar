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

# OAuthSignIn implementation for Facebook OAuth2
class FacebookSignIn(OAuthSignIn):
    # TODO working on it.
    pass

# OAuthSignIn implementation for Twitter OAuth2
class TwitterSignIn(OAuthSignIn):
    # TODO working on it.
    pass


# HTTP reverse proxy
# catches all the requests for the other container and checks if the user is authenticated
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    # If the user is not logged in, redirects to the oauth2authorize route
    if 'user' not in session:
        return redirect(url_for('oauth2authorize',
                        _external=True, _scheme='https'))

    # Builds the route to the container
    url = INTERNAL_BACKEND + '{0}'.format(path)

    # Initializes the empty request and parameters
    req = None
    params = None

    # Gets the json body if it exists
    body = request.get_json() if request.get_json() is not None else {}

    # Initializes the headers passing the user email in the X-Remote-User header
    headers = {}
    headers.update({"X-Remote-User": session['user']['email']})
    
    # If query string is present -> update params
    if request.args:
        params = request.args

    # If headers are present -> update headers
    if request.headers:
        headers.update(request.headers)
    
    # If the path is different from the base path "/"   
    if path:
        # If the request is for an oauth2 route, just redirect to it
        if path == 'oauth2authorize' or path == 'oauth2callback':
            return redirect(url_for(path, _external=True, _scheme='https'))
        # Else just call the INTERNAL_BACKEND route using the request HTTP method    
        else:
            if request.method == 'GET':
                req = requests.get(url, headers=headers, params=params)
            elif request.method == 'POST':
                req = requests.post(url, headers=headers, data=body, params=params)
            elif request.method == 'PUT':
                req = requests.put(url, headers=headers, data=body, params=params)
            elif request.method == 'DELETE':
                req = requests.delete(url, headers=headers, data=body, params=params)
    else:
        req = requests.get(url, headers=headers, params=params)

    # Return a Response built with the previous request result
    return Response(req.content, status=req.status_code, content_type=req.headers['content-type'])


# The OAuth2 authorize route - now working only with google
@app.route('/oauth2authorize')
def oauth2authorize():
    # Get the GoogleSignIn class
    oauth = OAuthSignIn.get_provider('google')

    # Call the authorize() method
    return oauth.authorize()


# The OAuth2 callback route - now working only with google
@app.route('/oauth2callback')
def oauth2callback():
    # Get the GoogleSignIn class
    oauth = OAuthSignIn.get_provider('google')

    # Call the callback() method
    _, me = oauth.callback()

    # If the result is null, abort with 404 NOT FOUND
    if me is None:
        return abort(404)

    # Set the session['user'] to the callback() method result
    session['user'] = me

    # Redirect to the catch_all route
    return redirect(url_for('catch_all'))

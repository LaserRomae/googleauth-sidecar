# External imports
import os
import unittest


class UnitTests(unittest.TestCase):

    def setUp(self):
        os.environ['CLIENT_ID'] = "TEST"
        os.environ['CLIENT_SECRET'] = "TEST"
        os.environ['INTERNAL_BACKEND'] = "http://localhost:9000"
        # Internal imports
        from app import app
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_option_autoreply(self):
        response = self.app.options('/', headers={'Access-Control-Request-Method': '*'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_option_autoreply_missing_header(self):
        response = self.app.options('/', follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_get_set_allow_origin(self):
        response = self.app.get('/', headers={'Origin': 'http://localhost:8000'})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_post_set_allow_origin(self):
        response = self.app.post('/', headers={'Origin': 'http://localhost:8000'})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_put_set_allow_origin(self):
        response = self.app.put('/', headers={'Origin': 'http://localhost:8000'})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_delete_set_allow_origin(self):
        response = self.app.delete('/', headers={'Origin': 'http://localhost:8000'})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_oauthsignin_get_callback_url(self):
        from app import app, OAuthSignIn
        app.config['SERVER_NAME'] = 'localhost:8000'
        with app.app_context():
            self.assertEqual(OAuthSignIn.get_callback_url(), 'https://localhost:8000/oauth2callback')

    def test_oauthsignin_get_provider(self):
        from app import app, OAuthSignIn, GoogleSignIn
        app.config['SERVER_NAME'] = 'localhost:8000'
        with app.app_context():
            oauthsignin = OAuthSignIn('google')
            googlesignin = GoogleSignIn()
            self.assertEqual(oauthsignin.get_provider('google').__class__, googlesignin.__class__)

    def test_googlesignin_authorize(self):
        from app import app, OAuthSignIn
        app.config['SERVER_NAME'] = 'localhost:8000'
        with app.app_context():
            oauth = OAuthSignIn.get_provider('google')
            self.assertEqual(oauth.authorize().status_code, 302)


if __name__ == "__main__":
    unittest.main()

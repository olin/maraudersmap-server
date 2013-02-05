import unittest
from app import app
import requests
import os
from flask.ext.testing import TestCase

TEST_USERNAME = "harrypotter"


class TestMagic(TestCase):

    def create_app(self):
        self.sessionid = get_sessionid()
        assert self.sessionid
        return app

    def tearDown(self):
        pass

    def test_public(self):
        rv = self.client.get('/')
        assert rv.status_code == 302  # should redirect

    def test_public_ui(self):
        rv = self.client.get('/ui/index.html')
        assert rv.status_code == 200

    def test_api_me_unauth(self):
        rv = self.client.get('/api/me/')
        assert rv.status_code == 302  # should redirect for auth

    def test_api_me(self):
        rv = self.client.get(self.auth_url('/api/me/'))
        assert rv.status_code == 200
        assert 'user' in rv.json

    def test_user_create_unauth(self):
        rv = self.client.put('/api/users/%s/' % TEST_USERNAME)
        assert rv.status_code == 302  # should redirect for auth

    def test_user_create(self):
        rv = self.client.put(self.auth_url('/api/users/%s/' % TEST_USERNAME))
        assert 'user' in rv.json

    def auth_url(self, urlbase):
        ''' Adds sessionid parameter to a url.
        '''
        return urlbase + "?sessionid=%s" % self.sessionid

#TODO: add a browser based test, filling out the form redirected to and ensure that
#sessions properly work using cookies


def get_sessionid():
    username = os.environ.get("OLIN-USERNAME", "")
    password = os.environ.get("OLIN-PASSWORD", "")
    if not username or not password:
        raise ValueError("Username and password not in ENV variables.")
    payload = {"username": username, "password": password}
    r = requests.post("https://olinapps.herokuapp.com/api/exchangelogin",
    data=payload)

    return r.json().get('sessionid', None)

if __name__ == '__main__':
    unittest.main()

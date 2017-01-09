from functools import wraps
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import time


def refresh(func):
    r"""
    Refresh the OAuth token prior to executing the method

    This will check that a token exists and will request a new one if it is
    expired.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not args[0].token:
            args[0].fetch_token()
        else:
            if args[0].token['expires_at'] - time.time() <= 0:
                args[0].fetch_token()
        return func(*args, **kwargs)
    return wrapper


class OAuthAgent(object):
    r"""
    OAuth handler/aide for Application access

    :param str client_id: Client ID code
    :param str client_secret: Client secret code
    :param str token_url: Endpoint for requesting OAuth2 tokens
    """

    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=self.client)
        self.token_url = token_url
        self.secret = client_secret
        self.fetch_token()

    def fetch_token(self):
        r"""
        Retrieve a new OAuth2 token from the service server
        """
        self.client.prepare_request_body()
        self.token = self.oauth.fetch_token(
            token_url=self.token_url, auth=(
                self.client_id, self.secret))

    @refresh
    def request(self, method, url, **kwargs):
        r"""
        Call `requests.request` internally using OAuth2Session

        :param str method: 'POST', 'GET', etc.
        :param str url: Endpoint
        :params kwargs: Keyword arguments
        :rtype: `requests.request`
        """
        return self.oauth.request(method, url, **kwargs)

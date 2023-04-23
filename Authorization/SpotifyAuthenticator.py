import spotipy
from spotipy import oauth2
from Constants import *

class SpotifyAuthenticator:
    def __init__(self):
        self.auth = oauth2.SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="user-read-playback-state user-modify-playback-state")
        
        _getAccesstoken(self):
            access_token = ""

            token_info = self.auth.get_cached_token()

            if token_info:
                print("Found cached token!")
                access_token = token_info['access_token']
            else:
                url = request.url
                code = self.auth.parse_response_code(url)
                if code != url:
                    print("Found Spotify auth code in Request URL! Trying to get valid access token...")
                    token_info = self.auth.get_access_token(code)
                    access_token = token_info['access_token']

            if access_token:
                print("Access token available! Trying to get user information...")
                sp = spotipy.Spotify(access_token)
                results = sp.current_user()
                return results

        
        

 
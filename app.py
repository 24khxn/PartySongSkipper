from Constants import AUTHORIZATION_TOKEN_KEY
from collections import defaultdict
from dataclasses import dataclass
import os
from flask import Flask, request, redirect, render_template, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yaml

#region Flask
app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

#endregion Flask

with open("spotify_config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

app.config["SPOTIPY_CLIENT_ID"] = config["client_id"]
app.config["SPOTIPY_CLIENT_SECRET"] = config["client_secret"]
app.config["SPOTIPY_REDIRECT_URI"] = config["redirect_uri"]

with app.app_context():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=app.config["SPOTIPY_CLIENT_ID"],
        client_secret=app.config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=app.config["SPOTIPY_REDIRECT_URI"],
        scope="user-read-playback-state user-modify-playback-state"
    ))

# pretty sure this was all failing because we weren't using the below
# with app.app_context():

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skip_votes.db"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db logic
# db = SQLAlchemy(app)

# class SkippedSong(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     song_id = db.Column(db.String(255), nullable=False)
#     num_votes = db.Column(db.Integer, default=0)

#     def __repr__(self):
#         return f"<SkippedSong {self.song_id}: {self.num_votes}>"

# db.create_all()

@dataclass
class Song:
    id: str
    href: str
    name: str
    artists: list[str]
    album: str
    
    
#region Login 
@app.route('/admin/login')
def login():
    auth = SpotifyOAuth(
        client_id=app.config["SPOTIPY_CLIENT_ID"],
        client_secret=app.config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=app.config["SPOTIPY_REDIRECT_URI"],
        scope="user-read-playback-state user-modify-playback-state"
    )
    
    access_token = ""

    token_info = auth.get_cached_token()

    if token_info:
        print("Found cached token!")
        access_token = token_info['access_token']
    else:
        url = request.url
        code = auth.parse_response_code(url)
        if code != url:
            print("Found Spotify auth code in Request URL! Trying to get valid access token...")
            token_info = auth.get_access_token(code)
            access_token = token_info['access_token']
            # refresh_token = token_info['refreh_token']

    if access_token:
        print("Access token available!")
        session[AUTHORIZATION_TOKEN_KEY] = access_token
        return index()

    else:
        return _htmlForLoginButton(auth)

def _htmlForLoginButton(auth):
    auth_url = _getSPOauthURI(auth)
    htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
    return htmlLoginButton

def _getSPOauthURI(auth):
    auth_url = auth.get_authorize_url()
    return auth_url
    
@app.route("/")
def index():
    if AUTHORIZATION_TOKEN_KEY in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

#endregion Login

@app.route('/dashboard')
def dashboard():
    song = sp.current_playback()
    key = _getKey(song) 
    return render_template('index.html',
                           current_song=key)

@app.route('/invalid')
def bad_route():
    raise NotImplementedError()

vote_skip_count = defaultdict(int)
voted_ips = set()
votes_per_song = defaultdict(set)
SKIP_THRESHOLD = 5  # Adjust this to the desired number of votes to skip a song

@app.route("/vote", methods=["POST"])
def vote():
    song_key = _getKey(sp.current_playback())
    if song_key is None:
        return "No currently playing song, wtf are you voting about"
    voter_ip = request.remote_addr
    if voter_ip in votes_per_song[song_key]:
        return "You have already voted"
    votes_per_song[song_key].add(voter_ip)
    skip_count = len(votes_per_song[song_key])
    if skip_count >= SKIP_THRESHOLD:
        sp.next_track()
    return render_template("index.html", skip_count=skip_count)
        
    
def _getKey(current_song) -> Song:
    if current_song is None or not current_song['is_playing']:
        return None
    song_dict = current_song['item']
    album = song_dict['album']['name']
    artists = [x['name'] for x in song_dict['artists']]
    return Song(id=song_dict['id'], href=song_dict['href'],
                name=song_dict['name'], album=album, artists=artists)


if __name__ == "__main__":
    app.run(debug=True)

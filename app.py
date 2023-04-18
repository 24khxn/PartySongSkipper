from collections import defaultdict
import os
from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

app.config["SPOTIPY_CLIENT_ID"] = os.environ.get("SPOTIPY_CLIENT_ID") or "your_client_id"
app.config["SPOTIPY_CLIENT_SECRET"] = os.environ.get("SPOTIPY_CLIENT_SECRET") or "your_client_secret"
app.config["SPOTIPY_REDIRECT_URI"] = os.environ.get("SPOTIPY_REDIRECT_URI") or "your_redirect_uri"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=app.config["SPOTIPY_CLIENT_ID"],
    client_secret=app.config["SPOTIPY_CLIENT_SECRET"],
    redirect_uri=app.config["SPOTIPY_REDIRECT_URI"],
    scope="user-read-playback-state user-modify-playback-state"
))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skip_votes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class SkippedSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.String(255), nullable=False)
    num_votes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<SkippedSong {self.song_id}: {self.num_votes}>"

db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

vote_skip_count = defaultdict(int)
voted_ips = set()
SKIP_THRESHOLD = 5  # Adjust this to the desired number of votes to skip a song

@app.route("/vote", methods=["POST"])
def vote():
    voter_ip = request.remote_addr
    if voter_ip in voted_ips:
        return "You have already voted"
    voted_ips.add(voter_ip)
    

@app.route("/vote", methods=["POST"])
def vote():
    # voter_ip = request.remote_addr
    user = sp.current_user()
    user_id = user["id"]
    if user_id not in vote_skip_count:
        vote_skip_count[user_id] += 1
        if sum(vote_skip_count.values()) >= SKIP_THRESHOLD:
            sp.next_track()
            vote_skip_count.clear()
            return "Song skipped"
        return f"Vote registered. {SKIP_THRESHOLD - sum(vote_skip_count.values())} votes needed to skip"
    return "You have already voted"


if __name__ == "__main__":
    app.run(debug=True)

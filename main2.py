from flask import Flask, request, redirect, session, render_template
import requests
from spotipy.oauth2 import SpotifyOAuth
import secrets


app = Flask(__name__)

# spotify api credentials
client_id = 'a1cab982635644aabcd6fcdc5f65d57b'
client_secret = '4d495bfc9b52424b9b344eb19286366e'
redirect_uri = 'http://localhost:8000/callback'



secret_key = secrets.token_hex(16)
app.secret_key = secret_key

# set up the SpotifyOAuth object
sp_oauth = SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope='user-library-read user-read-playback-state')


@app.route('/')
def index():
    rec_node_url = 'http://127.0.0.1:5000'
    # check if the user is already authenticated
    if 'sp_access_token' in session:
        response = requests.post(f"{rec_node_url}/recommender", json={'token': session['sp_access_token']})

        print(response.json())
        cur_track, cur_features, match_tracks, match_features, n_matches = response.json()

        return render_template('current.html', cur_track=cur_track, cur_features=cur_features, match_tracks=match_tracks, match_features=match_features, n_matches=n_matches)
        # return f"current song: {cur_track['name']} by {cur_track['artists'][0]['name']}"

    else:
        # redirect to the  authorization page
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

# for authentication
@app.route('/callback')
def callback():
    # get the authorization code
    code = request.args.get('code')

    # use the authorization code to get an access token
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info['access_token']

    # store the access token in the session
    session['sp_access_token'] = access_token

    # redirect back to the homepage
    return redirect('/')


if __name__ == '__main__':
    app.run(port=8000)

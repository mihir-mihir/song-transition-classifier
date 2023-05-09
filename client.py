from flask import Flask, request, redirect, session, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import secrets

app = Flask(__name__)

# Spotify API credentials
client_id = 'a1cab982635644aabcd6fcdc5f65d57b'
client_secret = '4d495bfc9b52424b9b344eb19286366e'
redirect_uri = 'http://localhost:8000/callback'

app = Flask(__name__)

secret_key = secrets.token_hex(16)
app.secret_key = secret_key

# Set up the SpotifyOAuth object with your client ID, client secret, and redirect URI
sp_oauth = SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope='user-library-read user-read-playback-state',
                        cache_path='/token_cache')


@app.route('/')
def index():
    # Check if the user is already authenticated
    if 'sp_access_token' in session:
        sp = spotipy.Spotify(auth=session['sp_access_token'])
        playlists = sp.current_user_playlists()
        # return render_template('playlists.html', playlists=playlists)
        return redirect('http://localhost:8000/current')
    else:
        # Redirect the user to the Spotify authorization page
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)


@app.route('/playlists/playlists/<playlist_id>', methods=['GET'])
def get_playlist(playlist_id):

    if 'sp_access_token' in session:
        sp = spotipy.Spotify(auth=session['sp_access_token'])
        tracks = sp.playlist_tracks(playlist_id=playlist_id)['items']
        for track in tracks:
            track_id = track['track']['id']

    else:
        # Redirect the user to the Spotify authorization page
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)


@app.route('/current', methods=['GET'])
def get_current():
    if 'sp_access_token' in session:
        sp = spotipy.Spotify(auth=session['sp_access_token'])
        track = sp.currently_playing()
        analysis = sp.audio_features(track_id=track['item']['id'])
        tempo = analysis['track']['tempo']
        key = analysis['track']['key']

        recs = []
        recs_a = []
        saved_tracks = sp.current_user_saved_tracks(limit=50)
        while saved_tracks:
            # Loop through each saved track and process the data as needed
            for item in saved_tracks['items']:
                t = item['track']
                a = sp.audio_features(track_id=t['id'])
                if tempo - 5 <= a['track']['tempo'] <= tempo + 5 and a['track']['tempo'] == key:
                    recs.append(t)
                    recs_a.append(a)
                    # Access track information, e.g. track['name'], track['artists'][0]['name'], etc.
                # print(t['name'], '-', t['artists'][0]['name'])

            # Check if there are more saved tracks to retrieve
            if saved_tracks['next']:
                saved_tracks = sp.next(saved_tracks)
            else:
                saved_tracks = None
        return render_template('current.html', current_track=track, analysis=analysis, recs=recs, recs_a=recs_a)
    else:
        # Redirect the user to the Spotify authorization page
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)


@app.route('/callback')
def callback():
    # Get the authorization code from the query parameters
    code = request.args.get('code')

    # Use the authorization code to get an access token
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info['access_token']

    # Store the access token in the session
    session['sp_access_token'] = access_token

    # Redirect the user back to the homepage
    return redirect('/')


if __name__ == '__main__':
    app.run(port=8000)

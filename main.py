from flask import Flask, request, redirect, session, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import secrets
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

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
    # check if the user is already authenticated
    if 'sp_access_token' in session:
        sp = spotipy.Spotify(auth=session['sp_access_token'])
        cur_track = sp.currently_playing()['item']
        cur_id = cur_track['id']
        cur_features = sp.audio_features(cur_id)
        cur_tempo = cur_features[0]['tempo']
        cur_key = cur_features[0]['key']

        # want to use these features to classify
        features = ['acousticness', 'danceability', 'energy', 'valence']
    
        saved_ids = []
        saved_tracks = sp.current_user_saved_tracks(limit=50)
        while saved_tracks:
            for item in saved_tracks['items']:
                saved_ids.append(item['track']['id'])
            if saved_tracks['next']:
                saved_tracks = sp.next(saved_tracks)
            else:
                saved_tracks = None

        # list of audio features for all the saved tracks
        audio_features_list = []
        batch_size = 100

        # api lets you get audio features for 100 tracks at a time
        for i in range(0, len(saved_ids), batch_size):
            batch_ids = saved_ids[i:i+batch_size]
            batch_features = sp.audio_features(tracks=batch_ids)
            audio_features_list += batch_features

        df = pd.DataFrame(audio_features_list, columns=features)


        # scale the data
        scaler = StandardScaler()
        scaler.fit_transform(df)
        df_scaled = scaler.transform(df)

        # cluster the songs
        n_clusters = 6
        kmeans = KMeans(n_clusters=n_clusters,
                        random_state=0).fit(df_scaled)
        labels = kmeans.predict(df_scaled)
            

        # the label assoiciated with the current song
        cur_df = pd.DataFrame(cur_features, columns=features)
        cur_df_scaled = scaler.transform(cur_df)
        rec_label = kmeans.predict(cur_df_scaled)

        # for the tracks that are a match
        match_tracks = []
        match_features = []

        # iterate through the audio feature objects of the saved tracks in the predicted cluster and add the ones with the same key and similar bpm to recs
        for i in range(len(audio_features_list)):
            # only pull from songs in the predicted cluster of the song that's currently playing
            if labels[i] == rec_label:
            # print(audio_features['id'])
                if (audio_features_list[i]['key'] == cur_key) and (cur_tempo - 5 <= audio_features_list[i]['tempo'] <= cur_tempo + 5) and (cur_id != audio_features_list[i]['id']):
                    match_track = sp.track(audio_features_list[i]['id'])
                    if not (cur_track['name'] == match_track['name'] and cur_track['artists'][0]['name'] == match_track['artists'][0]['name']):
                        match_tracks.append(match_track)
                        match_features.append(audio_features_list[i])
                        print(
                            f"{match_track['name']} by {match_track['artists'][0]['name']} is a match")

        n_matches = len(match_tracks)

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

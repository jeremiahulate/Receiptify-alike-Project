from flask import Flask, render_template, redirect, request, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
from config import *
from flask_session import Session
import uuid
import re
import redis
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=6379, db=0)  # Specify db=0
Session(app)  # Initialize server-side sessions

client_ID = client_id
client_Secret = client_secret
redirect_URI = redirect_uri

Scope = "user-read-email user-read-private playlist-read-collaborative user-top-read user-read-recently-played user-read-currently-playing user-library-read"

# Function to sanitize display names for use as a filename
def sanitize_display_name(display_name):
    # Remove invalid characters for file names
    return re.sub(r'[<>:"/\\|?*]', '', display_name)[:50]  # Limit to 50 characters

# Function to get Spotify OAuth object
def get_spotify_oauth():
    cache_path = f".cache-{session.get('session_id','default')}"
    return SpotifyOAuth(
        client_id=client_ID,
        client_secret=client_Secret,
        redirect_uri=redirect_URI,
        scope=Scope,
        cache_path=cache_path,
        cache_handler=MemoryCacheHandler()
    )

# Function to get user token from session
def get_user_token():
    if 'session_id' not in session:
        print("No session ID found. User is not logged in.")
        return None

    token_info = session.get(f"token_info_{session['session_id']}", None)

    if not token_info:
        print("No token found in session for this user.")
        return None

    auth_manager = get_spotify_oauth()
    if auth_manager.is_token_expired(token_info):
        print("Token expired. Refreshing...")
        token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
        session[f"token_info_{session['session_id']}"] = token_info  # store refreshed token correctly

    return token_info


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/authenticate')
def authenticate():
    # 
    session.clear()
    
    auth_manager = get_spotify_oauth()
    auth_url = auth_manager.get_authorize_url()

    # generate a new session ID for every login
    session['session_id'] = str(uuid.uuid4())

    print(f"New Session ID: {session['session_id']} assigned for authentication.")

    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed. No code received.", 400

    auth_manager = get_spotify_oauth()
    try:
        token_info = auth_manager.get_access_token(code)
        print("Retrieved token info:", token_info)
        print("Token scopes:", token_info.get("scope"))
        
        # create a unique session ID for each user
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        session[f"token_info_{session['session_id']}"] = token_info  #store token under unique key

        print(f"Session ID: {session['session_id']} now has a token.")
        return redirect(url_for('profile'))

    except Exception as e:
        print(f"Error during token retrieval: {e}")
        return f"Failed to get token: {str(e)}", 500


@app.route('/profile')
def profile():
    print("Session Data:", session)  #debug
    
    token_info = get_user_token()
    if not token_info:
        print("Redirecting to index because no token is found.")
        return redirect(url_for('index'))
    
    tokencollector = spotipy.Spotify(auth=token_info['access_token'])
    user = tokencollector.current_user()
    
    # check if user authentication actually worked
    if not user:
        print("Error: Unable to retrieve user data!")
        return "Error retrieving user data", 500

    # fetch user data
    try:
        top_tracks = tokencollector.current_user_top_tracks(10, 0, 'medium_term')
        saved_tracks = tokencollector.current_user_saved_tracks(12)
        user_playlists = tokencollector.current_user_playlists(21)
        for track in top_tracks['items']:
            tracklength = track['duration_ms']
            formatted = f"{tracklength // 60000}:{(tracklength % 60000) // 1000:02d}"
            track['length'] = formatted
    
        for item in saved_tracks['items']:
            tracklength = item['track']['duration_ms']
            formatted = f"{tracklength // 60000}:{(tracklength % 60000) // 1000:02d}"
            item['track']['length'] = formatted
    
    except Exception as e:
        print(f"Spotify API error: {e}")
        return f"Error fetching data from Spotify API: {str(e)}", 500

    # ensure all data is available before rendering
    print(f"Fetched {len(top_tracks['items'])} top tracks")
    print(f"Fetched {len(saved_tracks['items'])} saved tracks")
    print(f"Fetched {len(user_playlists['items'])} playlists")


    # ensure profile picture exists
    pfp = user['images'][0]['url'] if user['images'] else url_for('static', filename='default_pfp.jpg')

    return render_template('profile.html', 
                           user=user, 
                           top_tracks=top_tracks, 
                           saved_tracks=saved_tracks, 
                           user_playlists=user_playlists, 
                           pfp=pfp)

@app.route('/search')
def search():
    pass

@app.route('/logout')
def logout():
    print("LOgoiut")
    cache_file = f".cache-{session.get('session_id', 'default')}"
    # Remove the cache file if it exists
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print(f"Cleared cache file: {cache_file}")
    else:
        print("No cache file to remove.")
    
    session.clear()  # Clears all session data
    print("session.clear()")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
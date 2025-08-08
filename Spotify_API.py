#Read user's top records, artists, playlists, and saved records
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
from config import*
import sys
import io

client_ID = client_id
client_Secret = client_secret
redirect_URI = redirect_uri

Scope = "user-read-email user-read-private playlist-read-collaborative user-top-read user-read-recently-played user-read-currently-playing user-library-read"

#authenicating manager
auth_manager=SpotifyOAuth(
    client_id=client_ID, 
    client_secret=client_Secret, 
    redirect_uri=redirect_URI, 
    scope=Scope,
    cache_handler=MemoryCacheHandler()  # Using MemoryCacheHandler for simplicity
    )

#token collector
tokencollector = spotipy.Spotify(auth_manager=auth_manager)

#capture standard output
output = io.StringIO()
sys.stdout = output

#print out the tokens to verify that the user has been authenticated ( will probably take out later cuz it's not necessary and is sensitive)
token_info = auth_manager.get_cached_token()
if token_info:
    expiration = token_info['expires_at']
    expirationmin = expiration // 60000  #60000 ms in a minute
    expirationsec = (expiration % 60000) // 1000  #remaining ms to seconds

#format track length as "minutes:seconds"
    newexpiration = f"{expirationmin}:{expirationsec:02d}"  #:02d for two-digit seconds
    print(f"Your access token Expires: {newexpiration}")
else:
    print("No token info found. Please authorize the application.")
    auth_url = auth_manager.get_authorize_url()
    print(f"Please visit this URL to authorize the application: {auth_url}\n")


#get user email and display name
user = tokencollector.current_user()
print(f"\nWelcome {user['display_name']}!")
print(f"Your email: {user['email']}")
print(f"Country: {user['country']}")
print(f"Followers: {user['followers']['total']}\n")

#get user's top 10 records
top_tracks = tokencollector.current_user_top_tracks(10,0,'medium_term') #10 tracks, offset 0, medium term
print("Your top 10 records:")
printedtoprecords = set()
toptracks =[]

#track info loop so that it doesn't repeat the first entry twice
for idx, track in enumerate(top_tracks['items']):  
    trackname = track['name']
    tracklength = track['duration_ms'] #assuming since its not saved doesn't need to access the ['track'] dictionary
    artistname = track ['artists'][0]['name']
    albumarturl = track['album']['images'][0]['url'] 

#convert milliseconds to minutes and seconds
    tracklengthmin = tracklength // 60000  #60000 ms in a minute
    tracklengthsec = (tracklength % 60000) // 1000  #remaining ms to seconds

    #format track length as "minutes:seconds"
    newtracklength = f"{tracklengthmin}:{tracklengthsec:02d}"  #:02d for two-digit seconds
    print(f"Track: {trackname} Duration: {newtracklength}")  # Debug output
    
    toptracks.append({
        'name': trackname,
        'artist': artistname,
        'length': newtracklength,
        'albumarturl': albumarturl
    }) 

# Get user's top artists
top_artists = tokencollector.current_user_top_artists(5,0,'medium_term') #5 artists, offset 0, medium term
print("\nYour top 5 artists:")
printedartists = set()

#artist loop so that it doesn't repeat the first entry twice
for idx, artist in enumerate(top_artists['items']):
    if artist['name'] not in printedartists:
        print(f"{idx + 1}. {artist['name']}")
        printedartists.add(artist['name'])
    
#get user's playlists
userplaylists = tokencollector.current_user_playlists(21) #21 to get 20 playlists i don't know why it is 1 more than the number i want to display. 
print("\nYour 20 most recently played playlists:")
printedplaylsts = set()
usavplaylists = []
for idx, playlist in enumerate(userplaylists['items']):
    playlistname = playlist['name']
    playlistcreator = playlist['owner']['display_name']
    playlistsongs = playlist['tracks']['total']
    playlistimageurl = playlist['images'][0]['url']  # get the playlist art URL

#playlistlength = playlist[items['duration_ms']
    if playlist['name'] not in printedplaylsts:
        print(f"{idx + 1}. {playlist['name']} by {playlistcreator} ({playlistsongs} songs)")
        printedplaylsts.add(playlist['name'])
        
        usavplaylists.append( {
            'name': playlistname,
            'creator': playlistcreator,
            'songs': playlistsongs,
            'playlistimage': playlistimageurl  # get the playlist art URL
    })

#get user's 12 most recently saved tracks
usersavedtracks = tokencollector.current_user_saved_tracks(12)
print("\nYour 12 most recently saved records:")
printedusersavedrecords = set()
usavtracks = []

#track info loop for saved records so that it doesn't repeat the first entry twice
for idx, track in enumerate(usersavedtracks['items']):
    trackname = track['track']['name']
    tracklength = track['track']['duration_ms'] #assuming adding ['track'] will fix the error because it is saved in the user's library and needs to access the dictionary
    artistname = track['track']['artists'][0]['name']

# Check if the 'album' key exists and if images are present
    if 'album' in track['track'] and track['track']['album']['images']:
        albumarturl = track['track']['album']['images'][0]['url']  # get the album art URL
    else:
        albumarturl = 'No album art available'  # Fallback in case album art is missing

#convert milliseconds to minutes and seconds
    tracklengthmin = tracklength // 60000  #60000 ms in a minute
    tracklengthsec = (tracklength % 60000) // 1000  #remaining ms to seconds

#format track length as "minutes:seconds"
    newtracklength = f"{tracklengthmin}:{tracklengthsec:02d}"  #:02d for two-digit seconds
    
    usavtracks.append({
        'name': trackname,
        'artist': artistname,
        'length': newtracklength,
        'albumarturl': albumarturl
        })

#reset standard output
sys.stdout = sys.__stdout__
#store captured output in a variable
captured_output = output.getvalue()


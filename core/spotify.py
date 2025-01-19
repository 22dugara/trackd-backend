import requests
from django.conf import settings
from datetime import timedelta


def get_spotify_token():
    """
    Generate Spotify access token using Client Credentials Flow.
    """
    url = "https://accounts.spotify.com/api/token"
    payload = {"grant_type": "client_credentials"}
    auth = (settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET)
    
    response = requests.post(url, data=payload, auth=auth)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None


def search_spotify(query, content_type, token):
    """
    Search Spotify API for the given query and content type.
    """
    if content_type == "Profile":
        return None
        
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    
    # If no specific content type, search for all types
    if content_type is None:
        params = {
            "q": query,
            "type": "track,album,artist",  # Search all types
            "limit": 10,  # Limit results to 10 per type
        }
    else:
        # Handle "Song" -> "track" conversion
        if content_type == "Song":
            content_type = "track"
        params = {
            "q": query,
            "type": content_type.lower(),  # Spotify API expects lowercase type
            "limit": 10,  # Limit results to 10
        }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        results = {}
        
        # Map Spotify's response to our format
        type_mapping = {
            'tracks': 'tracks',
            'albums': 'albums',
            'artists': 'artists'
        }
        
        for spotify_type, our_type in type_mapping.items():
            if spotify_type in data:
                results[our_type] = data[spotify_type]['items']
        
        return results
    return {"error": "Failed to fetch results from Spotify"}

def get_spotify_item(content_type, spotify_id, token):
    """
    Get a specific item from Spotify API by ID and type.
    Args:
        content_type (str): The type of content ('artist', 'album', or 'track')
        spotify_id (str): The Spotify ID of the item
        token (str): Valid Spotify access token
    Returns:
        dict: The item data from Spotify, or None if request fails
    """
    if content_type not in ['artist', 'album', 'track']:
        return None
        
    url = f"https://api.spotify.com/v1/{content_type}s/{spotify_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print("Getting Spotify Item: " + spotify_id)
    print(response)
    if response.status_code == 200:
        return response.json()
    return None

def create_resource(content_type, spotify_uri, token):
    """
    Create a new resource in our database from Spotify data
    Args:
        content_type (str): The type of content ('artist', 'album', or 'track')
        spotify_uri (str): The Spotify URI of the item
        token (str): Valid Spotify access token
    Returns:
        Model instance: The created database object, or None if creation fails
    """
    from .models import Artist, Album, Song  # Import here to avoid circular imports
    
    # Extract Spotify ID from URI (format: spotify:type:id)
    spotify_id = spotify_uri.split(':')[-1]
    
    # Get detailed data from Spotify
    spotify_data = get_spotify_item(content_type, spotify_id, token)
    if not spotify_data:
        return None

    try:
        if content_type == 'artist':
            artist, created = Artist.objects.get_or_create(
                spotify_uri=spotify_uri,
                defaults={
                    'name': spotify_data['name'],
                    'genre': spotify_data['genres'][0] if spotify_data.get('genres') else '',
                    'image': spotify_data['images'][0]['url'] if spotify_data.get('images') else None
                }
            )
            return artist

        elif content_type == 'album':
            # First ensure we have the artist
            artist_uri = spotify_data['artists'][0]['uri']
            artist = create_resource('artist', artist_uri, token)
            
            album, created = Album.objects.get_or_create(
                spotify_uri=spotify_uri,
                defaults={
                    'title': spotify_data['name'],
                    'artist': artist,
                    'genre': artist.genre,  # Use artist's genre as default
                    'release_date': spotify_data['release_date'],
                    'cover_art': spotify_data['images'][0]['url'] if spotify_data.get('images') else None
                }
            )

            # If this is a new album, create all its tracks
            if created:
                tracks_url = f"https://api.spotify.com/v1/albums/{spotify_id}/tracks"
                headers = {"Authorization": f"Bearer {token}"}
                tracks_response = requests.get(tracks_url, headers=headers)
                
                if tracks_response.status_code == 200:
                    tracks_data = tracks_response.json()
                    
                    for track in tracks_data['items']:
                        # Create each track if it doesn't exist
                        Song.objects.get_or_create(
                            spotify_uri=track['uri'],
                            defaults={
                                'title': track['name'],
                                'artist': artist,
                                'album': album,
                                'duration': timedelta(milliseconds=track['duration_ms']),  # Convert to timedelta
                                'image': album.cover_art  # Use album cover for song image
                            }
                        )
            
            return album

        elif content_type == 'track':
            # Ensure we have the artist and album
            artist_uri = spotify_data['artists'][0]['uri']
            artist = create_resource('artist', artist_uri, token)
            
            album_uri = spotify_data['album']['uri']
            album = create_resource('album', album_uri, token)
            
            song, created = Song.objects.get_or_create(
                spotify_uri=spotify_uri,
                defaults={
                    'title': spotify_data['name'],
                    'artist': artist,
                    'album': album,
                    'duration': timedelta(milliseconds=spotify_data['duration_ms']),  # Convert to timedelta
                    'image': spotify_data['album']['images'][0]['url'] if spotify_data['album'].get('images') else None
                }
            )
            return song

    except Exception as e:
        print(f"Error creating resource: {str(e)}")
        return None

    return None


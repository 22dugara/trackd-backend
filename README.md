

# Trackd API

A Django REST API for managing music-related content including artists, albums, songs, reviews, and user favorites.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Profiles](#profiles)
  - [Artists](#artists)
  - [Albums](#albums)
  - [Songs](#songs)
  - [Reviews](#reviews)
  - [Favorites](#favorites)
  - [Recommendations](#recommendations)

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd trackd-backend
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Start the development server
```bash
python manage.py runserver
```

## Getting Started

The API will be available at `http://localhost:8000/api/`

To use protected endpoints, you'll need to:
1. Create a user account
2. Obtain a JWT token
3. Include the token in your requests

## API Documentation

### Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

#### Obtain Token
```http
POST /api/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

#### Refresh Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "your_refresh_token"
}
```

### Profiles
#### List/Create Profiles
```http
GET /api/profiles/
POST /api/profiles/
```

Fields:
- `user` (integer): User ID
- `display_picture` (file, optional): Profile picture
- `bio` (string, optional): User biography
- `favorite_genres` (array): List of favorite music genres

#### Retrieve/Update/Delete Profile
```http
GET /api/profiles/{id}/
PUT /api/profiles/{id}/
DELETE /api/profiles/{id}/
```

### Artists
#### List/Create Artists
```http
GET /api/artists/
POST /api/artists/
```

Fields:
- `name` (string): Artist name
- `genre` (string): Primary genre
- `description` (string, optional): Artist description
- `average_rating` (decimal): Read-only average rating

#### Retrieve/Update/Delete Artist
```http
GET /api/artists/{id}/
PUT /api/artists/{id}/
DELETE /api/artists/{id}/
```

### Albums
#### List/Create Albums
```http
GET /api/albums/
POST /api/albums/
```

Fields:
- `title` (string): Album title
- `artist` (integer): Artist ID
- `genre` (string): Album genre
- `release_date` (date): Release date
- `cover_art` (file, optional): Album cover image
- `average_rating` (decimal): Read-only average rating

Query Parameters:
- `genre`: Filter by genre
- `release_date`: Filter by release date
- `search`: Search in title and artist name

#### Retrieve/Update/Delete Album
```http
GET /api/albums/{id}/
PUT /api/albums/{id}/
DELETE /api/albums/{id}/
```

#### Get Album Reviews
```http
GET /api/albums/{id}/reviews/
```

### Songs
#### List/Create Songs
```http
GET /api/songs/
POST /api/songs/
```

Fields:
- `title` (string): Song title
- `artist` (integer): Artist ID
- `album` (integer, optional): Album ID
- `duration` (integer): Duration in seconds
- `average_rating` (decimal): Read-only average rating

#### Retrieve/Update/Delete Song
```http
GET /api/songs/{id}/
PUT /api/songs/{id}/
DELETE /api/songs/{id}/
```

### Reviews
#### List/Create Reviews
```http
GET /api/reviews/
POST /api/reviews/
```

Fields:
- `content_type` (string): Type of content being reviewed ('album', 'song', or 'artist')
- `content_id` (integer): ID of the content being reviewed
- `rating` (decimal): Rating value
- `review_text` (string): Review content
- `created_at` (datetime): Read-only timestamp

Authentication required for POST. Users can only create one review per content item.

#### Retrieve/Update/Delete Review
```http
GET /api/reviews/{id}/
PUT /api/reviews/{id}/
DELETE /api/reviews/{id}/
```

### Favorites
Authentication required for all favorites endpoints.

#### List/Create Favorites
```http
GET /api/favorites/
POST /api/favorites/
```

Fields:
- `content_type` (string): Type of content ('album', 'song', or 'artist')
- `content_id` (integer): ID of the favorited content

#### Retrieve/Delete Favorite
```http
GET /api/favorites/{id}/
DELETE /api/favorites/{id}/
```

#### Filter Favorites by Type
```http
GET /api/favorites/albums/
GET /api/favorites/songs/
GET /api/favorites/artists/
```

### Recommendations
```http
GET /api/recommendations/
```

Returns album recommendations based on user's favorite genres.
Authentication required.

### Notes:
- All POST/PUT requests should use `Content-Type: application/json`
- Dates should be in YYYY-MM-DD format
- File uploads should use `multipart/form-data`
- All protected endpoints require valid JWT token
- Server responses are in JSON format

## Contributing
[Add contribution guidelines if applicable]

## License
[Add your license information]

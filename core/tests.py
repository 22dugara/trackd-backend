from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Artist, Album, Song, Review, Favorite
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class CoreAPITests(APITestCase):
    def setUp(self):
        """
        Create initial data for testing.
        """
        # Create a test user and authenticate
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.login(username="testuser", password="password123")

        # Create test data
        self.artist = Artist.objects.create(name="Test Artist", genre="Rock")
        self.album = Album.objects.create(
            title="Test Album", artist=self.artist, genre="Rock", release_date="2023-01-01"
        )
        self.song = Song.objects.create(title="Test Song", artist=self.artist, album=self.album, duration="00:03:30")

    def test_get_artists(self):
        """
        Test retrieving the list of artists.
        """
        response = self.client.get("/api/artists/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Artist")

    def test_create_review(self):
        """
        Test creating a review for an album.
        """
        review_data = {
            "content_type": "album",
            "content_id": self.album.id,  # Ensure this ID matches an existing album
            "rating": 4.5,
            "review_text": "Great album!",
        }
        response = self.client.post("/api/reviews/", review_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_album_average_rating(self):
        """
        Test that the average rating for an album is calculated correctly.
        """
        # Create a second test user
        self.user2 = User.objects.create_user(username="testuser2", password="password123")
        
        # Post first review with original user
        review_data_1 = {"content_type": "album", "content_id": self.album.id, "rating": 4.0, "review_text": "Good!"}
        self.client.post("/api/reviews/", review_data_1)
        
        # Switch to second user
        self.client.logout()
        self.client.login(username="testuser2", password="password123")
        
        # Post second review with second user
        review_data_2 = {"content_type": "album", "content_id": self.album.id, "rating": 5.0, "review_text": "Excellent!"}
        self.client.post("/api/reviews/", review_data_2)

        # Fetch the album and check its average rating
        response = self.client.get(f"/api/albums/{self.album.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_rating"], '4.5')

    def test_overwrite_existing_review(self):
        """
        Test that submitting a new review overwrites the existing one for the same user.
        """
        # Create the first review
        initial_review = {
            "content_type": "album",
            "content_id": self.album.id,
            "rating": 4.5,
            "review_text": "Great album!",
        }
        first_response = self.client.post("/api/reviews/", initial_review)
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        
        # Submit an updated review
        updated_review = {
            "content_type": "album",
            "content_id": self.album.id,
            "rating": 3.0,
            "review_text": "Changed my mind - it's just okay.",
        }
        update_response = self.client.post("/api/reviews/", updated_review)
        self.assertEqual(update_response.status_code, status.HTTP_201_CREATED)

        # Verify only one review exists and it has the updated content
        response = self.client.get(f"/api/albums/{self.album.id}/reviews/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]["rating"]), 3.0)
        self.assertEqual(response.data[0]["review_text"], "Changed my mind - it's just okay.")



class FavoriteModelTests(TestCase):
    def setUp(self):
        """
        Set up test data for all test methods:
        - Creates a test user
        - Creates a test artist
        - Creates a test album
        - Creates a test song
        """
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.artist = Artist.objects.create(name='Test Artist')
        self.album = Album.objects.create(
            title='Test Album',
            artist=self.artist,
            genre='rock',
            release_date='2024-01-01'
        )
        self.song = Song.objects.create(
            title='Test Song',
            artist=self.artist,
            album=self.album,
            duration="00:03:30"
        )

    def test_create_favorite(self):
        """
        Ensures that a Favorite instance can be created with valid data
        and has the correct string representation
        """
        favorite = Favorite.objects.create(
            user=self.user,
            content_type='album',
            content_id=self.album.id
        )
        self.assertEqual(str(favorite), "testuser's favorite album: " + str(self.album.id) + "")

    def test_unique_together_constraint(self):
        """
        Verifies that the unique_together constraint prevents duplicate favorites
        for the same user, content_type, and content_id combination
        """
        Favorite.objects.create(
            user=self.user,
            content_type='album',
            content_id=self.album.id
        )
        with self.assertRaises(Exception):
            Favorite.objects.create(
                user=self.user,
                content_type='album',
                content_id=self.album.id
            )

class FavoriteAPITests(APITestCase):
    def setUp(self):
        """
        Set up test data for all API test methods:
        - Creates a test user and authenticates the client
        - Creates a test artist
        - Creates a test album
        - Creates a test song
        """
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.artist = Artist.objects.create(name='Test Artist')
        self.album = Album.objects.create(
            title='Test Album',
            artist=self.artist,
            genre='rock',
            release_date='2024-01-01'
        )
        self.song = Song.objects.create(
            title='Test Song',
            album=self.album,
            artist=self.artist,
            duration="00:03:30"
        )

    def test_create_favorite(self):
        """
        Tests POST request to create a new favorite
        Verifies successful creation and correct response status
        """
        url = reverse('favorite-list')
        data = {
            'user': self.user.id,
            'content_type': 'album',
            'content_id': self.album.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), 1)

    def test_list_favorites(self):
        """
        Tests GET request to list all favorites
        Verifies correct number of favorites are returned
        """
        Favorite.objects.create(
            user=self.user,
            content_type='album',
            content_id=self.album.id
        )
        Favorite.objects.create(
            user=self.user,
            content_type='song',
            content_id=self.song.id
        )

        url = reverse('favorite-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_favorite(self):
        """
        Tests DELETE request to remove a favorite
        Verifies successful deletion and database update
        """
        favorite = Favorite.objects.create(
            user=self.user,
            content_type='album',
            content_id=self.album.id
        )
        url = reverse('favorite-detail', args=[favorite.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_filter_favorites_by_type(self):
        """
        Tests the custom endpoints for filtering favorites by type
        Verifies correct filtering for albums and songs
        """
        Favorite.objects.create(
            user=self.user,
            content_type='album',
            content_id=self.album.id
        )
        Favorite.objects.create(
            user=self.user,
            content_type='song',
            content_id=self.song.id
        )

        url = reverse('favorite-albums')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content_type'], 'album')

        url = reverse('favorite-songs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content_type'], 'song')

    def test_unauthorized_access(self):
        """
        Tests that unauthenticated users cannot access the API
        Verifies 401 response for unauthorized requests
        """
        self.client.force_authenticate(user=None)
        url = reverse('favorite-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_invalid_content_type(self):
        """
        Tests validation of content_type field
        Verifies 400 response for invalid content types
        """
        url = reverse('favorite-list')
        data = {
            'content_type': 'invalid',
            'content_id': 1
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_nonexistent_content(self):
        """
        Tests validation of content_id field
        Verifies 400 response when referencing non-existent content
        """
        url = reverse('favorite-list')
        data = {
            'content_type': 'album',
            'content_id': 99999  # Non-existent ID
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_only_see_own_favorites(self):
        """
        Tests user isolation of favorites
        Verifies that users can only see their own favorites
        """
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        Favorite.objects.create(
            user=other_user,
            content_type='album',
            content_id=self.album.id
        )

        url = reverse('favorite-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Should only see own favorites
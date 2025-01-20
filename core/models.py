from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class SearchableMixin:
    """
    A mixin that defines common properties for searchable items.
    This is not a model, but a set of common properties.
    """
    @property
    def search_title(self):
        """Return the title of the object for search results"""
        if hasattr(self, 'title'):
            return self.title
        elif hasattr(self, 'name'):
            return self.name
        elif hasattr(self, 'username'):
            return self.username
        return str(self)

    @property
    def search_image(self):
        """Return the image URL for search results"""
        if hasattr(self, 'image'):
            return self.image
        elif hasattr(self, 'cover_art'):
            return self.cover_art
        elif hasattr(self, 'display_picture'):
            return self.display_picture
        return None

    @property
    def search_description(self):
        """Return the description for search results"""
        if hasattr(self, 'description'):
            return self.description
        elif hasattr(self, 'bio'):
            return self.bio
        return None

class RecentSearch(models.Model):
    """
    Model to store recent searches for a profile
    """
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='recent_searches')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    searched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-searched_at']
        unique_together = ('profile', 'content_type', 'object_id')

class Profile(models.Model, SearchableMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    favorite_genres = models.JSONField(default=list, blank=True)  # Store genres as a list of strings
    reviews = models.IntegerField(default=0)
    friends = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

    def add_recent_search(self, obj):
        """
        Add an object to recent searches
        """
        if isinstance(obj, (Song, Album, Artist, Profile)):
            content_type = ContentType.objects.get_for_model(obj)
            RecentSearch.objects.update_or_create(
                profile=self,
                content_type=content_type,
                object_id=obj.id,
                defaults={'searched_at': timezone.now()}
            )
            # Keep only the 10 most recent searches
            recent_searches = self.recent_searches.all()
            if recent_searches.count() > 10:
                recent_searches.last().delete()

class Artist(models.Model, SearchableMixin):
    name = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    image = models.URLField(max_length=500, blank=True, null=True)
    spotify_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
    
    def calculate_average_rating(self):
        reviews = Review.objects.filter(content_type='artist', content_id=self.id)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.save()

class Album(models.Model, SearchableMixin):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="albums")
    genre = models.CharField(max_length=255)
    release_date = models.DateField()
    cover_art = models.URLField(max_length=500, blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    tracks = models.PositiveIntegerField(default=0)
    spotify_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

    def calculate_average_rating(self):
        reviews = Review.objects.filter(content_type='album', content_id=self.id)
        print(f"Number of reviews: {reviews.count()}")

        for review in reviews:
            print(f"Review score: {review.rating}")
            print(f"Review text: {review.review_text}")
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.save()

class Song(models.Model, SearchableMixin):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="songs")
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="songs", blank=True, null=True)
    duration = models.DurationField()
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    image = models.URLField(max_length=500, blank=True, null=True)
    spotify_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

    def calculate_average_rating(self):
        reviews = Review.objects.filter(content_type='song', content_id=self.id)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.save()

class Review(models.Model):
    CONTENT_CHOICES = [
        ('album', 'Album'),
        ('track', 'Track'),
        ('artist', 'Artist'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    content_type = models.CharField(max_length=10, choices=CONTENT_CHOICES)
    content_id = models.PositiveIntegerField()  # ID of the album, song, or artist being reviewed
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.content_type} ({self.content_id})"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    content_type = models.CharField(max_length=10, choices=[('album', 'Album'), ('song', 'Song'), ('artist', 'Artist')])
    content_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'content_type', 'content_id')
        
    def __str__(self):
        return f"{self.user.username}'s favorite {self.content_type}: {self.content_id}"






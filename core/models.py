from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    favorite_genres = models.JSONField(default=list, blank=True)  # Store genres as a list of strings

    def __str__(self):
        return self.user.username

class Artist(models.Model):
    name = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)

    def __str__(self):
        return self.name
    
    def calculate_average_rating(self):
        reviews = Review.objects.filter(content_type='artist', content_id=self.id)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.save()

class Album(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="albums")
    genre = models.CharField(max_length=255)
    release_date = models.DateField()
    cover_art = models.ImageField(upload_to="album_covers/", blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)

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

class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="songs")
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="songs", blank=True, null=True)
    duration = models.DurationField()
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)

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
        ('song', 'Song'),
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






from django.contrib import admin
from .models import Profile, Artist, Album, Song, Review

admin.site.register(Profile)
admin.site.register(Artist)
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Review)

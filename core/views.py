from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Profile, Artist, Album, Song, Review, Favorite
from .serializers import ProfileSerializer, ArtistSerializer, AlbumSerializer, SongSerializer, ReviewSerializer, FavoriteSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Avg
from rest_framework.decorators import action

class HelloWorldView(APIView):
    def get(self, request):
        return Response({"message": "Hello, world!"})

class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class ArtistViewSet(ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

class AlbumViewSet(ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['genre', 'release_date']
    search_fields = ['title', 'artist__name']
    

class SongViewSet(ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer

class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Save the review instance
        review = serializer.save(user=self.request.user)

        # Update average rating for the related content
        if review.content_type == 'album':
            album = Album.objects.get(id=review.content_id)
            album.calculate_average_rating()
        elif review.content_type == 'song':
            song = Song.objects.get(id=review.content_id)
            song.calculate_average_rating()
        elif review.content_type == 'artist':
            artist = Artist.objects.get(id=review.content_id)
            artist.calculate_average_rating()

class AlbumReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        album_id = self.kwargs['pk']
        return Review.objects.filter(
            content_type='album',
            content_id=album_id
        )

class FavoriteViewSet(ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'], url_path='albums', url_name='albums')
    def albums(self, request):
        favorites = self.get_queryset().filter(content_type='album')
        return Response(FavoriteSerializer(favorites, many=True).data)

    @action(detail=False, methods=['GET'], url_path='songs', url_name='songs')
    def songs(self, request):
        favorites = self.get_queryset().filter(content_type='song')
        return Response(FavoriteSerializer(favorites, many=True).data)

    @action(detail=False, methods=['GET'], url_path='artists', url_name='artists')
    def artists(self, request):
        favorites = self.get_queryset().filter(content_type='artist')
        return Response(FavoriteSerializer(favorites, many=True).data)

class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorite_genres = request.user.profile.favorite_genres
        recommendations = Album.objects.filter(genre__in=favorite_genres).annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:10]
        serializer = AlbumSerializer(recommendations, many=True)
        return Response(serializer.data)
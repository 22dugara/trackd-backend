from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Profile, Artist, Album, Song, Review, Favorite, RecentSearch
from .serializers import ProfileSerializer, ArtistSerializer, AlbumSerializer, SongSerializer, ReviewSerializer, FavoriteSerializer, RecentSearchSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Avg
from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

class HelloWorldView(APIView):
    def get(self, request):
        return Response({"message": "Hello, world!"})

class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the profile of the authenticated user.
        """
        profile = self.get_queryset().filter(user=request.user).first()
        if profile:
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        return Response({"error": "Profile not found"}, status=404)

    @action(detail=False, methods=['GET'])
    def recent_searches(self, request):
        """
        Returns the authenticated user's recent searches
        """
        profile = request.user.profile
        recent_searches = profile.recent_searches.all()
        serializer = RecentSearchSerializer(recent_searches, many=True, context={'request': request})
        return Response(serializer.data)

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

class SearchView(APIView):
    """
    Search endpoint that returns results across different content types
    """
    def get(self, request):
        search_query = request.query_params.get('q', '')
        content_type = request.query_params.get('filter', None)
        
        valid_content_types = ['Album', 'Song', 'Artist', 'Profile']
        if content_type and content_type not in valid_content_types:
            return Response(
                {'error': f'Invalid filter type. Must be one of: {", ".join(valid_content_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For testing: Add superuser 'aryan' to recent searches
        if request.user.is_authenticated:
            User = get_user_model()
            test_user = get_object_or_404(User, username='aryan')
            test_profile = test_user.profile
            request.user.profile.add_recent_search(test_profile)

        results = {
            'query': search_query,
            'filter': content_type,
            'results': []
        }
        
        return Response(results)
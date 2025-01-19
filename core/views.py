from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Profile, Artist, Album, Song, Review, Favorite, RecentSearch
from .serializers import ProfileSerializer, ArtistSerializer, AlbumSerializer, SongSerializer, ReviewSerializer, FavoriteSerializer, RecentSearchSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Avg, Q
from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from .spotify import *

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
    #Improve recommendation algorithm
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
        
        # Initialize results
        results = {
            'query': search_query,
            'profiles': [], # Top 10 profiles
            'albums': [],   # Albums from Spotify
            'artists': [],  # Artists from Spotify
            'songs': []     # Songs from Spotify
        }

        # Search profiles
        profile_results = Profile.objects.filter(
            Q(user__username__icontains=search_query)             
        ).select_related('user')[:10]  # Limit to top 10 results

        # Add profile results to response
        profile_serializer = ProfileSerializer(
            profile_results, 
            many=True,
            context={'request': request}  # Include request for full URLs
        )
        results['profiles'] = profile_serializer.data
        
        # Get Spotify results for other content types
        token_response = get_spotify_token()
        if not token_response:
            return Response(
                {'error': 'Failed to authenticate with Spotify API'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        access_token = token_response
        spotify_results = search_spotify(search_query, None, access_token)
        
        # Add Spotify results to response
        results.update(spotify_results)  # This adds albums, songs, and artists from Spotify
        
        return Response(results)

class AddSearchView(APIView):
    """
    Add a searched item to user's recent searches
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Get query parameters
            content_type = request.query_params.get('content_type')
            content_id = request.query_params.get('content_id')
            print("Adding Search")
            # Validate parameters
            if not content_type or not content_id:
                return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create the searchable object
            searchable = None
            
            if content_type in ['Album', 'Song', 'Artist']:
                # Check if it exists in our database
                model = {
                    'Album': Album,
                    'Song': Song,
                    'Artist': Artist
                }[content_type]
                
                searchable = model.objects.filter(spotify_uri=content_id).first()
                print(searchable)
                
                # If not in database, create it from Spotify
                if not searchable:
                    print("Not in database")
                    spotify_type = content_type.lower()
                    if spotify_type == 'song':
                        spotify_type = 'track'
                        
                    token_response = get_spotify_token()
                    if not token_response:
                        return Response({"error": "Spotify API error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        
                    searchable = create_resource(spotify_type, content_id, token_response)
                    
            elif content_type == 'Profile':
                searchable = Profile.objects.filter(id=content_id).first()
                
            # Add to recent searches if we found or created a searchable object
            if searchable:
                request.user.profile.add_recent_search(searchable)
                return Response({"message": "Search added successfully"}, status=status.HTTP_200_OK)
            
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to register
    parser_classes = (MultiPartParser, FormParser)  # Add support for file uploads

    def post(self, request):
        User = get_user_model()
        
        # Extract data from request
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        display_picture = request.data.get('display_picture')  # Optional profile picture
        bio = request.data.get('bio')  # Optional bio
        
        # Validate required fields
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            
            # Create associated profile with optional fields
            profile = Profile.objects.create(
                user=user,
                bio=bio
            )
            
            # Handle profile picture if provided
            if display_picture:
                profile.display_picture = display_picture
                profile.save()

            return Response({
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username,
                'bio': profile.bio,
                'display_picture': request.build_absolute_uri(profile.display_picture.url) if profile.display_picture else None
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
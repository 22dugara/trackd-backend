from rest_framework.routers import DefaultRouter
from .views import (ProfileViewSet, ArtistViewSet, AlbumViewSet, SongViewSet, 
                   ReviewViewSet, AlbumReviewsView, FavoriteViewSet, 
                   RecommendationView, SearchView, AddSearchView, RegisterView)
from django.urls import path

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'artists', ArtistViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'songs', SongViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = router.urls + [
    path('albums/<int:pk>/reviews/', AlbumReviewsView.as_view(), name='album-reviews'),
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
    path('search/', SearchView.as_view(), name='search'),
    path('search/add/', AddSearchView.as_view(), name='search-add'),
    path('register/', RegisterView.as_view(), name='register'),
]


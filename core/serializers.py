from rest_framework import serializers
from .models import Profile, Artist, Album, Song, Review, Favorite, RecentSearch
from rest_framework.serializers import ImageField
from django.contrib.contenttypes.models import ContentType

class AbsoluteImageField(ImageField):
    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get('request', None)
        if request:
            return request.build_absolute_uri(value.url)
        return super().to_representation(value)

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'first_name', 'last_name', 'display_picture', 'bio', 'favorite_genres', 'reviews', 'friends']


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'

class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'
        
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, data):
        user = self.context['request'].user
        content_type = data['content_type']
        content_id = data['content_id']

        # Try to get existing review
        existing_review = Review.objects.filter(
            user=user, 
            content_type=content_type, 
            content_id=content_id
        ).first()

        # Store the existing review (if any) to use in create/update
        self.context['existing_review'] = existing_review
        return data

    def create(self, validated_data):
        existing_review = self.context.get('existing_review')
        
        if existing_review:
            # Update existing review instead of creating new one
            for key, value in validated_data.items():
                setattr(existing_review, key, value)
            existing_review.save()
            return existing_review
            
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

class RecentSearchSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = RecentSearch
        fields = ['id', 'title', 'image', 'description', 'type', 'searched_at']

    def get_title(self, obj):
        return obj.content_object.search_title

    def get_image(self, obj):
        return obj.content_object.search_image.url if obj.content_object.search_image else None

    def get_description(self, obj):
        return obj.content_object.search_description

    def get_type(self, obj):
        return obj.content_type.model.capitalize()



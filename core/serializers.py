from rest_framework import serializers
from .models import Profile, Artist, Album, Song, Review, Favorite

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

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



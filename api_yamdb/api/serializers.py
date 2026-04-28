from rest_framework import serializers
from reviews.models import Comment, Review


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    class Meta:
        model = Review
        fields = '__all__'

    def validate(self, data):
        if self.context['request'].method == 'POST':
            if Review.objects.filter(
                title_id=self.context['view'].kwargs['title_id'],
                author=self.context['request'].user
            ).exists():
                raise serializers.ValidationError('Вы уже оставляли отзыв.')
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

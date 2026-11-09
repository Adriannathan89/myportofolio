from urllib.parse import urlsplit

from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import (
    Award,
    Experience,
)


class AwardSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Award
        fields = ['id', 'title', 'description', 'thumbnail', 'issuer', 'date_received',
                  'starred_by', 'star_count', 'is_starred', 'starred_by_names']
        read_only_fields = ['id', 'starred_by', 'star_count', 'is_starred', 'starred_by_names']

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('Title cannot be empty.')
        return value

    def validate_description(self, value):
        return strip_tags(value).strip() if value else value

    def validate_issuer(self, value):
        return strip_tags(value).strip() if value else value

    def validate_thumbnail(self, value):
        value = strip_tags(value).strip() if value else value
        if not value:
            return value
        if value.startswith('/') and not value.startswith('//') and '\\' not in value:
            return value
        try:
            parsed = urlsplit(value)
        except ValueError as error:
            raise serializers.ValidationError('Use a local path or an http(s) URL.') from error
        if parsed.scheme.lower() not in {'http', 'https'} or not parsed.netloc or '\\' in value:
            raise serializers.ValidationError('Use a local path or an http(s) URL.')
        return value

    def get_star_count(self, obj):
        return len(obj.starred_by.all())

    def get_is_starred(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and request.user in obj.starred_by.all())

    def get_starred_by_names(self, obj):
        return ', '.join(user.username for user in obj.starred_by.all())

class ExperienceSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Experience
        fields = ['id', 'title', 'description', 'category', 'keyfeatures', 'start_at', 'ended_at',
                  'created_at', 'updated_at', 'is_ongoing', 'category_display', 'star_count', 'is_starred']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_ongoing', 'category_display', 'star_count', 'is_starred']

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.starred_by.filter(pk=request.user.pk).exists())

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('Title cannot be empty.')
        return value

    def validate_description(self, value):
        return strip_tags(value).strip() if value else value

    def validate_category(self, value):
        if value not in dict(Experience.EXPERIENCE_ENUM):
            raise serializers.ValidationError('Invalid category.')
        return value

    def validate_keyfeatures(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Key features must be a list.')
        if any(not isinstance(item, str) for item in value):
            raise serializers.ValidationError('Each key feature must be text.')
        return [cleaned for item in value if (cleaned := strip_tags(item).strip())]

    def validate(self, attrs):
        start_at = attrs.get('start_at', self.instance.start_at if self.instance else None)
        ended_at = attrs.get('ended_at', self.instance.ended_at if self.instance else None)
        if start_at and ended_at and start_at > ended_at:
            raise serializers.ValidationError('Start date cannot be after end date.')
        return attrs

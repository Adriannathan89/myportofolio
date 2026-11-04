from urllib.parse import urlsplit

from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import Award


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

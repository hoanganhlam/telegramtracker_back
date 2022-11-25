from media import models
from rest_framework import serializers
from sorl.thumbnail import get_thumbnail


class SimpleMediaSerializer(serializers.ModelSerializer):
    sizes = serializers.SerializerMethodField()

    class Meta:
        model = models.Media
        fields = ['sizes']

    def get_sizes(self, instance):
        if instance.path:
            return {
                "thumb_24": get_thumbnail(instance.path, '24x24', crop='center', quality=100).url,
                "thumb_128": get_thumbnail(instance.path, '128x128', crop='center', quality=100).url
            }
        else:
            return {}


class MediaSerializer(serializers.ModelSerializer):
    sizes = serializers.SerializerMethodField()

    class Meta:
        model = models.Media
        fields = '__all__'
        extra_fields = ['sizes']

    def get_field_names(self, declared_fields, info):
        expanded_fields = super(MediaSerializer, self).get_field_names(declared_fields, info)

        if getattr(self.Meta, 'extra_fields', None):
            return expanded_fields + self.Meta.extra_fields
        else:
            return expanded_fields

    def get_sizes(self, instance):
        if instance.path:
            return {
                "thumb_24": get_thumbnail(instance.path, '24x24', crop='center', quality=100).url,
                "thumb_128": get_thumbnail(instance.path, '128x128', crop='center', quality=100).url
            }
        else:
            return {}

    def to_representation(self, instance):
        return super(MediaSerializer, self).to_representation(instance)

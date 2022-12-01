from main import models
from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]

    def to_representation(self, instance):
        return super(UserSerializer, self).to_representation(instance)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Account
        fields = ["tg_name", "tg_username", "photo"]


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = ["name", "id_string", "taxonomy"]

    def to_representation(self, instance):
        return super(PropertySerializer, self).to_representation(instance)


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Snapshot
        fields = [
            "date",
            "post_id",
            "members",
            "online",
            "views",
            "replies",
            "messages"
        ]

    def to_representation(self, instance):
        return super(SnapshotSerializer, self).to_representation(instance)


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Request
        fields = ["user", "body"]

    def to_representation(self, instance):
        self.fields["user"] = UserSerializer(read_only=True)
        return super(RequestSerializer, self).to_representation(instance)


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Room
        fields = [
            "id_string", "name", "photo", "statistics", "is_group", "created",
            "views", "members", "online"
        ]


class DetailRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Room
        fields = [
            "id",
            "id_string",
            "name",
            "desc",
            "properties",
            "statistics",
            "photo", "created",
            "members", "online", "views", "messages"
        ]

    def to_representation(self, instance):
        self.fields["properties"] = PropertySerializer(many=True)
        self.fields["participants"] = ParticipantSerializer(many=True)
        return super(DetailRoomSerializer, self).to_representation(instance)


class RoomCrawlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Room
        fields = ["id_string", "last_post_id"]

    def to_representation(self, instance):
        return super(RoomCrawlSerializer, self).to_representation(instance)


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Participant
        fields = ["id", "account", "roles"]

    def to_representation(self, instance):
        self.fields["account"] = AccountSerializer()
        return super(ParticipantSerializer, self).to_representation(instance)


class StickerItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StickerItem
        fields = [
            "tg_id",
            "path"
        ]


class StickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sticker
        fields = [
            "id_string",
            "name",
            "id",
            "tg_id",
            "desc",
            "tags",
            "count",
            "is_archived",
            "is_official",
            "is_animated",
            "is_video",
            "sticker_items"
        ]

    def to_representation(self, instance):
        self.fields["sticker_items"] = StickerItemSerializer(many=True)
        return super(StickerSerializer, self).to_representation(instance)

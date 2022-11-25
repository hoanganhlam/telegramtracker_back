from main import models
from media.api.serializers import MediaSerializer
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
        fields = ["tg_name", "tg_username", "media"]

    def to_representation(self, instance):
        self.fields["media"] = MediaSerializer()
        return super(AccountSerializer, self).to_representation(instance)


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
            "id_string", "name", "media", "statistics", "is_group", "created",
            "views", "members", "online"
        ]

    def to_representation(self, instance):
        self.fields["media"] = MediaSerializer()
        return super(RoomSerializer, self).to_representation(instance)


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
            "media", "created",
            "members", "online", "views", "messages"
        ]

    def to_representation(self, instance):
        self.fields["media"] = MediaSerializer(read_only=True)
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

from django.db import models
from base.interface import BaseModel, HasIDString
from media.models import Media
from django.utils import timezone
from django.contrib.auth.models import User


# Create your models here.
class Property(BaseModel, HasIDString):
    desc = models.CharField(max_length=600, blank=True, null=True)
    taxonomy = models.CharField(max_length=10, default="category")

    class Meta:
        unique_together = [['id_string', 'taxonomy']]


class Account(BaseModel, HasIDString):
    tg_id = models.CharField(max_length=100, db_index=True)
    tg_username = models.CharField(max_length=256, null=True, blank=True)
    tg_name = models.CharField(max_length=256, null=True, blank=True)
    user = models.ForeignKey(User, related_name="accounts", on_delete=models.SET_NULL, null=True, blank=True)
    media = models.ForeignKey(Media, related_name="accounts", on_delete=models.SET_NULL, null=True, blank=True)
    raw = models.JSONField(null=True, blank=True)
    joined = models.DateTimeField(null=True, blank=True)


class Room(BaseModel):
    tg_id = models.CharField(max_length=100, db_index=True)
    batch = models.IntegerField(default=1)

    name = models.CharField(max_length=200, null=True, blank=True)
    id_string = models.CharField(max_length=200, db_index=True, unique=True)
    desc = models.TextField(max_length=500, null=True, blank=True)
    properties = models.ManyToManyField(Property, related_name="rooms", blank=True)

    statistics = models.JSONField(null=True, blank=True)
    members = models.IntegerField(default=0)
    online = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    messages = models.IntegerField(default=0)

    is_group = models.BooleanField(null=True, blank=True)
    media = models.ForeignKey(Media, related_name="rooms", on_delete=models.SET_NULL, null=True, blank=True)
    associate = models.ForeignKey(
        "self", related_name="associated_rooms", on_delete=models.SET_NULL, null=True,
        blank=True
    )
    last_post_id = models.IntegerField(null=True, blank=True)
    last_crawl = models.DateTimeField(null=True, blank=True)

    def cache_statistic(self):
        if self.statistics is None:
            self.statistics = {
                "members_24h": 0,
                "online_24h": 0,
                "subscribers_24h": 0,
                "views_24h": 0,
            }


class Participant(BaseModel):
    room = models.ForeignKey(Room, related_name="participants", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, related_name="participants", on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    rank = models.CharField(default="member", null=True, blank=True, max_length=50)
    roles = models.JSONField(null=True, blank=True)

    inviter = models.ForeignKey(
        Account, related_name="inviter_participants",
        on_delete=models.SET_NULL, null=True, blank=True
    )
    promoter = models.ForeignKey(
        Account, related_name="promoter_participants",
        on_delete=models.SET_NULL, null=True, blank=True
    )


class Snapshot(BaseModel):
    room = models.ForeignKey(Room, related_name="snapshots", on_delete=models.CASCADE)
    post_id = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    date_range = models.CharField(default="1h", max_length=3)

    members = models.IntegerField(default=0)
    online = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    messages = models.IntegerField(default=0)
    replies = models.IntegerField(default=0)


class Request(BaseModel):
    room = models.ForeignKey(Room, related_name="requests", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="requests", on_delete=models.CASCADE)
    body = models.TextField(max_length=500, null=True, blank=True)

import datetime
import asyncio
import re
import os
from typing import Union
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from base import pagination
from . import serializers
from main import models
from media.models import Media
from django_filters import rest_framework as filters
from django_filters import DateTimeFromToRangeFilter
from utils.telegram import Telegram, get_batch
from asgiref.sync import sync_to_async

from pyrogram.types import Photo
from pyrogram.raw.types.messages import ChatFull
from pyrogram.raw import functions
from pyrogram.errors.exceptions.see_other_303 import FileMigrate
from pyrogram.raw.types import InputPeerPhotoFileLocation, InputPeerChannel, \
    ChatPhoto, ChannelParticipantsAdmins, InputChannel, User, UserProfilePhoto

MEDIA_PATH = "files/media"


def make_account(item):
    try:
        account = models.Account.objects.get(tg_id=item["id"])
        if not account.tg_username or not account.tg_name or not account.raw or not account.joined:
            if account.tg_username is None and item.get("username"):
                account.tg_username = item["username"]
            if account.tg_name is None and item.get("username"):
                account.tg_name = item["username"]
            if account.raw is None and item.get("username"):
                account.raw = item
            if account.joined is None and item.get("joined"):
                account.joined = datetime.datetime.fromtimestamp(item["joined"], tz=timezone.utc)
            account.save()
    except models.Account.DoesNotExist:
        account = models.Account.objects.create(
            tg_id=item["id"],
            tg_name=item.get("username"),
            tg_username=item.get("username"),
            raw=item,
            joined=datetime.datetime.fromtimestamp(item.get("joined"), tz=timezone.utc) if item.get("joined") else None
        )
    return account


def make_room(data):
    room = models.Room.objects.filter(tg_id=data["id"]).first()
    if room is None:
        batch = 1
        for n in range(200):
            if models.Room.objects.filter(batch=batch).count() > 50:
                batch = n
                break
        room = models.Room.objects.create(
            tg_id=data["id"],
            id_string=data["room"] if data.get("title") else data["id"],
            name=data.get("title"),
            desc=data.get("desc"),
            batch=batch
        )
    elif data.get("title") and room.id_string == room.tg_id:
        media = None
        if data.get("image"):
            media = Media.objects.save_url(data["image"])
        room.id_string = data.get("room")
        room.media = media
        room.name = data.get("title")
        room.desc = data.get("desc")
        room.save()
    return room


def check_last(room, post_id, newest, date):
    try:
        if post_id:
            latest = models.Snapshot.objects.filter(
                room=room,
                post_id=post_id
            ).order_by("-date")[1]
        else:
            latest = models.Snapshot.objects.filter(
                room=room,
            ).order_by("-date")[1]
    except Exception as e:
        latest = None
    if latest:
        fields = ["members", "online", "views", "messages"]
        ranges = ["5m", "30m", "1h", "1d", "1M", "1y"]
        if room.statistics is None:
            room.statistics = {}
            for f in fields:
                for r in ranges:
                    room.statistics["{}_{}".format(f, r)] = 0
        if latest.date.minute + 1 < date.minute:
            latest.date_range = "1m"
            for f in fields:
                room.statistics["{}_1m".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date.minute + 5 < date.minute:
            latest.date_range = "5m"
            for f in fields:
                room.statistics["{}_5m".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date.minute + 30 < date.minute:
            latest.date_range = "30m"
            for f in fields:
                room.statistics["{}_30m".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date.hour < date.hour:
            latest.date_range = "1h"
            for f in fields:
                room.statistics["{}_1h".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date.day < date.day:
            latest.date_range = "1d"
            for f in fields:
                room.statistics["{}_1d".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date.month < date.month:
            latest.date_range = "1M"
            for f in fields:
                room.statistics["{}_1M".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date.year < date.year:
            latest.date_range = "1y"
            for f in fields:
                room.statistics["{}_1y".format(f)] = int(getattr(newest, f)) - int(getattr(latest, f))
        if latest.date_range:
            latest.save()
        room.save()


class SnapshotFilter(filters.FilterSet):
    date = DateTimeFromToRangeFilter()

    class Meta:
        model = models.Snapshot
        fields = [
            'post_id',
            'room__id_string',
            'date'
        ]


class RoomFilter(filters.FilterSet):
    class Meta:
        model = models.Room
        fields = [
            'properties__taxonomy',
            'properties__id_string',
            'is_group'
        ]


class PropertyViewSet(viewsets.GenericViewSet, generics.ListCreateAPIView, generics.RetrieveAPIView):
    models = models.Property
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.PropertySerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['name']
    lookup_field = 'id_string'


class SnapshotViewSet(viewsets.GenericViewSet, generics.ListCreateAPIView):
    models = models.Snapshot
    queryset = models.objects.order_by('-date')
    serializer_class = serializers.SnapshotSerializer
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    filterset_class = SnapshotFilter
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        q = Q()
        if request.GET.get("room__id_string"):
            q = q & Q(post_id__isnull=True)
        if request.GET.get("date_range"):
            if request.GET.get("date_range") == "1y":
                q = q & Q(date_range="1y")
            elif request.GET.get("date_range") == "1m":
                q = q & Q(date_range__in=["1y", "1m"])
            elif request.GET.get("date_range") == "1d":
                q = q & Q(date_range__in=["1y", "1m", "1d"])
            elif request.GET.get("date_range") == "1h":
                q = q & Q(date_range__in=["1y", "1m", "1d", "1h"])
            elif request.GET.get("date_range") == "30m":
                q = q & Q(date_range__in=["1y", "1m", "1d", "1h", "30m"])

        queryset = self.filter_queryset(self.get_queryset()).filter(q)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RequestViewSet(viewsets.GenericViewSet, generics.ListCreateAPIView):
    models = models.Request
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.RequestSerializer
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'


class ParticipantViewSet(viewsets.GenericViewSet, generics.ListCreateAPIView):
    models = models.Participant
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.ParticipantSerializer
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'


class RoomViewSet(viewsets.GenericViewSet, generics.ListCreateAPIView, generics.RetrieveAPIView):
    models = models.Room
    queryset = models.objects.order_by('-members')
    serializer_class = serializers.DetailRoomSerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter, filters.DjangoFilterBackend]
    filterset_class = RoomFilter
    search_fields = ['name']
    lookup_field = 'id_string'

    def list(self, request, *args, **kwargs):
        self.serializer_class = serializers.RoomSerializer
        q = Q()
        if request.GET.get("batch"):
            self.serializer_class = serializers.RoomCrawlSerializer
            now = timezone.now()
            q = (Q(last_crawl__isnull=True) | Q(last_crawl__lte=now - datetime.timedelta(minutes=1))) & Q(
                batch=request.GET.get("batch"))
        queryset = self.filter_queryset(self.get_queryset()).filter(q)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StickerViewSet(viewsets.GenericViewSet, generics.ListCreateAPIView, generics.RetrieveAPIView):
    models = models.Sticker
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.StickerSerializer
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'id_string'


@sync_to_async
def save_room(chat_full: ChatFull):
    full_chat = chat_full.full_chat
    chat = None
    chat_linked = None
    for item in chat_full.chats:
        if item.id == full_chat.id:
            chat = item
        elif full_chat.linked_chat_id == item.id:
            chat_linked = item
    if chat is None:
        return None
    room = models.Room.objects.filter(tg_id=full_chat.id).first()
    if room is None:
        room = models.Room.objects.create(
            tg_id=chat.id,
            id_string=chat.username,
            name=chat.title,
            batch=get_batch(),
            desc=full_chat.about
        )
    elif room.desc is None:
        room.desc = full_chat.about
    if chat_linked and chat_linked.username:
        associate, _ = models.Room.objects.get_or_create(
            tg_id=chat_linked.id,
            defaults={
                "id_string": chat_linked.username,
                "name": chat_linked.title,
                "batch": get_batch(),
                "access_hash": chat_linked.access_hash
            }
        )
        room.associate = associate
    if room.meta is None:
        room.meta = {}
    room.meta["can_view_participants"] = full_chat.can_view_participants
    room.meta["can_set_username"] = full_chat.can_set_username
    room.meta["can_set_stickers"] = full_chat.can_set_stickers
    room.meta["can_set_location"] = full_chat.can_set_location
    room.meta["can_view_stats"] = full_chat.can_view_stats
    room.meta["can_view_stats"] = full_chat.can_view_stats
    room.meta["broadcast"] = chat.broadcast
    room.meta["verified"] = chat.verified
    room.meta["megagroup"] = chat.megagroup
    room.meta["restricted"] = chat.restricted
    room.meta["signatures"] = chat.signatures
    room.meta["scam"] = chat.scam
    room.meta["join_request"] = chat.join_request
    room.meta["gigagroup"] = chat.gigagroup
    room.meta["fake"] = chat.fake
    room.members = full_chat.participants_count or 0
    room.online = full_chat.online_count or 0
    room.is_group = not chat.broadcast
    room.access_hash = chat.access_hash
    room.save()
    return room


@sync_to_async
def save_photo(
        self, photo: Union[Photo, ChatPhoto, UserProfilePhoto],
        path="room", extension="png", peer=None
):
    pa = "{}/{}.{}".format(path, photo.id if hasattr(photo, "id") else photo.photo_id, extension)
    fn = "{}/{}".format(MEDIA_PATH, pa)
    if not os.path.exists("{}/{}".format(MEDIA_PATH, path)):
        os.makedirs("{}/{}".format(MEDIA_PATH, path))
    file_id = None
    if hasattr(photo, "file_id"):
        file_id = photo.file_id
    elif hasattr(photo, "id"):
        file_id = Photo._parse(self.app, photo).file_id
    if file_id:
        file = self.app.download_media(file_id, in_memory=True)
        with open(fn, "wb") as binary_file:
            binary_file.write(bytes(file.getbuffer()))
    elif hasattr(photo, "photo_id"):
        try:
            info = self.app.invoke(
                functions.upload.GetFile(
                    location=InputPeerPhotoFileLocation(
                        photo_id=photo.photo_id,
                        peer=peer,
                        big=True
                    ),
                    offset=0,
                    limit=1024 * 1024
                )
            )
            with open(fn, "wb") as binary_file:
                binary_file.write(info.bytes)
        except FileMigrate as e:
            print(e.MESSAGE)
            return None
    return pa


@api_view(['GET'])
def get_chat(request):
    async def main(username):
        tg = Telegram()
        async with tg.app:
            peer_id = re.sub(r"[@+\s]", "", username.lower())
            peer = await tg.app.invoke(
                functions.contacts.ResolveUsername(
                    username=peer_id
                )
            )
            input_channel = InputChannel(
                channel_id=peer.chats[0].id,
                access_hash=peer.chats[0].access_hash
            )
            info = await tg.app.invoke(
                functions.channels.GetFullChannel(
                    channel=input_channel
                )
            )
            r = await tg.app.invoke(
                functions.messages.GetHistory(
                    peer=InputPeerChannel(
                        channel_id=peer.chats[0].id,
                        access_hash=peer.chats[0].access_hash
                    ),
                    offset_id=0,
                    offset_date=0,
                    add_offset=0,
                    limit=1,
                    max_id=0,
                    min_id=0,
                    hash=0
                )
            )
            return await save_room(info), r.count

    un = request.GET.get("username")
    room = models.Room.objects.filter(id_string=un)
    if room is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        room, count = loop.run_until_complete(main(un))
        if room:
            room.messages = count
            if room.last_post_id == 0 or room.last_post_id is None:
                room.last_post_id = room.messages
                room.save()
        loop.close()
    return Response(serializers.DetailRoomSerializer(room).data)


@api_view(['GET'])
def get_posts(request):
    page_size = 6
    page = int(request.GET.get("page", "1"))
    start = page * page_size - page_size
    end = start + page_size
    snapshots = models.Snapshot.objects.filter(
        room__id_string=request.GET.get("room__id_string"),
        post_id__isnull=False
    ).order_by("-post_id", "-date").distinct("post_id")[start: end]
    return Response(serializers.SnapshotSerializer(snapshots, many=True).data)


@api_view(['POST'])
def import_room(request):
    if request.data["pwd"] == "NINOFATHER":
        room = make_room(request.data)
        date = datetime.datetime.fromtimestamp(request.data["date"] / 1000, tz=timezone.utc)
        # if room.last_crawl and date.timestamp() < (room.last_crawl + datetime.timedelta(hours=1)).timestamp():
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

        # associate
        if request.data.get("associate") and (
                room.associate is None or room.associate.tg_id != request.data["associate"]):
            room.associate = make_room({"id": request.data["associate"]})

        # check
        if room.name != request.data.get("title"):
            if room.media is None and request.data["image"]:
                room.media = Media.objects.save_url(request.data["image"])
            room.name = request.data.get("title")
            room.desc = request.data.get("desc")
        if room.id_string == request.data["id"]:
            room.id_string = request.data["room"]
        if room.tg_id is None:
            room.tg_id = request.data["id"]

        room.last_crawl = date
        if room.is_group is None and "is_group" in request.data:
            room.is_group = request.data["is_group"]

        # statistics
        room.members = request.data.get("members", 0)
        room.online = request.data.get("online", 0)
        room.views = request.data.get("views", 0)
        room.messages = request.data.get("messages", 0)
        room.save()

        # snapshot

        newest = models.Snapshot.objects.create(
            room=room,
            date=date,
            members=request.data.get("members", 0),
            online=request.data.get("online", 0),
            views=request.data.get("views", 0),
            messages=request.data.get("messages", 0),
        )
        check_last(room=room, post_id=None, newest=newest, date=date)

        # participants
        raw_id_participants = list(map(lambda x: x["id"], request.data["participants"]))
        q = ~Q(account__tg_id__in=raw_id_participants)
        room.participants.filter(q).delete()
        current_id_participants = room.participants.all().values_list("account__tg_id", flat=True)
        raw_id_participants = [a for a in raw_id_participants if a not in current_id_participants]
        for item in request.data["participants"]:
            if item["id"] in raw_id_participants:
                account = make_account(item)
                p, _ = models.Participant.objects.get_or_create(
                    account=account,
                    room=room
                )
                if item.get("rank"):
                    p.rank = item.get("rank")
                if item.get("roles"):
                    p.roles = item.get("roles")
                if item.get("inviter"):
                    p.inviter = make_account({"id": item.get("inviter")})
                if item.get("promoter"):
                    p.promoter = make_account({"id": item.get("promoter")})
                p.save()

        return Response(status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def import_post(request):
    if request.data["pwd"] == "NINOFATHER":
        room = make_room(request.data["room"])
        for item in request.data["posts"]:
            created = datetime.datetime.fromtimestamp(item["created"], tz=timezone.utc)
            if room.last_post_id is None or room.last_post_id < item["id"]:
                if room.last_post_id is None:
                    room.created = created
                room.last_post_id = item["id"]
                room.messages = item["id"]
                room.views = item.get("views", 0)
                room.save()

            date = datetime.datetime.fromtimestamp(item["date"] / 1000, tz=timezone.utc)
            newest = models.Snapshot.objects.create(
                room=room,
                post_id=item["id"],
                date=date,
                views=item.get("views", 0),
                replies=item.get("replies", 0)
            )
            check_last(room=room, post_id=item["id"], newest=newest, date=date)

            try:
                models.Snapshot.objects.get(
                    room=room,
                    post_id=item["id"],
                    date=created
                )
            except models.Snapshot.DoesNotExist:
                models.Snapshot.objects.create(
                    room=room,
                    post_id=item["id"],
                    date=created,
                    views=0,
                    replies=0
                )
        return Response(status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

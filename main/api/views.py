import datetime
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
        media = None
        if data.get("image"):
            media = Media.objects.save_url(data["image"])
        room = models.Room.objects.create(
            tg_id=data["id"],
            id_string=data["room"] if data.get("title") else data["id"],
            name=data.get("title"),
            desc=data.get("desc"),
            media=media,
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
        # room: 'vietnamtradecoin',
        # id: '1281256891',
        # associate: '1128353406',
        # date: 1668870454046,
        # title: 'TradeCoinVietNam',
        # desc: '',
        # image: '',
        # members: 97416,
        # online: 4915
        # participants: []
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
        print("0_{}".format(room.name))
        room.members = request.data.get("members", 0)
        room.online = request.data.get("online", 0)
        room.views = request.data.get("views", 0)
        room.messages = request.data.get("messages", 0)
        print("1_{}".format(room.name))
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

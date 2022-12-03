import re
import os
import gzip
import time
import zipfile
from django.db.models import Q
from django.utils import timezone
from typing import Union
from pyrogram import Client
from pyrogram.raw import functions
from pyrogram.raw.types import InputStickerSetID, InputPeerPhotoFileLocation, InputMessageID, InputPeerChannel, \
    ChatPhoto, ChannelParticipantsAdmins, InputChannel, User, UserProfilePhoto, \
    InputPeerUser
from pyrogram.raw.types.messages import FoundStickerSets, ChatFull
from pyrogram.raw.types.message import Message
from pyrogram.types import Document, Photo
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import BotMethodInvalid, ChatAdminRequired
from pyrogram.errors.exceptions.see_other_303 import FileMigrate
from main.models import Sticker, StickerItem, Participant, Room, Snapshot, Account

import datetime

MEDIA_PATH = "files/media"

BOTS = [
    "",
    [
        "5808667607:AAEIeKiyY_Ef6snzxIpsRNYofLgvrqSjyuY",
        "5960732338:AAEjFVL8_rjDG-wiZ5UOutHx4zeJUO2pO1w",
        "5487922392:AAEW1R6AEiJlxR1NDuuY0prw_4o_QPIOSTE",
        "5515725190:AAEOG0bap41nxVKQEPmJ-R4-fM_L1CgTBDU",
        "5774315449:AAEfTL5vGlvafSysM567JZuukhjAUMTwlCg",
    ],
    [
        "5197829672:AAELHqovNYF-RjoHgqE-0ZiCj3r2V2_KRPw",
        "5864458684:AAG3qtbyYMEyVLB8_824MRz3TD_hlE3tLLk",
        "5653725878:AAGhOrHmenE9mbE3psi80BhLG0H_z9MhjJU",
        "5645968227:AAEwns7WfUfui7uGPW41S77yarqX7HhZSmA",
        "5892944154:AAFoLbyTZF4bS78cRqxVtfMqsekHWVAiCjA",
        "5633292420:AAG0fsqdUT4Z7cBNwvih168HpdVQtXawCYM",
    ],
    [
        "5931254056:AAHFSc-7f4BMyXlLEgdWywjYyh8vpNFbDG0",
        "5435775441:AAEsLTPhyyi37l-BlWx3TmnisZf270hxvhk",
        "5953540723:AAFLOoqDWWfG-7dwkBWv56OOMcwHFoe3K2c",
        "5725633834:AAFjHeynEgALc7wgiJ1bDTCoiQbCEl-El_c",
        "5631121429:AAHmLfIA1e_AMaNDR7H5OStEkBIHLnZuIgM",
        "5862833945:AAG06pcn5ANXUDm9abmJOx2l47rEwwwrUpM",
    ],
]


class TelegramGreetLimit(Exception):
    pass


def get_batch():
    batch = 1
    for n in range(200):
        if Room.objects.filter(batch=batch).count() > 25:
            batch = n
            break
    return batch


def check_last(room, post_id, newest, date):
    try:
        if post_id:
            latest = Snapshot.objects.filter(
                room=room,
                post_id=post_id
            ).order_by("-date")[1]
        else:
            latest = Snapshot.objects.filter(
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


def zip_folder(folder_path, output_path):
    contents = os.walk(folder_path)
    try:
        zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                zip_file.write(absolute_path, file_name)
    except Exception as e:
        print(e)


def to_x_json(obj):
    out = {}
    attr = dir(obj)
    for att in attr:
        if "__" not in att and att not in ["read", "write", "default", "_", "QUALNAME"]:
            out[att] = getattr(obj, att)
    return out


class Telegram:
    api_id = 9245358
    api_hash = "53530778484f8cab535f87ccc2c4b472"
    apps = []
    bot_index = 0
    batch = 0

    def __init__(self, batch=0):
        self.app = self.make_client(batch)

    def make_client(self, batch=0, bot_index=0):
        self.batch = batch
        name = "my_account"
        bot_token = None
        if batch > 0:
            if bot_index == len(BOTS[batch]):
                bot_index = 0
            self.bot_index = bot_index
            bot_token = BOTS[batch][bot_index]
            name = "my_bot_{}".format(batch)
        return Client(name, api_id=self.api_id, api_hash=self.api_hash, bot_token=bot_token, workdir="pyrogram")

    def remake_client(self):
        self.app.stop()
        self.bot_index = self.bot_index + 1
        print("REGENERATE: {}".format(self.bot_index))
        self.app = self.make_client(batch=self.batch, bot_index=self.bot_index)
        self.app.start()

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

    def get_sticker_packer(self, sticker_id, access_hash):
        test = Sticker.objects.filter(tg_id=sticker_id).first()
        if test:
            return
        try:
            x = self.app.invoke(
                functions.messages.GetStickerSet(
                    stickerset=InputStickerSetID(
                        id=sticker_id,
                        access_hash=access_hash
                    ),
                    hash=0
                )
            )
            sticker = Sticker.objects.create(
                tg_id=x.set.id,
                name=x.set.title,
                id_string=x.set.short_name,
                count=x.set.count,
                is_archived=x.set.archived,
                is_official=x.set.official,
                is_animated=x.set.animated,
                is_video=x.set.videos
            )
            directory = "{}/{}".format(MEDIA_PATH, sticker_id)
            if not os.path.exists(directory):
                os.makedirs(directory)
            for document in x.documents:
                document_parsed = Document._parse(
                    client=self.app,
                    document=document,
                    file_name="{}.png".format(document.id)
                )
                if x.set.videos:
                    extension = "mp4"
                elif x.set.animated:
                    extension = "json"
                else:
                    extension = "webp"
                if extension:
                    file = self.app.download_media(document_parsed.file_id, in_memory=True)
                    fn = "{}/{}.{}".format(directory, document.id, extension)
                    with open(fn, "wb") as binary_file:
                        if x.set.animated:
                            binary_file.write(gzip.decompress(bytes(file.getbuffer())))
                        else:
                            binary_file.write(bytes(file.getbuffer()))
                    StickerItem.objects.get_or_create(
                        tg_id=document.id,
                        defaults={
                            "sticker": sticker,
                            "path": "{}/{}.{}".format(sticker_id, document.id, extension)
                        }
                    )
            zip_folder(folder_path=directory, output_path="{}.zip".format(directory))
        except FloodWait as e:
            if e.value < 100:
                print("Waiting: {}".format(e.value))
                time.sleep(e.value + 3)
                self.get_sticker_packer(sticker_id, access_hash)
            else:
                print("GREET_LIMIT: get_sticker_packer")
                raise TelegramGreetLimit("ENDED")

    def get_message_count(self, input_channel):
        r = self.app.invoke(
            functions.messages.GetHistory(
                peer=input_channel,
                offset_id=0,
                offset_date=0,
                add_offset=0,
                limit=1,
                max_id=0,
                min_id=0,
                hash=0
            )
        )
        return r.count

    def search_sticker(self, query, page_hash=0):
        x = self.app.invoke(
            functions.messages.SearchStickerSets(
                q=query,
                hash=page_hash,
                exclude_featured=False
            )
        )
        if type(x) is FoundStickerSets:
            for item in x.sets:
                self.get_sticker_packer(item.set.id, item.set.access_hash)
            if x.hash != 0:
                self.search_sticker(query, x.hash)

    def get_chat(self, chat):
        try:
            peer_id = re.sub(r"[@+\s]", "", chat.lower())
            peer = self.app.invoke(
                functions.contacts.ResolveUsername(
                    username=peer_id
                )
            )
            input_channel = InputChannel(
                channel_id=peer.chats[0].id,
                access_hash=peer.chats[0].access_hash
            )
            if not input_channel:
                return
            info = self.app.invoke(
                functions.channels.GetFullChannel(
                    channel=input_channel
                )
            )
            # SAVE STICKER
            if info.full_chat.stickerset:
                self.get_sticker_packer(
                    sticker_id=info.full_chat.stickerset.id,
                    access_hash=info.full_chat.stickerset.access_hash
                )
            # SAVE ROOM
            room = self.save_room(info)
            room.messages = self.get_message_count(input_channel)
            if room.last_post_id == 0 or room.last_post_id is None:
                room.last_post_id = room.messages
            room.access_hash = input_channel.access_hash
            room.save()
            now = datetime.datetime.now(tz=timezone.utc)
            newest = Snapshot.objects.create(
                room=room,
                date=now,
                members=info.full_chat.participants_count or 0,
                online=info.full_chat.online_count or 0,
                views=0,
                messages=0,
            )
            check_last(room=room, post_id=None, newest=newest, date=now)
            self.save_participants(input_channel, room)
            if not room.is_group:
                self.get_chat_messages(input_channel, room)
            return room

        except FloodWait as e:
            if e.value < 100:
                print("Waiting: {}".format(e.value))
                time.sleep(e.value + 1)
                return self.get_chat(chat)
            else:
                print("GREET_LIMIT: get_chat")
                self.remake_client()
                return self.get_chat(chat)
        except TelegramGreetLimit:
            print("GREET_LIMIT: get_chat")
            self.remake_client()
            return self.get_chat(chat)

    def save_room(self, chat_full: ChatFull):
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
        room = Room.objects.filter(tg_id=full_chat.id).first()
        if room is None:
            room = Room.objects.create(
                tg_id=chat.id,
                id_string=chat.username,
                name=chat.title,
                batch=get_batch(),
                desc=full_chat.about
            )
        elif room.desc is None:
            room.desc = full_chat.about
        if chat_linked and chat_linked.username:
            associate, _ = Room.objects.get_or_create(
                tg_id=chat_linked.id,
                defaults={
                    "id_string": chat_linked.username,
                    "name": chat_linked.title,
                    "batch": get_batch()
                }
            )
            if not associate.photo and chat_linked.photo:
                associate.photo = self.save_photo(chat_linked.photo, peer=InputPeerChannel(
                    channel_id=chat_linked.id,
                    access_hash=chat_linked.access_hash
                ))
                associate.save()
            room.associate = associate
        if room.meta is None:
            room.meta = {}
        if not room.photo and chat.photo:
            room.photo = self.save_photo(full_chat.chat_photo, peer=InputPeerChannel(
                channel_id=chat.id,
                access_hash=chat.access_hash
            ))
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
        room.save()
        return room

    def save_account(self, user_raw: Union[User, int]):
        account, _ = Account.objects.get_or_create(
            tg_id=user_raw.id if type(user_raw) == User else user_raw
        )
        if type(user_raw) == User:
            if user_raw.photo and not account.photo:
                account.photo = self.save_photo(
                    user_raw.photo, path="account", extension="png",
                    peer=InputPeerUser(
                        user_id=user_raw.id,
                        access_hash=user_raw.access_hash
                    )
                )
            if account.tg_name is None:
                account.tg_name = user_raw.first_name
                if user_raw.last_name:
                    account.tg_name = " " + user_raw.last_name
            if account.tg_username is None:
                account.tg_username = user_raw.username
            if not account.meta:
                account.meta = {}
            account.access_hash = user_raw.access_hash
            account.meta["is_scam"] = user_raw.scam
            account.meta["is_premium"] = user_raw.premium
            account.meta["is_verified"] = user_raw.verified
            account.meta["is_fake"] = user_raw.fake
            account.save()
        return account

    def get_chat_messages(self, chat: InputChannel, room: Room):
        now = datetime.datetime.now(tz=timezone.utc)
        message_ids = []
        start = room.last_post_id
        end = room.last_post_id + 200
        while start < end:
            message_ids.append(InputMessageID(id=start))
            start = start + 1
        try:
            p = self.app.invoke(
                functions.channels.GetMessages(
                    channel=chat,
                    id=message_ids
                ),
            )
            count_message = 0
            for message in p.messages:
                if type(message) == Message:
                    count_message = count_message + 1
                    # HANDLE HERE
                    if room.last_post_id is None or room.last_post_id < message.id:
                        room.last_post_id = message.id
                        room.views = message.views if message.views else 0
                        room.save()
                    Snapshot.objects.get_or_create(
                        room=room,
                        post_id=message.id,
                        date=datetime.datetime.fromtimestamp(message.date, tz=timezone.utc),
                    )
                    newest = Snapshot.objects.create(
                        room=room,
                        post_id=message.id,
                        date=now,
                        views=message.views if message.views else 0,
                        replies=message.replies.replies if message.replies else 0
                    )
                    check_last(room=room, post_id=message.id, newest=newest, date=now)
            if count_message > 1:
                time.sleep(2)
                self.get_chat_messages(chat, room)
            room.save()
        except FloodWait as e:
            if e.value < 100:
                print("Waiting: {}".format(e.value))
                time.sleep(e.value + 1)
                self.get_chat_messages(chat, room)
            else:
                print("GREET_LIMIT: get_chat_messages")
                raise TelegramGreetLimit("ENDED")

    def save_participants(self, chat: InputChannel, room: Room):
        try:
            participants = self.app.invoke(
                functions.channels.GetParticipants(
                    channel=chat,
                    filter=ChannelParticipantsAdmins(),
                    offset=0,
                    limit=10,
                    hash=0
                ),
            )
            room.participants.filter(~Q(account__tg_id__in=list(map(lambda x: x.id, participants.users)))).delete()
            for p in participants.participants:
                for u in participants.users:
                    if p.user_id == u.id:
                        account = self.save_account(u)
                        np, _ = Participant.objects.get_or_create(
                            room=room,
                            account=account,
                            defaults={
                                "roles": to_x_json(p.admin_rights),
                                "rank": p.rank,
                                "is_admin": True,
                                "date": datetime.datetime.fromtimestamp(p.date, tz=timezone.utc) if hasattr(p,
                                                                                                            "date") else timezone.now()
                            }
                        )
                        if hasattr(p, "promoted_by") and p.promoted_by:
                            np.promoter = self.save_account(p.promoted_by)
                            np.save()
        except ChatAdminRequired as e:
            print(e.MESSAGE)
        except FloodWait as e:
            if e.value < 100:
                print("Waiting: {}".format(e.value))
                time.sleep(e.value + 1)
                self.save_participants(chat, room)
            else:
                print("GREET_LIMIT: save_participants")
                raise TelegramGreetLimit("ENDED")

    def monitor(self, batch):
        if batch == 0:
            batch = 1
        for item in Room.objects.filter(batch=batch):
            self.get_chat(chat=item.id_string)
            break

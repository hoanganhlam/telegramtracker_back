from django.core.management.base import BaseCommand
from pyrogram import Client
from pyrogram.raw import functions
from pyrogram.raw.types import InputChannel

api_id = 9245358
api_hash = "53530778484f8cab535f87ccc2c4b472"

app = Client("my_account", api_id=api_id, api_hash=api_hash)


# app.run()

class Command(BaseCommand):
    def handle(self, *args, **options):
        with app:
            x = app.invoke(
                functions.channels.GetMessages(
                    channel=app.resolve_peer("GetFullChannel"),
                    id=[800]
                )
            )
            print(x)

from django.core.management.base import BaseCommand
from utils.telegram import Telegram


class Command(BaseCommand):
    def handle(self, *args, **options):
        tg = Telegram(batch=0)
        tg.app.start()
        # tg.test(sticker_id=110438048860209168, access_hash=-2483522464574001900)
        # tg.search_sticker("duck")
        tg.get_chat("OxalusAnnoucement")
        # tg.search_sticker(query="a", page_hash=0)
        # vietnamtradecoin margintradingTCVN

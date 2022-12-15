from django.core.management.base import BaseCommand
from utils.telegram import Telegram
from main.models import Sticker


class Command(BaseCommand):
    def handle(self, *args, **options):
        tg = Telegram(batch=0)
        tg.app.start()
        for item in Sticker.objects.filter(is_animated=True):
            tg.get_sticker_packer(short_name=item.id_string, force=True)

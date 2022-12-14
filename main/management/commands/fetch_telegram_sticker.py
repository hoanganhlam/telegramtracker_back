from django.core.management.base import BaseCommand
from utils.telegram import Telegram


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--k', type=str)

    def handle(self, *args, **options):
        tg = Telegram(batch=0)
        tg.app.start()
        tg.get_sticker_packer(short_name=options['k'], force=True)

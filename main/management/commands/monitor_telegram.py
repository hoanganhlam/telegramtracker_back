from django.core.management.base import BaseCommand
from utils.telegram import Telegram


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int)

    def handle(self, *args, **options):
        tg = Telegram(batch=options["batch"])
        tg.app.start()
        tg.monitor(options["batch"])

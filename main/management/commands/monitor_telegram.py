import time
from django.core.management.base import BaseCommand
from utils.telegram import Telegram


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int)

    def handle(self, *args, **options):
        tg = Telegram(batch=options["batch"])
        tg.app.start()
        while True:
            start_time = time.time()
            tg.monitor(options["batch"])
            executed = time.time() - start_time
            if executed < 5 * 60:
                time.sleep(5 * 60 - executed)

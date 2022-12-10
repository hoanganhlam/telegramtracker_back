import time
from django.core.management.base import BaseCommand
from utils.telegram import Telegram


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int)
        parser.add_argument('--index', type=int)

    def handle(self, *args, **options):
        tg = Telegram(batch=options["batch"], bot_index=options["index"] if options.get("index") else 0)
        tg.app.start()
        while True:
            start_time = time.time()
            tg.monitor(options["batch"])
            executed = time.time() - start_time
            print("--- %s seconds ---" % executed)
            if executed < 30 * 60:
                time.sleep(30 * 60 - executed)

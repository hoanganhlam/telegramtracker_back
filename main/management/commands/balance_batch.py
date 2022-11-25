import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from main.models import Room


class Command(BaseCommand):
    def handle(self, *args, **options):
        rooms = Room.objects.filter(batch=0)
        # y = 1
        # i = 1
        # r = 0
        for room in rooms:
            room.batch = 4
            room.save()
        #     if y <= 50 * i:
        #         room.batch = i
        #         room.save()
        #         r = r + 1
        #     if r == 50:
        #         r = 0
        #         i = i + 1
        #     y = y + 1

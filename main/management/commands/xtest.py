import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from main.models import Room, Sticker


class Command(BaseCommand):
    def handle(self, *args, **options):
        for item in Room.objects.all():
            item.id_string = item.id_string.lower()
            item.save()
        for item in Sticker.objects.all():
            item.id_string = item.id_string.lower()
            item.save()

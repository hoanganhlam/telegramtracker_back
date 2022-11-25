from django.core.management.base import BaseCommand
from apps.media.models import Media
from apps.media.api.serializers import MediaSerializer


class Command(BaseCommand):
    def handle(self, *args, **options):
        Media.objects.save_url("https://imgur.com/2YYXKsw.png")

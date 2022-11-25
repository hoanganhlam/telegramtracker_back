import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        res = requests.get("https://t.me/fixedmatches0089")
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find("meta", {"property": "og:title"})["content"]
        desc = soup.find("div", {"class": "tgme_page_description"}).encode_contents()
        image = soup.find("img", {"class": "tgme_page_photo_image"})["src"]
        out = {
            "title": title,
            "desc": desc,
            "image": image,
        }
        extras = soup.select(".tgme_page_extra")[0].text.split(", ")
        for item in extras:
            sp = item.split(" ")
            key = sp.pop()
            out[key] = "".join(sp)
        print(out)

from django.http import HttpResponse
from django.template import loader
from main.models import Property, Room, Sticker
from django.core.cache import cache


def sitemap_style(request):
    template = loader.get_template('./main-sitemap.xsl')
    return HttpResponse(template.render({}, request), content_type='text/xml')


def sitemap_index(request):
    sm = [
        "/sticker-sitemap.xml",
        "/channel-sitemap.xml",
        "/group-sitemap.xml",
    ]
    template = loader.get_template('./sitemap_index.xml')
    return HttpResponse(template.render({
        "sitemaps": sm
    }, request), content_type='text/xml')


def sitemap_detail(request, flag):
    template = loader.get_template('./sitemap.xml')
    ds = []
    if flag in ["group", "channel"]:
        ds = list(map(
            lambda x: {
                "location": "https://telegramtracker.com/{}/{}".format("group" if flag == "group" else "channel", x.id_string),
                "priority": 0.8,
                "updated": x.updated,
                "changefreq": "daily"
            },
            Room.objects.filter(is_group=flag == "group").order_by("-updated")
        ))
    elif flag == "sticker":
        ds = list(map(
            lambda x: {
                "location": "https://telegramtracker.com/sticker/{}".format(x.id_string),
                "priority": 0.8,
                "updated": x.updated,
                "changefreq": "daily"
            },
            Sticker.objects.order_by("-updated")
        ))
    return HttpResponse(template.render({
        "dataset": ds
    }, request), content_type='text/xml')

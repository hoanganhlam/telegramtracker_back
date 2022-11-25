from django.http import HttpResponse
from django.template import loader
from main.models import Property, Room
from django.core.cache import cache


def sitemap_style(request):
    template = loader.get_template('./main-sitemap.xsl')
    return HttpResponse(template.render({}, request), content_type='text/xml')


def sitemap_index(request):
    sm = [
        "/project-sitemap.xml",
    ]
    template = loader.get_template('./sitemap_index.xml')
    return HttpResponse(template.render({
        "sitemaps": sm
    }, request), content_type='text/xml')


def sitemap_detail(request, flag):
    template = loader.get_template('./sitemap.xml')
    ds = []
    if flag == "project":
        ds = list(map(
            lambda x: {
                "location": "https://issomethingdown.com/{}".format(x.id_string),
                "priority": 0.8,
                "updated": x.updated,
                "changefreq": "daily"
            },
            Room.objects.all()
        ))
    return HttpResponse(template.render({
        "dataset": ds
    }, request), content_type='text/xml')

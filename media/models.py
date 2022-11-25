from django.db import models
from base.interface import BaseModel
import os
from django.core.exceptions import ValidationError
from sorl.thumbnail import ImageField
from django.core.files.temp import NamedTemporaryFile
from urllib.parse import urlparse
import requests
from django.core.files import File


# Create your models here.

def validate_file_size(value):
    file_size = value.size

    if file_size > 10485760:
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
    else:
        return value


def re_path(instance, filename, bucket):
    return os.path.join(instance.title if not filename else filename)


def path_and_rename(instance, filename):
    return re_path(instance, filename, '')


class MediaManager(models.Manager):

    def save_url(self, url, **extra_fields):
        if url is None:
            return None
        name = urlparse(url).path.split('/')[-1]
        temp = NamedTemporaryFile(delete=True)
        try:
            req = requests.get(url=url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
            disposition = req.headers.get("Content-Disposition")
            if disposition:
                test = disposition.split("=")
                if len(test) > 1:
                    name = test[1].replace("\"", "")
            temp.write(req.content)
            ext = name.split('.')[-1]
            name = name.split(".")[0]
            if len(name) > 100:
                name = name[0: 100]
            if ext == '':
                ext = 'jpg'
            name = name + '.' + ext
            if ext.lower() in ['jpg', 'jpeg', 'png']:
                temp.flush()
                img = self.model(
                    title=extra_fields.get("title") if extra_fields.get("title", None) is not None else name
                )
                img.path.save(name, File(temp))
                return img
            return None
        except Exception as e:
            print(e)
            return None


class Media(BaseModel):
    title = models.CharField(max_length=120, blank=True)
    desc = models.CharField(max_length=200, blank=True)
    path = ImageField(upload_to=path_and_rename, max_length=500, validators=[validate_file_size])

    objects = MediaManager()

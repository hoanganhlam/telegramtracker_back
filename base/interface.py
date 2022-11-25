from django.db import models
from utils.slug import unique_slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    STATUS_CHOICE = (
        (-1, _("Deleted")),
        (0, _("Pending")),
        (1, _("Active")),
    )
    meta = models.JSONField(null=True, blank=True)
    updated = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)
    db_status = models.IntegerField(choices=STATUS_CHOICE, default=1)

    class Meta:
        abstract = True


class HasIDString(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    id_string = models.CharField(max_length=200, db_index=True)

    def save(self, **kwargs):
        # generate unique slug
        if hasattr(self, 'id_string') and self.id is None and self.id_string is None or self.id_string == "":
            unique_slugify(self, self.name, "id_string")
        elif self.id is not None and self.id_string:
            unique_slugify(self, self.id_string, "id_string")
        super(HasIDString, self).save(**kwargs)

    class Meta:
        abstract = True


class BlockChain(models.Model):
    chain_id = models.CharField(default="56", max_length=50)
    address = models.CharField(max_length=100, db_index=True)

    class Meta:
        abstract = True
        unique_together = ['chain_id', 'address']

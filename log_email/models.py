from django.db import models
from django.utils.translation import gettext_lazy as _


class EmailLogQuerySetQuery:
    select_related = False
    order_by = []  # type: ignore


class EmailLogQuerySet:
    query = EmailLogQuerySetQuery()

    def __init__(self, model, data):
        self.model = model
        self._data = data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def count(self):
        return len(self._data)

    def filter(self, *args, **kwargs):
        # You could add support for filtering if you want,
        # otherwise just return self for compatibility.
        return self

    def order_by(self, *args, **kwargs):
        return self

    def __getitem__(self, k):
        return self._data[k]

    def _clone(self):
        return EmailLogQuerySet(self.model, self._data)


class EmailLog(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    to = models.EmailField(verbose_name=_("Recipient"))
    subject = models.CharField(max_length=255, verbose_name=_("Subject"))
    status = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Status")
    )
    date = models.DateTimeField(verbose_name=_("Date"))

    class Meta:
        managed = False
        verbose_name = "Email log"
        verbose_name_plural = "Email logs"

    def __str__(self):
        return f"{self.to} - {self.subject}"

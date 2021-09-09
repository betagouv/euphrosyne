from django.db import models


class Institution(models.Model):
    name = models.CharField(max_length=255)

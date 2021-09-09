from django.contrib import admin

from . import models


@admin.register(models.Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ["name", "date", "particle_type", "modified", "created"]

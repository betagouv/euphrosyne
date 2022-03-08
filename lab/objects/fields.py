from typing import Any

from django.forms.models import ModelChoiceField

from .models import ObjectGroup


class ObjectGroupChoiceField(ModelChoiceField):
    """Field for ObjectGroup in a manytomany context.
    Querysets for displaying choices and doing validation are different.
    The field displays only ObjectGroup objects used inside a project, while
    it accepts ObjectGroup objects that do not have project attached (yet)
    in validation. This is usefull when a user creates a object group
    via the Run admin page but the ObjectGroup has not been linked to the Run yet.
    """

    def __init__(self, project_id: int, **kwargs: Any) -> None:
        self.project_id = project_id
        queryset = ObjectGroup.objects.filter(runs__project=project_id)
        self.choices = [
            (objectgroup.id, str(objectgroup)) for objectgroup in queryset.distinct()
        ]
        queryset = queryset | ObjectGroup.objects.filter(runs=None)
        super().__init__(queryset, **kwargs)

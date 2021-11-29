import enum
from typing import Any, Dict, Optional

from django import forms
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from ..models import Object, ObjectGroup


class ObjectGroupAddChoices(enum.Enum):
    OBJECT_GROUP = "OBJECT_GROUP", _("Group of objects")
    SINGLE_OBJECT = "SINGLE_OBJECT", _("One object")

    @classmethod
    def to_choices(cls):
        return (choice.value for choice in cls)


class ObjectGroupForm(forms.ModelForm):
    add_type = forms.ChoiceField(
        label=_("Number of objects"), choices=ObjectGroupAddChoices.to_choices()
    )

    class Meta:
        model = ObjectGroup
        fields = ("add_type", "label", "materials", "dating")

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        add_type = cleaned_data["add_type"]
        if add_type == ObjectGroupAddChoices.OBJECT_GROUP.value[0]:
            if not cleaned_data.get("label"):
                raise ValidationError(
                    {
                        "label": ValidationError(
                            _(
                                "Group label must be specified "
                                "when adding multiple objects"
                            ),
                            code="label-required-for-mulitple-objects",
                        )
                    }
                )
        return cleaned_data


class ObjectInline(admin.TabularInline):
    model = Object
    verbose_name = _("Object")
    fields = ("label", "differentiation_information")
    extra = 1

    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True


@admin.register(ObjectGroup)
class ObjectGroupAdmin(ModelAdmin):
    list_display = ("label",)
    form = ObjectGroupForm

    inlines = (ObjectInline,)

    class Media:
        js = ("js/admin/object-group.js",)
        css = {"all": ("css/admin/object-group.css",)}

    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_add_permission(self, request: HttpRequest) -> bool:
        return True

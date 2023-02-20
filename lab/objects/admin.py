import io
import json
from dataclasses import asdict
from typing import Any, Dict, List, Mapping, Optional, Tuple

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from django.forms import BaseInlineFormSet, ValidationError
from django.forms.utils import ErrorList
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from lab.models.run import Run
from lab.permissions import is_lab_admin

from .csv_upload import CSVParseError, parse_csv
from .forms import ObjectGroupForm
from .models import Object, ObjectGroup


class CSVValidationError(ValidationError):
    pass


class ObjectFormSet(BaseInlineFormSet):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Optional[QueryDict] = None,
        files: Optional[dict[str, UploadedFile]] = None,
        instance: Optional[Object] = None,
        save_as_new: bool = False,
        prefix: Optional[str] = None,
        queryset: Optional[QuerySet] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(data, files, instance, save_as_new, prefix, queryset, **kwargs)
        if instance and (instance.collection or instance.inventory):
            for form in self:
                form.fields["collection"].widget.attrs["disabled"] = bool(
                    instance.collection
                )
                form.fields["inventory"].widget.attrs["disabled"] = bool(
                    instance.inventory
                )

    def save(self, commit: bool = True):
        saved_objects = super().save(commit)
        object_set_count = self.instance.object_set.count()
        if object_set_count and self.instance.object_count != object_set_count:
            self.instance.object_count = object_set_count
            self.instance.save()
        return saved_objects

    def full_clean(self) -> Any:
        if not self.instance.id and self.files and "objects-template" in self.files:
            # if present, extract data from CSV file and
            # replace self.data with its content.
            csv_data = {f"{self.prefix}-INITIAL_FORMS": "0"}
            total_forms = 0
            csv_file = io.TextIOWrapper(self.files["objects-template"])
            try:
                for index, object_in_csv in enumerate(parse_csv(csv_file)):
                    csv_data[f"{self.prefix}-{index}-id"] = ""
                    for field, value in asdict(object_in_csv).items():
                        csv_data[f"{self.prefix}-{index}-{field}"] = value
                    total_forms += 1
            except CSVParseError:
                error_message = _(
                    "We cannot process the CSV file because it is not valid. "
                    "Please refer to the template to fill it properly."
                )
                self._non_form_errors = self.error_class(
                    [
                        CSVValidationError(
                            error_message,
                            code="csv-not-valid",
                        )
                    ],
                    error_class="nonform",
                    renderer=self.renderer,  # pylint: disable=no-member
                )
                self._errors = []
                return
            csv_data[f"{self.prefix}-TOTAL_FORMS"] = str(total_forms)
            self.data = csv_data
        super().full_clean()

    def clean(self) -> None:
        super().clean()
        if len(self.forms) == 1:
            raise ValidationError(
                _(
                    "A differentiated object group must contain at least 2 objects."
                    "If you want to add a single object, "
                    "please click on the one object tab."
                ),
                code="differentiated-object-group-too-few",
            )

    def csv_differentiation_errors(self) -> Any:
        errors: ErrorList = self.non_form_errors()
        errors.data = list(
            filter(lambda error: isinstance(error, CSVValidationError), errors.data)
        )
        return errors

    def manual_differentiation_errors(self) -> Any:
        errors: ErrorList = self.non_form_errors()
        errors.data = list(
            filter(
                lambda error: not isinstance(error, CSVValidationError),
                errors.data,
            )
        )
        return errors


class ObjectInline(admin.TabularInline):
    model = Object
    verbose_name = _("Object")
    template = "admin/edit_inline/tabular_object_in_objectgroup.html"
    fields = (
        "label",
        "inventory",
        "collection",
    )
    extra = 0

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def get_formset(
        self, request: Any, obj: Optional[ObjectGroup] = None, **kwargs: Any
    ):
        return super().get_formset(request, obj, formset=ObjectFormSet, **kwargs)

    def get_min_num(
        self,
        request: HttpRequest,
        obj: Optional[ObjectGroup] = None,
        **kwargs: Mapping[str, Any],
    ) -> Optional[int]:
        if request.method == "POST":
            # Forbids empty form in formset to enforce object_count is equal to
            # number of differentiared objects.
            return int(request.POST["object_set-TOTAL_FORMS"])
        return super().get_min_num(request, obj, **kwargs)

    def get_max_num(
        self,
        request: HttpRequest,
        obj: Optional[ObjectGroup] = None,
        **kwargs: Mapping[str, Any],
    ) -> Optional[int]:
        if obj and obj.object_set.count() == 1:
            return 1
        return super().get_max_num(request, obj=obj, **kwargs)


@admin.register(ObjectGroup)
class ObjectGroupAdmin(ModelAdmin):
    inlines = (ObjectInline,)
    form = ObjectGroupForm

    class Media:
        js = ("pages/objectgroup.js",)
        css = {"all": ("css/admin/objectgroup.css",)}

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return is_lab_admin(request.user) or (
            obj and obj.runs.filter(project__members=request.user.id).exists()
        )

    def get_fieldsets(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> List[Tuple[Optional[str], Dict[str, Any]]]:
        return [
            (
                None,
                {
                    "fields": self.get_fields(request, obj),
                    "description": _(
                        "Fill up dating and inventory number if you object \
                        group is undifferentiated."
                    ),
                },
            )
        ]

    def save_model(
        self, request: Any, obj: ObjectGroup, form: ObjectGroupForm, change: bool
    ) -> None:
        super().save_model(request, obj, form, change)
        if not change and request.POST.get(IS_POPUP_VAR) and "run" in request.GET:
            try:
                run = Run.objects.get(pk=request.GET["run"])
            except Run.DoesNotExist:
                return
            obj.runs.add(run)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: Optional[str] = None,
        form_url: str = "",
        extra_context: Optional[Dict[str, bool]] = None,
    ) -> Any:
        obj: ObjectGroup = self.get_object(request, object_id=object_id)
        are_objects_differentiated = self.get_are_objects_differentiated(request, obj)

        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context={
                **(extra_context if extra_context else {}),
                "are_objects_differentiated": are_objects_differentiated,
                "show_save_as_new": False,
                "show_save_and_add_another": False,
                "show_save_and_continue": False,
            },
        )

    def response_add(
        self,
        request: HttpRequest,
        obj: ObjectGroup,
        post_url_continue: Optional[str] = None,
    ) -> HttpResponse:
        response = super().response_add(request, obj, post_url_continue)
        if request.method == "POST" and request.POST.get(IS_POPUP_VAR, 0):
            response.context_data["popup_response_data"] = json.dumps(
                {
                    **json.loads(response.context_data["popup_response_data"]),
                    "objectgroup_run_run_ids": list(
                        obj.runs.through.objects.filter(objectgroup=obj.id).values_list(
                            "id", "run_id"
                        )
                    ),
                }
            )
        return response

    def response_change(self, request: HttpRequest, obj: ObjectGroup) -> HttpResponse:
        response = super().response_change(request, obj)
        if "next" in request.GET:
            return HttpResponseRedirect(request.GET["next"])
        return response

    @staticmethod
    def get_are_objects_differentiated(request: HttpRequest, obj: ObjectGroup = None):
        if obj:
            return obj.object_set.exists()
        if request.method == "POST" and "object_set-TOTAL_FORMS" in request.POST:
            return int(request.POST["object_set-TOTAL_FORMS"]) > 0
        return False

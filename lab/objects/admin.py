import io
import json
from dataclasses import asdict
from typing import Any, Mapping, Optional

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.views.main import IS_POPUP_VAR  # type: ignore[attr-defined]
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from django.forms import BaseInlineFormSet, ModelForm, ValidationError
from django.forms.utils import ErrorList
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.http.request import HttpRequest
from django.template.response import TemplateResponse
from django.utils.datastructures import MultiValueDict
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from lab.models import Project, Run
from lab.permissions import is_lab_admin

from .c2rmf import fetch_full_objectgroup_from_eros
from .csv_upload import CSVParseError, parse_csv
from .forms import (
    ObjectGroupForm,
    ObjectGroupImportC2RMFReadonlyForm,
    ObjectGroupThumbnailForm,
)
from .models import Object, ObjectGroup, ObjectGroupThumbnail


class CSVValidationError(ValidationError):
    pass


class ObjectGroupThumbnailInline(admin.StackedInline):
    def image_tag(self, obj):
        return format_html('<img src="{}" />', obj.image.url)

    image_tag.short_description = _("Preview")  # type: ignore[attr-defined]

    model = ObjectGroupThumbnail
    verbose_name = _("Thumbnail")
    form = ObjectGroupThumbnailForm
    readonly_fields = ("image_tag",)


class ProjectInline(admin.TabularInline):
    model = Run.run_object_groups.through
    verbose_name = "Run"
    verbose_name_plural = "Runs"
    extra = 0

    fields = ("run",)

    def has_change_permission(
        self, request: HttpRequest, obj: Project | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Project | None = None
    ) -> bool:
        return False

    def has_add_permission(
        self, request: HttpRequest, obj: Project | None = None
    ) -> bool:
        return False


class ObjectFormSet(BaseInlineFormSet):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: QueryDict | None = None,
        files: MultiValueDict[str, UploadedFile] | None = None,
        instance: Object | None = None,
        save_as_new: bool = False,
        prefix: str | None = None,
        queryset: QuerySet | None = None,
        **kwargs,
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
        if self.instance.pk:
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
            csv_file = io.TextIOWrapper(  # type: ignore[type-var]
                self.files["objects-template"]  # type: ignore[arg-type]
            )
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
                    renderer=self.renderer,  # type: ignore[attr-defined] # pylint: disable=no-member
                )
                self._errors = []  # type: ignore[var-annotated]
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
    inlines = (ObjectInline, ObjectGroupThumbnailInline)
    form = ObjectGroupForm
    list_display = ("label", "project_num", "c2rmf_id")

    class Media:
        js = ("pages/objectgroup.js",)
        css = {"all": ("css/admin/objectgroup.css",)}

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_view_permission(
        self, request: HttpRequest, obj: ObjectGroup | None = None
    ) -> bool:
        # We must implement this to use has_change_permission to make
        # page readonly. Otherwise will throw 403 error when viewing the page
        # for non admin users.
        return is_lab_admin(request.user) or bool(
            obj and obj.runs.filter(project__members=request.user.id).exists()
        )

    def has_change_permission(
        self, request: HttpRequest, obj: ObjectGroup | None = None
    ) -> bool:
        # If obj was imported from Eros, make page readonly
        if obj and obj.c2rmf_id:
            return False
        return is_lab_admin(request.user) or bool(
            obj and obj.runs.filter(project__members=request.user.id).exists()
        )

    def get_form(
        self,
        request: HttpRequest,
        obj: Optional[ObjectGroup] = None,
        change: bool = False,
        **kwargs: Any,
    ):
        if obj and obj.c2rmf_id:
            # After EROS import, readonly
            return ObjectGroupImportC2RMFReadonlyForm
        # Manual creation / edition
        return super().get_form(request, obj, change, **kwargs)

    def get_fieldsets(self, request: HttpRequest, obj: Optional[ObjectGroup] = None):
        description = ""
        if obj and obj.c2rmf_id:
            description = str(_("This object was imported from EROS."))
        else:
            description = str(
                _(
                    # pylint: disable=line-too-long
                    "Fill up collection and inventory number if you object group is undifferentiated."
                )
            )
        fieldsets = [
            (
                None,
                {"fields": self.get_fields(request, obj), "description": description},
            )
        ]
        return fieldsets

    def get_inlines(self, request: HttpRequest, obj: ObjectGroup | None):
        if "run" not in request.GET and is_lab_admin(request.user):
            return (ObjectInline, ProjectInline)
        return (ObjectInline, ObjectGroupThumbnailInline)

    def get_object(
        self, request: HttpRequest, object_id: str, from_field=None
    ) -> Any | None:
        object_group = super().get_object(request, object_id, from_field)
        if object_group and object_group.c2rmf_id:
            object_group = fetch_full_objectgroup_from_eros(
                object_group.c2rmf_id, object_group
            )
        return object_group

    def save_form(
        self, request: HttpRequest, form: ModelForm, change: bool
    ) -> ObjectGroup:
        # Calls save_form in any case to populate ModelForm.save_m2m
        object_group = super().save_form(request, form, change)
        return object_group

    def save_model(
        self, request: Any, obj: ObjectGroup, form: ModelForm, change: bool
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
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, bool] | None = None,
    ) -> Any:
        obj: ObjectGroup | None = (
            self.get_object(request, object_id=object_id) if object_id else None
        )
        are_objects_differentiated = self.get_are_objects_differentiated(request, obj)

        run_id = request.GET.get("run")
        run = (
            Run.objects.filter(id=run_id).values("id", "label").first()
            if run_id
            else None
        )

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
                "show_close": False,
                "objectgroup_run": run,
            },
        )

    def response_add(
        self,
        request: HttpRequest,
        obj: ObjectGroup,
        post_url_continue: str | None = None,
    ) -> TemplateResponse:
        response: TemplateResponse = super().response_add(  # type: ignore[assignment]
            request, obj, post_url_continue
        )
        if (
            response.context_data
            and request.method == "POST"
            and request.POST.get(IS_POPUP_VAR, False)
        ):
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

    @admin.display
    def project_num(self, obj: ObjectGroup) -> int:
        run_ids = obj.runs.values_list("id", flat=True)
        return Project.objects.filter(runs__id__in=run_ids).distinct().count()

    @staticmethod
    def get_are_objects_differentiated(
        request: HttpRequest, obj: ObjectGroup | None = None
    ):
        if obj:
            return obj.object_set.exists()
        if request.method == "POST" and "object_set-TOTAL_FORMS" in request.POST:
            return int(request.POST["object_set-TOTAL_FORMS"]) > 0
        return False

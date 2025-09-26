from typing import Any, Dict, Optional

from django.apps import apps
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import ShowFacets
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from lab.participations.models import Participation
from lab.permissions import is_lab_admin
from lab.runs.models import Run

from .emails import send_invitation_email
from .forms import UserChangeForm, UserCreationForm
from .models import User, UserInvitation


class ProjectInline(admin.TabularInline):
    model = Participation
    verbose_name = _("Related project")
    verbose_name_plural = _("Related projects")
    extra = 0

    fields = ("project", "status_display")
    readonly_fields = ("project", "status_display")

    def has_view_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        return is_lab_admin(request.user) or request.user == obj

    def has_change_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False

    def has_view_or_change_permission(
        self, request: HttpRequest, obj: User | None = None
    ) -> bool:
        if not obj:
            return True
        return is_lab_admin(request.user) or request.user == obj

    @admin.display(description=_("Status"))
    def status_display(self, obj: Participation) -> str:
        return format_html(
            '<p class="fr-tag {}">{}</p>',
            obj.project.status.name.lower(),
            obj.project.status.value[1],
        )


class InvitationCompletedStatusListFilter(admin.SimpleListFilter):
    title = _("invitation completed")
    template = "admin/lab/project/filter.html"
    parameter_name = "invitation_completed"

    def lookups(self, request, model_admin):
        return [
            (True, _("Yes")),
            (False, _("No")),
        ]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "True":
                return queryset.filter(
                    invitation_completed_at__isnull=False,
                )
            if self.value() == "False":
                return queryset.filter(
                    invitation_completed_at__isnull=True,
                )
        return queryset


class OnPremiseParticipationDateListFilter(admin.SimpleListFilter):
    title = _("date of on-site presence")
    template = "admin/lab/project/filter.html"
    parameter_name = "on_premise"

    def lookups(self, request, model_admin):
        return [
            ("upcoming", _("Upcoming")),
            ("this month", _("This month")),
            ("this year", _("This year")),
            ("last month", _("Last month")),
            ("last year", _("Last year")),
        ]

    def queryset(self, request, queryset):
        if self.value():
            run_qs = Run.objects
            if self.value() == "upcoming":
                run_qs = run_qs.filter(
                    start_date__gte=timezone.now(),
                )
            elif self.value() == "this month":
                run_qs = run_qs.filter(
                    start_date__month=timezone.now().month,
                    start_date__year=timezone.now().year,
                )
            elif self.value() == "last month":
                run_qs = run_qs.filter(
                    start_date__month=timezone.now().month - 1,
                    start_date__year=timezone.now().year,
                )
            elif self.value() == "this year":
                run_qs = run_qs.filter(
                    start_date__year=timezone.now().year,
                )
            elif self.value() == "last year":
                run_qs = run_qs.filter(
                    start_date__month=timezone.now().month - 1,
                    start_date__year=timezone.now().year,
                )

            project_ids = run_qs.values_list("project_id", flat=True)
            participation_qs = Participation.objects.filter(
                on_premises=True, project_id__in=project_ids
            )
            queryset = queryset.filter(participation__in=participation_qs).distinct()

        return queryset


class UserAdmin(DjangoUserAdmin):
    class Media:
        css = {"all": ("css/admin/user.css",)}

    model = User

    add_form_template = "euphro_add_form.html"

    add_form = UserCreationForm
    form = UserChangeForm

    list_filter = (
        InvitationCompletedStatusListFilter,
        OnPremiseParticipationDateListFilter,
    )
    list_per_page = 30
    show_facets = ShowFacets.NEVER
    actions = ("send_invitation_mail_action",)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = (
        "last_name",
        "first_name",
        "email",
    )

    readonly_fields = ("password_display", "has_radiation_certification")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("groups")

    def get_list_display(self, request):
        list_display = [
            "email",
            "full_name_display",
            "last_institution_display",
            "invitation_completed_display",
            "is_lab_admin",
        ]
        if request.user.is_superuser:
            list_display += ["is_superuser_display"]
        if apps.is_installed("radiation_protection"):
            list_display += ["has_radiation_certification"]
        return list_display

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[User] = None):
        if request.user.is_superuser:
            return self.readonly_fields + ("is_superuser",)
        return self.readonly_fields

    def get_fieldsets(self, request: HttpRequest, obj: Optional[User] = None):
        fieldset_classes = [
            "fr-mb-0",
            "fr-pb-1w",
        ]
        fieldsets = []
        fieldsets += [
            (
                _("Profile"),
                {
                    "fields": (
                        ("email", "password_display"),
                        "first_name",
                        "last_name",
                    ),
                    "classes": [*fieldset_classes],
                },
            ),
        ]
        if is_lab_admin(request.user):
            fieldsets += [
                (
                    _("Permissions"),
                    {
                        "fields": ("is_staff", "is_lab_admin", "is_active", "groups"),
                        "classes": [*fieldset_classes],
                    },
                ),
                (
                    _("Certifications"),
                    {
                        "fields": ("has_radiation_certification",),
                        "classes": [*fieldset_classes],
                    },
                ),
            ]
        if request.user.is_superuser:
            fieldsets += [
                (  # type: ignore[list-item]
                    str(gettext("Superuser")),
                    {"fields": ("is_superuser",), "classes": [*fieldset_classes]},
                ),
            ]
        return fieldsets

    def get_inlines(self, request: HttpRequest, obj: Optional[User] = None):
        if obj:
            return [ProjectInline]
        return []

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict[str, str]] = None
    ):
        return super().changelist_view(
            request,
            {
                **(extra_context if extra_context else {}),
                "title": _("Users"),
            },
        )

    def changeform_view(  # type: ignore[override]
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, str] | None = None,
    ):  # pylint: disable=signature-differs
        return super().changeform_view(
            request,
            object_id,
            form_url,
            {
                **(extra_context if extra_context else {}),
                "show_save_and_add_another": False,
                "show_save_as_new": False,
            },
        )

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[User] = None
    ) -> bool:
        return request.user.is_staff and (
            is_lab_admin(request.user) or request.user == obj
        )

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[User] = None
    ) -> bool:
        return request.user.is_staff and (
            is_lab_admin(request.user) or request.user == obj
        )

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description=_("Send invitation e-mail again"))
    def send_invitation_mail_action(
        self, request: HttpRequest, queryset: QuerySet[UserInvitation]
    ):
        users = queryset.filter(invitation_completed_at=None)
        if users:
            for user in users:
                send_invitation_email(user)
            message = _(
                "Invitations sent to : {}.",
            ).format(", ".join([user.email for user in users]))
            self.message_user(
                request,
                message,
                messages.SUCCESS,
            )

        completed_registration_users = queryset.exclude(invitation_completed_at=None)
        if completed_registration_users:
            message = _(
                "Invitations were not sent to the following accounts, "
                "the registrations have already been completed : {}",
            ).format(", ".join([user.email for user in completed_registration_users]))
            self.message_user(
                request,
                message,
                messages.WARNING,
            )

    @admin.display(description=_("Name"))
    def full_name_display(self, obj: User) -> str:
        return obj.get_full_name()

    @admin.display(description=_("Last institution"))
    def last_institution_display(self, obj: User) -> str:
        last_participation = obj.participation_set.order_by("-created").first()
        if last_participation and last_participation.institution:
            return str(last_participation.institution)
        return ""

    @admin.display(description=_("Invitation completed"), boolean=True)
    def invitation_completed_display(self, obj: User) -> bool:
        return obj.invitation_completed_at is not None

    @admin.display(description="Super-user", boolean=True)
    def is_superuser_display(self, obj: User):
        return obj.is_superuser

    @admin.display(description=_("Password"))
    def password_display(self, obj: User):
        change_pasword_link = format_html(
            '<a href="{}">{}</a>',
            reverse("admin:auth_user_password_change", args=[obj.pk]),
            _("this form"),
        )
        text = (
            _("Change password using {}.")
            if obj.password
            else _("No password. You can set one using {}.")
        ).format(change_pasword_link)
        return format_html('<div class="help">{}</div>', mark_safe(text))

    @admin.display(description=_("Radiation protection"), boolean=True)
    def has_radiation_certification(self, obj: User) -> bool:
        if apps.is_installed("radiation_protection"):
            # pylint: disable=import-outside-toplevel
            from radiation_protection import certification as radiation_protection

            return radiation_protection.user_has_active_certification(obj)
        return False


class UserInvitationAdmin(ModelAdmin):
    list_display = ("email", "invitation_completed", "invitation_completed_at")
    fields = ("email", "first_name", "last_name")

    def add_view(
        self,
        request: HttpRequest,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        extra_context = {"title": _("Invite new user")}
        return super().add_view(request, form_url, extra_context)

    @admin.display(
        description=_("Invitation completed"),
        boolean=True,
        ordering="invitation_completed_at",
    )
    def invitation_completed(self, instance: UserInvitation):
        return instance.invitation_completed_at is not None

    def save_model(
        self,
        request: HttpRequest,
        obj: UserInvitation,
        form: ModelForm,
        change: bool,
    ) -> None:
        if not change:
            obj.save()
            send_invitation_email(obj)
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff and is_lab_admin(request.user)

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[UserInvitation] = None
    ):
        return request.user.is_staff and is_lab_admin(request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[UserInvitation] = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[UserInvitation] = None
    ) -> bool:
        return False


admin.site.register(User, UserAdmin)
admin.site.register(UserInvitation, UserInvitationAdmin)

from typing import Any, Dict, List, Optional, Tuple

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.forms.models import ModelForm
from django.http.request import HttpRequest
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from .emails import send_invitation_email
from .forms import UserChangeForm, UserCreationForm
from .models import User, UserGroups, UserInvitation


class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    add_form_template = "euphro_add_form.html"
    form = UserChangeForm
    model = User
    list_display = (
        "email",
        "is_staff",
        "is_active",
        "in_admin_group",
        "in_participant_group",
    )
    list_filter = ("email", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Profile"), {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "groups")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
    search_fields = ("email",)
    ordering = (
        "last_name",
        "first_name",
        "email",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("groups")

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display + ("is_superuser",)
        return self.list_display

    def get_readonly_fields(self, request: HttpRequest, obj: Optional[User] = None):
        if request.user.is_superuser:
            return self.readonly_fields + ("is_superuser",)
        return self.readonly_fields

    def get_fieldsets(
        self, request: HttpRequest, obj: Optional[User] = None
    ) -> List[Tuple[Optional[str], Dict[str, Any]]]:
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets + (
                (
                    gettext("Superuser"),
                    {"fields": ("is_superuser",)},
                ),
            )
        return fieldsets


class UserInvitationAdmin(ModelAdmin):
    list_display = ("email", "invitation_completed_at")
    fields = ("email",)
    actions = ("view", "add")

    def save_model(
        self,
        request: HttpRequest,
        obj: UserInvitation,
        form: ModelForm,
        change: bool,
    ) -> None:
        if not change:
            obj.is_staff = True
            obj.save()
            obj.groups.add(Group.objects.get(name=UserGroups.PARTICIPANT.value))

            token = default_token_generator.make_token(obj)
            send_invitation_email(email=obj.email, user_id=obj.pk, token=token)
            return obj
        return super().save_model(request, obj, form, change)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[UserInvitation] = ...
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[UserInvitation] = ...
    ) -> bool:
        return False


admin.site.register(User, UserAdmin)
admin.site.register(UserInvitation, UserInvitationAdmin)

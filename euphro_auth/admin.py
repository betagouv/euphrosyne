from typing import Any, Dict, List, Optional, Tuple

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.http.request import HttpRequest
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from .emails import send_invitation_email
from .forms import UserChangeForm, UserCreationForm, UserSendInvitationForm
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


class UserInvitationAdmin(admin.ModelAdmin):
    form = UserSendInvitationForm
    add_form_template = "invitation_add_form.html"
    list_display = ["user", "created"]
    actions = ["view", "add"]

    def save_model(
        self,
        request: HttpRequest,
        obj: UserInvitation,
        form: UserSendInvitationForm,
        change: bool,
    ) -> None:
        if obj.user and not obj.user.id:
            user: User = obj.user
            user.is_staff = True
            user.save()
            user.groups.add(Group.objects.get(name=UserGroups.PARTICIPANT.value))

            token = default_token_generator.make_token(user)
            send_invitation_email(email=user.email, user_id=user.pk, token=token)
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

from typing import Any, Optional

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.http.request import HttpRequest

from .forms import UserChangeForm, UserCreationForm, UserSendInvitationForm
from .models import User, UserInvitation


class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    add_form_template = "euphro_add_form.html"
    form = UserChangeForm
    model = User
    list_display = (
        "email",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "email",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups")}),
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
    ordering = ("email",)


class UserInvitationAdmin(admin.ModelAdmin):
    form = UserSendInvitationForm
    add_form_template = "invitation_add_form.html"
    list_display = ["user", "created"]
    actions = ["view", "add"]

    def save_model(
        self,
        request: Any,
        obj: UserInvitation,
        form: UserSendInvitationForm,
        change: bool,
    ) -> None:
        if obj.user and not obj.user.id:
            obj.user.save()
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

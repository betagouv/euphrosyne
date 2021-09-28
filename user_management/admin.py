from django.contrib import admin

from .forms import UserInvitationForm
from .models import Profile, UserInvitation


class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "last_name",
        "first_name",
    ]


class UserInvitationAdmin(admin.ModelAdmin):
    form = UserInvitationForm
    add_form_template = "invitation_add_form.html"
    list_display = ["user", "created"]


admin.site.register(UserInvitation, UserInvitationAdmin)
admin.site.register(Profile, ProfileAdmin)

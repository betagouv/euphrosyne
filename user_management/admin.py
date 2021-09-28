from django.contrib import admin

from .models import UserInvitation
from .forms import UserInvitationForm


class UserInvitationAdmin(admin.ModelAdmin):
    form = UserInvitationForm
    add_form_template = "invitation_add_form.html"
    list_display = ["user", "created"]


admin.site.register(UserInvitation, UserInvitationAdmin)

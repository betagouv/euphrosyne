from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User


class UserCreationForm(DjangoUserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class UserChangeForm(DjangoUserChangeForm):
    class Meta:
        model = User
        fields = ("email",)


class UserInvitationRegistrationForm(DjangoSetPasswordForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def clean_email(self) -> str:
        if self.user and self.user.email == self.cleaned_data["email"]:
            return self.cleaned_data["email"]
        if User.objects.filter(email=self.cleaned_data["email"]).count():
            raise ValidationError(_("An account with this email already exists."))
        return self.cleaned_data["email"]

    def save(self, commit: bool = True) -> AbstractBaseUser:
        self.user.email = self.cleaned_data["email"]
        return super().save(commit=commit)

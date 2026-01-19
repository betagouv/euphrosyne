from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
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
    user: User

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    first_name = forms.CharField(
        label=_("First name"),
        max_length=50,
        widget=forms.TextInput(),
    )

    last_name = forms.CharField(
        label=_("Last name"),
        max_length=50,
    )

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower()
        if self.user and self.user.email and self.user.email.lower() == email:
            return email
        query = User.objects.filter(email__iexact=email)
        if self.user and self.user.pk:
            query = query.exclude(pk=self.user.pk)
        if query.exists():
            raise ValidationError(
                _("An account with this email already exists."),
                code="invitation_email_already_exists",
            )
        return email

    def save(self, commit: bool = True) -> AbstractBaseUser:
        self.user.email = self.cleaned_data["email"]
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.invitation_completed_at = timezone.now()
        return super().save(commit=commit)


class CGUAcceptanceForm(forms.Form):
    accept_cgu = forms.BooleanField(
        label=_("I have read and accept the Terms and Conditions."), required=True
    )

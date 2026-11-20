from allauth.account.forms import LoginForm as AllauthLoginForm
from allauth.account.forms import ResetPasswordForm as AllauthResetPasswordForm
from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
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

    def clean(self):
        # Set the submitted identity before Django checks password similarity.
        for field in ("email", "first_name", "last_name"):
            if field in self.cleaned_data:
                setattr(self.user, field, self.cleaned_data[field])
        return super().clean()

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


class ResetPasswordForm(AllauthResetPasswordForm):
    users: list[User]

    def clean_email(self) -> str:
        email = super().clean_email()
        # pylint: disable=attribute-defined-outside-init
        # Like Django's password reset, skip accounts without a usable password
        # (ORCID-only accounts).
        self.users = [user for user in self.users if user.has_usable_password()]
        return email


class LoginForm(AllauthLoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The page shows its own "forgotten password" link.
        self.fields["password"].help_text = ""

    @property
    def password_locked_out(self) -> bool:
        return self.has_error(NON_FIELD_ERRORS, "too_many_login_attempts")

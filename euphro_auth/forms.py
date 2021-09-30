from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .emails import send_invitation_email
from .models import User, UserInvitation


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


class UserInvitationForm(forms.ModelForm):

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta:
        fields = ("email",)
        model = UserInvitation

    def clean_email(self):
        email: str = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                _("This user has already been invited."), code="email-unique"
            )
        return email

    def save(
        self,
        commit=True,
    ):
        email = self.cleaned_data["email"]
        user = User.objects.create(email=email)
        token = default_token_generator.make_token(user)

        self.instance.user = user
        super().save(commit=commit)
        send_invitation_email(email=email, user_id=user.pk, token=token)
        return self.instance

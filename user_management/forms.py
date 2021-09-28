from django import forms
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User

from .emails import send_invitation_email
from .models import Profile, UserInvitation


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
        if User.objects.filter(email=email).count():
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


class ProfileRegistrationForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("first_name", "last_name", "profession")

    def __init__(self, user: User, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True) -> Profile:
        self.instance.user = self.user
        return super().save(commit=commit)

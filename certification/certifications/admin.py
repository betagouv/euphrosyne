from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin

from .models import Certification, CertificationType, QuizCertification, QuizResult


class CertificationAdminForm(forms.ModelForm):
    def clean_invitation_to_complete_email_template_path(self):
        return self._clean_template(
            self.cleaned_data["invitation_to_complete_email_template_path"]
        )

    def clean_success_email_template_path(self):
        return self._clean_template(self.cleaned_data["success_email_template_path"])

    @classmethod
    def _clean_template(cls, template: str | None):
        if template is None:
            return template
        if not cls._check_template_exists(template):
            raise forms.ValidationError(_("Template does not exist"))
        return template

    @staticmethod
    def _check_template_exists(template: str):
        try:
            get_template(template)
        except TemplateDoesNotExist:
            return False
        return True


class QuizCertificationInline(LabAdminAllowedMixin, admin.StackedInline):
    model = QuizCertification
    verbose_name = _("Quiz certification")

    fields = ("url", "passing_score")

    extra = 1

    def get_extra(
        self, request: HttpRequest, obj: Certification | None = None, **kwargs: Any
    ) -> int:
        return 1 if not obj.quizzes.count() else 0  # type: ignore


@admin.register(Certification)
class CertificationAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("name", "created")
    fields = (
        "type_of",
        "name",
        "description",
        "num_days_valid",
        "invitation_to_complete_email_template_path",
        "success_email_template_path",
    )

    form = CertificationAdminForm

    def get_inlines(
        self, request: HttpRequest, obj: Certification | None
    ) -> list[type[InlineModelAdmin]]:
        if obj and obj.type_of == CertificationType.QUIZ:
            return [QuizCertificationInline]
        return []


@admin.register(QuizResult)
class QuizResultAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("quiz", "user", "score_with_passing_score", "is_passed", "created")
    fields = ("quiz", "user", "score", "is_passed")
    readonly_fields = ("created",)
    list_filter = ("is_passed", "quiz__certification__name")
    search_fields = ("user__email",)

    @admin.display(description=_("Score"))
    def score_with_passing_score(self, obj: QuizResult) -> str:
        return f"{obj.score} / {obj.quiz.passing_score}"

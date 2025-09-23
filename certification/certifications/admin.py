from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils.html import format_html
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

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj:
            fields += ("results_display", "notifications_display")
        return fields

    def get_fieldsets(self, request, obj: Certification | None = None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            fieldsets = list(fieldsets)
            fieldsets.append(
                (
                    _("Certification Activity"),
                    {
                        "fields": ("results_display", "notifications_display"),
                    },
                )
            )
        return fieldsets

    @admin.display(description=_("Results"))
    def results_display(self, obj: Certification):
        results_link = format_html(
            '<a href="{}" class="fr-link fr-icon-award-line fr-link--icon-left">{}</a>',
            reverse(
                "admin:certification_quizresult_changelist",
            )
            + f"?quiz__certification={obj.id}",
            _("View results"),
        )
        return results_link

    @admin.display(description=_("Notifications"))
    def notifications_display(self, obj: Certification):
        notifications_link = format_html(
            '<a href="{}" class="fr-link fr-icon-mail-line fr-link--icon-left">{}</a>',
            reverse(
                "admin:certification_certificationnotification_changelist",
            )
            + f"?certification={obj.id}",
            _("See notifications for this certification"),
        )
        return notifications_link


@admin.register(QuizResult)
class QuizResultAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("quiz", "user", "score_with_passing_score", "is_passed", "created")
    fields = ("quiz", "user", "score", "is_passed")
    readonly_fields = ("created",)
    list_filter = ("is_passed", "quiz__certification__name", "quiz__certification")
    search_fields = ("user__email",)

    @admin.display(description=_("Score"))
    def score_with_passing_score(self, obj: QuizResult) -> str:
        return f"{obj.score} / {obj.quiz.passing_score}"

import csv
from datetime import timedelta
from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.http import HttpRequest, HttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import slugify
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
    actions = ("export_passed_users_as_csv",)
    fields = (
        "type_of",
        "name",
        "description",
        "num_days_valid",
        "invitation_to_complete_email_template_path",
        "success_email_template_path",
    )

    form = CertificationAdminForm

    @admin.action(description=_("Export passed users as CSV"))
    def export_passed_users_as_csv(self, request: HttpRequest, queryset):
        response = HttpResponse(content_type="text/csv")

        def get_passed_users_export_filename(queryset) -> str:
            certification_name = "selected-certifications"
            if queryset.count() == 1:
                certification_name = slugify(queryset.first().name)
            timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
            return f"export-cert-{certification_name}-{timestamp}.csv"

        filename = get_passed_users_export_filename(queryset)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "certification",
                "first_name",
                "last_name",
                "email",
                "score",
                "quiz_url",
                "certificate_date",
                "expiration_date",
            ]
        )

        results = (
            QuizResult.objects.filter(
                quiz__certification__in=queryset,
                is_passed=True,
            )
            .select_related("user", "quiz", "quiz__certification")
            .order_by("quiz__certification_id", "user_id", "-created", "-id")
        )

        def escape_csv_cell(value):
            dangerous_csv_cell_prefixes = ("=", "+", "-", "@", "\t", "\r")
            if isinstance(value, str) and value.startswith(dangerous_csv_cell_prefixes):
                return f"'{value}"
            return value

        exported_keys = set()
        for result in results:
            certification = result.quiz.certification
            key = (certification.id, result.user_id)
            if key in exported_keys:
                continue
            exported_keys.add(key)

            certificate_date = timezone.localdate(result.created).isoformat()
            expiration_date = ""
            if certification.num_days_valid is not None:
                expiration_date = timezone.localdate(
                    result.created + timedelta(days=certification.num_days_valid)
                ).isoformat()

            writer.writerow(
                [
                    escape_csv_cell(certification.name),
                    escape_csv_cell(result.user.first_name),
                    escape_csv_cell(result.user.last_name),
                    escape_csv_cell(result.user.email),
                    result.score,
                    result.quiz.url,
                    certificate_date,
                    expiration_date,
                ]
            )

        return response

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

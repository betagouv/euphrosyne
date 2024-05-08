from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin

from .models import Certification, CertificationType, QuizzCertification, QuizzResult


class QuizzCertificationInline(LabAdminAllowedMixin, admin.StackedInline):
    model = QuizzCertification
    verbose_name = _("Quizz certification")

    fields = ("url", "passing_score")


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

    def get_inlines(
        self, request: HttpRequest, obj: Certification | None
    ) -> list[InlineModelAdmin]:
        if obj and obj.type_of == CertificationType.QUIZZ:
            return [QuizzCertificationInline]
        return []


@admin.register(QuizzResult)
class QuizzResultAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("quizz", "user", "score", "is_passed", "created")
    fields = ("quizz", "user", "score", "is_passed")
    readonly_fields = ("created",)

from django.db import migrations


def create_radiation_protection_certification(apps, schema_editor):
    """Create the radiation protection certification."""
    from ..constants import (
        RADIATION_PROTECTION_CERTIFICATION_NAME,
        RADIATION_PROTECTION_CERTIFICATION_NUM_DAYS_VALID,
    )
    from certification.certifications.models import CertificationType

    Certification = apps.get_model("certification", "Certification")

    Certification.objects.get_or_create(
        name=RADIATION_PROTECTION_CERTIFICATION_NAME,
        defaults={
            "type_of": CertificationType.QUIZ,
            "description": "Radiation protection certification for AGLAE beamline users",
            "num_days_valid": RADIATION_PROTECTION_CERTIFICATION_NUM_DAYS_VALID,
            "invitation_to_complete_email_template_path": "radiation_protection/email/radioprotection_invitation.html",
            "success_email_template_path": "radiation_protection/email/radioprotection_success.html",
        },
    )


def remove_radiation_protection_certification(apps, schema_editor):
    """Remove the radiation protection certification."""
    from ..constants import RADIATION_PROTECTION_CERTIFICATION_NAME

    Certification = apps.get_model("certification", "Certification")
    Certification.objects.filter(name=RADIATION_PROTECTION_CERTIFICATION_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("certification", "0002_alter_certificationnotification_type_of"),
    ]

    operations = [
        migrations.RunPython(
            create_radiation_protection_certification,
            remove_radiation_protection_certification,
        ),
    ]

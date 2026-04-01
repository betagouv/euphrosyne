from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_management", "0004_backfill_project_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="lifecycleoperation",
            name="from_data_deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="lifecycleoperation",
            name="from_data_deletion_error",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="lifecycleoperation",
            name="from_data_deletion_status",
            field=models.CharField(
                choices=[
                    ("NOT_REQUESTED", "Not requested"),
                    ("RUNNING", "Running"),
                    ("SUCCEEDED", "Succeeded"),
                    ("FAILED", "Failed"),
                ],
                default="NOT_REQUESTED",
                max_length=16,
            ),
        ),
    ]

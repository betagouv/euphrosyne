# Generated by Django 4.0a1 on 2021-11-04 10:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0006_project_admin_project_comments_project_run_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='run_date',
        ),
    ]

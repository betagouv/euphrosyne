# Generated by Django 5.0.6 on 2024-07-15 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_request", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="datarequest",
            options={
                "verbose_name": "data request",
                "verbose_name_plural": "data requests",
            },
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created"),
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="description",
            field=models.TextField(blank=True, verbose_name="Description"),
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="Modified"),
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="user_email",
            field=models.EmailField(max_length=254, verbose_name="User email"),
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="user_first_name",
            field=models.CharField(max_length=150, verbose_name="First name"),
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="user_institution",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Institution"
            ),
        ),
        migrations.AlterField(
            model_name="datarequest",
            name="user_last_name",
            field=models.CharField(max_length=150, verbose_name="Last name"),
        ),
    ]

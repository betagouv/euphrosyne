# Generated by Django 5.1.1 on 2024-11-15 17:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("standard", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="measuringpointstandard",
            options={
                "verbose_name": "measuring point standard",
                "verbose_name_plural": "measuring point standards",
            },
        ),
        migrations.AlterModelOptions(
            name="standard",
            options={"verbose_name": "standard", "verbose_name_plural": "standards"},
        ),
    ]
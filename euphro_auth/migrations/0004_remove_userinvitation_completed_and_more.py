# Generated by Django 4.0a1 on 2021-09-30 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('euphro_auth', '0003_userinvitation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userinvitation',
            name='completed',
        ),
        migrations.AddField(
            model_name='user',
            name='invitation_completed',
            field=models.BooleanField(default=False, verbose_name='invitation completed'),
        ),
    ]

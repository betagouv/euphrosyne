# Generated by Django 4.0a1 on 2021-09-28 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('euphro_auth', '0002_load_group_fixture'),
        ('user_management', '0002_remove_userinvitation_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='euphro_auth.user'),
        ),
    ]

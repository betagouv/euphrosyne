# Generated by Django 3.2.7 on 2021-09-09 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='Date this entry was first created', verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, help_text='Date this entry was most recently changed.', verbose_name='Modified')),
                ('status', models.IntegerField(choices=[(1, 'Open'), (2, 'Closed')], default=1, verbose_name='Status')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Experiment name')),
                ('date', models.DateTimeField(blank=True, help_text='Date of the experiment.', verbose_name='Experiment date')),
                ('particle_type', models.IntegerField(choices=[(1, 'Proton'), (2, 'Alpha particle'), (3, 'Deuton')], verbose_name='Particle type')),
            ],
        ),
    ]

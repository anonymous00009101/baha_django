# Generated by Django 5.2.1 on 2025-05-09 16:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speech', '0002_audiorecord'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SpeechReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audio_file', models.FileField(upload_to='analyzed_audio/')),
                ('recognized_text', models.TextField()),
                ('analysis', models.TextField()),
                ('wpm', models.FloatField()),
                ('pause_count', models.IntegerField()),
                ('total_pause_duration', models.FloatField()),
                ('clarity', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

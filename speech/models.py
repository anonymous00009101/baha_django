# filepath: speech/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Поле для даты создания

    def __str__(self):
        return self.user.username

class AudioRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_records')
    file = models.FileField(upload_to='audio/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processed', 'Processed')], default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"

class SpeechReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='analyzed_audio/')
    recognized_text = models.TextField()
    analysis = models.TextField()
    wpm = models.FloatField()  # Words per minute
    pause_count = models.IntegerField()
    total_pause_duration = models.FloatField()
    clarity = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Speech Report ({self.created_at}) - {self.user.username}"

from django import forms
from .models import UserProfile, AudioRecord

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']

class AudioRecordForm(forms.ModelForm):
    class Meta:
        model = AudioRecord
        fields = ['file']
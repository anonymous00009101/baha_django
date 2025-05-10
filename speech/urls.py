# filepath: speech/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('signup/', views.signup, name='signup'),  # Маршрут для регистрации
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('upload/', views.upload_audio, name='upload_audio'),
    path('audio_list/', views.audio_list, name='audio_list'),
    path('record/', views.record_audio, name='record_audio'),  # Новый маршрут
    path('telegram/', views.telegram_web_app, name='telegram_web_app'),
    path('send_message/', views.send_message_to_bot, name='send_message_to_bot'),
    path('send_audio_to_bot/', views.send_audio_to_bot, name='send_audio_to_bot'),
    path('analyze_audio/', views.analyze_audio, name='analyze_audio'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analysis_history/', views.analysis_history, name='analysis_history'),
    path('upgrade_subscription/', views.upgrade_subscription, name='upgrade_subscription'),
]
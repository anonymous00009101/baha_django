# filepath: speech/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('signup/', views.signup, name='signup'),  # Маршрут для регистрации
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
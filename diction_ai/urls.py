from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from speech import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('speech/', include('speech.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Встроенные маршруты для входа/выхода
    path('', lambda request: redirect('login')),  # Перенаправление на страницу входа
    path('audio_list/', views.audio_list, name='audio_list'),
    path('audio/delete/<int:pk>/', views.delete_audio, name='delete_audio'),
]

# Обработка медиафайлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
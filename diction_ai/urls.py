from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Встроенные маршруты для входа/выхода
    path('', lambda request: redirect('login')),  # Перенаправление на страницу входа
    path('', include('speech.urls')),  # Подключение маршрутов приложения speech
]

# Обработка медиафайлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
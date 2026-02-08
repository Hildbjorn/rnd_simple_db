"""
Настройки маршрутов проекта RnD Simple DB
Copyright (c) 2026 Artem Fomin
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # маршрут к админке Django
    path('admin/', admin.site.urls),
    # маршрут к главной странице
    path('', include('rnd.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
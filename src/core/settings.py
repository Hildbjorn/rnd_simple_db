"""
Настройки проекта RnD Simple DB
Copyright (c) 2026 Artem Fomin
"""

import os
from pathlib import Path

# ============================= БАЗОВЫЕ НАСТРОЙКИ =============================

# Базовый директория проекта (корневая папка проекта)
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ
SECRET_KEY = 'django-insecure-#@vm788!mz-a^=+c^42f1tcl6q1f_(l51m@-xiu2-n+tf7u^7-'

# Режим отладки (включать только для разработки!)
DEBUG = True

# Разрешенные хосты (для production указывать конкретные домены)
ALLOWED_HOSTS = []


# Базовые приложения Django

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Кастомные приложения проекта
LOCAL_APPS = [
    'rnd',
]

# Объединение всех приложений
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

# Промежуточные слои (обработчики запросов)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =========================== КОНФИГУРАЦИЯ ШАБЛОНОВ ==========================

# Корневой конфигуратор URL
ROOT_URLCONF = 'core.urls'

# Настройки шаблонов
TEMPLATES_BASE_DIR = os.path.join(BASE_DIR, 'templates')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_BASE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =============================== БАЗА ДАННЫХ =================================

# Конфигурация базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'rnd_simple_db.sqlite3',
    }
}


# ============================= АУТЕНТИФИКАЦИЯ ================================

# Валидаторы паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# =========================== ИНТЕРНАЦИОНАЛИЗАЦИЯ =============================

# Языковые настройки
LANGUAGE_CODE = 'ru'                  # Язык по умолчанию
TIME_ZONE = 'Europe/Moscow'           # Часовой пояс
USE_I18N = True                       # Включение интернационализации
USE_L10N = True                       # Включение локализации
USE_TZ = True                         # Использование часовых поясов

# Форматы даты и времени
DATE_FORMAT = 'd.m.Y'
DATETIME_FORMAT = 'd.m.Y H:i'
SHORT_DATE_FORMAT = 'd.m.Y'
SHORT_DATETIME_FORMAT = 'd.m.Y H:i'

# =========================== СТАТИЧЕСКИЕ ФАЙЛЫ ==============================

# Конфигурация статических файлов (CSS, JavaScript, изображения)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Папки со статикой
STATIC_ROOT = BASE_DIR / 'staticfiles'          # Финалная сборка статики

# Медиа-файлы (загружаемые пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Лимиты загрузки файлов
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024   # 50MB

# ============================= ПРОЧИЕ НАСТРОЙКИ ==============================

# Авто-поле для моделей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Корневое приложение WSGI
WSGI_APPLICATION = 'core.wsgi.application'
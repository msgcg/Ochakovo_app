import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-ochakovo-career-hub-production-key-2026')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'careers.apps.CareersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'careers.middleware.VisitorTrackingMiddleware',
]

ROOT_URLCONF = 'ochakovo_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'careers.context_processors.ochakovo_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ochakovo_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Whitenoise storage for production static files compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sber GigaChat & SaluteSpeech configuration
GIGACHAT_CLIENT_ID = os.getenv('GIGACHAT_CLIENT_ID', '')
GIGACHAT_CLIENT_SECRET = os.getenv('GIGACHAT_CLIENT_SECRET', '')
GIGACHAT_AUTH_KEY = os.getenv('GIGACHAT_AUTH_KEY', '')
GIGACHAT_SCOPE = os.getenv('GIGACHAT_SCOPE', 'GIGACHAT_API_PERS')
GIGACHAT_MODEL = os.getenv('GIGACHAT_MODEL', 'GigaChat-Max')
SALUTESPEECH_AUTH_KEY = os.getenv('SALUTESPEECH_AUTH_KEY', '')
SALUTESPEECH_SCOPE = os.getenv('SALUTESPEECH_SCOPE', 'SALUTE_SPEECH_PERS')

# GGML / Whisper Hardware Acceleration Configuration
GGML_ACCELERATION = os.getenv('GGML_ACCELERATION', os.getenv('GGML_MODE', 'auto')).strip().lower()
GGML_VULKAN_FALLBACK_CPU = os.getenv('GGML_VULKAN_FALLBACK_CPU', 'True').strip().lower() in ('true', '1', 'yes')

# Security headers for PWA & SEO
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'



# VK ID OAuth 2.0 configuration
VK_CLIENT_ID = os.getenv('VK_CLIENT_ID', '').strip()
VK_CLIENT_SECRET = os.getenv('VK_CLIENT_SECRET', '').strip()
VK_REDIRECT_URI = os.getenv('VK_REDIRECT_URI', '').strip()

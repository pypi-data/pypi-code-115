import os
from pathlib import Path
from re import match

import yaml
from django.utils import timezone

from expressmoney.utils import get_secret

BASE_DIR = Path(__file__).resolve().parent.parent
with open(f'{BASE_DIR}/app.yaml') as gae_conf:
    gae_conf = yaml.safe_load(gae_conf)
SERVICE = gae_conf.get('service')
IS_PROD = True if match(r'projects/expressmoney/\.*', gae_conf.get('vpc_access_connector').get('name')) else False
IS_LOCAL = False if os.getenv('GAE_APPLICATION') else True
DEBUG = False if IS_PROD else True

ALLOWED_HOSTS = (
    '127.0.0.1',
    '.expressmoney.com',
    f'.{SERVICE}-dot-expressmoney.appspot.com',
    f'.{SERVICE}-dot-expressmoney.ew.r.appspot.com',
    '.expressmoney.appspot.com',
    '.expressmoney.ew.r.appspot.com',
    f'.{SERVICE}-dot-expressmoney-dev-1.appspot.com',
    f'.{SERVICE}-dot-expressmoney-dev-1.ew.r.appspot.com',
    '.expressmoney-dev-1.appspot.com',
    '.expressmoney-dev-1.ew.r.appspot.com',
)


MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'conf.urls'

TEMPLATES = (
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ),
        },
    },
)

WSGI_APPLICATION = 'conf.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': os.getenv('PAGE_SIZE', 1),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%S",
    'DEFAULT_RENDERER_CLASSES':
        ('rest_framework.renderers.JSONRenderer',) if IS_PROD else
        ('rest_framework.renderers.JSONRenderer', 'rest_framework.renderers.BrowsableAPIRenderer',),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        # 'view_name': '1/minute' if not os.getenv('IS_DISABLE_THROTTLING', False) else '10/minute',
    },
}

AUTHENTICATION_BACKENDS = ('expressmoney.django.authentications.BackendAuthentication',)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timezone.timedelta(minutes=5) if IS_PROD else timezone.timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timezone.timedelta(days=1) if IS_PROD else timezone.timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'AUTH_HEADER_NAME': 'HTTP_X_FORWARDED_AUTHORIZATION',  # X-Forwarded-Authorization
}

CORS_ALLOWED_ORIGINS = (
    "http://127.0.0.1:8000",
)


SECRET_KEY = get_secret('SECRET_KEY')
IAP_CLIENT_ID = get_secret('IAP_CLIENT_ID')
DB_HOST = get_secret('DB_HOST')
DB_USER = get_secret('DB_USER')
DB_PASSWORD = get_secret('DB_PASSWORD')
DB_HOST_AUTH = get_secret('DB_HOST_AUTH')
DB_USER_AUTH = get_secret('DB_USER_AUTH')
DB_PASSWORD_AUTH = get_secret('DB_PASSWORD_AUTH')

DATABASE_ROUTERS = ('expressmoney.django.db_router.AuthRouter',)
# .\cloud_sql_proxy_x64.exe -enable_iam_login -instances="expressmoney:europe-west1:prod"=tcp:5432
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1' if IS_LOCAL else DB_HOST,
        'PORT': '5432',
        'NAME': SERVICE,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'CONN_MAX_AGE': 60,
        # 'ATOMIC_REQUESTS': True, IMPORTANT: DO NOT ENABLE
    },
    'auth_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1' if IS_LOCAL else DB_HOST_AUTH,
        'PORT': '5432',
        'NAME': 'auth',
        'USER': DB_USER_AUTH,
        'PASSWORD': DB_PASSWORD_AUTH,
        'CONN_MAX_AGE': 60,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://10.132.0.12:6379',
        'KEY_PREFIX': 'prod' if IS_PROD else 'dev'
    }
}

# for django-toolbar
INTERNAL_IPS = ('127.0.0.1',)

LOCALE_PATHS = (os.path.join(BASE_DIR, 'conf/locale'),)

# Security settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

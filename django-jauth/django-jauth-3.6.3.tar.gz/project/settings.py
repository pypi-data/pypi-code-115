from .base_settings import *  # noqa

ALLOWED_HOSTS = ['localhost.kajala.com']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'p6s-tt=c5%mekou#1y2mj5-fu4!n1ocxk94k8tvwujh6-!5#cf'  # noqa

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'django_jauth',
        'USER': 'dev',
        'PASSWORD': 'dev',
        'HOST': 'localhost',
        'PORT': 5432,
        'CONN_MAX_AGE': 180,
    },
}

# Account kit

ACCOUNT_KIT_API_URL = 'https://graph.accountkit.com/v1.3'
# ACCOUNT_KIT_APP_ID = '816317165422097'  # JobClick.vn
# ACCOUNT_KIT_APP_SECRET = 'bb2c5b75ef0007b8c6e39762512ca7dd'  # noqa
# ACCOUNT_KIT_REDIRECT_URL = 'https://api.jobclick.vn/accounts/account-kit-redirect'
ACCOUNT_KIT_APP_ID = '1665638637020288'  # Vuokrahelppi.fi
ACCOUNT_KIT_APP_SECRET = 'da2466317755c3d35587739365a388ed'  # noqa
ACCOUNT_KIT_REDIRECT_URL = 'https://vuokrahelppi.fi/accounts/account-kit-redirect'

# Facebook

FACEBOOK_API_URL = 'https://graph.facebook.com/v3.3'
# FACEBOOK_APP_ID = '816317165422097'  # JobClick.vn
# FACEBOOK_APP_SECRET = '2c4db23547a58f6531fb90af7d7802ee'  # noqa
# FACEBOOK_REDIRECT_URL = 'https://api.jobclick.vn/accounts/facebook-redirect'
FACEBOOK_APP_ID = '1665638637020288'  # Vuokrahelppi.fi
FACEBOOK_APP_SECRET = '7a683e2dd2b37ba5ff600afb4f93202a'  # noqa
FACEBOOK_REDIRECT_URL = 'https://vuokrahelppi.fi/accounts/facebook-redirect'

# Google

GOOGLE_API_URL = 'https://www.googleapis.com'
# GOOGLE_APP_ID = '324641390827-uvjal2fqnqeddpatgvfl0jt7png2nack.apps.googleusercontent.com'  # JobClick.vn
# GOOGLE_APP_SECRET = '92NWmE-Grto331XoINHadBF8'  # noqa
# GOOGLE_REDIRECT_URL = 'https://api.jobclick.vn/accounts/google-redirect'
GOOGLE_APP_ID = '507856415676-hgjibjqiv55jdcv6atu9ucamlqv2hcaq.apps.googleusercontent.com'  # Vuokrahelppi.fi
GOOGLE_APP_SECRET = 'hpdtKo7PCi_6O9RticN2LVey'  # noqa
GOOGLE_REDIRECT_URL = 'https://vuokrahelppi.fi/accounts/google-redirect'

# JAuth configuration

# JAUTH_AUTHENTICATION_SUCCESS_REDIRECT = '/'  # if missing then only postMessage is sent
# JAUTH_AUTHENTICATION_ERROR_REDIRECT = '/accounts/login'  # if missing then only postMessage is sent
JAUTH_AUTHENTICATION_SUCCESS_REDIRECT = None
JAUTH_AUTHENTICATION_ERROR_REDIRECT = None

"""
Django settings for ucf project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()  # only for local development

# ============================================================
# BASE PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# CLOUDINARY CONFIGURATION (persistent media storage)
# ============================================================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    'TIMEOUT': 300,   # 5 minutes – allows slow mobile uploads
}

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-fa9i+i4$h4n=-zjbsvh$ujk48lqnf@6@#213&z++m^u(myz+n9'
)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,.onrender.com'
).split(',')

# ============================================================
# APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'cloudinary_storage',
    'cloudinary',
    'imagekit',
    'members.apps.MembersConfig',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'pwa',
]

# ============================================================
# STORAGES (Cloudinary for media, default for static)
# ============================================================
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'ucf.urls'

# ============================================================
# TEMPLATES
# ============================================================
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
                'members.context_processors.currency_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ucf.wsgi.application'

# ============================================================
# DATABASE
# Uses DATABASE_URL if valid, otherwise falls back to SQLite
# ============================================================
database_url = os.environ.get('DATABASE_URL', '').strip()

if database_url:
    try:
        DATABASES = {
            'default': dj_database_url.parse(database_url, conn_max_age=600)
        }
        print("✅ Connected to PostgreSQL database via DATABASE_URL")
    except Exception as e:
        print(f"⚠️ Error parsing DATABASE_URL: {e}. Falling back to SQLite.")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    print("⚠️ No DATABASE_URL found. Using SQLite.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kampala'
USE_I18N = True
USE_TZ = True

# ============================================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================
# MEDIA FILES (local fallback – not used if Cloudinary is active)
# ============================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# UPLOAD SIZE LIMITS
# iPhone photos can be 5–15MB. These settings prevent
# timeouts and "file too large" errors on mobile uploads.
# ============================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024    # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024    # 10 MB

# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# AUTHENTICATION
# ============================================================
LOGIN_URL = '/members/login/'
LOGIN_REDIRECT_URL = '/dashboard/'          # regular login → dashboard
LOGOUT_REDIRECT_URL = 'login'

# Allauth-specific redirects (only used for first-time signups)
ACCOUNT_SIGNUP_REDIRECT_URL = '/members/complete-profile/'
SOCIALACCOUNT_SIGNUP_REDIRECT_URL = '/members/complete-profile/'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# ============================================================
# CSRF / SESSION / COOKIE SETTINGS
# Tuned for compatibility with mobile browsers (Safari,
# Brave, in-app browsers, older Android browsers).
# ============================================================
CSRF_TRUSTED_ORIGINS = [
    'https://ucf-system.onrender.com',
    'http://ucf-system.onrender.com',
]

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_FAILURE_VIEW = 'members.views.custom_csrf_failure'

# ============================================================
# REVERSE PROXY / HTTPS (Render sits behind a proxy)
# ============================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ============================================================
# PWA CONFIGURATION (University Community Fellowship)
# ============================================================
PWA_APP_NAME = 'UCF'
PWA_APP_DESCRIPTION = "University Community Fellowship — Friends for Life"
PWA_APP_THEME_COLOR = '#6B1F2E'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_START_URL = '/dashboard/'
PWA_APP_ORIENTATION = 'any'

PWA_APP_ICONS = [
    {
        'src': '/static/icons/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png',
    },
    {
        'src': '/static/icons/icon-512x512.png',
        'sizes': '512x512',
        'type': 'image/png',
    }
]

PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/icons/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png',
    }
]

PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/icons/icon-512x512.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)',
    }
]

PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en'

# ============================================================
# DJANGO-ALLAUTH CONFIGURATION
# ============================================================

# Enable automatic signup — user is created without a form
SOCIALACCOUNT_AUTO_SIGNUP = True

# Trust Google's verified emails (safe for Google)
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# Google provider configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
        'EMAIL_AUTHENTICATION': True,
        'VERIFIED_EMAIL': True,
    }
}

# Custom adapter to auto-populate Member + profile picture
SOCIALACCOUNT_ADAPTER = 'members.adapters.UCFSocialAccountAdapter'

# Let allauth use our own login template
ACCOUNT_LOGIN_TEMPLATE = 'login.html'
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'

# Social login button on GET (safer and clearer)
SOCIALACCOUNT_LOGIN_ON_GET = True

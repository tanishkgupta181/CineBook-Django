
import os
from pathlib import Path

from dotenv import load_dotenv
import dj_database_url


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")


# ==========================================
# SECURITY
# ==========================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-change-this-secret-key"
)

TMDB_API_KEY = os.getenv(
    "TMDB_API_KEY"
)

DEBUG = os.getenv(
    "DEBUG",
    "True"
).lower() == "true"


# ==========================================
# ALLOWED HOSTS
# ==========================================

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "192.168.0.105",
    "testserver",
]

# Railway public domain
railway_domain = os.getenv(
    "RAILWAY_PUBLIC_DOMAIN",
    "cinebook-django-production.up.railway.app"
).strip()

# Prevent accidental https:// inside ALLOWED_HOSTS
railway_domain = railway_domain.replace(
    "https://",
    ""
).replace(
    "http://",
    ""
).rstrip("/")

if railway_domain:
    ALLOWED_HOSTS.append(
        railway_domain
    )

# Optional custom hosts
extra_allowed_hosts = os.getenv(
    "ALLOWED_HOSTS",
    ""
)

if extra_allowed_hosts:
    ALLOWED_HOSTS.extend(
        host.strip()
        for host in extra_allowed_hosts.split(",")
        if host.strip()
    )


# ==========================================
# CSRF TRUSTED ORIGINS
# ==========================================

CSRF_TRUSTED_ORIGINS = [
    "https://cinebook-django-production.up.railway.app",
]

# Add Railway domain dynamically
if railway_domain:
    CSRF_TRUSTED_ORIGINS.append(
        f"https://{railway_domain}"
    )

# Optional custom CSRF origins
extra_csrf_origins = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    ""
)

if extra_csrf_origins:
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip().rstrip("/")
        for origin in extra_csrf_origins.split(",")
        if origin.strip()
    )

# Remove duplicate origins
CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        CSRF_TRUSTED_ORIGINS
    )
)


# ==========================================
# INSTALLED APPS
# ==========================================

INSTALLED_APPS = [

    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",

    # Project apps
    "movies",
]


# ==========================================
# MIDDLEWARE
# ==========================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise for production static files
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================
# URL CONFIGURATION
# ==========================================

ROOT_URLCONF = "bookmyshow.urls"


# ==========================================
# TEMPLATES
# ==========================================

TEMPLATES = [

    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates"
        ],

        "APP_DIRS": True,

        "OPTIONS": {

            "context_processors": [

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==========================================
# WSGI
# ==========================================

WSGI_APPLICATION = "bookmyshow.wsgi.application"


# ==========================================
# DATABASE
# ==========================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if DATABASE_URL:

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

else:

    # Local development database
    DATABASES = {

        "default": {

            "ENGINE":
                "django.db.backends.sqlite3",

            "NAME":
                BASE_DIR / "db.sqlite3",
        }
    }


# ==========================================
# PASSWORD VALIDATION
# ==========================================

AUTH_PASSWORD_VALIDATORS = []


# ==========================================
# LANGUAGE & TIMEZONE
# ==========================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ==========================================
# STATIC FILES
# ==========================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = (
    BASE_DIR / "staticfiles"
)


# ==========================================
# WHITENOISE
# ==========================================

STORAGES = {

    "default": {
        "BACKEND":
            "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND":
            (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
    },
}


# ==========================================
# MEDIA FILES
# ==========================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ==========================================
# DEFAULT PRIMARY KEY
# ==========================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ==========================================
# EMAIL CONFIGURATION - RESEND
# ==========================================

# Resend HTTPS API key
# Railway provides this through the
# RESEND_API_KEY service variable.

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY"
)

# Default sender used by the application.
# The actual sending in tasks.py is done
# through the Resend HTTPS API.

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "CineBook <onboarding@resend.dev>"
)


# ==========================================
# RAZORPAY PAYMENT GATEWAY
# ==========================================

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID"
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET"
)


# ==========================================
# CELERY + REDIS
# ==========================================

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0"
)

CELERY_BROKER_URL = REDIS_URL

CELERY_RESULT_BACKEND = REDIS_URL

CELERY_ACCEPT_CONTENT = [
    "json"
]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "Asia/Kolkata"


# ==========================================
# LOGIN / LOGOUT
# ==========================================

LOGIN_URL = "/accounts/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/accounts/login/"


# ==========================================
# SESSION
# ==========================================

# Login session expires when browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
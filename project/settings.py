from os import getenv
from pathlib import Path

ENVIRONMENT = getenv("ENVIRONMENT", "dev")
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = getenv("SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "compressor",
    "coltrane",
    "django_unicorn",
]

INTERNAL_APPS = [
    "unicorn",
    "www",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + INTERNAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_DIRS = (BASE_DIR / "static",)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False
COMPRESS_CACHEABLE_PRECOMPILERS = ("text/javascript",)
COMPRESS_PRECOMPILERS = ()
COMPRESS_CSS_HASHING_METHOD = "content"
COMPRESS_CSS_FILTERS = [
    "compressor.filters.css_default.CssRelativeFilter",
    "compressor.filters.cssmin.rCSSMinFilter",
]
COMPRESS_STORAGE = "compressor.storage.GzipCompressorFileStorage"

APPEND_SLASH = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

UNICORN = {
    "RELOAD_SCRIPT_ELEMENTS": True,
}

ANALYTICS_HTML = getenv("ANALYTICS_HTML")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[%(asctime)s][%(levelname)s] %(name)s "
            "%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "verbose": {
            "format": (
                "%(asctime)s [%(process)d] [%(levelname)s] "
                + "pathname=%(pathname)s lineno=%(lineno)s "
                + "funcname=%(funcName)s %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "django_rich_logging": {
            "class": "django_rich_logging.logging.DjangoRequestHandler",
            # "filters": ["require_debug_true"],
            "level": "INFO",
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "PytzUsageWarning": {"handlers": ["null"]},
        # "django.server": {"handlers": ["console"], "level": "WARNING"},
        "django.server": {"handlers": ["django_rich_logging"], "level": "INFO"},
        "django.request": {"level": "INFO"},
    },
}
COLTRANE = {"MARKDOWN_RENDERER": "mistune"}

GIT_VERSION = getenv("CAPROVER_GIT_COMMIT_SHA")


if ENVIRONMENT == "live":
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

    DEBUG = False
    ALLOWED_HOSTS = getenv("ALLOWED_HOSTS", "").split(",")
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]

    COMPRESS_OFFLINE = True

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": getenv("REDIS_URL"),
        }
    }

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "[%(asctime)s][%(levelname)s] %(name)s "
                "%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "verbose": {
                "format": (
                    "%(asctime)s [%(process)d] [%(levelname)s] "
                    + "pathname=%(pathname)s lineno=%(lineno)s "
                    + "funcname=%(funcName)s %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "null": {"level": "DEBUG", "class": "logging.NullHandler"},
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }

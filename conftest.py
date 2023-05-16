from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv

load_dotenv()


pytest_plugins = ["tests.account.fixtures", "tests.www.fixtures"]


def pytest_configure():
    caches = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }

    databases = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
        }
    }

    BASE_DIR = Path(__file__).resolve().parent.parent

    settings.configure(
        ENVIRONMENT="unittest",
        SECRET_KEY="this-is-a-secret",
        UNIT_TEST=True,
        CACHES=caches,
        INSTALLED_APPS=(
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.sites",
            "django.contrib.admin",
            "django.contrib.sessions",
            "compressor",
            "django_unicorn",
            "account",
            "activity",
            "unicorn",
            "www",
        ),
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "fbv.middleware.RequestMethodMiddleware",
        ],
        SITE_ID=1,
        DATABASES=databases,
        AUTH_USER_MODEL="account.User",
        ROOT_URLCONF="project.urls",
        ADMIN_SITE_BASE_URL="test-admin",
        ANALYTICS_HTML="",
        GIT_VERSION="",
        COMPRESS_ENABLED=False,
        TEMPLATES=[
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
        ],
        STATICFILES_FINDERS=(
            "django.contrib.staticfiles.finders.FileSystemFinder",
            "django.contrib.staticfiles.finders.AppDirectoriesFinder",
            "compressor.finders.CompressorFinder",
        ),
        STATIC_URL="static/",
        STATIC_ROOT=BASE_DIR / "staticfiles",
    )

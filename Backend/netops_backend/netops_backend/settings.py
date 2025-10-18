"""
Django settings for netops_backend project.
"""

from pathlib import Path
import os
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # fallback if not installed

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load env from Backend/.env reliably (try Backend/.env then project/.env)
if load_dotenv is not None:
    candidates = [
        BASE_DIR.parent / ".env",   # Backend/.env
        BASE_DIR / ".env",          # project-level .env (fallback)
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(str(p))
            break

# SECURITY: configuration via environment variables
# NOTE: For development, defaults are provided. Override in .env or host env.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-insecure-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'chatbot',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Moved to the top after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'netops_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'netops_backend.wsgi.application'


# Database
# Support both SQLite (development) and PostgreSQL (production)
# Set DATABASE_URL environment variable for PostgreSQL
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv('DATABASE_URL', '')

if DATABASE_URL and DATABASE_URL.startswith('postgresql'):
    # PostgreSQL configuration
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=int(os.getenv('DB_CONN_MAX_AGE', '600')),
            conn_health_checks=True,
        )
    }
else:
    # SQLite fallback (development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# PostgreSQL-specific settings
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default'].setdefault('OPTIONS', {
        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
        'options': '-c statement_timeout=' + os.getenv('DB_STATEMENT_TIMEOUT', '30000'),
    })


# Password validation
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


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ✅ CORS Settings to allow Next.js frontend
# Comma-separated list from env; defaults to localhost dev URLs
_cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',') if o.strip()]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt', 'origin',
    'user-agent', 'x-csrftoken', 'x-requested-with'
]
CORS_EXPOSE_HEADERS = ['content-type']
CORS_PREFLIGHT_MAX_AGE = 86400

CORS_ALLOW_CREDENTIALS = True

# Auth: AllowAny in development by default. Override in production.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

# Structured logging configuration
import logging.config
LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'

class StructuredFormatter(logging.Formatter):
    """JSON formatter with context fields for production observability."""
    def format(self, record):
        import json
        from datetime import datetime
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        # Add extra context fields if present
        if hasattr(record, 'alias'):
            log_data['alias'] = record.alias
        if hasattr(record, 'host'):
            log_data['host'] = record.host
        if hasattr(record, 'query'):
            log_data['query'] = record.query
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'strategy'):
            log_data['strategy'] = record.strategy
        if hasattr(record, 'vendor'):
            log_data['vendor'] = record.vendor
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        if hasattr(record, 'error'):
            log_data['error'] = record.error
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': StructuredFormatter,
        },
        'verbose': {
            'format': '{asctime} [{levelname}] {name} {module}.{funcName}:{lineno} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {name} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if LOG_FORMAT == 'json' else 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR.parent, 'logs', 'netops.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json' if LOG_FORMAT == 'json' else 'verbose',
        },
    },
    'loggers': {
        'chatbot': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'netops_backend': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_FRAMEWORK_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR.parent, 'logs'), exist_ok=True)

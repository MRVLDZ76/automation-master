import os
from pathlib import Path
import sys
import dj_database_url
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv
import environ  
from django.core.files.storage import FileSystemStorage

env = environ.Env()
environ.Env.read_env()
load_dotenv(dotenv_path='./.env')

BASE_DIR = Path(__file__).resolve().parent.parent
 
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true' 

DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'True').lower(
) == 'true'  # original in pro set true
 
# DEBUG = True if DEVELOPMENT_MODE else False

if DEVELOPMENT_MODE:
    BASE_URL = 'http://localhost:8000'
else:
    BASE_URL = 'https://ppall.applikuapp.com/'

# Set to 'True' in production when using S3
USE_S3 = os.getenv('USE_S3', 'False').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())
ALLOWED_HOSTS = ["*"]

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'automation',
    'django_celery_results',
    'django.contrib.postgres',
    'storages',
    'rest_framework',
]

LOGIN_URL = '/login/'  
LOGIN_REDIRECT_URL = '/dashboard/'   


CSRF_TRUSTED_ORIGINS = [
    "https://localsecrets.zoondia.org",
    "https://ppall.applikuapp.com/"
]


# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'automation.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'automation.wsgi.application'



# Configuración de la base de datos
import logging
logger = logging.getLogger(__name__)

# Log environment variables to help with debugging
db_url = os.getenv('DATABASE_URL')
dev_mode = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'
db_host = os.getenv('DB_HOST')

logger.debug(f"Environment variables for database connection: DATABASE_URL: {db_url}  DEVELOPMENT_MODE: {dev_mode} DB_HOST: {db_host}")

# Database Configuration
if dev_mode:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'ppall-automation'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'Thesecret1'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    # Determine SSL requirement based on host
    # If connecting to a development-like database, disable SSL
    ssl_required = True
    if db_url and ('localhost' in db_url or '127.0.0.1' in db_url or '2762-db' in db_url):
        ssl_required = False
        logger.info(f"Detected development database in URL: {db_url}. Disabling SSL requirement.")
    
    DATABASES = {
        'default': dj_database_url.parse(
            db_url,
            conn_max_age=600, 
            ssl_require=ssl_required)
    }
    
    # Log the final database configuration
    db_config = DATABASES['default'].copy()
    if 'PASSWORD' in db_config:
        db_config['PASSWORD'] = '***HIDDEN***'
    logger.info(f"Database configuration: {db_config}")

 
# Static and Media file settings
STATIC_URL = env.str('STATIC_URL', default="/static/")
STATIC_ROOT = env.str('STATIC_ROOT', default=BASE_DIR / 'staticfiles')
 
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG 


# Define base directories for different types of content
TASK_FILES_DIR = os.path.join('task_files')
SCRAPING_RESULTS_DIR = os.path.join('scraping_results')
BUSINESS_IMAGES_DIR = os.path.join('business_images')

# Define custom storage classes
class TaskFilesStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', os.path.join(MEDIA_ROOT, TASK_FILES_DIR))
        kwargs.setdefault('base_url', os.path.join(MEDIA_URL, TASK_FILES_DIR))
        super().__init__(*args, **kwargs)
        
    def get_available_name(self, name, max_length=None):
        # You can customize file naming here if needed
        return super().get_available_name(name, max_length)

class ScrapingResultsStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', os.path.join(MEDIA_ROOT, SCRAPING_RESULTS_DIR))
        kwargs.setdefault('base_url', os.path.join(MEDIA_URL, SCRAPING_RESULTS_DIR))
        super().__init__(*args, **kwargs)

class BusinessImagesStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', os.path.join(MEDIA_ROOT, BUSINESS_IMAGES_DIR))
        kwargs.setdefault('base_url', os.path.join(MEDIA_URL, BUSINESS_IMAGES_DIR))
        super().__init__(*args, **kwargs)

# AWS S3 settings
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
USE_S3_STORAGE = os.environ.get('USE_S3_STORAGE', 'False') == 'True'

# Use S3 as default file storage
if USE_S3_STORAGE:
    DEFAULT_FILE_STORAGE = 'automation.storage.S3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_LOCATION = 'static'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    # Local storage settings (for development)
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Static Files Storage
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DEFAULT_IMAGE_URL = os.getenv(
    'DEFAULT_IMAGE_URL',
    'https://www.localsecrets.travel/wp-content/uploads/2024/08/cropped-cropped-logo-web-1.png'
)

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Authentication Configuration
AUTH_USER_MODEL = 'automation.CustomUser'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.path.dirname(__file__), 'logs/debug.log'),  # Creates the logs directory if not exists
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_PERMISSIONS = 0o644
REQUEST_TIMEOUT = 120  # in seconds

# Database Options
DATABASE_OPTIONS = {
    'connect_timeout': 60,
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all origins in development
if not DEBUG:
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Static Files Finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Message Storage
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


# Ensure SECURITY settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# API keys and additional configs
TRANSLATION_OPENAI_API_KEY = os.getenv('GENAI_OPENAI_API_KEY')

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')

FALLBACK_1_OPENAI_API_KEY = os.getenv('FALLBACK_1_OPENAI_API_KEY')
FALLBACK_2_OPENAI_API_KEY = os.getenv('FALLBACK_2_OPENAI_API_KEY')

OPENAI_KEYS = [
    OPENAI_API_KEY,
    FALLBACK_1_OPENAI_API_KEY,
    FALLBACK_2_OPENAI_API_KEY
]

SERPAPI_KEY =  os.getenv('SERPAPI_KEY')

DEFAULT_IMAGES = 3
 
# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Task-specific settings
CELERY_TASK_ROUTES = {
    'automation.tasks.process_scraping_task': {'queue': 'scraping'},
    #'automation.tasks.bulk_business_translation': {'queue': 'translation'},
    #'automation.tasks.download_images': {'queue': 'images'},
}

# Task time limits
CELERY_TASK_TIME_LIMIT = 1800  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 1500  # 25 minutes

 
print("DEBUG: Environment variables for database connection:", file=sys.stderr)
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}", file=sys.stderr)
print(f"DEVELOPMENT_MODE: {os.getenv('DEVELOPMENT_MODE')}", file=sys.stderr)
print(f"DB_HOST: {os.getenv('DB_HOST')}", file=sys.stderr)

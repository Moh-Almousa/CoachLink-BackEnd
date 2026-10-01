
from datetime import timedelta
from pathlib import Path
import dj_database_url
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv
import os
load_dotenv()


# Read a comma-separated env variable as a list
def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY =os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework',
    'drf_spectacular',
    'users',
    'logs',
    'programs',
    'subscriptions',
    'nutritions',
    'notifications',
    'chats',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Frontend origins allowed to call the API
CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000',
)

# Trusted origins for CSRF (e.g. admin login)
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')

# رابط الفرونت اند - بينحط بالإيميلات (متل رابط دعوة اللاعب)
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000/')

ROOT_URLCONF = 'CoachLink.urls'

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

WSGI_APPLICATION = 'CoachLink.wsgi.application'
#web soket
ASGI_APPLICATION = 'CoachLink.asgi.application'

# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels.layers.InMemoryChannelLayer',
#     },
# }
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [{
                'address': os.environ.get('CHANNEL_REDIS_URL', 'redis://127.0.0.1:6379/1'),
                'socket_timeout': 10,
            }],
        },
    },
}



# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default':  dj_database_url.parse(os.environ.get('DATABASE_URL'))
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ( 
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
SIMPLE_JWT={
        'ACCESS_TOKEN_LIFETIME':timedelta(hours=1),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
        "CHECK_USER_IS_ACTIVE": False,
}
# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
# collectstatic output
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (الملفات يلي بيرفعها المستخدمين، متل شهادات الكوتش)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


SITE_ID = 1
AUTH_USER_MODEL = "users.User"

MAX_OTP_TRY = 5

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SPECTACULAR_SETTINGS = {
    "TITLE": "CoachLink API",
    "DESCRIPTION": "API documentation for CoachLink",
    "VERSION": "1.0.0",
    # No SERVERS: Swagger uses the current host
    # Separate request/response components so file fields show as binary (file picker in Swagger)
    "COMPONENT_SPLIT_REQUEST": True,
    # Keep the JWT token after refreshing the Swagger page
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
    # Views serving both list and detail URLs: show each method only on its matching URL
    "PREPROCESSING_HOOKS": ["CoachLink.schema_hooks.match_methods_to_pk_urls"],
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL=False
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# مفتاح خدمة Stripe
STRIPE_PUBLIC_KEY =os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY =os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET =os.environ.get('STRIPE_WEBHOOK_SECRET')

# مكتبة التمارين الخارجية 
EXERCISEDB_RAPIDAPI_KEY = os.environ.get('EXERCISEDB_RAPIDAPI_KEY')
EXERCISEDB_RAPIDAPI_HOST = os.environ.get('EXERCISEDB_RAPIDAPI_HOST')


# مكتبة الأطعمة الخارجية (Edamam Food Database API)
EDAMAM_APP_ID = os.environ.get('EDAMAM_APP_ID')
EDAMAM_APP_KEY = os.environ.get('EDAMAM_APP_KEY')

CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL')

# Timezone used by the beat schedule
CELERY_TIMEZONE = 'Asia/Damascus'

# Periodic tasks (celery beat)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # تذكير اللاعبين يلي اشتراكهن رح يخلص خلال 3 أيام - كل يوم الساعة 9:00 الصبح
    'send-expiry-reminders-daily': {
        'task': 'notifications.tasks.send_expiry_reminders_task',
        'schedule': crontab(hour=9, minute=0),
    },
    # تحويل الاشتراكات المنتهية من active لـ finish - كل ساعة عند الدقيقة 0
    'expire-subscriptions-hourly': {
        'task': 'subscriptions.tasks.expire_subscriptions_task',
        'schedule': crontab(minute=0),
    },
}

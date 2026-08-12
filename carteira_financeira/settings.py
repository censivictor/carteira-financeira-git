"""
Django settings for carteira_financeira project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/
"""

from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-only-troque-em-producao')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Origem do Vite dev server (frontend/) — Django 4+ valida o header Origin
# em requisições que mudam estado mesmo em HTTP puro, e o proxy do Vite não
# reescreve esse header (ele só troca o destino da requisição). Só entra em
# DEBUG (dev local); em produção o Vue já vem buildado e servido pelo
# próprio Django, mesma origem, sem precisar disso.
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost:5173', 'http://127.0.0.1:5173'] if DEBUG else [],
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'core',
    'investimentos',
    'financas',
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
]

ROOT_URLCONF = 'carteira_financeira.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'carteira_financeira.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

# Formata números como 1.234,56 (padrão brasileiro) nos templates.
USE_THOUSAND_SEPARATOR = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Cache — usado para as cotações de ações/cripto (evita estourar rate limit
# das APIs externas). FileBasedCache funciona entre múltiplos workers do
# gunicorn em produção sem precisar de Redis.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(BASE_DIR / 'cache'),
    }
}

# Tempo (segundos) que uma cotação fica em cache antes de buscar de novo.
COTACAO_CACHE_TTL = env.int('COTACAO_CACHE_TTL', default=60)

# Token opcional do brapi.dev (https://brapi.dev) — algumas rotas/planos
# exigem cadastro gratuito. Sem token, o app funciona com o que a API
# liberar publicamente.
BRAPI_TOKEN = env('BRAPI_TOKEN', default='').strip()

# Chave opcional da CoinGecko (plano Demo gratuito) — aumenta o limite de
# requisições por minuto nas buscas/cotações de cripto.
COINGECKO_API_KEY = env('COINGECKO_API_KEY', default='').strip()


# Render (como a maioria dos PaaS) termina TLS na borda e repassa a
# requisição pro Gunicorn em HTTP puro, sinalizando o protocolo original no
# header X-Forwarded-Proto — sem isso, o Django acha que a conexão não é
# segura: SECURE_SSL_REDIRECT vira loop de redirect e os cookies "Secure"
# nunca voltam no browser.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# API (consumida pelo front Vue em desenvolvimento — frontend/) — auth por
# sessão Django (mesmo login de sempre), não JWT. O Vite dev server faz
# proxy de /api pro Django, então cookie de sessão/CSRF funcionam sem
# precisar de django-cors-headers.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

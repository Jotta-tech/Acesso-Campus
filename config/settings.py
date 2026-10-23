"""
Configurações do projeto Acesso Campus (protótipo acadêmico).

Valores sensíveis ou que mudam entre ambientes (SECRET_KEY, DEBUG,
ALLOWED_HOSTS) são lidos de variáveis de ambiente ou do arquivo .env.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o arquivo .env (se existir) para dentro de os.environ.
load_dotenv(BASE_DIR / ".env")


def _env_bool(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "yes", "on", "sim"}


# --- Segurança -------------------------------------------------------------

# Por padrão DEBUG é False: o modo seguro é o padrão.
DEBUG = _env_bool("DEBUG", False)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        # Chave insegura, permitida somente em desenvolvimento local.
        SECRET_KEY = "django-insecure-somente-para-desenvolvimento-local"
    else:
        raise ImproperlyConfigured(
            "Defina a variável SECRET_KEY (copie .env.example para .env)."
        )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

# Origens confiáveis para desenvolvimento local
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# --- Aplicações ------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "rest_framework",
    "django_filters",
    # Projeto
    "ocorrencias",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Os templates abaixo são necessários apenas para o Django Admin.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Banco de dados --------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalização ---------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Belem"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework -------------------------------------------------

# Taxa máxima de criação de ocorrências por IP anônimo.
THROTTLE_CRIACAO_ANONIMA = os.environ.get("THROTTLE_CRIACAO_ANONIMA", "60/hour")

REST_FRAMEWORK = {
    # Basic Auth facilita testes no Postman/Insomnia (use só local ou com HTTPS).
    # Session permite usar a API logado pelo Django Admin no navegador.
    # Basic vem primeiro para que requisições sem credenciais recebam 401.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Padrão restritivo: cada view libera explicitamente o que for público.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    # Tamanho fixo: o cliente não consegue pedir páginas maiores.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_RATES": {
        "criacao_anonima": THROTTLE_CRIACAO_ANONIMA,
    },
}

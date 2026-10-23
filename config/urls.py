"""Rotas principais do projeto."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("ocorrencias.urls")),
]

# Rotas administrativas do Acesso Campus (acesso restrito)
from django.urls import path as acesso_path, include as acesso_include
urlpatterns += [acesso_path("api/acesso-admin/", acesso_include("config.acesso_auth_urls"))]

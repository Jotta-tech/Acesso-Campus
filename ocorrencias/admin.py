"""Configuração do painel administrativo nativo do Django."""
from django.contrib import admin

from .models import Ocorrencia


@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "titulo",
        "categoria",
        "localizacao",
        "prioridade",
        "status",
        "data_criacao",
        "data_atualizacao",
    )
    list_filter = ("categoria", "prioridade", "status")
    search_fields = ("titulo", "localizacao")
    readonly_fields = ("data_criacao", "data_atualizacao")
    list_per_page = 25

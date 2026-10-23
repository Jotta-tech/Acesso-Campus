"""Serializers: validam a entrada e controlam a saída da API."""
from rest_framework import serializers

from .models import Ocorrencia


class OcorrenciaSerializer(serializers.ModelSerializer):
    """Representação completa. Usado na leitura e na edição por gestores."""

    categoria_display = serializers.CharField(
        source="get_categoria_display", read_only=True
    )
    prioridade_display = serializers.CharField(
        source="get_prioridade_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Ocorrencia
        fields = [
            "id",
            "titulo",
            "descricao",
            "categoria",
            "categoria_display",
            "localizacao",
            "prioridade",
            "prioridade_display",
            "status",
            "status_display",
            "data_criacao",
            "data_atualizacao",
        ]
        read_only_fields = ["id", "data_criacao", "data_atualizacao"]


class OcorrenciaCriacaoSerializer(serializers.ModelSerializer):
    """
    Entrada da criação pública.

    Aceita SOMENTE os quatro campos abaixo. Se o cliente enviar "status" ou
    "prioridade", os valores são ignorados e valem os padrões do modelo
    (pendente / media).
    """

    class Meta:
        model = Ocorrencia
        fields = ["titulo", "descricao", "categoria", "localizacao"]


class StatusSerializer(serializers.ModelSerializer):
    """Altera somente o status. Nenhum outro campo é aceito."""

    class Meta:
        model = Ocorrencia
        fields = ["status"]
        # O modelo tem valor padrão para "status", o que tornaria o campo
        # opcional. Aqui ele precisa ser obrigatório: sem ele não há o que
        # alterar.
        extra_kwargs = {"status": {"required": True}}

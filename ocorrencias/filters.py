"""Filtros da listagem de ocorrências."""
import django_filters

from .models import Ocorrencia


class OcorrenciaFilter(django_filters.FilterSet):
    """
    Parâmetros aceitos em GET /api/ocorrencias/:

    - categoria, status, prioridade: valor exato de uma das choices do modelo
      (valores inválidos geram 400).
    - localizacao: contém o texto informado (sem diferenciar maiúsculas).
    """

    localizacao = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Ocorrencia
        fields = ["categoria", "status", "prioridade", "localizacao"]

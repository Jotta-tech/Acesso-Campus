"""Views da API do Acesso Campus."""
from django.db.models import Count
from django.http import Http404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .filters import OcorrenciaFilter
from .models import Ocorrencia
from .permissions import PodeGerenciarOcorrencias
from .serializers import (
    OcorrenciaCriacaoSerializer,
    OcorrenciaSerializer,
    StatusSerializer,
)


class CriacaoAnonimaThrottle(AnonRateThrottle):
    """Limita a criação de ocorrências por IP. Não afeta usuários logados."""

    scope = "criacao_anonima"


class OcorrenciaViewSet(viewsets.ModelViewSet):
    """
    CRUD de ocorrências.

    Público: listar, consultar e criar (com campos restritos).
    Gestores: editar (PUT/PATCH), alterar status e excluir.
    """

    queryset = Ocorrencia.objects.all()
    filterset_class = OcorrenciaFilter
    search_fields = ["titulo", "descricao"]

    def get_serializer_class(self):
        if self.action == "create":
            return OcorrenciaCriacaoSerializer
        if self.action == "alterar_status":
            return StatusSerializer
        return OcorrenciaSerializer

    def get_permissions(self):
        # Leitura (GET/HEAD/OPTIONS) e criação são públicas.
        if self.action == "create" or self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [PodeGerenciarOcorrencias()]

    def get_throttles(self):
        if self.action == "create":
            return [CriacaoAnonimaThrottle()]
        return []

    def get_object(self):
        # Mensagem de 404 em português (a padrão do Django vem em inglês).
        try:
            return super().get_object()
        except Http404:
            raise NotFound("Ocorrência não encontrada.")

    def create(self, request, *args, **kwargs):
        entrada = self.get_serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        ocorrencia = entrada.save()
        # A resposta usa a representação completa (com id, status e datas).
        saida = OcorrenciaSerializer(
            ocorrencia, context=self.get_serializer_context()
        )
        return Response(saida.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="status")
    def alterar_status(self, request, pk=None):
        """PATCH /api/ocorrencias/{id}/status/ com {"status": "..."}."""
        ocorrencia = self.get_object()
        entrada = self.get_serializer(ocorrencia, data=request.data)
        entrada.is_valid(raise_exception=True)
        entrada.save()
        saida = OcorrenciaSerializer(
            ocorrencia, context=self.get_serializer_context()
        )
        return Response(saida.data)


def _contar_por(campo, valores_possiveis):
    """
    Conta ocorrências agrupadas por `campo`, incluindo valores com zero.

    O order_by() vazio é necessário: sem ele, o ordering padrão do modelo
    entraria no GROUP BY e quebraria a agregação.
    """
    contagem = dict(
        Ocorrencia.objects.order_by()
        .values_list(campo)
        .annotate(total=Count("id"))
    )
    return {valor: contagem.get(valor, 0) for valor in valores_possiveis}


class DashboardView(APIView):
    """GET /api/dashboard/ - indicadores calculados direto do banco."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "total": Ocorrencia.objects.count(),
                "por_status": _contar_por("status", Ocorrencia.Status.values),
                "por_categoria": _contar_por(
                    "categoria", Ocorrencia.Categoria.values
                ),
                "por_prioridade": _contar_por(
                    "prioridade", Ocorrencia.Prioridade.values
                ),
            }
        )

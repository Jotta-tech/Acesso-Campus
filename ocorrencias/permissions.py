"""Regras de autorização do Acesso Campus."""
from rest_framework.permissions import BasePermission

# Nome do grupo criado automaticamente após o "migrate" (veja apps.py).
GRUPO_GESTORES = "Gestores"

PERMISSAO_EDITAR = "ocorrencias.change_ocorrencia"
PERMISSAO_EXCLUIR = "ocorrencias.delete_ocorrencia"


class PodeGerenciarOcorrencias(BasePermission):
    """
    Libera operações administrativas (editar, alterar status, excluir).

    - Anônimo: negado (a API responde 401).
    - Logado sem permissão: negado (403).
    - Superusuário: liberado.
    - Demais usuários: precisam da permissão nativa do Django correspondente
      (change_ocorrencia para editar/alterar status, delete_ocorrencia para
      excluir), normalmente concedida pelo grupo "Gestores".
    """

    message = "Você não tem permissão para realizar esta operação."

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if usuario.is_superuser:
            return True
        if request.method == "DELETE":
            return usuario.has_perm(PERMISSAO_EXCLUIR)
        return usuario.has_perm(PERMISSAO_EDITAR)

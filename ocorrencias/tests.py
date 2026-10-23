"""
Testes automatizados da API do Acesso Campus.

Executar com:  python manage.py test
"""
import base64
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Ocorrencia
from .permissions import GRUPO_GESTORES
from .views import CriacaoAnonimaThrottle

User = get_user_model()

SENHA = "senha-de-teste-123"

DADOS_VALIDOS = {
    "titulo": "Rampa bloqueada no Bloco A",
    "descricao": "A rampa de acesso ao Bloco A está bloqueada por entulho.",
    "categoria": "rampa",
    "localizacao": "Bloco A - Entrada principal",
}


def criar_ocorrencia(**campos):
    """Cria uma ocorrência diretamente no banco (atalho para os testes)."""
    return Ocorrencia.objects.create(**{**DADOS_VALIDOS, **campos})


def url_lista():
    return reverse("ocorrencia-list")


def url_detalhe(pk):
    return reverse("ocorrencia-detail", args=[pk])


def url_status(pk):
    return reverse("ocorrencia-alterar-status", args=[pk])


def url_dashboard():
    return reverse("dashboard")


# Hasher de senha rápido, usado SOMENTE nos testes (o padrão do Django é lento
# de propósito, o que deixaria a suíte demorada). Não afeta o ambiente real.
@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class BaseTestCase(APITestCase):
    """Cria os três perfis de usuário usados nos testes."""

    def setUp(self):
        cache.clear()  # zera os contadores do limitador de requisições
        self.superusuario = User.objects.create_superuser(
            "admin", password=SENHA
        )
        self.gestor = User.objects.create_user("gestor", password=SENHA)
        self.gestor.groups.add(Group.objects.get(name=GRUPO_GESTORES))
        self.comum = User.objects.create_user("comum", password=SENHA)


# --------------------------------------------------------------------------
# 1, 2 - Criação
# --------------------------------------------------------------------------
class CriacaoTests(BaseTestCase):
    def test_cria_ocorrencia_valida_sem_login(self):
        resp = self.client.post(url_lista(), DADOS_VALIDOS, format="json")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ocorrencia.objects.count(), 1)
        criada = Ocorrencia.objects.get()
        self.assertEqual(criada.titulo, DADOS_VALIDOS["titulo"])
        # Padrões definidos pelo sistema, não pelo cliente.
        self.assertEqual(criada.status, Ocorrencia.Status.PENDENTE)
        self.assertEqual(criada.prioridade, Ocorrencia.Prioridade.MEDIA)
        # A resposta traz a representação completa.
        self.assertEqual(resp.data["id"], criada.id)
        self.assertEqual(resp.data["status"], "pendente")
        self.assertIn("data_criacao", resp.data)

    def test_publico_nao_consegue_definir_status_nem_prioridade(self):
        dados = {**DADOS_VALIDOS, "status": "resolvida", "prioridade": "alta"}

        resp = self.client.post(url_lista(), dados, format="json")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        criada = Ocorrencia.objects.get()
        self.assertEqual(criada.status, Ocorrencia.Status.PENDENTE)
        self.assertEqual(criada.prioridade, Ocorrencia.Prioridade.MEDIA)

    def test_rejeita_dados_invalidos(self):
        # (campo, valor). Valor None significa "campo ausente".
        casos = [
            ("titulo", None),
            ("titulo", "abc"),
            ("titulo", "a" * 121),
            ("titulo", "      "),
            ("descricao", None),
            ("descricao", "curta"),
            ("descricao", "x" * 2001),
            ("categoria", None),
            ("categoria", "inexistente"),
            ("localizacao", ""),
            ("localizacao", "ab"),
            ("localizacao", "b" * 151),
        ]
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=str(valor)[:15]):
                dados = dict(DADOS_VALIDOS)
                if valor is None:
                    dados.pop(campo)
                else:
                    dados[campo] = valor

                resp = self.client.post(url_lista(), dados, format="json")

                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, resp.data)

        self.assertEqual(Ocorrencia.objects.count(), 0)

    def test_aceita_limites_maximos(self):
        dados = {
            "titulo": "t" * 120,
            "descricao": "d" * 2000,
            "categoria": "outros",
            "localizacao": "l" * 150,
        }
        resp = self.client.post(url_lista(), dados, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


# --------------------------------------------------------------------------
# 3, 4, 5 - Listagem, consulta e 404
# --------------------------------------------------------------------------
class LeituraTests(BaseTestCase):
    def test_listagem_publica_paginada_e_ordenada(self):
        criadas = [criar_ocorrencia(titulo=f"Ocorrência número {i}") for i in range(12)]

        resp = self.client.get(url_lista())

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 12)
        self.assertEqual(len(resp.data["results"]), 10)
        self.assertIsNotNone(resp.data["next"])
        # Mais recente primeiro.
        self.assertEqual(resp.data["results"][0]["id"], criadas[-1].id)

        pagina2 = self.client.get(url_lista(), {"page": 2})
        self.assertEqual(len(pagina2.data["results"]), 2)
        self.assertIsNone(pagina2.data["next"])

    def test_cliente_nao_consegue_ampliar_tamanho_da_pagina(self):
        for i in range(12):
            criar_ocorrencia(titulo=f"Ocorrência número {i}")

        resp = self.client.get(url_lista(), {"page_size": 100})

        self.assertEqual(len(resp.data["results"]), 10)

    def test_listagem_vazia(self):
        resp = self.client.get(url_lista())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)
        self.assertEqual(resp.data["results"], [])

    def test_consulta_ocorrencia_existente(self):
        o = criar_ocorrencia(prioridade="alta")

        resp = self.client.get(url_detalhe(o.pk))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], o.pk)
        self.assertEqual(resp.data["titulo"], o.titulo)
        self.assertEqual(resp.data["prioridade"], "alta")
        self.assertEqual(resp.data["prioridade_display"], "Alta")
        self.assertEqual(resp.data["status_display"], "Pendente")

    def test_ocorrencia_inexistente_retorna_404(self):
        resp = self.client.get(url_detalhe(99999))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data["detail"], "Ocorrência não encontrada.")

    def test_404_tambem_para_gestor_em_operacoes_administrativas(self):
        self.client.force_authenticate(self.gestor)
        self.assertEqual(
            self.client.patch(url_detalhe(99999), {"prioridade": "alta"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.patch(url_status(99999), {"status": "resolvida"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(url_detalhe(99999)).status_code,
            status.HTTP_404_NOT_FOUND,
        )


# --------------------------------------------------------------------------
# 6 - Filtros e pesquisa
# --------------------------------------------------------------------------
class FiltrosTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.a = criar_ocorrencia(
            titulo="Elevador quebrado no Bloco B",
            descricao="O elevador social está parado há vários dias.",
            categoria="elevador",
            localizacao="Bloco B - 1º andar",
            prioridade="alta",
            status="pendente",
        )
        self.b = criar_ocorrencia(
            titulo="Rampa sem corrimão",
            descricao="A rampa do estacionamento não tem corrimão.",
            categoria="rampa",
            localizacao="Estacionamento",
            prioridade="media",
            status="em_andamento",
        )
        self.c = criar_ocorrencia(
            titulo="Banheiro sem barra de apoio",
            descricao="Falta barra de apoio. O elevador próximo também demora.",
            categoria="banheiro",
            localizacao="Bloco B - Térreo",
            prioridade="baixa",
            status="resolvida",
        )

    def ids(self, **params):
        resp = self.client.get(url_lista(), params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return {item["id"] for item in resp.data["results"]}

    def test_filtro_por_categoria(self):
        self.assertEqual(self.ids(categoria="elevador"), {self.a.id})

    def test_filtro_por_status(self):
        self.assertEqual(self.ids(status="em_andamento"), {self.b.id})

    def test_filtro_por_prioridade(self):
        self.assertEqual(self.ids(prioridade="baixa"), {self.c.id})

    def test_filtro_por_localizacao_parcial_sem_diferenciar_maiusculas(self):
        self.assertEqual(self.ids(localizacao="bloco b"), {self.a.id, self.c.id})

    def test_pesquisa_em_titulo_e_descricao(self):
        # "elevador" está no título de A e só na descrição de C.
        self.assertEqual(self.ids(search="elevador"), {self.a.id, self.c.id})
        self.assertEqual(self.ids(search="corrimão"), {self.b.id})
        self.assertEqual(self.ids(search="inexistente-xyz"), set())

    def test_filtros_combinados(self):
        self.assertEqual(
            self.ids(localizacao="bloco b", status="resolvida"), {self.c.id}
        )
        self.assertEqual(
            self.ids(search="elevador", prioridade="alta"), {self.a.id}
        )

    def test_valor_invalido_retorna_400(self):
        for parametro, valor in [
            ("status", "concluida"),
            ("categoria", "inexistente"),
            ("prioridade", "urgente"),
        ]:
            with self.subTest(parametro=parametro):
                resp = self.client.get(url_lista(), {parametro: valor})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(parametro, resp.data)


# --------------------------------------------------------------------------
# 7 - Atualização de status
# --------------------------------------------------------------------------
class StatusTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.o = criar_ocorrencia(prioridade="alta")
        # Coloca data_atualizacao no passado para provar que ela é renovada.
        Ocorrencia.objects.filter(pk=self.o.pk).update(
            data_atualizacao=timezone.now() - timedelta(days=1)
        )
        self.o.refresh_from_db()

    def test_gestor_altera_status_sem_modificar_outros_campos(self):
        antes = self.o
        self.client.force_authenticate(self.gestor)

        resp = self.client.patch(
            url_status(antes.pk), {"status": "em_andamento"}, format="json"
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "em_andamento")
        depois = Ocorrencia.objects.get(pk=antes.pk)
        self.assertEqual(depois.status, "em_andamento")
        for campo in ("titulo", "descricao", "categoria", "localizacao", "prioridade", "data_criacao"):
            self.assertEqual(getattr(depois, campo), getattr(antes, campo), campo)
        self.assertGreater(depois.data_atualizacao, antes.data_atualizacao)

    def test_superusuario_pode_marcar_como_resolvida(self):
        self.client.force_authenticate(self.superusuario)
        resp = self.client.patch(
            url_status(self.o.pk), {"status": "resolvida"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.o.refresh_from_db()
        self.assertEqual(self.o.status, Ocorrencia.Status.RESOLVIDA)

    def test_status_invalido_ou_ausente_retorna_400_sem_alterar(self):
        self.client.force_authenticate(self.gestor)
        for corpo in ({"status": "finalizada"}, {"status": ""}, {}):
            with self.subTest(corpo=corpo):
                resp = self.client.patch(url_status(self.o.pk), corpo, format="json")
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("status", resp.data)
        self.o.refresh_from_db()
        self.assertEqual(self.o.status, Ocorrencia.Status.PENDENTE)

    def test_endpoint_de_status_ignora_outros_campos_enviados(self):
        self.client.force_authenticate(self.gestor)
        resp = self.client.patch(
            url_status(self.o.pk),
            {"status": "resolvida", "titulo": "Título adulterado", "prioridade": "baixa"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.o.refresh_from_db()
        self.assertEqual(self.o.status, "resolvida")
        self.assertEqual(self.o.titulo, DADOS_VALIDOS["titulo"])
        self.assertEqual(self.o.prioridade, "alta")

    def test_ocorrencia_resolvida_pode_ser_reaberta(self):
        self.client.force_authenticate(self.gestor)
        self.client.patch(url_status(self.o.pk), {"status": "resolvida"}, format="json")
        resp = self.client.patch(url_status(self.o.pk), {"status": "pendente"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.o.refresh_from_db()
        self.assertEqual(self.o.status, "pendente")


# --------------------------------------------------------------------------
# 8 - Permissões
# --------------------------------------------------------------------------
class PermissoesTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.o = criar_ocorrencia()

    def tentativas_administrativas(self):
        """Todas as operações que exigem gestor."""
        detalhe, status_url = url_detalhe(self.o.pk), url_status(self.o.pk)
        return [
            ("put", detalhe, {**DADOS_VALIDOS, "status": "resolvida"}),
            ("patch", detalhe, {"prioridade": "alta"}),
            ("patch", status_url, {"status": "resolvida"}),
            ("delete", detalhe, None),
        ]

    def assert_ocorrencia_intacta(self):
        self.assertTrue(Ocorrencia.objects.filter(pk=self.o.pk).exists())
        atual = Ocorrencia.objects.get(pk=self.o.pk)
        self.assertEqual(atual.status, Ocorrencia.Status.PENDENTE)
        self.assertEqual(atual.prioridade, Ocorrencia.Prioridade.MEDIA)

    def test_anonimo_recebe_401_em_operacoes_administrativas(self):
        for metodo, url, corpo in self.tentativas_administrativas():
            with self.subTest(metodo=metodo, url=url):
                resp = getattr(self.client, metodo)(url, corpo, format="json")
                self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assert_ocorrencia_intacta()

    def test_usuario_comum_recebe_403_em_operacoes_administrativas(self):
        self.client.force_authenticate(self.comum)
        for metodo, url, corpo in self.tentativas_administrativas():
            with self.subTest(metodo=metodo, url=url):
                resp = getattr(self.client, metodo)(url, corpo, format="json")
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assert_ocorrencia_intacta()

    def test_usuario_comum_logado_ainda_pode_consultar_e_criar(self):
        self.client.force_authenticate(self.comum)
        self.assertEqual(self.client.get(url_lista()).status_code, 200)
        resp = self.client.post(url_lista(), DADOS_VALIDOS, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Estar logado não dá direito de definir status na criação.
        resp = self.client.post(
            url_lista(), {**DADOS_VALIDOS, "status": "resolvida"}, format="json"
        )
        self.assertEqual(resp.data["status"], "pendente")

    def test_gestor_edita_com_patch_e_put(self):
        self.client.force_authenticate(self.gestor)

        resp = self.client.patch(
            url_detalhe(self.o.pk), {"prioridade": "alta"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.o.refresh_from_db()
        self.assertEqual(self.o.prioridade, "alta")
        self.assertEqual(self.o.titulo, DADOS_VALIDOS["titulo"])  # intacto

        novo = {**DADOS_VALIDOS, "titulo": "Título totalmente novo", "status": "em_andamento"}
        resp = self.client.put(url_detalhe(self.o.pk), novo, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.o.refresh_from_db()
        self.assertEqual(self.o.titulo, "Título totalmente novo")
        self.assertEqual(self.o.status, "em_andamento")

    def test_edicao_administrativa_valida_os_dados(self):
        self.client.force_authenticate(self.gestor)
        for corpo in ({"prioridade": "urgentissima"}, {"status": "x"}, {"categoria": "y"}):
            with self.subTest(corpo=corpo):
                resp = self.client.patch(url_detalhe(self.o.pk), corpo, format="json")
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assert_ocorrencia_intacta()

    def test_gestor_exclui_e_depois_recebe_404(self):
        self.client.force_authenticate(self.gestor)

        resp = self.client.delete(url_detalhe(self.o.pk))

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ocorrencia.objects.filter(pk=self.o.pk).exists())
        self.assertEqual(
            self.client.get(url_detalhe(self.o.pk)).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_permissao_e_granular_editar_nao_implica_excluir(self):
        editor = User.objects.create_user("editor", password=SENHA)
        editor.user_permissions.add(Permission.objects.get(codename="change_ocorrencia"))
        self.client.force_authenticate(editor)

        patch = self.client.patch(url_status(self.o.pk), {"status": "resolvida"}, format="json")
        delete = self.client.delete(url_detalhe(self.o.pk))

        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Ocorrencia.objects.filter(pk=self.o.pk).exists())

    def test_autenticacao_basic_real_com_usuario_e_senha(self):
        def basic(usuario, senha):
            token = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
            return f"Basic {token}"

        self.client.credentials(HTTP_AUTHORIZATION=basic("gestor", SENHA))
        ok = self.client.patch(url_status(self.o.pk), {"status": "resolvida"}, format="json")
        self.assertEqual(ok.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=basic("gestor", "senha-errada"))
        erro = self.client.patch(url_status(self.o.pk), {"status": "pendente"}, format="json")
        self.assertEqual(erro.status_code, status.HTTP_401_UNAUTHORIZED)
        self.o.refresh_from_db()
        self.assertEqual(self.o.status, "resolvida")

    def test_grupo_gestores_criado_com_as_permissoes_corretas(self):
        grupo = Group.objects.get(name=GRUPO_GESTORES)
        codigos = set(grupo.permissions.values_list("codename", flat=True))
        self.assertEqual(codigos, {"change_ocorrencia", "delete_ocorrencia"})


# --------------------------------------------------------------------------
# 9, 10 - Dashboard
# --------------------------------------------------------------------------
class DashboardTests(BaseTestCase):
    def test_dashboard_vazio_traz_todas_as_chaves_com_zero(self):
        resp = self.client.get(url_dashboard())

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 0)
        self.assertEqual(
            resp.data["por_status"],
            {"pendente": 0, "em_andamento": 0, "resolvida": 0},
        )
        self.assertEqual(
            set(resp.data["por_categoria"]), set(Ocorrencia.Categoria.values)
        )
        self.assertEqual(
            set(resp.data["por_prioridade"]), {"baixa", "media", "alta"}
        )
        self.assertTrue(all(v == 0 for v in resp.data["por_categoria"].values()))

    def test_dashboard_calcula_valores_corretos(self):
        criar_ocorrencia(categoria="elevador", prioridade="alta", status="pendente")
        criar_ocorrencia(categoria="elevador", prioridade="alta", status="em_andamento")
        criar_ocorrencia(categoria="rampa", prioridade="media", status="pendente")
        criar_ocorrencia(categoria="digital", prioridade="baixa", status="resolvida")
        criar_ocorrencia(categoria="rampa", prioridade="media", status="resolvida")

        resp = self.client.get(url_dashboard())  # sem login: é público

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total"], 5)
        self.assertEqual(
            resp.data["por_status"],
            {"pendente": 2, "em_andamento": 1, "resolvida": 2},
        )
        categorias = resp.data["por_categoria"]
        self.assertEqual(categorias["elevador"], 2)
        self.assertEqual(categorias["rampa"], 2)
        self.assertEqual(categorias["digital"], 1)
        self.assertEqual(categorias["banheiro"], 0)
        self.assertEqual(
            resp.data["por_prioridade"], {"baixa": 1, "media": 2, "alta": 2}
        )

    def assert_coerente(self, dados, total, pendente, andamento, resolvida):
        self.assertEqual(dados["total"], total)
        self.assertEqual(dados["por_status"]["pendente"], pendente)
        self.assertEqual(dados["por_status"]["em_andamento"], andamento)
        self.assertEqual(dados["por_status"]["resolvida"], resolvida)
        # Os totais por status, categoria e prioridade sempre somam o total.
        self.assertEqual(sum(dados["por_status"].values()), total)
        self.assertEqual(sum(dados["por_categoria"].values()), total)
        self.assertEqual(sum(dados["por_prioridade"].values()), total)

    def test_indicadores_acompanham_criacao_alteracao_e_exclusao(self):
        def dashboard():
            return self.client.get(url_dashboard()).data

        self.assert_coerente(dashboard(), 0, 0, 0, 0)

        # Criação pública (anônimo)
        id1 = self.client.post(url_lista(), DADOS_VALIDOS, format="json").data["id"]
        id2 = self.client.post(
            url_lista(), {**DADOS_VALIDOS, "categoria": "elevador"}, format="json"
        ).data["id"]
        dados = dashboard()
        self.assert_coerente(dados, 2, 2, 0, 0)
        self.assertEqual(dados["por_categoria"]["rampa"], 1)
        self.assertEqual(dados["por_categoria"]["elevador"], 1)

        # Alterações feitas pelo gestor
        self.client.force_authenticate(self.gestor)
        self.client.patch(url_status(id1), {"status": "em_andamento"}, format="json")
        self.assert_coerente(dashboard(), 2, 1, 1, 0)

        self.client.patch(url_status(id1), {"status": "resolvida"}, format="json")
        self.assert_coerente(dashboard(), 2, 1, 0, 1)

        self.client.patch(url_detalhe(id2), {"prioridade": "alta"}, format="json")
        dados = dashboard()
        self.assertEqual(dados["por_prioridade"], {"baixa": 0, "media": 1, "alta": 1})

        # Exclusão
        self.client.delete(url_detalhe(id1))
        self.assert_coerente(dashboard(), 1, 1, 0, 0)

        self.client.delete(url_detalhe(id2))
        self.assert_coerente(dashboard(), 0, 0, 0, 0)


# --------------------------------------------------------------------------
# Limitador de criação anônima
# --------------------------------------------------------------------------
class LimiteDeCriacaoTests(BaseTestCase):
    def test_criacao_anonima_e_limitada_mas_gestor_e_leitura_nao(self):
        taxa_de_teste = {"criacao_anonima": "2/hour"}
        with patch.object(CriacaoAnonimaThrottle, "THROTTLE_RATES", taxa_de_teste):
            for _ in range(2):
                resp = self.client.post(url_lista(), DADOS_VALIDOS, format="json")
                self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

            bloqueada = self.client.post(url_lista(), DADOS_VALIDOS, format="json")
            self.assertEqual(bloqueada.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertEqual(Ocorrencia.objects.count(), 2)

            # Leitura continua liberada para o mesmo IP.
            self.assertEqual(self.client.get(url_lista()).status_code, 200)

            # Usuário autenticado não é afetado pelo limite anônimo.
            self.client.force_authenticate(self.gestor)
            ok = self.client.post(url_lista(), DADOS_VALIDOS, format="json")
            self.assertEqual(ok.status_code, status.HTTP_201_CREATED)

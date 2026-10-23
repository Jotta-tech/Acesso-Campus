"""Modelo de dados do Acesso Campus."""
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models


class Ocorrencia(models.Model):
    """Relato de uma barreira de acessibilidade no ambiente universitário."""

    class Categoria(models.TextChoices):
        RAMPA = "rampa", "Rampa bloqueada ou inadequada"
        ELEVADOR = "elevador", "Elevador ou plataforma indisponível"
        CORREDOR = "corredor", "Corredor obstruído"
        BANHEIRO = "banheiro", "Banheiro acessível"
        SINALIZACAO = "sinalizacao", "Sinalização ausente ou inadequada"
        DIGITAL = "digital", "Acessibilidade digital"
        OUTROS = "outros", "Outras dificuldades de acesso"

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        RESOLVIDA = "resolvida", "Resolvida"

    titulo = models.CharField(
        "título",
        max_length=120,
        validators=[MinLengthValidator(5)],
    )
    descricao = models.TextField(
        "descrição",
        validators=[MinLengthValidator(10), MaxLengthValidator(2000)],
    )
    categoria = models.CharField(
        "categoria", max_length=20, choices=Categoria.choices
    )
    localizacao = models.CharField(
        "localização",
        max_length=150,
        validators=[MinLengthValidator(3)],
        help_text="Bloco, andar ou local específico.",
    )
    prioridade = models.CharField(
        "prioridade",
        max_length=10,
        choices=Prioridade.choices,
        default=Prioridade.MEDIA,
    )
    status = models.CharField(
        "status",
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        verbose_name = "ocorrência"
        verbose_name_plural = "ocorrências"
        # O "-id" desempata registros criados no mesmo instante e mantém
        # a paginação estável.
        ordering = ["-data_criacao", "-id"]

    def __str__(self):
        return f"#{self.pk} {self.titulo}"

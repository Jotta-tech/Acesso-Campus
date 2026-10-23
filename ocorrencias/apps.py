from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate


def criar_grupo_gestores(sender, using=DEFAULT_DB_ALIAS, apps=None, **kwargs):
    """
    Após o "migrate", garante que o grupo "Gestores" exista com as permissões
    de editar e excluir ocorrências. A função é idempotente: pode rodar
    quantas vezes for preciso sem duplicar nada.
    """
    # Imports aqui dentro porque os modelos de auth só podem ser carregados
    # depois que o registro de apps do Django estiver pronto.
    from django.apps import apps as global_apps
    from django.contrib.auth.management import create_permissions
    from django.contrib.auth.models import Group, Permission

    from .permissions import GRUPO_GESTORES

    # Garante que as permissões do app já existam, independentemente da
    # ordem em que os handlers de post_migrate são executados.
    create_permissions(
        sender, verbosity=0, using=using, apps=apps or global_apps
    )

    grupo, _ = Group.objects.using(using).get_or_create(name=GRUPO_GESTORES)
    permissoes = Permission.objects.using(using).filter(
        content_type__app_label="ocorrencias",
        codename__in=["change_ocorrencia", "delete_ocorrencia"],
    )
    grupo.permissions.add(*permissoes)


class OcorrenciasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ocorrencias"
    verbose_name = "Ocorrências"

    def ready(self):
        post_migrate.connect(criar_grupo_gestores, sender=self)

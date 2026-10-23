from django.urls import path

from . import acesso_auth_views as views

urlpatterns = [
    path("csrf/", views.csrf_token, name="acesso_csrf"),
    path("session/", views.session_info, name="acesso_session"),
    path("login/", views.login_admin, name="acesso_login"),
    path("logout/", views.logout_admin, name="acesso_logout"),
    path("ocorrencias/<int:ocorrencia_id>/", views.update_ocorrencia, name="acesso_atualizar_ocorrencia"),
]


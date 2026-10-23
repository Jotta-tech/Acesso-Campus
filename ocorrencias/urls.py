"""Rotas da API (montadas em /api/ por config/urls.py)."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardView, OcorrenciaViewSet

router = DefaultRouter()
router.register("ocorrencias", OcorrenciaViewSet, basename="ocorrencia")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    *router.urls,
]

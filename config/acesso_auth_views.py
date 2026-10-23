import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from ocorrencias.models import Ocorrencia


def can_manage(user):
    return bool(user.is_authenticated and user.has_perm("ocorrencias.change_ocorrencia"))


def session_payload(user):
    return {
        "authenticated": bool(user.is_authenticated),
        "can_manage": can_manage(user),
        "username": user.get_username() if user.is_authenticated else "",
    }


def parse_json(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        return data
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"ok": True})


@require_GET
def session_info(request):
    return JsonResponse(session_payload(request.user))


@require_POST
@csrf_protect
def login_admin(request):
    data = parse_json(request)
    if data is None:
        return JsonResponse({"detail": "Dados inválidos."}, status=400)
    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return JsonResponse({"detail": "Usuário ou senha inválidos."}, status=400)
    user = authenticate(request, username=username, password=password)
    if user is None or not can_manage(user):
        return JsonResponse({"detail": "Credenciais inválidas ou usuário sem permissão administrativa."}, status=403)
    login(request, user)
    return JsonResponse(session_payload(request.user))


@require_POST
@csrf_protect
def logout_admin(request):
    logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["PATCH"])
@csrf_protect
def update_ocorrencia(request, ocorrencia_id):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Autenticação necessária."}, status=401)
    if not can_manage(request.user):
        return JsonResponse({"detail": "Sem permissão para gerenciar ocorrências."}, status=403)
    data = parse_json(request)
    if data is None or not data or not set(data).issubset({"status", "prioridade"}):
        return JsonResponse({"detail": "Informe status e/ou prioridade válidos."}, status=400)
    item = get_object_or_404(Ocorrencia, pk=ocorrencia_id)
    for field in ("status", "prioridade"):
        if field in data:
            options = {key for key, label in Ocorrencia._meta.get_field(field).choices}
            if not isinstance(data[field], str) or data[field] not in options:
                return JsonResponse({"detail": f"{field} inválido."}, status=400)
    for field in ("status", "prioridade"):
        if field in data:
            setattr(item, field, data[field])
    item.save()
    return JsonResponse({"ok": True, "id": item.pk, "status": item.status, "prioridade": item.prioridade})


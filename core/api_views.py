"""Views da API DRF do app core: dashboard agregado + autenticação.

Autenticação por SESSÃO Django (não JWT) — mesmo `django.contrib.auth` de
sempre. O front Vue chama /api/auth/login/, o Django seta o cookie de
sessão, e as próximas chamadas (com `credentials: 'include'`) já vêm
autenticadas — igual ao fluxo do login.html atual, só que via fetch em vez
de form POST tradicional.
"""

from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import build_dashboard_data


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_dashboard_data())


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Usuário ou senha inválidos.'}, status=401)
        login(request, user)
        return Response({'username': user.username})


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=204)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MeAPIView(APIView):
    """Devolve o usuário logado (ou 401/403). O front chama isso no boot do
    app pra saber se já tem sessão válida — e é essa chamada que garante o
    cookie `csrftoken` no navegador antes de qualquer POST (login inclusive),
    já que nenhuma view de API renderiza template com {% csrf_token %}."""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Não autenticado.'}, status=401)
        return Response({'username': request.user.username})

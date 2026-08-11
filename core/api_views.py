"""Views da API DRF do app core: dashboard agregado + autenticação.

Autenticação por SESSÃO Django (não JWT) — mesmo `django.contrib.auth` de
sempre. O front Vue chama /api/auth/login/, o Django seta o cookie de
sessão, e as próximas chamadas (com `credentials: 'include'`) já vêm
autenticadas — igual ao fluxo do login.html atual, só que via fetch em vez
de form POST tradicional.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import build_dashboard_data


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_dashboard_data(request.user))


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


class SignupAPIView(APIView):
    """Cria uma conta nova e já loga na hora (mesmo formato de resposta do
    LoginAPIView). Erros voltam por campo — mesmo formato que os forms de
    Finanças já sabem exibir (`e.data.<campo>[0]`)."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password', '')
        password2 = request.data.get('password2', '')

        erros = {}
        if not username:
            erros['username'] = ['Informe um usuário.']
        elif User.objects.filter(username__iexact=username).exists():
            erros['username'] = ['Esse usuário já existe.']

        if not password or password != password2:
            erros['password2'] = ['As senhas não coincidem.']
        else:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                erros['password'] = e.messages

        if erros:
            return Response(erros, status=400)

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return Response({'username': user.username}, status=201)


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

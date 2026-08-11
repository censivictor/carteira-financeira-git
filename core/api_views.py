"""Views da API DRF do app core: dashboard agregado + autenticação.

Autenticação por SESSÃO Django (não JWT) — mesmo `django.contrib.auth` de
sempre. O front Vue chama /api/auth/login/, o Django seta o cookie de
sessão, e as próximas chamadas (com `credentials: 'include'`) já vêm
autenticadas — igual ao fluxo do login.html atual, só que via fetch em vez
de form POST tradicional.
"""

from django.contrib.auth import authenticate, login, logout
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


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'username': request.user.username})

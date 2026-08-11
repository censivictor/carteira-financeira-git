"""Views da API DRF do app investimentos — consumidas pelo front Vue.

Toda a lógica de negócio (cotações, autocomplete, cálculo de renda fixa)
continua morando em investimentos/services.py, sem nenhuma mudança — essas
views só trocam quem chama (antes: templates Django; agora: também a API).
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from . import services
from .models import Ativo, Provento, TransacaoAtivo
from .serializers import AtivoSerializer, ProventoSerializer, TransacaoAtivoSerializer

TIPOS_COTADOS_B3 = (Ativo.Tipo.ACAO, Ativo.Tipo.FII)


class AtivoViewSet(ModelViewSet):
    serializer_class = AtivoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ativo.objects.filter(usuario=self.request.user, ativo_flag=True)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class TransacaoAtivoViewSet(ModelViewSet):
    serializer_class = TransacaoAtivoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TransacaoAtivo.objects.filter(ativo__usuario=self.request.user)
        ativo_id = self.request.query_params.get('ativo')
        if ativo_id:
            qs = qs.filter(ativo_id=ativo_id)
        return qs


class ProventoViewSet(ModelViewSet):
    serializer_class = ProventoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Provento.objects.filter(ativo__usuario=self.request.user)
        ativo_id = self.request.query_params.get('ativo')
        if ativo_id:
            qs = qs.filter(ativo_id=ativo_id)
        return qs


class CotacoesAPIView(APIView):
    """Mesma lógica de investimentos/views.py::cotacoes_json, exposta na API."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ativos = Ativo.objects.filter(usuario=request.user, ativo_flag=True)
        tickers = [a.ticker for a in ativos if a.tipo in TIPOS_COTADOS_B3]
        cripto_ids = [a.coingecko_id for a in ativos if a.tipo == Ativo.Tipo.CRIPTO and a.coingecko_id]

        cotacoes_acoes = services.get_cotacoes_acoes(tickers)
        cotacoes_cripto = services.get_cotacoes_cripto(cripto_ids)

        resultado = {}
        for ativo in ativos:
            if ativo.tipo in TIPOS_COTADOS_B3:
                info = cotacoes_acoes.get(ativo.ticker, {})
            elif ativo.tipo == Ativo.Tipo.CRIPTO:
                info = cotacoes_cripto.get(ativo.coingecko_id, {})
            else:
                continue

            preco = info.get('preco')
            resultado[ativo.ticker] = {
                'preco': preco,
                'variacao_dia_pct': info.get('variacao_dia_pct'),
                'valor_atual': float(ativo.quantidade) * preco if preco is not None else None,
            }
        return Response(resultado)


class BuscarAtivosAPIView(APIView):
    """Mesma lógica de investimentos/views.py::buscar_ativos_json, exposta na API."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipo = request.query_params.get('tipo', '')
        q = request.query_params.get('q', '')

        if tipo in ('ACAO', 'FII'):
            resultados = services.buscar_tickers_b3(q, tipo)
        elif tipo == 'CRIPTO':
            resultados = services.buscar_cripto(q)
        else:
            resultados = []

        return Response({'results': resultados})

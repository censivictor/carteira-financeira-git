"""Views da API DRF do app investimentos — consumidas pelo front Vue.

Toda a lógica de negócio (cotações, autocomplete, cálculo de renda fixa)
continua morando em investimentos/services.py, sem nenhuma mudança — essas
views só trocam quem chama (antes: templates Django; agora: também a API).
"""

from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from . import services
from .models import AlocacaoAlvo, Ativo, Provento, TransacaoAtivo
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


class AlocacaoAlvoAPIView(APIView):
    """Alocação-alvo por classe de ativo, como um "documento" só —
    {tipo: percentual} — em vez de um CRUD de linhas: o front sempre lê e
    grava o conjunto inteiro de uma vez (no máximo 4 classes existem)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alvos = AlocacaoAlvo.objects.filter(usuario=request.user)
        return Response({a.tipo: float(a.percentual_alvo) for a in alvos})

    def put(self, request):
        tipos_validos = {t for t, _ in Ativo.Tipo.choices}
        novos = {}
        soma = Decimal('0')
        for tipo, pct in request.data.items():
            if tipo not in tipos_validos:
                return Response({'detail': f'Tipo inválido: {tipo}.'}, status=400)
            try:
                pct_dec = Decimal(str(pct))
            except InvalidOperation:
                return Response({'detail': f'Percentual inválido para {tipo}.'}, status=400)
            if pct_dec < 0 or pct_dec > 100:
                return Response({'detail': f'Percentual de {tipo} precisa estar entre 0 e 100.'}, status=400)
            novos[tipo] = pct_dec
            soma += pct_dec

        if novos and soma != Decimal('100'):
            return Response({'detail': f'A soma dos percentuais precisa dar 100% (está em {soma}%).'}, status=400)

        with transaction.atomic():
            AlocacaoAlvo.objects.filter(usuario=request.user).delete()
            AlocacaoAlvo.objects.bulk_create([
                AlocacaoAlvo(usuario=request.user, tipo=tipo, percentual_alvo=pct)
                for tipo, pct in novos.items() if pct > 0
            ])

        alvos = AlocacaoAlvo.objects.filter(usuario=request.user)
        return Response({a.tipo: float(a.percentual_alvo) for a in alvos})


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

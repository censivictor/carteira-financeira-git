"""Views da API DRF do app cartoes — consumidas pelo front Vue.

Lógica de negócio (em qual fatura cada parcela cai, pagamento de fatura)
mora em cartoes/services.py — essas views só validam entrada e delegam.
"""

from datetime import date

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from financas.models import CategoriaDespesa

from . import services
from .models import CartaoCredito, CompraCartao, FaturaCartao
from .serializers import CartaoCreditoSerializer, CompraCartaoSerializer, FaturaCartaoSerializer

COR_CATEGORIA_CARTOES = '#0891b2'


class CartaoCreditoViewSet(ModelViewSet):
    serializer_class = CartaoCreditoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartaoCredito.objects.filter(usuario=self.request.user, ativo_flag=True)

    def perform_create(self, serializer):
        categoria, _ = CategoriaDespesa.objects.get_or_create(
            usuario=self.request.user, nome='Cartão de Crédito', defaults={'cor': COR_CATEGORIA_CARTOES},
        )
        serializer.save(usuario=self.request.user, categoria=categoria)


class CompraCartaoViewSet(ModelViewSet):
    serializer_class = CompraCartaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CompraCartao.objects.filter(cartao__usuario=self.request.user)
        cartao_id = self.request.query_params.get('cartao')
        if cartao_id:
            qs = qs.filter(cartao_id=cartao_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        # PROTECT em ParcelaCompraCartao.fatura: se alguma parcela dessa
        # compra já caiu numa fatura paga, apagar a compra deixaria a
        # despesa já lançada sem lastro — trata como erro amigável.
        compra = self.get_object()
        if compra.parcelas.filter(fatura__paga=True).exists():
            return Response(
                {'detail': 'Não dá pra excluir — já tem parcela dessa compra numa fatura paga.'}, status=400,
            )
        return super().destroy(request, *args, **kwargs)


class FaturaCartaoViewSet(ModelViewSet):
    """Só leitura + a action de pagar — faturas são sempre criadas sob
    demanda por `services.registrar_compra`, nunca direto pela API."""
    serializer_class = FaturaCartaoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options', 'post']

    def get_queryset(self):
        qs = FaturaCartao.objects.filter(cartao__usuario=self.request.user)
        cartao_id = self.request.query_params.get('cartao')
        if cartao_id:
            qs = qs.filter(cartao_id=cartao_id)
        return qs

    @action(detail=True, methods=['post'], url_path='pagar')
    def pagar(self, request, pk=None):
        fatura = self.get_object()
        data_pagamento_raw = request.data.get('data_pagamento')
        if data_pagamento_raw:
            try:
                data_pagamento = date.fromisoformat(data_pagamento_raw)
            except ValueError:
                return Response({'data_pagamento': ['Data inválida.']}, status=400)
        else:
            data_pagamento = None

        try:
            services.pagar_fatura(fatura, data_pagamento)
        except services.FaturaJaPagaError:
            return Response({'detail': 'Essa fatura já está paga.'}, status=400)
        except services.FaturaVaziaError:
            return Response({'detail': 'Essa fatura não tem nenhuma compra lançada.'}, status=400)

        return Response(FaturaCartaoSerializer(fatura).data)

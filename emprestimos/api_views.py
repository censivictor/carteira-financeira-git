"""Views da API DRF do app emprestimos — consumidas pelo front Vue.

Toda a lógica de negócio (tabela de amortização, pagamento de parcela,
amortização extra) mora em emprestimos/services.py — essas views só validam
entrada e delegam.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from financas.models import CategoriaDespesa

from . import services
from .models import Emprestimo, ParcelaEmprestimo
from .serializers import EmprestimoSerializer, ParcelaEmprestimoSerializer

# Cor só pra diferenciar essa categoria automática das que o usuário cria à
# mão — não aparece em nenhum seletor, só na legenda do gráfico de gastos.
COR_CATEGORIA_EMPRESTIMOS = '#7c3aed'


class EmprestimoViewSet(ModelViewSet):
    serializer_class = EmprestimoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Emprestimo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # Categoria gerenciada pelo próprio app (o usuário não escolhe na
        # hora de cadastrar) — ver Emprestimo.categoria.
        categoria, _ = CategoriaDespesa.objects.get_or_create(
            usuario=self.request.user, nome='Empréstimos', defaults={'cor': COR_CATEGORIA_EMPRESTIMOS},
        )
        emprestimo = serializer.save(usuario=self.request.user, categoria=categoria)
        services.gerar_parcelas(emprestimo)

    def perform_update(self, serializer):
        emprestimo = serializer.save()
        # validate() do serializer já bloqueia mudar valor/taxa/prazo/
        # sistema com parcela paga — só regenera a tabela quando ainda dá.
        if emprestimo.parcelas_pagas_count == 0:
            services.gerar_parcelas(emprestimo)

    @action(detail=True, methods=['post'], url_path='pagar-parcela')
    def pagar_parcela(self, request, pk=None):
        emprestimo = self.get_object()
        numero = request.data.get('numero')
        parcela = emprestimo.parcelas.filter(numero=numero, paga=False).first()
        if parcela is None:
            return Response({'detail': 'Parcela pendente não encontrada.'}, status=404)

        data_pagamento_raw = request.data.get('data_pagamento')
        if data_pagamento_raw:
            try:
                data_pagamento = date.fromisoformat(data_pagamento_raw)
            except ValueError:
                return Response({'data_pagamento': ['Data inválida.']}, status=400)
        else:
            data_pagamento = date.today()

        services.registrar_pagamento_parcela(parcela, data_pagamento)
        return Response(EmprestimoSerializer(emprestimo).data)

    @action(detail=True, methods=['post'], url_path='amortizar')
    def amortizar(self, request, pk=None):
        emprestimo = self.get_object()
        try:
            valor_extra = Decimal(str(request.data.get('valor_extra')))
        except (InvalidOperation, TypeError):
            return Response({'valor_extra': ['Informe um valor válido.']}, status=400)
        if valor_extra <= 0:
            return Response({'valor_extra': ['O valor deve ser maior que zero.']}, status=400)

        modo = request.data.get('modo', 'PRAZO')
        if modo not in ('PRAZO', 'PARCELA'):
            return Response({'modo': ['Modo inválido — use PRAZO ou PARCELA.']}, status=400)

        try:
            services.registrar_amortizacao_extra(emprestimo, valor_extra, modo)
        except services.SemParcelasPendentesError:
            return Response({'detail': 'Esse empréstimo já está quitado.'}, status=400)
        except ValueError as exc:
            return Response({'valor_extra': [str(exc)]}, status=400)

        return Response(EmprestimoSerializer(emprestimo).data)


class ParcelaEmprestimoViewSet(ModelViewSet):
    """Só leitura na prática — parcelas são sempre geradas/recalculadas via
    services (ver EmprestimoViewSet), nunca criadas/editadas direto pela API."""
    serializer_class = ParcelaEmprestimoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        qs = ParcelaEmprestimo.objects.filter(emprestimo__usuario=self.request.user)
        emprestimo_id = self.request.query_params.get('emprestimo')
        if emprestimo_id:
            qs = qs.filter(emprestimo_id=emprestimo_id)
        return qs

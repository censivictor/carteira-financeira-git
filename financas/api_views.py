from decimal import Decimal, InvalidOperation

from django.db.models import ProtectedError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import CategoriaDespesa, Despesa, DespesaRecorrente, Receita
from .serializers import (
    CategoriaDespesaSerializer,
    DespesaRecorrenteSerializer,
    DespesaSerializer,
    ReceitaSerializer,
)


class CategoriaDespesaViewSet(ModelViewSet):
    serializer_class = CategoriaDespesaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CategoriaDespesa.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # on_delete=PROTECT em Despesa/DespesaRecorrente — sem isso, o DRF
        # deixaria a exceção estourar como 500 em vez de um erro amigável
        # (mesmo tratamento que o CategoriaDespesaDeleteView do template
        # antigo já fazia com messages.error).
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'Não é possível excluir — existem despesas ou recorrências vinculadas a essa categoria.'},
                status=400,
            )


class DespesaViewSet(ModelViewSet):
    serializer_class = DespesaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Despesa.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class DespesaRecorrenteViewSet(ModelViewSet):
    serializer_class = DespesaRecorrenteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DespesaRecorrente.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class ReceitaViewSet(ModelViewSet):
    serializer_class = ReceitaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Receita.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class ImportarExtratoAPIView(APIView):
    """Import em lote de despesas/receitas — o parsing do CSV (delimitador,
    formato de data/valor do banco) acontece no front, que já manda uma
    lista pronta pra criar. Aqui só valida e evita duplicata: uma linha
    com a mesma (usuário, data, valor, descrição) de um lançamento já
    existente é pulada, não duplicada — útil pra reimportar um extrato que
    se sobrepõe a um período já importado antes."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        despesas_in = request.data.get('despesas', [])
        receitas_in = request.data.get('receitas', [])
        if not isinstance(despesas_in, list) or not isinstance(receitas_in, list):
            return Response({'detail': 'Formato inválido — "despesas" e "receitas" precisam ser listas.'}, status=400)

        resultado = {'criadas_despesas': 0, 'duplicadas_despesas': 0, 'criadas_receitas': 0, 'duplicadas_receitas': 0, 'erros': []}

        for item in despesas_in:
            descricao = (item.get('descricao') or '').strip()[:150]
            data = item.get('data')
            try:
                valor = Decimal(str(item.get('valor')))
            except (InvalidOperation, TypeError):
                resultado['erros'].append(f'Valor inválido pra "{descricao or "?"}".')
                continue
            if not descricao or not data or valor <= 0:
                resultado['erros'].append(f'Linha de despesa incompleta: "{descricao or "?"}".')
                continue
            try:
                categoria = CategoriaDespesa.objects.get(id=item.get('categoria'), usuario=request.user)
            except (CategoriaDespesa.DoesNotExist, ValueError, TypeError):
                resultado['erros'].append(f'Categoria inválida pra "{descricao}".')
                continue

            if Despesa.objects.filter(usuario=request.user, data=data, valor=valor, descricao=descricao).exists():
                resultado['duplicadas_despesas'] += 1
                continue
            Despesa.objects.create(usuario=request.user, categoria=categoria, descricao=descricao, valor=valor, data=data)
            resultado['criadas_despesas'] += 1

        for item in receitas_in:
            descricao = (item.get('descricao') or '').strip()[:150]
            data = item.get('data')
            try:
                valor = Decimal(str(item.get('valor')))
            except (InvalidOperation, TypeError):
                resultado['erros'].append(f'Valor inválido pra "{descricao or "?"}".')
                continue
            if not descricao or not data or valor <= 0:
                resultado['erros'].append(f'Linha de receita incompleta: "{descricao or "?"}".')
                continue

            if Receita.objects.filter(usuario=request.user, data=data, valor=valor, descricao=descricao).exists():
                resultado['duplicadas_receitas'] += 1
                continue
            tipo = item.get('tipo') if item.get('tipo') in Receita.Tipo.values else Receita.Tipo.OUTRO
            Receita.objects.create(usuario=request.user, descricao=descricao, valor=valor, data=data, tipo=tipo)
            resultado['criadas_receitas'] += 1

        return Response(resultado)

from django.db.models import ProtectedError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

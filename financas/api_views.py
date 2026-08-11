from rest_framework.permissions import IsAuthenticated
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
    queryset = CategoriaDespesa.objects.all()


class DespesaViewSet(ModelViewSet):
    serializer_class = DespesaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Despesa.objects.all()


class DespesaRecorrenteViewSet(ModelViewSet):
    serializer_class = DespesaRecorrenteSerializer
    permission_classes = [IsAuthenticated]
    queryset = DespesaRecorrente.objects.all()


class ReceitaViewSet(ModelViewSet):
    serializer_class = ReceitaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Receita.objects.all()

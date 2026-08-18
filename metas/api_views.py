from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import AporteMeta, MetaFinanceira
from .serializers import AporteMetaSerializer, MetaFinanceiraSerializer


class MetaFinanceiraViewSet(ModelViewSet):
    serializer_class = MetaFinanceiraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MetaFinanceira.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class AporteMetaViewSet(ModelViewSet):
    serializer_class = AporteMetaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = AporteMeta.objects.filter(meta__usuario=self.request.user)
        meta_id = self.request.query_params.get('meta')
        if meta_id:
            qs = qs.filter(meta_id=meta_id)
        return qs

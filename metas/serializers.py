from rest_framework import serializers

from .models import AporteMeta, MetaFinanceira


class MetaFinanceiraSerializer(serializers.ModelSerializer):
    valor_atual = serializers.ReadOnlyField()
    pct = serializers.ReadOnlyField()
    concluida = serializers.ReadOnlyField()

    class Meta:
        model = MetaFinanceira
        fields = ['id', 'nome', 'valor_alvo', 'data_alvo', 'valor_atual', 'pct', 'concluida', 'criado_em']
        read_only_fields = ['id', 'criado_em']


class AporteMetaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = AporteMeta
        fields = ['id', 'meta', 'tipo', 'tipo_display', 'valor', 'data', 'observacao', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            # sem isso, o campo aceitaria o ID de uma meta de outro usuário.
            self.fields['meta'].queryset = MetaFinanceira.objects.filter(usuario=request.user)

    def validate(self, attrs):
        meta = attrs.get('meta') or getattr(self.instance, 'meta', None)
        tipo = attrs.get('tipo') or getattr(self.instance, 'tipo', None)
        valor = attrs.get('valor') or getattr(self.instance, 'valor', None)
        if meta and tipo == AporteMeta.Tipo.RETIRADA and valor is not None:
            saldo_atual = meta.valor_atual
            if self.instance and self.instance.pk and self.instance.tipo == AporteMeta.Tipo.RETIRADA:
                # numa edição, a retirada original ainda conta no saldo
                # atual — soma de volta antes de comparar.
                saldo_atual += self.instance.valor
            if valor > saldo_atual:
                raise serializers.ValidationError(
                    {'valor': [f'Você tem R$ {saldo_atual} guardado nessa meta — não dá pra retirar mais que isso.']}
                )
        return attrs

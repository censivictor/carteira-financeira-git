from investimentos import services as investimentos_services
from investimentos.models import Ativo
from rest_framework import serializers

from .models import AporteMeta, MetaFinanceira


class MetaFinanceiraSerializer(serializers.ModelSerializer):
    valor_atual = serializers.ReadOnlyField()
    pct = serializers.ReadOnlyField()
    concluida = serializers.ReadOnlyField()
    ativos_detail = serializers.SerializerMethodField()

    class Meta:
        model = MetaFinanceira
        fields = [
            'id', 'nome', 'valor_alvo', 'data_alvo', 'ativos', 'ativos_detail',
            'valor_atual', 'pct', 'concluida', 'criado_em',
        ]
        read_only_fields = ['id', 'criado_em']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            # sem isso, o campo aceitaria o ID de um ativo de outro usuário.
            self.fields['ativos'].queryset = Ativo.objects.filter(usuario=request.user)

    def get_ativos_detail(self, obj):
        ativos = list(obj.ativos.all())
        if not ativos:
            return []
        # 2ª chamada de avaliação nessa mesma resposta (a 1ª é o campo
        # `valor_atual`, via MetaFinanceira.valor_atual) — sem problema:
        # get_cotacoes_acoes/get_cotacoes_cripto já cacheiam por 60s, então
        # não vira 2 chamadas de verdade pra API externa.
        valores = investimentos_services.avaliar_ativos(ativos)
        return [
            {
                'id': a.id, 'ticker': a.ticker, 'tipo': a.tipo, 'tipo_display': a.get_tipo_display(),
                'valor_atual': float(valores.get(a.id, 0)),
            }
            for a in ativos
        ]


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

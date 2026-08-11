from rest_framework import serializers

from .models import Ativo, Provento, TransacaoAtivo


class AtivoSerializer(serializers.ModelSerializer):
    # quantidade/preco_medio_compra/valor_investido são properties calculadas
    # a partir do ledger de transações (ver Ativo._calcular_posicao) — nunca
    # campos editáveis diretamente, por isso ReadOnlyField.
    quantidade = serializers.ReadOnlyField()
    preco_medio_compra = serializers.ReadOnlyField()
    valor_investido = serializers.ReadOnlyField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    indexador_display = serializers.CharField(source='get_indexador_display', read_only=True)

    class Meta:
        model = Ativo
        fields = [
            'id', 'ticker', 'nome', 'tipo', 'tipo_display', 'coingecko_id',
            'indexador', 'indexador_display', 'taxa_contratada', 'valor_aplicado', 'data_aplicacao',
            'quantidade', 'preco_medio_compra', 'valor_investido',
            'ativo_flag', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class TransacaoAtivoSerializer(serializers.ModelSerializer):
    valor_total = serializers.ReadOnlyField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = TransacaoAtivo
        fields = [
            'id', 'ativo', 'tipo', 'tipo_display', 'quantidade', 'preco_unitario',
            'valor_total', 'data', 'observacao', 'criado_em',
        ]
        read_only_fields = ['id', 'criado_em']

    def validate(self, attrs):
        ativo = attrs.get('ativo') or getattr(self.instance, 'ativo', None)
        tipo = attrs.get('tipo') or getattr(self.instance, 'tipo', None)
        quantidade = attrs.get('quantidade') or getattr(self.instance, 'quantidade', None)
        if ativo and tipo == TransacaoAtivo.Tipo.VENDA and quantidade is not None:
            qtd_atual = ativo.quantidade or 0
            if self.instance and self.instance.pk:
                # numa edição, a quantidade da própria transação ainda conta
                # na posição atual — soma de volta antes de comparar.
                if self.instance.tipo == TransacaoAtivo.Tipo.VENDA:
                    qtd_atual += self.instance.quantidade
            if quantidade > qtd_atual:
                raise serializers.ValidationError(
                    {'quantidade': f'Você tem {qtd_atual} unidades — não é possível vender mais que isso.'}
                )
        return attrs


class ProventoSerializer(serializers.ModelSerializer):
    quantidade_na_data = serializers.ReadOnlyField()
    valor_total = serializers.ReadOnlyField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Provento
        fields = [
            'id', 'ativo', 'tipo', 'tipo_display', 'valor_por_cota',
            'data_com', 'data_pagamento', 'quantidade_na_data', 'valor_total',
            'observacao', 'criado_em',
        ]
        read_only_fields = ['id', 'criado_em']

    def validate_ativo(self, ativo):
        if ativo.tipo not in (Ativo.Tipo.ACAO, Ativo.Tipo.FII):
            raise serializers.ValidationError('Proventos só fazem sentido pra Ação ou FII.')
        return ativo

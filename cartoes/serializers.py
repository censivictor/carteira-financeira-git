from rest_framework import serializers

from .models import CartaoCredito, CompraCartao, FaturaCartao, ParcelaCompraCartao
from . import services


class CartaoCreditoSerializer(serializers.ModelSerializer):
    limite_utilizado = serializers.ReadOnlyField()
    limite_disponivel = serializers.ReadOnlyField()

    class Meta:
        model = CartaoCredito
        fields = [
            'id', 'nome', 'limite', 'dia_fechamento', 'dia_vencimento',
            'limite_utilizado', 'limite_disponivel', 'ativo_flag', 'criado_em',
        ]
        read_only_fields = ['id', 'criado_em']


class ParcelaCompraCartaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelaCompraCartao
        fields = ['id', 'numero', 'valor', 'fatura']
        read_only_fields = fields


class CompraCartaoSerializer(serializers.ModelSerializer):
    parcelas = ParcelaCompraCartaoSerializer(many=True, read_only=True)

    class Meta:
        model = CompraCartao
        fields = ['id', 'cartao', 'descricao', 'valor_total', 'numero_parcelas', 'data_compra', 'parcelas', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            # sem isso, o campo aceitaria o ID de um cartão de outro usuário.
            self.fields['cartao'].queryset = CartaoCredito.objects.filter(usuario=request.user)

    def create(self, validated_data):
        # A compra não é criada direto pelo ModelViewSet: precisa gerar as
        # parcelas (e as faturas que elas caem) na hora, via services.
        return services.registrar_compra(
            cartao=validated_data['cartao'],
            descricao=validated_data['descricao'],
            valor_total=validated_data['valor_total'],
            numero_parcelas=validated_data['numero_parcelas'],
            data_compra=validated_data['data_compra'],
        )


class FaturaCartaoSerializer(serializers.ModelSerializer):
    valor_total = serializers.ReadOnlyField()
    data_vencimento = serializers.SerializerMethodField()
    cartao_nome = serializers.CharField(source='cartao.nome', read_only=True)

    class Meta:
        model = FaturaCartao
        fields = [
            'id', 'cartao', 'cartao_nome', 'ano', 'mes', 'valor_total',
            'data_vencimento', 'paga', 'data_pagamento', 'despesa',
        ]
        read_only_fields = fields

    def get_data_vencimento(self, obj):
        return services.data_vencimento_fatura(obj.cartao, obj.ano, obj.mes)

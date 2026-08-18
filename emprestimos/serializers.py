from rest_framework import serializers

from .models import Emprestimo, ParcelaEmprestimo

# Depois que a 1ª parcela é paga, mudar qualquer um desses campos invalidaria
# o histórico de parcelas já pagas (o saldo devedor delas foi calculado com
# as condições antigas) — só a descrição continua livre pra editar.
CAMPOS_TRAVADOS_APOS_PAGAMENTO = [
    'valor_total', 'taxa_juros', 'periodo_taxa', 'sistema_amortizacao', 'numero_parcelas', 'data_primeira_parcela',
]


class ParcelaEmprestimoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelaEmprestimo
        fields = [
            'id', 'numero', 'data_vencimento', 'valor_parcela', 'valor_juros',
            'valor_amortizacao', 'saldo_devedor', 'paga', 'data_pagamento', 'despesa',
        ]
        read_only_fields = fields


class EmprestimoSerializer(serializers.ModelSerializer):
    # saldo_devedor/quitado/parcelas_pagas_count são properties calculadas a
    # partir da tabela de parcelas (ver Emprestimo.saldo_devedor) — nunca
    # campos editáveis diretamente, por isso ReadOnlyField.
    saldo_devedor = serializers.ReadOnlyField()
    quitado = serializers.ReadOnlyField()
    parcelas_pagas_count = serializers.ReadOnlyField()
    periodo_taxa_display = serializers.CharField(source='get_periodo_taxa_display', read_only=True)
    sistema_amortizacao_display = serializers.CharField(source='get_sistema_amortizacao_display', read_only=True)

    class Meta:
        model = Emprestimo
        fields = [
            'id', 'descricao', 'valor_total', 'taxa_juros', 'periodo_taxa', 'periodo_taxa_display',
            'sistema_amortizacao', 'sistema_amortizacao_display', 'numero_parcelas', 'data_primeira_parcela',
            'saldo_devedor', 'quitado', 'parcelas_pagas_count', 'criado_em',
        ]
        read_only_fields = ['id', 'criado_em']

    def validate(self, attrs):
        if self.instance and self.instance.parcelas_pagas_count > 0:
            mudou = [
                campo for campo in CAMPOS_TRAVADOS_APOS_PAGAMENTO
                if campo in attrs and attrs[campo] != getattr(self.instance, campo)
            ]
            if mudou:
                raise serializers.ValidationError(
                    'Não dá pra mudar valor, juros, prazo ou sistema depois que alguma parcela já foi paga '
                    '— só a descrição continua editável. Pra mudar as condições, exclua e recadastre o empréstimo.'
                )
        return attrs

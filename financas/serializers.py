from rest_framework import serializers

from .models import CategoriaDespesa, Despesa, DespesaRecorrente, Receita


class CategoriaDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDespesa
        fields = ['id', 'nome', 'cor', 'orcamento_mensal', 'criado_em']
        read_only_fields = ['id', 'criado_em']


class DespesaSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    categoria_cor = serializers.CharField(source='categoria.cor', read_only=True)

    class Meta:
        model = Despesa
        fields = [
            'id', 'categoria', 'categoria_nome', 'categoria_cor', 'descricao', 'valor',
            'data', 'recorrente', 'criado_em',
        ]
        read_only_fields = ['id', 'recorrente', 'criado_em']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            # sem isso, o campo aceitaria o ID de categoria de qualquer
            # usuário — restringe às categorias de quem está autenticado.
            self.fields['categoria'].queryset = CategoriaDespesa.objects.filter(usuario=request.user)


class DespesaRecorrenteSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)

    class Meta:
        model = DespesaRecorrente
        fields = ['id', 'categoria', 'categoria_nome', 'descricao', 'valor', 'dia_do_mes', 'ativa', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            self.fields['categoria'].queryset = CategoriaDespesa.objects.filter(usuario=request.user)


class ReceitaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Receita
        fields = ['id', 'descricao', 'tipo', 'tipo_display', 'valor', 'data', 'criado_em']
        read_only_fields = ['id', 'criado_em']

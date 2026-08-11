from decimal import Decimal

from django import forms

from .models import Ativo, TransacaoAtivo


class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = [
            'ticker',
            'nome',
            'tipo',
            'coingecko_id',
            'indexador',
            'taxa_contratada',
            'valor_aplicado',
            'data_aplicacao',
            'ativo_flag',
        ]
        labels = {
            'ticker': 'Ticker',
            'nome': 'Nome',
            'tipo': 'Tipo',
            'coingecko_id': 'Criptomoeda (digite o nome pra buscar)',
            'indexador': 'Indexador',
            'taxa_contratada': 'Taxa contratada (%)',
            'valor_aplicado': 'Valor aplicado (R$)',
            'data_aplicacao': 'Data da aplicação',
            'ativo_flag': 'Ativo (não arquivado)',
        }
        widgets = {
            'ticker': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'PETR4, MXRF11 ou rótulo (renda fixa)',
                'autocomplete': 'off',
            }),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo'}),
            'coingecko_id': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'ex: digite "bitcoin"', 'autocomplete': 'off',
            }),
            'indexador': forms.Select(attrs={'class': 'form-select'}),
            'taxa_contratada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_aplicado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_aplicacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ativo_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'taxa_contratada': (
                'Para CDI/Selic: % do indexador (ex: 110 = 110% do CDI). '
                'Para Prefixado: taxa fixa ao ano (ex: 12.5 = 12,5% a.a.).'
            ),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')

        if tipo == Ativo.Tipo.CRIPTO and not cleaned.get('coingecko_id'):
            self.add_error(
                'coingecko_id',
                'Obrigatório para criptomoedas — busque pelo nome e selecione uma sugestão.',
            )

        elif tipo == Ativo.Tipo.RENDA_FIXA:
            for campo in ('indexador', 'taxa_contratada', 'valor_aplicado', 'data_aplicacao'):
                if not cleaned.get(campo):
                    self.add_error(campo, 'Obrigatório para renda fixa.')

        return cleaned


class TransacaoAtivoForm(forms.ModelForm):
    class Meta:
        model = TransacaoAtivo
        fields = ['tipo', 'quantidade', 'preco_unitario', 'data', 'observacao']
        labels = {
            'tipo': 'Tipo',
            'quantidade': 'Quantidade',
            'preco_unitario': 'Preço unitário (R$)',
            'data': 'Data',
            'observacao': 'Observação (opcional)',
        }
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacao': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, ativo=None, **kwargs):
        self.ativo = ativo
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if self.ativo and cleaned.get('tipo') == TransacaoAtivo.Tipo.VENDA:
            qtd_atual = self.ativo.quantidade or Decimal('0')
            qtd_venda = cleaned.get('quantidade') or Decimal('0')
            if qtd_venda > qtd_atual:
                self.add_error(
                    'quantidade',
                    f'Você tem {qtd_atual} unidades — não é possível vender mais que isso.',
                )
        return cleaned

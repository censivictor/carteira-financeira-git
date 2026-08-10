from django import forms

from .models import Ativo


class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = [
            'ticker',
            'nome',
            'tipo',
            'coingecko_id',
            'quantidade',
            'preco_medio_compra',
            'ativo_flag',
        ]
        labels = {
            'ticker': 'Ticker',
            'nome': 'Nome',
            'tipo': 'Tipo',
            'coingecko_id': 'ID do CoinGecko',
            'quantidade': 'Quantidade',
            'preco_medio_compra': 'Preço médio de compra (R$)',
            'ativo_flag': 'Ativo (não arquivado)',
        }
        widgets = {
            'ticker': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PETR4 ou BTC'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'coingecko_id': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'bitcoin (só p/ cripto)'}
            ),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'preco_medio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo_flag': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('tipo') == 'CRIPTO' and not cleaned.get('coingecko_id'):
            self.add_error(
                'coingecko_id',
                'Obrigatório para criptomoedas — use o ID do CoinGecko (ex: bitcoin, ethereum).',
            )
        return cleaned

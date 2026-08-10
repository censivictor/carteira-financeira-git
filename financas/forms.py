from django import forms

from .models import Despesa, Receita


class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ['categoria', 'descricao', 'valor', 'data']
        labels = {
            'categoria': 'Categoria',
            'descricao': 'Descrição',
            'valor': 'Valor (R$)',
            'data': 'Data',
        }
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ['descricao', 'tipo', 'valor', 'data']
        labels = {
            'descricao': 'Descrição',
            'tipo': 'Tipo',
            'valor': 'Valor (R$)',
            'data': 'Data',
        }
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

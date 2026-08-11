from django import forms

from .models import CategoriaDespesa, Despesa, DespesaRecorrente, Receita


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


class CategoriaDespesaForm(forms.ModelForm):
    class Meta:
        model = CategoriaDespesa
        fields = ['nome', 'cor', 'orcamento_mensal']
        labels = {
            'nome': 'Nome',
            'cor': 'Cor (legenda do gráfico)',
            'orcamento_mensal': 'Orçamento mensal (R$)',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cor': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'orcamento_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        help_texts = {
            'orcamento_mensal': 'Deixe em branco pra não definir um limite de gasto pra essa categoria.',
        }


class DespesaRecorrenteForm(forms.ModelForm):
    class Meta:
        model = DespesaRecorrente
        fields = ['categoria', 'descricao', 'valor', 'dia_do_mes', 'ativa']
        labels = {
            'categoria': 'Categoria',
            'descricao': 'Descrição',
            'valor': 'Valor (R$)',
            'dia_do_mes': 'Dia do mês',
            'ativa': 'Ativa',
        }
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dia_do_mes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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

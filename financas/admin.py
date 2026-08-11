from django.contrib import admin

from .models import CategoriaDespesa, Despesa, DespesaRecorrente, Receita


@admin.register(CategoriaDespesa)
class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor', 'orcamento_mensal')


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'valor', 'data', 'recorrente')
    list_filter = ('categoria',)
    date_hierarchy = 'data'


@admin.register(DespesaRecorrente)
class DespesaRecorrenteAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'valor', 'dia_do_mes', 'ativa')
    list_filter = ('ativa', 'categoria')


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'valor', 'data')
    list_filter = ('tipo',)
    date_hierarchy = 'data'

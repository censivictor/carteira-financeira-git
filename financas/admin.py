from django.contrib import admin

from .models import CategoriaDespesa, Despesa, DespesaRecorrente, Receita


@admin.register(CategoriaDespesa)
class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'cor', 'orcamento_mensal')
    list_filter = ('usuario',)


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'usuario', 'valor', 'data', 'recorrente')
    list_filter = ('categoria', 'usuario')
    date_hierarchy = 'data'


@admin.register(DespesaRecorrente)
class DespesaRecorrenteAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'usuario', 'valor', 'dia_do_mes', 'ativa')
    list_filter = ('ativa', 'categoria', 'usuario')


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'usuario', 'valor', 'data')
    list_filter = ('tipo', 'usuario')
    date_hierarchy = 'data'

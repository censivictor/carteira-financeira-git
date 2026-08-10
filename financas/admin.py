from django.contrib import admin

from .models import CategoriaDespesa, Despesa, Receita


@admin.register(CategoriaDespesa)
class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor')


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'categoria', 'valor', 'data')
    list_filter = ('categoria',)
    date_hierarchy = 'data'


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'valor', 'data')
    list_filter = ('tipo',)
    date_hierarchy = 'data'

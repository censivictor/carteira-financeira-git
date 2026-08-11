from django.contrib import admin

from .models import Ativo, PatrimonioSnapshot, TransacaoAtivo


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'tipo', 'quantidade', 'preco_medio_compra', 'ativo_flag')
    list_filter = ('tipo', 'ativo_flag')
    search_fields = ('ticker', 'nome')


@admin.register(TransacaoAtivo)
class TransacaoAtivoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'tipo', 'quantidade', 'preco_unitario', 'data')
    list_filter = ('tipo',)
    date_hierarchy = 'data'


@admin.register(PatrimonioSnapshot)
class PatrimonioSnapshotAdmin(admin.ModelAdmin):
    list_display = ('data', 'valor_total', 'valor_investido_total')
    date_hierarchy = 'data'

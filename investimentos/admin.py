from django.contrib import admin

from .models import AlocacaoAlvo, Ativo, PatrimonioSnapshot, Provento, TransacaoAtivo


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'tipo', 'usuario', 'quantidade', 'preco_medio_compra', 'ativo_flag')
    list_filter = ('tipo', 'ativo_flag', 'usuario')
    search_fields = ('ticker', 'nome')


@admin.register(TransacaoAtivo)
class TransacaoAtivoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'tipo', 'quantidade', 'preco_unitario', 'data')
    list_filter = ('tipo',)
    date_hierarchy = 'data'


@admin.register(Provento)
class ProventoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'tipo', 'valor_por_cota', 'data_com', 'valor_total')
    list_filter = ('tipo',)
    date_hierarchy = 'data_com'


@admin.register(PatrimonioSnapshot)
class PatrimonioSnapshotAdmin(admin.ModelAdmin):
    list_display = ('data', 'usuario', 'valor_total', 'valor_investido_total')
    list_filter = ('usuario',)
    date_hierarchy = 'data'


@admin.register(AlocacaoAlvo)
class AlocacaoAlvoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'percentual_alvo')
    list_filter = ('tipo', 'usuario')

from django.contrib import admin

from .models import Ativo


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'tipo', 'quantidade', 'preco_medio_compra', 'ativo_flag')
    list_filter = ('tipo', 'ativo_flag')
    search_fields = ('ticker', 'nome')

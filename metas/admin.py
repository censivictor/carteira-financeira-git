from django.contrib import admin

from .models import AporteMeta, MetaFinanceira


class AporteMetaInline(admin.TabularInline):
    model = AporteMeta
    extra = 0


@admin.register(MetaFinanceira)
class MetaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'valor_alvo', 'valor_atual', 'data_alvo', 'concluida')
    list_filter = ('usuario',)
    inlines = [AporteMetaInline]

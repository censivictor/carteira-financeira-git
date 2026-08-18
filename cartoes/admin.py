from django.contrib import admin

from .models import CartaoCredito, CompraCartao, FaturaCartao, ParcelaCompraCartao


class ParcelaCompraCartaoInline(admin.TabularInline):
    model = ParcelaCompraCartao
    extra = 0
    can_delete = False
    fields = ('numero', 'fatura', 'valor')
    readonly_fields = fields


@admin.register(CartaoCredito)
class CartaoCreditoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'limite', 'limite_utilizado', 'dia_fechamento', 'dia_vencimento', 'ativo_flag')
    list_filter = ('usuario', 'ativo_flag')


@admin.register(CompraCartao)
class CompraCartaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'cartao', 'valor_total', 'numero_parcelas', 'data_compra')
    list_filter = ('cartao',)
    date_hierarchy = 'data_compra'
    inlines = [ParcelaCompraCartaoInline]


@admin.register(FaturaCartao)
class FaturaCartaoAdmin(admin.ModelAdmin):
    list_display = ('cartao', 'ano', 'mes', 'valor_total', 'paga', 'data_pagamento')
    list_filter = ('cartao', 'paga')

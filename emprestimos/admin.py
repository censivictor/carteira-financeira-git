from django.contrib import admin

from .models import AmortizacaoExtra, Emprestimo, ParcelaEmprestimo


class ParcelaEmprestimoInline(admin.TabularInline):
    model = ParcelaEmprestimo
    extra = 0
    can_delete = False
    fields = ('numero', 'data_vencimento', 'valor_parcela', 'valor_juros', 'valor_amortizacao', 'saldo_devedor', 'paga', 'data_pagamento')
    readonly_fields = fields


class AmortizacaoExtraInline(admin.TabularInline):
    model = AmortizacaoExtra
    extra = 0
    can_delete = False
    fields = ('valor', 'data', 'despesa')
    readonly_fields = fields


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'usuario', 'valor_total', 'sistema_amortizacao', 'numero_parcelas', 'saldo_devedor', 'quitado')
    list_filter = ('sistema_amortizacao', 'periodo_taxa', 'usuario')
    inlines = [ParcelaEmprestimoInline, AmortizacaoExtraInline]

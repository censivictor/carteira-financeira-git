from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class CartaoCredito(models.Model):
    """Um cartão de crédito do usuário. Limite é informativo (não bloqueia
    lançar compra acima dele — só serve pra calcular o disponível exibido)."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cartoes')
    nome = models.CharField(max_length=100, help_text='Ex: Nubank, Inter Black.')
    limite = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        help_text='Limite total do cartão, em BRL. Deixe em branco pra não acompanhar limite.',
    )
    dia_fechamento = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês em que a fatura fecha.',
    )
    dia_vencimento = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês em que a fatura vence.',
    )
    # Categoria gerenciada pelo próprio app (get_or_create em
    # CartaoCreditoViewSet.perform_create), igual emprestimos.Emprestimo.categoria.
    categoria = models.ForeignKey(
        'financas.CategoriaDespesa', on_delete=models.PROTECT, related_name='cartoes',
        help_text='Categoria usada na despesa gerada ao pagar uma fatura.',
    )
    ativo_flag = models.BooleanField(default=True, verbose_name='Ativo (não arquivado)')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Cartão de crédito'
        verbose_name_plural = 'Cartões de crédito'

    def __str__(self):
        return self.nome

    @property
    def limite_utilizado(self) -> Decimal:
        """Soma de todas as parcelas de compras cujas faturas ainda não
        foram pagas — parcelas futuras de compra parcelada também consomem
        limite, igual no mundo real."""
        total = ParcelaCompraCartao.objects.filter(compra__cartao=self).exclude(fatura__paga=True) \
            .aggregate(s=Sum('valor'))['s']
        return total or Decimal('0')

    @property
    def limite_disponivel(self):
        if self.limite is None:
            return None
        return self.limite - self.limite_utilizado


class FaturaCartao(models.Model):
    """A fatura de um mês/ano de um cartão — soma das parcelas de compra que
    caíram nesse ciclo. Só existe uma linha por (cartão, ano, mês), criada
    sob demanda (`services.registrar_compra`) igual `PatrimonioSnapshot`."""

    cartao = models.ForeignKey(CartaoCredito, on_delete=models.CASCADE, related_name='faturas')
    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    paga = models.BooleanField(default=False)
    data_pagamento = models.DateField(blank=True, null=True)
    despesa = models.OneToOneField(
        'financas.Despesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='fatura_cartao',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ano', '-mes']
        unique_together = ('cartao', 'ano', 'mes')
        verbose_name = 'Fatura de cartão'
        verbose_name_plural = 'Faturas de cartão'

    def __str__(self):
        return f'Fatura {self.mes:02d}/{self.ano} - {self.cartao.nome}'

    @property
    def valor_total(self) -> Decimal:
        return self.parcelas.aggregate(s=Sum('valor'))['s'] or Decimal('0')


class CompraCartao(models.Model):
    """Uma compra no cartão, à vista ou parcelada — gera 1 `ParcelaCompraCartao`
    por parcela, cada uma já associada à `FaturaCartao` em que cai."""

    cartao = models.ForeignKey(CartaoCredito, on_delete=models.CASCADE, related_name='compras')
    descricao = models.CharField(max_length=150)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    numero_parcelas = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    data_compra = models.DateField(default=timezone.now)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_compra', '-criado_em']
        verbose_name = 'Compra no cartão'
        verbose_name_plural = 'Compras no cartão'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor_total} ({self.numero_parcelas}x)'


class ParcelaCompraCartao(models.Model):
    compra = models.ForeignKey(CompraCartao, on_delete=models.CASCADE, related_name='parcelas')
    fatura = models.ForeignKey(FaturaCartao, on_delete=models.PROTECT, related_name='parcelas')
    numero = models.PositiveSmallIntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['numero']
        unique_together = ('compra', 'numero')
        verbose_name = 'Parcela de compra'
        verbose_name_plural = 'Parcelas de compra'

    def __str__(self):
        return f'Parcela {self.numero}/{self.compra.numero_parcelas} - {self.compra.descricao}'

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Emprestimo(models.Model):
    """Um empréstimo/financiamento contratado pelo usuário (consignado,
    financiamento de veículo, empréstimo pessoal...).

    A tabela de parcelas (`ParcelaEmprestimo`) é gerada automaticamente pelo
    sistema de amortização escolhido — ver
    `emprestimos/services.py::gerar_parcelas`. Igual o padrão de `Ativo` em
    investimentos: valores derivados (saldo devedor, se está quitado) nunca
    são editados diretamente, sempre calculados a partir do histórico de
    parcelas.
    """

    class Sistema(models.TextChoices):
        PRICE = 'PRICE', 'Price (parcela fixa)'
        SAC = 'SAC', 'SAC (parcela decrescente)'

    class PeriodoTaxa(models.TextChoices):
        MENSAL = 'MENSAL', 'Ao mês'
        ANUAL = 'ANUAL', 'Ao ano'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emprestimos')
    descricao = models.CharField(
        max_length=150, help_text='Ex: Financiamento do carro, Empréstimo consignado Banco X.'
    )
    # Categoria gerenciada pelo próprio app (get_or_create em
    # EmprestimoViewSet.perform_create) — o usuário não escolhe na hora de
    # cadastrar, só serve pra toda parcela paga cair organizada no
    # orçamento/gráficos de despesas que já existem.
    categoria = models.ForeignKey(
        'financas.CategoriaDespesa', on_delete=models.PROTECT, related_name='emprestimos',
        help_text='Categoria usada nas despesas geradas ao pagar uma parcela.',
    )
    valor_total = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Valor total tomado emprestado (principal), em BRL.',
    )
    taxa_juros = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal('0'))],
        help_text='Taxa de juros em %% — ver "Período da taxa" pra dizer se é ao mês ou ao ano.',
    )
    periodo_taxa = models.CharField(max_length=6, choices=PeriodoTaxa.choices, default=PeriodoTaxa.MENSAL)
    sistema_amortizacao = models.CharField(max_length=5, choices=Sistema.choices, default=Sistema.PRICE)
    numero_parcelas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    data_primeira_parcela = models.DateField(default=timezone.now)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor_total} ({self.numero_parcelas}x {self.sistema_amortizacao})'

    @property
    def saldo_devedor(self) -> Decimal:
        """Saldo devedor atual: valor total menos tudo que já foi
        amortizado — via parcela paga ou via amortização extra. Nunca
        armazenado direto, sempre somado do ledger (`parcelas` +
        `amortizacoes_extras`), igual `Ativo._calcular_posicao` reconstrói a
        posição a partir do histórico de transações. Não dá pra derivar
        isso do saldo_devedor de uma parcela vizinha específica: uma
        amortização extra pode acontecer entre duas parcelas sem gerar
        nenhuma parcela nova pra "carimbar" o saldo ajustado."""
        amortizado_parcelas = self.parcelas.filter(paga=True).aggregate(s=Sum('valor_amortizacao'))['s'] or Decimal('0')
        amortizado_extra = self.amortizacoes_extras.aggregate(s=Sum('valor'))['s'] or Decimal('0')
        saldo = self.valor_total - amortizado_parcelas - amortizado_extra
        return saldo if saldo > 0 else Decimal('0')

    @property
    def quitado(self) -> bool:
        if self.parcelas.filter(paga=False).exists():
            return False
        return self.parcelas.filter(paga=True).exists() or self.amortizacoes_extras.exists()

    @property
    def parcelas_pagas_count(self) -> int:
        return self.parcelas.filter(paga=True).count()


class ParcelaEmprestimo(models.Model):
    """Uma parcela da tabela de amortização de um Emprestimo — sempre gerada
    por `services.gerar_parcelas`/`services.registrar_amortizacao_extra`,
    nunca criada/editada na mão pela API."""

    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name='parcelas')
    numero = models.PositiveSmallIntegerField()
    data_vencimento = models.DateField()
    valor_parcela = models.DecimalField(max_digits=12, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=12, decimal_places=2)
    valor_amortizacao = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_devedor = models.DecimalField(
        max_digits=12, decimal_places=2, help_text='Saldo devedor logo após essa parcela.'
    )
    paga = models.BooleanField(default=False)
    data_pagamento = models.DateField(blank=True, null=True)
    # Despesa gerada quando a parcela é marcada como paga (mesmo padrão de
    # DespesaRecorrente → Despesa). SET_NULL: apagar a parcela/empréstimo
    # não deve apagar a despesa já lançada no orçamento do usuário.
    despesa = models.OneToOneField(
        'financas.Despesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='parcela_emprestimo',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['numero']
        unique_together = ('emprestimo', 'numero')
        verbose_name = 'Parcela de empréstimo'
        verbose_name_plural = 'Parcelas de empréstimo'

    def __str__(self):
        return f'Parcela {self.numero}/{self.emprestimo.numero_parcelas} - {self.emprestimo.descricao}'


class AmortizacaoExtra(models.Model):
    """Um pagamento avulso, além das parcelas normais, que abate direto o
    saldo devedor (ver `services.registrar_amortizacao_extra`). Faz parte do
    ledger que `Emprestimo.saldo_devedor` soma — sem isso, um abatimento
    feito antes de qualquer parcela paga não teria onde "carimbar" o saldo
    ajustado."""

    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name='amortizacoes_extras')
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField(default=timezone.now)
    despesa = models.OneToOneField(
        'financas.Despesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='amortizacao_extra',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Amortização extra'
        verbose_name_plural = 'Amortizações extras'

    def __str__(self):
        return f'Amortização extra de R$ {self.valor} - {self.emprestimo.descricao}'

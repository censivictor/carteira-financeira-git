from decimal import Decimal
from functools import cached_property

from django.db import models
from django.utils import timezone


class Ativo(models.Model):
    """Um ativo (ação/FII da B3, criptomoeda ou renda fixa) que o usuário possui.

    Para Ação/FII/Criptomoeda, quantidade e preço médio de compra NÃO são mais
    campos diretos — são calculados a partir do histórico de transações
    (`TransacaoAtivo`) pelo método de custo médio ponderado. Valores
    monetários sempre em BRL.

    Renda fixa não usa transações (não tem lotes de compra/venda): usa
    valor_aplicado + data_aplicacao + indexador + taxa_contratada, e o valor
    atual é estimado via composição de taxas históricas do Banco Central
    (ver investimentos/services.py).
    """

    class Tipo(models.TextChoices):
        ACAO = 'ACAO', 'Ação B3'
        FII = 'FII', 'Fundo Imobiliário (FII)'
        CRIPTO = 'CRIPTO', 'Criptomoeda'
        RENDA_FIXA = 'RENDA_FIXA', 'Renda Fixa (CDI/Selic/Prefixado)'

    class Indexador(models.TextChoices):
        CDI = 'CDI', '% do CDI'
        SELIC = 'SELIC', '% da Selic'
        PREFIXADO = 'PREFIXADO', 'Prefixado (taxa fixa ao ano)'

    ticker = models.CharField(
        max_length=15,
        help_text=(
            'Código na B3 (ex: PETR4, MXRF11) ou símbolo da cripto (ex: BTC). '
            'Para renda fixa, use um rótulo livre (ex: CDB Banco X).'
        ),
    )
    nome = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    coingecko_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='ID do CoinGecko (ex: bitcoin, ethereum). Obrigatório só para criptomoedas.',
    )

    # --- Campos específicos de Renda Fixa ---
    indexador = models.CharField(
        max_length=10, choices=Indexador.choices, blank=True, null=True,
    )
    taxa_contratada = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True,
        help_text=(
            'Para CDI/Selic: % do indexador contratado (ex: 110 = 110%% do CDI). '
            'Para Prefixado: taxa fixa ao ano, em %% (ex: 12.5).'
        ),
    )
    valor_aplicado = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True,
        help_text='Valor aplicado, em BRL.',
    )
    data_aplicacao = models.DateField(blank=True, null=True)

    ativo_flag = models.BooleanField(
        default=True, verbose_name='Ativo (não arquivado)'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('ticker', 'tipo')
        ordering = ['tipo', 'ticker']
        verbose_name = 'Ativo'
        verbose_name_plural = 'Ativos'

    def __str__(self):
        return f'{self.ticker} ({self.get_tipo_display()})'

    @cached_property
    def _posicao(self):
        """(quantidade, preco_medio) calculados a partir do histórico de
        transações, pelo método de custo médio ponderado: compra recalcula
        o preço médio, venda reduz a quantidade sem alterar o preço médio
        do que sobrou. `cached_property` evita recalcular mais de uma vez
        por request."""
        qtd = Decimal('0')
        custo_total = Decimal('0')
        for t in self.transacoes.order_by('data', 'criado_em'):
            if t.tipo == TransacaoAtivo.Tipo.COMPRA:
                custo_total += t.quantidade * t.preco_unitario
                qtd += t.quantidade
            else:  # VENDA
                if qtd > 0:
                    preco_medio_no_momento = custo_total / qtd
                    custo_total -= preco_medio_no_momento * min(t.quantidade, qtd)
                qtd -= t.quantidade
        preco_medio = (custo_total / qtd) if qtd > 0 else Decimal('0')
        return qtd, preco_medio

    @property
    def quantidade(self):
        if self.tipo == self.Tipo.RENDA_FIXA:
            return None
        return self._posicao[0]

    @property
    def preco_medio_compra(self):
        if self.tipo == self.Tipo.RENDA_FIXA:
            return None
        return self._posicao[1]

    @property
    def valor_investido(self) -> Decimal:
        if self.tipo == self.Tipo.RENDA_FIXA:
            return self.valor_aplicado or Decimal('0')
        return (self.quantidade or Decimal('0')) * (self.preco_medio_compra or Decimal('0'))


class TransacaoAtivo(models.Model):
    """Uma compra ou venda de um ativo (ação/FII/cripto), numa data específica.

    A posição atual do `Ativo` (quantidade/preço médio) é sempre calculada a
    partir dessas transações — nunca editada diretamente.
    """

    class Tipo(models.TextChoices):
        COMPRA = 'COMPRA', 'Compra'
        VENDA = 'VENDA', 'Venda'

    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='transacoes')
    tipo = models.CharField(max_length=6, choices=Tipo.choices)
    quantidade = models.DecimalField(max_digits=20, decimal_places=8)
    preco_unitario = models.DecimalField(
        max_digits=18, decimal_places=2, help_text='Preço por unidade nessa transação, em BRL.'
    )
    data = models.DateField(default=timezone.now)
    observacao = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'

    def __str__(self):
        return f'{self.get_tipo_display()} {self.quantidade} {self.ativo.ticker} @ R$ {self.preco_unitario}'

    @property
    def valor_total(self) -> Decimal:
        return self.quantidade * self.preco_unitario


class PatrimonioSnapshot(models.Model):
    """Registro diário do valor total da carteira — acumulado a cada
    carregamento do dashboard, vira o histórico do gráfico 'patrimônio ao
    longo do tempo'. Não é retroativo: só existe a partir de quando o
    usuário começou a usar essa versão do app."""

    data = models.DateField(unique=True)
    valor_total = models.DecimalField(max_digits=18, decimal_places=2)
    valor_investido_total = models.DecimalField(max_digits=18, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data']
        verbose_name = 'Snapshot de patrimônio'
        verbose_name_plural = 'Snapshots de patrimônio'

    def __str__(self):
        return f'{self.data}: R$ {self.valor_total}'

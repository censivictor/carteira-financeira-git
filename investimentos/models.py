from decimal import Decimal

from django.db import models


class Ativo(models.Model):
    """Um ativo (ação/FII da B3, criptomoeda ou renda fixa) que o usuário possui.

    Quantidade e preço médio de compra são informados manualmente pelo
    usuário — não há livro-razão de transações nesta versão, só a posição
    atual. Valores monetários sempre em BRL.

    Renda fixa não usa quantidade/preço médio (não tem cotação de mercado):
    usa valor_aplicado + data_aplicacao + indexador + taxa_contratada, e o
    valor atual é estimado via composição de taxas históricas do Banco
    Central (ver investimentos/services.py).
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
    quantidade = models.DecimalField(
        max_digits=20, decimal_places=8, blank=True, null=True,
        help_text='Obrigatório para Ação, FII e Criptomoeda. Não se aplica a Renda Fixa.',
    )
    preco_medio_compra = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True,
        help_text='Preço médio de compra, em BRL. Não se aplica a Renda Fixa.',
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

    @property
    def valor_investido(self) -> Decimal:
        if self.tipo == self.Tipo.RENDA_FIXA:
            return self.valor_aplicado or Decimal('0')
        return (self.quantidade or Decimal('0')) * (self.preco_medio_compra or Decimal('0'))

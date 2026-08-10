from decimal import Decimal

from django.db import models


class Ativo(models.Model):
    """Um ativo (ação da B3 ou criptomoeda) que o usuário possui.

    Quantidade e preço médio de compra são informados manualmente pelo
    usuário — não há livro-razão de transações nesta versão, só a posição
    atual. Valores monetários sempre em BRL.
    """

    class Tipo(models.TextChoices):
        ACAO = 'ACAO', 'Ação B3'
        CRIPTO = 'CRIPTO', 'Criptomoeda'

    ticker = models.CharField(
        max_length=15,
        help_text='Código na B3 (ex: PETR4) ou símbolo da cripto (ex: BTC).',
    )
    nome = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    coingecko_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='ID do CoinGecko (ex: bitcoin, ethereum). Obrigatório só para criptomoedas.',
    )
    quantidade = models.DecimalField(max_digits=20, decimal_places=8)
    preco_medio_compra = models.DecimalField(
        max_digits=18, decimal_places=2, help_text='Preço médio de compra, em BRL.'
    )
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
        return self.quantidade * self.preco_medio_compra

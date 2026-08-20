from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class MetaFinanceira(models.Model):
    """Uma meta de economia (reserva de emergência, viagem, entrada de
    imóvel...). O valor guardado (`valor_atual`) nunca é editado direto —
    é sempre a soma do ledger de `AporteMeta`, mesmo padrão de
    `Ativo._calcular_posicao` a partir das transações."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='metas')
    nome = models.CharField(max_length=150, help_text='Ex: Reserva de emergência, Viagem pra Europa.')
    valor_alvo = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data_alvo = models.DateField(blank=True, null=True, help_text='Data em que você quer atingir a meta (opcional).')
    # Ex: "reserva de emergência" = esses ativos da carteira, sem precisar
    # digitar aporte manual toda vez que o valor deles muda. M2M simples (sem
    # through-model) porque não há nenhum dado extra por vínculo — só a
    # relação em si.
    ativos = models.ManyToManyField(
        'investimentos.Ativo', blank=True, related_name='metas',
        help_text='Ativos da carteira que contam pro valor guardado dessa meta.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_alvo', 'nome']
        verbose_name = 'Meta financeira'
        verbose_name_plural = 'Metas financeiras'

    def __str__(self):
        return f'{self.nome} - R$ {self.valor_alvo}'

    @property
    def valor_atual(self) -> Decimal:
        aportado = self.aportes.filter(tipo=AporteMeta.Tipo.APORTE).aggregate(s=Sum('valor'))['s'] or Decimal('0')
        retirado = self.aportes.filter(tipo=AporteMeta.Tipo.RETIRADA).aggregate(s=Sum('valor'))['s'] or Decimal('0')
        saldo = aportado - retirado
        saldo = saldo if saldo > 0 else Decimal('0')

        # Ativos vinculados contam pelo valor de mercado ATUAL (igual todo o
        # resto do app trata "valor" — nunca custo/valor aplicado), reaproveitando
        # a mesma lógica de cotação+fallback do dashboard — ver
        # investimentos/services.py::avaliar_ativos. Só bate na API de
        # cotação se a meta realmente tiver ativo vinculado.
        if self.pk and self.ativos.exists():
            from investimentos import services
            saldo += sum(services.avaliar_ativos(self.ativos.all()).values(), Decimal('0'))

        return saldo

    @property
    def pct(self) -> float:
        return min(float(self.valor_atual / self.valor_alvo * 100), 100) if self.valor_alvo else 0

    @property
    def concluida(self) -> bool:
        return self.valor_atual >= self.valor_alvo


class AporteMeta(models.Model):
    """Um aporte ou retirada numa meta — ledger, igual `TransacaoAtivo`."""

    class Tipo(models.TextChoices):
        APORTE = 'APORTE', 'Aporte'
        RETIRADA = 'RETIRADA', 'Retirada'

    meta = models.ForeignKey(MetaFinanceira, on_delete=models.CASCADE, related_name='aportes')
    tipo = models.CharField(max_length=8, choices=Tipo.choices, default=Tipo.APORTE)
    valor = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(default=timezone.now)
    observacao = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Aporte de meta'
        verbose_name_plural = 'Aportes de meta'

    def __str__(self):
        return f'{self.get_tipo_display()} {self.valor} - {self.meta.nome}'

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .models import AporteMeta, MetaFinanceira


class MetaFinanceiraTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.meta = MetaFinanceira.objects.create(
            usuario=self.usuario, nome='Reserva de emergência', valor_alvo=Decimal('10000'),
        )

    def test_valor_atual_soma_aportes(self):
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('1000'), data=date(2026, 1, 5))
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('500'), data=date(2026, 2, 5))
        self.assertEqual(self.meta.valor_atual, Decimal('1500'))
        self.assertEqual(self.meta.pct, 15.0)
        self.assertFalse(self.meta.concluida)

    def test_retirada_reduz_valor_atual(self):
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('1000'), data=date(2026, 1, 5))
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.RETIRADA, valor=Decimal('300'), data=date(2026, 2, 5))
        self.assertEqual(self.meta.valor_atual, Decimal('700'))

    def test_meta_concluida_quando_atinge_valor_alvo(self):
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('10000'), data=date(2026, 1, 5))
        self.assertTrue(self.meta.concluida)
        self.assertEqual(self.meta.pct, 100.0)

    def test_pct_nao_passa_de_100(self):
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('15000'), data=date(2026, 1, 5))
        self.assertEqual(self.meta.pct, 100.0)

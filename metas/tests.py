from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from investimentos.models import Ativo

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


class MetaAtivosVinculadosTests(TestCase):
    """Ativo vinculado à meta conta pelo valor de mercado ATUAL, somado ao
    ledger manual de aportes — ver metas/models.py::MetaFinanceira.valor_atual."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.meta = MetaFinanceira.objects.create(
            usuario=self.usuario, nome='Reserva de emergência', valor_alvo=Decimal('10000'),
        )
        self.ativo = Ativo.objects.create(usuario=self.usuario, ticker='RESERVA11', tipo=Ativo.Tipo.FII)

    @patch('investimentos.services.avaliar_ativos')
    def test_valor_atual_soma_ativos_vinculados_e_aportes(self, mock_avaliar):
        mock_avaliar.return_value = {self.ativo.id: Decimal('4000.00')}
        self.meta.ativos.add(self.ativo)
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('1000'), data=date(2026, 1, 5))

        self.assertEqual(self.meta.valor_atual, Decimal('5000.00'))
        mock_avaliar.assert_called_once()

    def test_meta_sem_ativo_vinculado_nao_bate_na_cotacao(self):
        AporteMeta.objects.create(meta=self.meta, tipo=AporteMeta.Tipo.APORTE, valor=Decimal('1000'), data=date(2026, 1, 5))
        with patch('investimentos.services.avaliar_ativos') as mock_avaliar:
            self.assertEqual(self.meta.valor_atual, Decimal('1000'))
            mock_avaliar.assert_not_called()

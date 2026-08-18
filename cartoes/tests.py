from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from financas.models import CategoriaDespesa, Despesa
from . import services
from .models import CartaoCredito, FaturaCartao


class CartaoCreditoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.categoria = CategoriaDespesa.objects.create(usuario=self.usuario, nome='Cartão de Crédito')
        self.cartao = CartaoCredito.objects.create(
            usuario=self.usuario, categoria=self.categoria, nome='Cartão teste',
            limite=Decimal('5000'), dia_fechamento=20, dia_vencimento=27,
        )

    def test_compra_antes_do_fechamento_cai_na_fatura_do_mesmo_mes(self):
        compra = services.registrar_compra(self.cartao, 'Mercado', Decimal('300'), 1, date(2026, 3, 10))
        parcela = compra.parcelas.get()
        self.assertEqual((parcela.fatura.ano, parcela.fatura.mes), (2026, 3))

    def test_compra_depois_do_fechamento_cai_na_fatura_do_mes_seguinte(self):
        compra = services.registrar_compra(self.cartao, 'Mercado', Decimal('300'), 1, date(2026, 3, 25))
        parcela = compra.parcelas.get()
        self.assertEqual((parcela.fatura.ano, parcela.fatura.mes), (2026, 4))

    def test_compra_parcelada_distribui_uma_parcela_por_mes(self):
        compra = services.registrar_compra(self.cartao, 'Notebook', Decimal('3000'), 3, date(2026, 3, 10))
        parcelas = list(compra.parcelas.order_by('numero'))
        self.assertEqual([(p.fatura.ano, p.fatura.mes) for p in parcelas], [(2026, 3), (2026, 4), (2026, 5)])
        self.assertEqual(sum((p.valor for p in parcelas), Decimal('0')), Decimal('3000.00'))

    def test_limite_utilizado_considera_parcelas_futuras_nao_pagas(self):
        services.registrar_compra(self.cartao, 'Notebook', Decimal('3000'), 3, date(2026, 3, 10))
        self.assertEqual(self.cartao.limite_utilizado, Decimal('3000.00'))
        self.assertEqual(self.cartao.limite_disponivel, Decimal('2000.00'))

    def test_pagar_fatura_gera_despesa_e_libera_limite(self):
        compra = services.registrar_compra(self.cartao, 'Notebook', Decimal('3000'), 3, date(2026, 3, 10))
        fatura_marco = compra.parcelas.get(numero=1).fatura

        services.pagar_fatura(fatura_marco, date(2026, 3, 27))
        fatura_marco.refresh_from_db()

        self.assertTrue(fatura_marco.paga)
        self.assertIsNotNone(fatura_marco.despesa)
        self.assertEqual(fatura_marco.despesa.valor, fatura_marco.valor_total)
        # só a parcela de março foi paga — abril e maio continuam pendentes
        self.assertEqual(self.cartao.limite_utilizado, Decimal('2000.00'))

    def test_pagar_fatura_ja_paga_falha(self):
        compra = services.registrar_compra(self.cartao, 'Mercado', Decimal('300'), 1, date(2026, 3, 10))
        fatura = compra.parcelas.get().fatura
        services.pagar_fatura(fatura)
        with self.assertRaises(services.FaturaJaPagaError):
            services.pagar_fatura(fatura)

    def test_pagar_fatura_vazia_falha(self):
        fatura = FaturaCartao.objects.create(cartao=self.cartao, ano=2026, mes=3)
        with self.assertRaises(services.FaturaVaziaError):
            services.pagar_fatura(fatura)

    def test_data_vencimento_no_mes_seguinte_quando_vencimento_antes_do_fechamento(self):
        # fecha dia 20, vence dia 27 -> mesmo mês
        self.assertEqual(services.data_vencimento_fatura(self.cartao, 2026, 3), date(2026, 3, 27))

        cartao2 = CartaoCredito.objects.create(
            usuario=self.usuario, categoria=self.categoria, nome='Cartão 2',
            dia_fechamento=28, dia_vencimento=5,
        )
        self.assertEqual(services.data_vencimento_fatura(cartao2, 2026, 3), date(2026, 4, 5))

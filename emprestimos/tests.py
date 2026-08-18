from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from financas.models import CategoriaDespesa
from . import services
from .models import Emprestimo


class TabelaAmortizacaoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.categoria = CategoriaDespesa.objects.create(usuario=self.usuario, nome='Empréstimos')

    def _criar(self, **kwargs):
        defaults = dict(
            usuario=self.usuario,
            categoria=self.categoria,
            descricao='Empréstimo teste',
            valor_total=Decimal('10000'),
            taxa_juros=Decimal('2'),
            periodo_taxa=Emprestimo.PeriodoTaxa.MENSAL,
            sistema_amortizacao=Emprestimo.Sistema.PRICE,
            numero_parcelas=10,
            data_primeira_parcela=date(2026, 1, 5),
        )
        defaults.update(kwargs)
        return Emprestimo.objects.create(**defaults)

    def test_price_parcela_fixa_e_saldo_zera(self):
        emprestimo = self._criar(sistema_amortizacao=Emprestimo.Sistema.PRICE)
        services.gerar_parcelas(emprestimo)
        parcelas = list(emprestimo.parcelas.order_by('numero'))

        self.assertEqual(len(parcelas), 10)
        # Price: toda parcela tem o mesmo valor (a última pode variar 1
        # centavo por causa do arredondamento acumulado).
        valores = {p.valor_parcela for p in parcelas[:-1]}
        self.assertEqual(len(valores), 1)
        self.assertEqual(parcelas[-1].saldo_devedor, Decimal('0.00'))

        # soma das amortizações == principal
        soma_amortizacao = sum((p.valor_amortizacao for p in parcelas), Decimal('0'))
        self.assertEqual(soma_amortizacao, emprestimo.valor_total)

    def test_sac_amortizacao_fixa_e_parcela_decrescente(self):
        emprestimo = self._criar(sistema_amortizacao=Emprestimo.Sistema.SAC)
        services.gerar_parcelas(emprestimo)
        parcelas = list(emprestimo.parcelas.order_by('numero'))

        amortizacoes = {p.valor_amortizacao for p in parcelas[:-1]}
        self.assertEqual(len(amortizacoes), 1)
        # parcela cai a cada mês (juros incide sobre saldo decrescente)
        for anterior, atual in zip(parcelas, parcelas[1:]):
            self.assertLess(atual.valor_parcela, anterior.valor_parcela)
        self.assertEqual(parcelas[-1].saldo_devedor, Decimal('0.00'))

    def test_taxa_anual_converte_pra_mensal_por_juros_compostos(self):
        emprestimo = self._criar(taxa_juros=Decimal('12.6825'), periodo_taxa=Emprestimo.PeriodoTaxa.ANUAL)
        # 1% ao mês composto 12x ≈ 12.6825% ao ano
        self.assertAlmostEqual(float(services.taxa_mensal(emprestimo)), 0.01, places=4)

    def test_pagar_parcela_gera_despesa_e_marca_paga(self):
        emprestimo = self._criar()
        services.gerar_parcelas(emprestimo)
        parcela = emprestimo.parcelas.get(numero=1)

        services.registrar_pagamento_parcela(parcela, date(2026, 1, 5))
        parcela.refresh_from_db()

        self.assertTrue(parcela.paga)
        self.assertIsNotNone(parcela.despesa)
        self.assertEqual(parcela.despesa.valor, parcela.valor_parcela)
        self.assertEqual(parcela.despesa.categoria, self.categoria)

    def test_saldo_devedor_do_emprestimo_reflete_pagamentos(self):
        emprestimo = self._criar()
        services.gerar_parcelas(emprestimo)
        self.assertEqual(emprestimo.saldo_devedor, emprestimo.valor_total)

        primeira = emprestimo.parcelas.get(numero=1)
        services.registrar_pagamento_parcela(primeira, date(2026, 1, 5))
        primeira.refresh_from_db()
        self.assertEqual(emprestimo.saldo_devedor, primeira.saldo_devedor)

    def test_amortizacao_extra_reduzindo_prazo_encurta_tabela(self):
        emprestimo = self._criar(numero_parcelas=12)
        services.gerar_parcelas(emprestimo)
        total_antes = emprestimo.parcelas.count()

        services.registrar_amortizacao_extra(emprestimo, Decimal('3000'), 'PRAZO')

        parcelas_depois = list(emprestimo.parcelas.order_by('numero'))
        self.assertLess(len(parcelas_depois), total_antes)
        self.assertEqual(parcelas_depois[-1].saldo_devedor, Decimal('0.00'))
        # despesa da amortização extra foi lançada
        from financas.models import Despesa
        self.assertTrue(Despesa.objects.filter(descricao__icontains='amortização extra').exists())

    def test_amortizacao_extra_reduzindo_parcela_mantem_quantidade(self):
        emprestimo = self._criar(numero_parcelas=12)
        services.gerar_parcelas(emprestimo)
        parcela_1_valor = emprestimo.parcelas.get(numero=1).valor_parcela

        services.registrar_amortizacao_extra(emprestimo, Decimal('3000'), 'PARCELA')

        parcelas_depois = list(emprestimo.parcelas.order_by('numero'))
        self.assertEqual(len(parcelas_depois), 12)
        self.assertLess(parcelas_depois[0].valor_parcela, parcela_1_valor)

    def test_amortizacao_extra_maior_que_saldo_falha(self):
        emprestimo = self._criar()
        services.gerar_parcelas(emprestimo)
        with self.assertRaises(ValueError):
            services.registrar_amortizacao_extra(emprestimo, Decimal('999999'), 'PRAZO')

    def test_amortizacao_extra_quita_emprestimo(self):
        emprestimo = self._criar()
        services.gerar_parcelas(emprestimo)
        services.registrar_amortizacao_extra(emprestimo, emprestimo.valor_total, 'PRAZO')
        self.assertEqual(emprestimo.parcelas.filter(paga=False).count(), 0)
        self.assertEqual(emprestimo.saldo_devedor, Decimal('0'))
        self.assertTrue(emprestimo.quitado)

    def test_saldo_devedor_combina_parcela_paga_com_amortizacao_extra(self):
        # Regressão: saldo_devedor não pode depender do saldo_devedor
        # "carimbado" numa parcela vizinha — uma amortização extra entre
        # duas parcelas não gera parcela nova nenhuma pra carregar esse
        # ajuste, então precisa vir do ledger (parcelas pagas + extras).
        emprestimo = self._criar(numero_parcelas=12)
        services.gerar_parcelas(emprestimo)

        primeira = emprestimo.parcelas.get(numero=1)
        services.registrar_pagamento_parcela(primeira, date(2026, 1, 5))
        primeira.refresh_from_db()
        saldo_apos_parcela = emprestimo.saldo_devedor
        self.assertEqual(saldo_apos_parcela, primeira.saldo_devedor)

        services.registrar_amortizacao_extra(emprestimo, Decimal('2000'), 'PRAZO')
        self.assertEqual(emprestimo.saldo_devedor, saldo_apos_parcela - Decimal('2000'))

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from emprestimos.models import Emprestimo
from financas.models import CategoriaDespesa
from investimentos.models import Ativo, TransacaoAtivo

from .views import build_dashboard_data


class DashboardDataTests(TestCase):
    """build_dashboard_data agrega investimentos + dívidas num patrimônio
    líquido só — é a função mais crítica do app e não tinha nenhum teste.
    Toda chamada externa (cotações, CDI, Ibovespa) é mockada: o objetivo
    aqui é a agregação, não a integração de verdade com brapi.dev/CoinGecko/BCB
    (isso já é coberto em investimentos/tests.py)."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')

    @patch('investimentos.services.calcular_valor_atual_renda_fixa')
    def test_renda_fixa_usa_valor_calculado_e_conta_no_patrimonio(self, mock_calc):
        mock_calc.return_value = Decimal('1100.00')
        Ativo.objects.create(
            usuario=self.usuario, ticker='CDB X', tipo=Ativo.Tipo.RENDA_FIXA,
            indexador=Ativo.Indexador.CDI, taxa_contratada=Decimal('100'),
            valor_aplicado=Decimal('1000.00'), data_aplicacao=date(2026, 1, 1),
        )
        dados = build_dashboard_data(self.usuario)

        self.assertEqual(dados['patrimonio_total'], 1100.0)
        self.assertEqual(dados['valor_investido_total'], 1000.0)
        self.assertEqual(dados['patrimonio_liquido'], 1100.0)
        self.assertTrue(dados['tem_ativos'])

    @patch('investimentos.services.calcular_valor_atual_renda_fixa')
    def test_divida_de_emprestimo_reduz_patrimonio_liquido_sem_afetar_patrimonio_total(self, mock_calc):
        mock_calc.return_value = Decimal('1000.00')
        Ativo.objects.create(
            usuario=self.usuario, ticker='CDB X', tipo=Ativo.Tipo.RENDA_FIXA,
            indexador=Ativo.Indexador.CDI, taxa_contratada=Decimal('100'),
            valor_aplicado=Decimal('1000.00'), data_aplicacao=date(2026, 1, 1),
        )
        categoria = CategoriaDespesa.objects.create(usuario=self.usuario, nome='Empréstimos')
        Emprestimo.objects.create(
            usuario=self.usuario, categoria=categoria, descricao='Consignado',
            valor_total=Decimal('400.00'), taxa_juros=Decimal('0'),
            numero_parcelas=1, data_primeira_parcela=date(2026, 2, 1),
        )  # nenhuma parcela gerada/paga ainda -> saldo_devedor = valor_total inteiro

        dados = build_dashboard_data(self.usuario)

        self.assertEqual(dados['patrimonio_total'], 1000.0)
        self.assertEqual(dados['divida_emprestimos'], 400.0)
        self.assertEqual(dados['divida_total'], 400.0)
        self.assertEqual(dados['patrimonio_liquido'], 600.0)

    @patch('investimentos.services.get_variacao_ibovespa')
    @patch('investimentos.services.get_variacao_cdi')
    @patch('investimentos.services.get_cotacoes_cripto')
    @patch('investimentos.services.get_cotacoes_acoes')
    def test_fallback_para_preco_medio_quando_cotacao_indisponivel(
        self, mock_acoes, mock_cripto, mock_cdi, mock_ibov,
    ):
        # API de cotação não devolveu nada pra esse ticker (fora do ar, ou
        # ticker não encontrado) — o dashboard não pode quebrar nem zerar o
        # card de patrimônio, tem que cair no preço médio de compra.
        mock_acoes.return_value = {}
        mock_cripto.return_value = {}
        mock_cdi.return_value = None
        mock_ibov.return_value = None

        ativo = Ativo.objects.create(usuario=self.usuario, ticker='PETR4', tipo=Ativo.Tipo.ACAO)
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('10'), preco_unitario=Decimal('30.00'), data=date(2026, 1, 10),
        )

        dados = build_dashboard_data(self.usuario)

        self.assertEqual(dados['patrimonio_total'], 300.0)  # 10 * 30 (preço médio, fallback)
        self.assertEqual(len(dados['alocacao']), 1)
        self.assertFalse(dados['alocacao'][0]['cotacao_disponivel'])

    def test_sem_nenhum_ativo_retorna_patrimonio_zerado_sem_quebrar(self):
        dados = build_dashboard_data(self.usuario)

        self.assertEqual(dados['patrimonio_total'], 0.0)
        self.assertEqual(dados['patrimonio_liquido'], 0.0)
        self.assertFalse(dados['tem_ativos'])
        self.assertEqual(dados['alocacao'], [])

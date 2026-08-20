import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from . import services
from .models import Ativo, Provento, TransacaoAtivo

# `date` normal (não subclasse) pra usar no lugar de `investimentos.services.date`
# em testes que precisam de um "hoje" fixo — sem isso, calcular_valor_atual_renda_fixa
# e get_variacao_cdi dependeriam da data real de quando o teste roda.
class _FakeDate(date):
    @classmethod
    def today(cls):
        return date(2026, 1, 5)


class PosicaoAtivoTests(TestCase):
    """Ativo.quantidade/preco_medio_compra são calculados a partir do ledger
    de TransacaoAtivo (custo médio ponderado) — nunca campos diretos."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')

    def _ativo(self, tipo=Ativo.Tipo.ACAO, **kwargs):
        defaults = dict(usuario=self.usuario, ticker='TEST3', tipo=tipo)
        defaults.update(kwargs)
        return Ativo.objects.create(**defaults)

    def test_compra_unica_define_preco_medio(self):
        ativo = self._ativo()
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('10'), preco_unitario=Decimal('10.00'), data=date(2026, 1, 5),
        )
        self.assertEqual(ativo.quantidade, Decimal('10'))
        self.assertEqual(ativo.preco_medio_compra, Decimal('10.00'))

    def test_duas_compras_pondera_preco_medio(self):
        ativo = self._ativo()
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('10'), preco_unitario=Decimal('10.00'), data=date(2026, 1, 5),
        )
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('10'), preco_unitario=Decimal('20.00'), data=date(2026, 1, 10),
        )
        self.assertEqual(ativo.quantidade, Decimal('20'))
        self.assertEqual(ativo.preco_medio_compra, Decimal('15'))

    def test_venda_reduz_quantidade_sem_mudar_preco_medio(self):
        ativo = self._ativo()
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('10'), preco_unitario=Decimal('10.00'), data=date(2026, 1, 5),
        )
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('10'), preco_unitario=Decimal('20.00'), data=date(2026, 1, 10),
        )
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.VENDA,
            quantidade=Decimal('5'), preco_unitario=Decimal('25.00'), data=date(2026, 1, 15),
        )
        self.assertEqual(ativo.quantidade, Decimal('15'))
        self.assertEqual(ativo.preco_medio_compra, Decimal('15'))

    def test_cripto_com_preco_fracao_de_centavo_preserva_8_casas(self):
        # Regressão do bug real: token barato comprado com R$ (não por
        # quantidade) tem preço unitário na casa de frações de centavo.
        ativo = self._ativo(tipo=Ativo.Tipo.CRIPTO, ticker='SHIB', coingecko_id='shiba-inu')
        TransacaoAtivo.objects.create(
            ativo=ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('1000000'), preco_unitario=Decimal('0.00005971'), data=date(2026, 1, 5),
        )
        self.assertEqual(ativo.preco_medio_compra, Decimal('0.00005971'))
        self.assertEqual(ativo.valor_investido, Decimal('59.71000000'))

    def test_valor_investido_renda_fixa_usa_valor_aplicado(self):
        ativo = self._ativo(
            tipo=Ativo.Tipo.RENDA_FIXA, ticker='CDB X', indexador=Ativo.Indexador.CDI,
            taxa_contratada=Decimal('100'), valor_aplicado=Decimal('1000.00'), data_aplicacao=date(2026, 1, 1),
        )
        self.assertEqual(ativo.valor_investido, Decimal('1000.00'))
        # renda fixa não tem lote de compra/venda — quantidade não se aplica
        self.assertIsNone(ativo.quantidade)


class ProventoTests(TestCase):
    """valor_total do provento depende da quantidade que o usuário tinha na
    data-com — reaproveita o ledger de TransacaoAtivo, não é digitado."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.ativo = Ativo.objects.create(usuario=self.usuario, ticker='PROV3', tipo=Ativo.Tipo.ACAO)
        TransacaoAtivo.objects.create(
            ativo=self.ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('100'), preco_unitario=Decimal('10.00'), data=date(2026, 1, 5),
        )
        TransacaoAtivo.objects.create(
            ativo=self.ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('50'), preco_unitario=Decimal('12.00'), data=date(2026, 2, 10),
        )

    def test_data_com_antes_da_segunda_compra_considera_so_a_posicao_de_entao(self):
        provento = Provento.objects.create(
            ativo=self.ativo, tipo=Provento.Tipo.DIVIDENDO,
            valor_por_cota=Decimal('0.50'), data_com=date(2026, 1, 31),
        )
        self.assertEqual(provento.quantidade_na_data, Decimal('100'))
        self.assertEqual(provento.valor_total, Decimal('50.00'))

    def test_data_com_depois_das_duas_compras_soma_tudo(self):
        provento = Provento.objects.create(
            ativo=self.ativo, tipo=Provento.Tipo.DIVIDENDO,
            valor_por_cota=Decimal('0.50'), data_com=date(2026, 3, 1),
        )
        self.assertEqual(provento.quantidade_na_data, Decimal('150'))
        self.assertEqual(provento.valor_total, Decimal('75.00'))


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class CotacoesServiceTests(TestCase):
    """services.py é a única camada que fala com brapi.dev/CoinGecko — testa
    o parsing da resposta e o fallback pro cache "stale" quando a API cai.
    Cache trocado pra LocMemCache (o padrão do projeto é FileBasedCache em
    disco, que vazaria estado entre testes)."""

    def setUp(self):
        cache.clear()

    @patch('investimentos.services.requests.get')
    def test_get_cotacoes_acoes_sucesso(self, mock_get):
        mock_get.return_value = Mock(json=lambda: {
            'results': [{'symbol': 'PETR4', 'regularMarketPrice': 30.5, 'regularMarketChangePercent': 1.2}]
        })
        resultado = services.get_cotacoes_acoes(['PETR4'])
        self.assertEqual(resultado, {'PETR4': {'preco': 30.5, 'variacao_dia_pct': 1.2}})

    @patch('investimentos.services.requests.get')
    def test_get_cotacoes_acoes_cai_no_stale_quando_api_falha(self, mock_get):
        mock_get.return_value = Mock(json=lambda: {
            'results': [{'symbol': 'PETR4', 'regularMarketPrice': 30.5, 'regularMarketChangePercent': 1.2}]
        })
        services.get_cotacoes_acoes(['PETR4'])  # popula o cache normal + o stale
        cache.delete('brapi:PETR4')  # expira só o curto, mantém o stale (24h)

        mock_get.side_effect = requests.RequestException('API fora do ar')
        resultado = services.get_cotacoes_acoes(['PETR4'])
        self.assertEqual(resultado, {'PETR4': {'preco': 30.5, 'variacao_dia_pct': 1.2}})

    @patch('investimentos.services.requests.get')
    def test_get_cotacoes_acoes_sem_stale_retorna_vazio(self, mock_get):
        mock_get.side_effect = requests.RequestException('API fora do ar')
        self.assertEqual(services.get_cotacoes_acoes(['PETR4']), {})

    @patch('investimentos.services.requests.get')
    def test_get_cotacoes_cripto_sucesso(self, mock_get):
        mock_get.return_value = Mock(json=lambda: {
            'bitcoin': {'brl': 350000.0, 'brl_24h_change': -2.5}
        })
        resultado = services.get_cotacoes_cripto(['bitcoin'])
        self.assertEqual(resultado, {'bitcoin': {'preco': 350000.0, 'variacao_dia_pct': -2.5}})

    def test_listas_vazias_nao_chamam_a_api(self):
        self.assertEqual(services.get_cotacoes_acoes([]), {})
        self.assertEqual(services.get_cotacoes_cripto([]), {})


class RendaFixaCalculoTests(TestCase):
    """calcular_valor_atual_renda_fixa estima o valor via composição de taxa
    histórica (CDI/Selic) ou juros simples anualizados (Prefixado)."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')

    def test_retorna_none_sem_dados_suficientes(self):
        ativo = Ativo.objects.create(usuario=self.usuario, ticker='CDB incompleto', tipo=Ativo.Tipo.RENDA_FIXA)
        self.assertIsNone(services.calcular_valor_atual_renda_fixa(ativo))

    @patch('investimentos.services.date', _FakeDate)
    @patch('investimentos.services.get_serie_bcb')
    def test_cdi_composto_diariamente(self, mock_serie):
        # 100% do CDI, dois dias úteis a 0.05% cada -> fator = 1.0005 * 1.0005
        mock_serie.return_value = {
            date(2026, 1, 2): Decimal('0.05'),
            date(2026, 1, 3): Decimal('0.05'),
        }
        ativo = Ativo.objects.create(
            usuario=self.usuario, ticker='CDB X', tipo=Ativo.Tipo.RENDA_FIXA,
            indexador=Ativo.Indexador.CDI, taxa_contratada=Decimal('100'),
            valor_aplicado=Decimal('1000'), data_aplicacao=date(2026, 1, 1),
        )
        resultado = services.calcular_valor_atual_renda_fixa(ativo)
        esperado = 1000 * 1.0005 * 1.0005
        self.assertAlmostEqual(float(resultado), esperado, places=4)

    @patch('investimentos.services.date', _FakeDate)
    @patch('investimentos.services.get_serie_bcb')
    def test_cdi_sem_serie_do_bcb_retorna_none(self, mock_serie):
        mock_serie.return_value = {}
        ativo = Ativo.objects.create(
            usuario=self.usuario, ticker='CDB Y', tipo=Ativo.Tipo.RENDA_FIXA,
            indexador=Ativo.Indexador.CDI, taxa_contratada=Decimal('100'),
            valor_aplicado=Decimal('1000'), data_aplicacao=date(2026, 1, 1),
        )
        self.assertIsNone(services.calcular_valor_atual_renda_fixa(ativo))

    @patch('investimentos.services.date', _FakeDate)
    def test_prefixado_juros_anualizados_act_365(self):
        # hoje fixado em 2026-01-05, aplicação em 2025-01-05 -> 365 dias
        ativo = Ativo.objects.create(
            usuario=self.usuario, ticker='CDB Prefixado', tipo=Ativo.Tipo.RENDA_FIXA,
            indexador=Ativo.Indexador.PREFIXADO, taxa_contratada=Decimal('12'),
            valor_aplicado=Decimal('1000'), data_aplicacao=date(2025, 1, 5),
        )
        resultado = services.calcular_valor_atual_renda_fixa(ativo)
        self.assertAlmostEqual(float(resultado), 1120.0, places=2)


class TransacaoAtivoAPITests(TestCase):
    """Validação de venda a descoberto e isolamento multi-tenant no
    endpoint /api/investimentos/transacoes/."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.ativo = Ativo.objects.create(usuario=self.usuario, ticker='TEST3', tipo=Ativo.Tipo.ACAO)
        self.client = Client()
        self.client.login(username='teste', password='senha123')

    def _post(self, payload):
        return self.client.post('/api/investimentos/transacoes/', json.dumps(payload), content_type='application/json')

    def test_venda_maior_que_posicao_falha(self):
        self._post({
            'ativo': self.ativo.id, 'tipo': 'COMPRA', 'quantidade': '10',
            'preco_unitario': '10.00', 'data': '2026-01-05',
        })
        resp = self._post({
            'ativo': self.ativo.id, 'tipo': 'VENDA', 'quantidade': '15',
            'preco_unitario': '12.00', 'data': '2026-01-10',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('quantidade', resp.json())
        self.assertEqual(TransacaoAtivo.objects.filter(tipo=TransacaoAtivo.Tipo.VENDA).count(), 0)

    def test_venda_ate_a_posicao_atual_funciona(self):
        self._post({
            'ativo': self.ativo.id, 'tipo': 'COMPRA', 'quantidade': '10',
            'preco_unitario': '10.00', 'data': '2026-01-05',
        })
        resp = self._post({
            'ativo': self.ativo.id, 'tipo': 'VENDA', 'quantidade': '10',
            'preco_unitario': '12.00', 'data': '2026-01-10',
        })
        self.assertEqual(resp.status_code, 201)

    def test_nao_deixa_lancar_transacao_em_ativo_de_outro_usuario(self):
        outro = User.objects.create_user('outro', password='senha123')
        ativo_alheio = Ativo.objects.create(usuario=outro, ticker='ALHEIO3', tipo=Ativo.Tipo.ACAO)
        resp = self._post({
            'ativo': ativo_alheio.id, 'tipo': 'COMPRA', 'quantidade': '10',
            'preco_unitario': '10.00', 'data': '2026-01-05',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(TransacaoAtivo.objects.count(), 0)


class AlocacaoAlvoAPITests(TestCase):
    """PUT /api/investimentos/alocacao-alvo/ é um "documento" só — exige que
    a soma dos percentuais dê exatamente 100%."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.client = Client()
        self.client.login(username='teste', password='senha123')

    def _put(self, payload):
        return self.client.put('/api/investimentos/alocacao-alvo/', json.dumps(payload), content_type='application/json')

    def test_soma_100_por_cento_salva(self):
        resp = self._put({'ACAO': 60, 'FII': 30, 'RENDA_FIXA': 10})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'ACAO': 60.0, 'FII': 30.0, 'RENDA_FIXA': 10.0})

    def test_soma_diferente_de_100_falha(self):
        resp = self._put({'ACAO': 60, 'FII': 30})
        self.assertEqual(resp.status_code, 400)


class AvaliarAtivoMoedaTests(TestCase):
    """Ativo.moeda é só a moeda de EXIBIÇÃO da cripto — valor_atual (usado
    nos totais do patrimônio) é sempre calculado em BRL, independente dela."""

    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.ativo = Ativo.objects.create(
            usuario=self.usuario, ticker='BTC', tipo=Ativo.Tipo.CRIPTO,
            coingecko_id='bitcoin', moeda=Ativo.Moeda.USD,
        )
        TransacaoAtivo.objects.create(
            ativo=self.ativo, tipo=TransacaoAtivo.Tipo.COMPRA,
            quantidade=Decimal('0.1'), preco_unitario=Decimal('300000.00'), data=date(2026, 1, 5),
        )

    def test_valor_atual_usa_sempre_a_cotacao_brl(self):
        cotacoes_cripto = {'bitcoin': {'preco': 350000.0, 'variacao_dia_pct': 1.0}}
        avaliacao = services.avaliar_ativo(self.ativo, {}, cotacoes_cripto)
        self.assertEqual(avaliacao['valor_atual'], Decimal('35000.0'))
        self.assertIsNone(avaliacao['preco_atual_nativo'])

    def test_preco_atual_nativo_vem_da_cotacao_na_moeda_do_ativo(self):
        cotacoes_cripto = {'bitcoin': {'preco': 350000.0, 'variacao_dia_pct': 1.0}}
        cotacoes_cripto_nativa = {'USD': {'bitcoin': {'preco': 65000.0, 'variacao_dia_pct': 1.0}}}
        avaliacao = services.avaliar_ativo(self.ativo, {}, cotacoes_cripto, cotacoes_cripto_nativa)
        # valor_atual continua em BRL, preco_atual_nativo é só informativo
        self.assertEqual(avaliacao['valor_atual'], Decimal('35000.0'))
        self.assertEqual(avaliacao['preco_atual_nativo'], Decimal('65000.0'))

    def test_cripto_em_brl_nunca_tem_preco_nativo(self):
        ativo_brl = Ativo.objects.create(usuario=self.usuario, ticker='ETH', tipo=Ativo.Tipo.CRIPTO, coingecko_id='ethereum')
        cotacoes_cripto_nativa = {'USD': {'ethereum': {'preco': 3000.0}}}
        avaliacao = services.avaliar_ativo(ativo_brl, {}, {}, cotacoes_cripto_nativa)
        self.assertIsNone(avaliacao['preco_atual_nativo'])

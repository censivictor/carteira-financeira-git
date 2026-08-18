from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from .models import CategoriaDespesa, Despesa, Receita


class ImportarExtratoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('teste', password='senha123')
        self.categoria = CategoriaDespesa.objects.create(usuario=self.usuario, nome='Mercado')
        self.client = Client()
        self.client.login(username='teste', password='senha123')

    def _importar(self, despesas=None, receitas=None):
        return self.client.post(
            '/api/financas/importar/',
            {'despesas': despesas or [], 'receitas': receitas or []},
            content_type='application/json',
        )

    def test_importa_despesas_e_receitas(self):
        resp = self._importar(
            despesas=[{'descricao': 'Supermercado', 'valor': '150.50', 'data': '2026-03-05', 'categoria': self.categoria.id}],
            receitas=[{'descricao': 'Salário', 'valor': '5000', 'data': '2026-03-01'}],
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['criadas_despesas'], 1)
        self.assertEqual(data['criadas_receitas'], 1)
        self.assertEqual(Despesa.objects.count(), 1)
        self.assertEqual(Receita.objects.count(), 1)
        self.assertEqual(Despesa.objects.first().valor, Decimal('150.50'))

    def test_reimportar_a_mesma_linha_nao_duplica(self):
        item = {'descricao': 'Supermercado', 'valor': '150.50', 'data': '2026-03-05', 'categoria': self.categoria.id}
        self._importar(despesas=[item])
        resp = self._importar(despesas=[item])
        data = resp.json()
        self.assertEqual(data['criadas_despesas'], 0)
        self.assertEqual(data['duplicadas_despesas'], 1)
        self.assertEqual(Despesa.objects.count(), 1)

    def test_categoria_de_outro_usuario_falha_com_erro_amigavel(self):
        outro = User.objects.create_user('outro', password='senha123')
        categoria_alheia = CategoriaDespesa.objects.create(usuario=outro, nome='Alheia')
        resp = self._importar(
            despesas=[{'descricao': 'Suspeita', 'valor': '10', 'data': '2026-03-05', 'categoria': categoria_alheia.id}],
        )
        data = resp.json()
        self.assertEqual(data['criadas_despesas'], 0)
        self.assertEqual(len(data['erros']), 1)
        self.assertEqual(Despesa.objects.count(), 0)

    def test_linha_com_valor_invalido_vira_erro_sem_quebrar_as_outras(self):
        resp = self._importar(despesas=[
            {'descricao': 'Ruim', 'valor': 'abc', 'data': '2026-03-05', 'categoria': self.categoria.id},
            {'descricao': 'Boa', 'valor': '20', 'data': '2026-03-06', 'categoria': self.categoria.id},
        ])
        data = resp.json()
        self.assertEqual(data['criadas_despesas'], 1)
        self.assertEqual(len(data['erros']), 1)

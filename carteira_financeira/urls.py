from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.api_views import (
    DashboardAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    SignupAPIView,
)
from financas.api_views import (
    CategoriaDespesaViewSet,
    DespesaRecorrenteViewSet,
    DespesaViewSet,
    ImportarExtratoAPIView,
    ReceitaViewSet,
)
from investimentos.api_views import (
    AlocacaoAlvoAPIView,
    AtivoViewSet,
    BuscarAtivosAPIView,
    CotacoesAPIView,
    ProventoViewSet,
    TransacaoAtivoViewSet,
)
from emprestimos.api_views import EmprestimoViewSet, ParcelaEmprestimoViewSet
from cartoes.api_views import CartaoCreditoViewSet, CompraCartaoViewSet, FaturaCartaoViewSet
from metas.api_views import AporteMetaViewSet, MetaFinanceiraViewSet

# API consumida pelo front Vue (frontend/) — aditiva, não mexe nas rotas
# de template abaixo. Ver plano de migração em core/api_views.py.
router = DefaultRouter()
router.register('investimentos/ativos', AtivoViewSet, basename='api-ativo')
router.register('investimentos/transacoes', TransacaoAtivoViewSet, basename='api-transacao')
router.register('investimentos/proventos', ProventoViewSet, basename='api-provento')
router.register('financas/categorias', CategoriaDespesaViewSet, basename='api-categoria')
router.register('financas/despesas', DespesaViewSet, basename='api-despesa')
router.register('financas/recorrentes', DespesaRecorrenteViewSet, basename='api-recorrente')
router.register('financas/receitas', ReceitaViewSet, basename='api-receita')
router.register('emprestimos', EmprestimoViewSet, basename='api-emprestimo')
router.register('emprestimos-parcelas', ParcelaEmprestimoViewSet, basename='api-parcela-emprestimo')
router.register('cartoes', CartaoCreditoViewSet, basename='api-cartao')
router.register('cartoes-compras', CompraCartaoViewSet, basename='api-compra-cartao')
router.register('cartoes-faturas', FaturaCartaoViewSet, basename='api-fatura-cartao')
router.register('metas', MetaFinanceiraViewSet, basename='api-meta')
router.register('metas-aportes', AporteMetaViewSet, basename='api-aporte-meta')

api_urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view(), name='api-dashboard'),
    path('auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('auth/signup/', SignupAPIView.as_view(), name='api-signup'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api-logout'),
    path('auth/me/', MeAPIView.as_view(), name='api-me'),
    path('investimentos/cotacoes/', CotacoesAPIView.as_view(), name='api-cotacoes'),
    path('investimentos/buscar/', BuscarAtivosAPIView.as_view(), name='api-buscar-ativos'),
    path('investimentos/alocacao-alvo/', AlocacaoAlvoAPIView.as_view(), name='api-alocacao-alvo'),
    path('financas/importar/', ImportarExtratoAPIView.as_view(), name='api-importar-extrato'),
    path('', include(router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
]

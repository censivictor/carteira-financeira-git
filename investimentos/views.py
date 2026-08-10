from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from . import services
from .forms import AtivoForm
from .models import Ativo

TIPOS_COTADOS_B3 = (Ativo.Tipo.ACAO, Ativo.Tipo.FII)


class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'investimentos/ativo_list.html'
    context_object_name = 'ativos'

    def get_queryset(self):
        return Ativo.objects.filter(ativo_flag=True)


class AtivoCreateView(LoginRequiredMixin, CreateView):
    model = Ativo
    form_class = AtivoForm
    template_name = 'investimentos/ativo_form.html'
    success_url = reverse_lazy('ativo-list')


class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    form_class = AtivoForm
    template_name = 'investimentos/ativo_form.html'
    success_url = reverse_lazy('ativo-list')


class AtivoDeleteView(LoginRequiredMixin, DeleteView):
    model = Ativo
    template_name = 'investimentos/ativo_confirm_delete.html'
    success_url = reverse_lazy('ativo-list')


def cotacoes_json(request):
    """Endpoint JSON usado pelo polling do dashboard (atualização periódica
    de preços sem recarregar a página). Renda fixa não entra aqui — o valor
    muda por dia, não por minuto, então não faz sentido recalcular a cada
    polling (o dashboard já mostra o valor calculado no carregamento)."""
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Não autenticado.'}, status=401)

    ativos = Ativo.objects.filter(ativo_flag=True)
    tickers = [a.ticker for a in ativos if a.tipo in TIPOS_COTADOS_B3]
    cripto_ids = [a.coingecko_id for a in ativos if a.tipo == Ativo.Tipo.CRIPTO and a.coingecko_id]

    cotacoes_acoes = services.get_cotacoes_acoes(tickers)
    cotacoes_cripto = services.get_cotacoes_cripto(cripto_ids)

    resultado = {}
    for ativo in ativos:
        if ativo.tipo in TIPOS_COTADOS_B3:
            info = cotacoes_acoes.get(ativo.ticker, {})
        elif ativo.tipo == Ativo.Tipo.CRIPTO:
            info = cotacoes_cripto.get(ativo.coingecko_id, {})
        else:
            continue  # RENDA_FIXA não é atualizada pelo polling

        preco = info.get('preco')
        resultado[ativo.ticker] = {
            'preco': preco,
            'variacao_dia_pct': info.get('variacao_dia_pct'),
            'valor_atual': float(ativo.quantidade) * preco if preco is not None else None,
        }

    return JsonResponse(resultado)


def buscar_ativos_json(request):
    """Autocomplete usado no formulário de novo/editar ativo.

    GET params: tipo (ACAO|FII|CRIPTO), q (texto digitado).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Não autenticado.'}, status=401)

    tipo = request.GET.get('tipo', '')
    q = request.GET.get('q', '')

    if tipo in ('ACAO', 'FII'):
        resultados = services.buscar_tickers_b3(q, tipo)
    elif tipo == 'CRIPTO':
        resultados = services.buscar_cripto(q)
    else:
        resultados = []

    return JsonResponse({'results': resultados})

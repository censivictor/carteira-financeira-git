from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from . import services
from .forms import AtivoForm
from .models import Ativo


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
    de preços sem recarregar a página)."""
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Não autenticado.'}, status=401)

    ativos = Ativo.objects.filter(ativo_flag=True)
    tickers = [a.ticker for a in ativos if a.tipo == Ativo.Tipo.ACAO]
    cripto_ids = [a.coingecko_id for a in ativos if a.tipo == Ativo.Tipo.CRIPTO and a.coingecko_id]

    cotacoes_acoes = services.get_cotacoes_acoes(tickers)
    cotacoes_cripto = services.get_cotacoes_cripto(cripto_ids)

    resultado = {}
    for ativo in ativos:
        if ativo.tipo == Ativo.Tipo.ACAO:
            info = cotacoes_acoes.get(ativo.ticker, {})
        else:
            info = cotacoes_cripto.get(ativo.coingecko_id, {})
        preco = info.get('preco')
        resultado[ativo.ticker] = {
            'preco': preco,
            'variacao_dia_pct': info.get('variacao_dia_pct'),
            'valor_atual': float(ativo.quantidade) * preco if preco is not None else None,
        }

    return JsonResponse(resultado)

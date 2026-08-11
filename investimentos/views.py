from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from . import services
from .forms import AtivoForm, ProventoForm, TransacaoAtivoForm
from .models import Ativo, Provento, TransacaoAtivo

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

    def get_success_url(self):
        # Renda fixa já fica completa ao salvar. Ação/FII/Cripto começam sem
        # posição — manda pro detalhe pra já convidar a lançar a 1ª compra.
        if self.object.tipo == Ativo.Tipo.RENDA_FIXA:
            return reverse('ativo-list')
        return reverse('ativo-detail', args=[self.object.pk])


class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    form_class = AtivoForm
    template_name = 'investimentos/ativo_form.html'
    success_url = reverse_lazy('ativo-list')


class AtivoDeleteView(LoginRequiredMixin, DeleteView):
    model = Ativo
    template_name = 'investimentos/ativo_confirm_delete.html'
    success_url = reverse_lazy('ativo-list')


class AtivoDetailView(LoginRequiredMixin, DetailView):
    model = Ativo
    template_name = 'investimentos/ativo_detail.html'
    context_object_name = 'ativo'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['transacoes'] = self.object.transacoes.all()
        if self.object.tipo in TIPOS_COTADOS_B3:
            proventos = self.object.proventos.all()
            ctx['proventos'] = proventos
            ctx['proventos_total'] = sum((p.valor_total for p in proventos), Decimal('0'))
        return ctx


class TransacaoCreateView(LoginRequiredMixin, CreateView):
    model = TransacaoAtivo
    form_class = TransacaoAtivoForm
    template_name = 'investimentos/transacao_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.ativo = get_object_or_404(Ativo, pk=kwargs['ativo_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['ativo'] = self.ativo
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ativo'] = self.ativo
        return ctx

    def form_valid(self, form):
        form.instance.ativo = self.ativo
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('ativo-detail', args=[self.ativo.pk])


class TransacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = TransacaoAtivo
    template_name = 'investimentos/transacao_confirm_delete.html'

    def get_success_url(self):
        return reverse('ativo-detail', args=[self.object.ativo.pk])


class ProventoCreateView(LoginRequiredMixin, CreateView):
    model = Provento
    form_class = ProventoForm
    template_name = 'investimentos/provento_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Proventos só fazem sentido pra Ação/FII — cripto e renda fixa não
        # passam por aqui (404 em vez de deixar criar fora de contexto).
        self.ativo = get_object_or_404(Ativo, pk=kwargs['ativo_pk'], tipo__in=TIPOS_COTADOS_B3)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ativo'] = self.ativo
        return ctx

    def form_valid(self, form):
        form.instance.ativo = self.ativo
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('ativo-detail', args=[self.ativo.pk])


class ProventoDeleteView(LoginRequiredMixin, DeleteView):
    model = Provento
    template_name = 'investimentos/provento_confirm_delete.html'

    def get_success_url(self):
        return reverse('ativo-detail', args=[self.object.ativo.pk])


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

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CategoriaDespesaForm, DespesaForm, DespesaRecorrenteForm, ReceitaForm
from .models import CategoriaDespesa, Despesa, DespesaRecorrente, Receita


class DespesaListView(LoginRequiredMixin, ListView):
    model = Despesa
    template_name = 'financas/despesa_list.html'
    context_object_name = 'despesas'
    paginate_by = 30


class DespesaCreateView(LoginRequiredMixin, CreateView):
    model = Despesa
    form_class = DespesaForm
    template_name = 'financas/despesa_form.html'
    success_url = reverse_lazy('despesa-list')


class DespesaUpdateView(LoginRequiredMixin, UpdateView):
    model = Despesa
    form_class = DespesaForm
    template_name = 'financas/despesa_form.html'
    success_url = reverse_lazy('despesa-list')


class DespesaDeleteView(LoginRequiredMixin, DeleteView):
    model = Despesa
    template_name = 'financas/despesa_confirm_delete.html'
    success_url = reverse_lazy('despesa-list')


class ReceitaListView(LoginRequiredMixin, ListView):
    model = Receita
    template_name = 'financas/receita_list.html'
    context_object_name = 'receitas'
    paginate_by = 30


class ReceitaCreateView(LoginRequiredMixin, CreateView):
    model = Receita
    form_class = ReceitaForm
    template_name = 'financas/receita_form.html'
    success_url = reverse_lazy('receita-list')


class ReceitaUpdateView(LoginRequiredMixin, UpdateView):
    model = Receita
    form_class = ReceitaForm
    template_name = 'financas/receita_form.html'
    success_url = reverse_lazy('receita-list')


class ReceitaDeleteView(LoginRequiredMixin, DeleteView):
    model = Receita
    template_name = 'financas/receita_confirm_delete.html'
    success_url = reverse_lazy('receita-list')


class CategoriaDespesaListView(LoginRequiredMixin, ListView):
    model = CategoriaDespesa
    template_name = 'financas/categoria_list.html'
    context_object_name = 'categorias'


class CategoriaDespesaCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaDespesa
    form_class = CategoriaDespesaForm
    template_name = 'financas/categoria_form.html'
    success_url = reverse_lazy('categoria-list')


class CategoriaDespesaUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaDespesa
    form_class = CategoriaDespesaForm
    template_name = 'financas/categoria_form.html'
    success_url = reverse_lazy('categoria-list')


class CategoriaDespesaDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaDespesa
    template_name = 'financas/categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria-list')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir essa categoria — existem despesas (ou recorrências) '
                'vinculadas a ela. Mova ou exclua essas despesas primeiro.',
            )
            return redirect('categoria-list')


class DespesaRecorrenteListView(LoginRequiredMixin, ListView):
    model = DespesaRecorrente
    template_name = 'financas/recorrente_list.html'
    context_object_name = 'recorrentes'


class DespesaRecorrenteCreateView(LoginRequiredMixin, CreateView):
    model = DespesaRecorrente
    form_class = DespesaRecorrenteForm
    template_name = 'financas/recorrente_form.html'
    success_url = reverse_lazy('recorrente-list')


class DespesaRecorrenteUpdateView(LoginRequiredMixin, UpdateView):
    model = DespesaRecorrente
    form_class = DespesaRecorrenteForm
    template_name = 'financas/recorrente_form.html'
    success_url = reverse_lazy('recorrente-list')


class DespesaRecorrenteDeleteView(LoginRequiredMixin, DeleteView):
    model = DespesaRecorrente
    template_name = 'financas/recorrente_confirm_delete.html'
    success_url = reverse_lazy('recorrente-list')

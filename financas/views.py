from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import DespesaForm, ReceitaForm
from .models import Despesa, Receita


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

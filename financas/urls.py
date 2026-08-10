from django.urls import path

from . import views

urlpatterns = [
    path('despesas/', views.DespesaListView.as_view(), name='despesa-list'),
    path('despesas/nova/', views.DespesaCreateView.as_view(), name='despesa-create'),
    path('despesas/<int:pk>/editar/', views.DespesaUpdateView.as_view(), name='despesa-update'),
    path('despesas/<int:pk>/excluir/', views.DespesaDeleteView.as_view(), name='despesa-delete'),
    path('receitas/', views.ReceitaListView.as_view(), name='receita-list'),
    path('receitas/nova/', views.ReceitaCreateView.as_view(), name='receita-create'),
    path('receitas/<int:pk>/editar/', views.ReceitaUpdateView.as_view(), name='receita-update'),
    path('receitas/<int:pk>/excluir/', views.ReceitaDeleteView.as_view(), name='receita-delete'),
]

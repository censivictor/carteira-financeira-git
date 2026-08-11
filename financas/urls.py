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
    path('categorias/', views.CategoriaDespesaListView.as_view(), name='categoria-list'),
    path('categorias/nova/', views.CategoriaDespesaCreateView.as_view(), name='categoria-create'),
    path('categorias/<int:pk>/editar/', views.CategoriaDespesaUpdateView.as_view(), name='categoria-update'),
    path('categorias/<int:pk>/excluir/', views.CategoriaDespesaDeleteView.as_view(), name='categoria-delete'),
    path('recorrentes/', views.DespesaRecorrenteListView.as_view(), name='recorrente-list'),
    path('recorrentes/nova/', views.DespesaRecorrenteCreateView.as_view(), name='recorrente-create'),
    path('recorrentes/<int:pk>/editar/', views.DespesaRecorrenteUpdateView.as_view(), name='recorrente-update'),
    path('recorrentes/<int:pk>/excluir/', views.DespesaRecorrenteDeleteView.as_view(), name='recorrente-delete'),
]

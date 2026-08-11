from django.urls import path

from . import views

urlpatterns = [
    path('', views.AtivoListView.as_view(), name='ativo-list'),
    path('novo/', views.AtivoCreateView.as_view(), name='ativo-create'),
    path('cotacoes.json', views.cotacoes_json, name='cotacoes-json'),
    path('buscar.json', views.buscar_ativos_json, name='buscar-ativos-json'),
    path('<int:pk>/editar/', views.AtivoUpdateView.as_view(), name='ativo-update'),
    path('<int:pk>/excluir/', views.AtivoDeleteView.as_view(), name='ativo-delete'),
    path('<int:ativo_pk>/transacoes/nova/', views.TransacaoCreateView.as_view(), name='transacao-create'),
    path('transacoes/<int:pk>/excluir/', views.TransacaoDeleteView.as_view(), name='transacao-delete'),
    path('<int:pk>/', views.AtivoDetailView.as_view(), name='ativo-detail'),
]

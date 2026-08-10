from django.urls import path

from . import views

urlpatterns = [
    path('', views.AtivoListView.as_view(), name='ativo-list'),
    path('novo/', views.AtivoCreateView.as_view(), name='ativo-create'),
    path('<int:pk>/editar/', views.AtivoUpdateView.as_view(), name='ativo-update'),
    path('<int:pk>/excluir/', views.AtivoDeleteView.as_view(), name='ativo-delete'),
    path('cotacoes.json', views.cotacoes_json, name='cotacoes-json'),
]

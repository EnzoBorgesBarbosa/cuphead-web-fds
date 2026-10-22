from django.urls import path
from . import views

urlpatterns = [
    # Rota opcional para servir o index.html direto pelo Django
    path('', views.tela_jogo, name='tela_jogo'),

    # Endpoints JSON consumidos via fetch() pelo nosso JavaScript
    path('configuracoes/', views.api_configuracoes, name='api_configuracoes'),
    path('progresso/', views.api_progresso, name='api_progresso'),
    path('leaderboard/', views.api_leaderboard, name='api_leaderboard'),
]
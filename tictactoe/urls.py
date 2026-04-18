from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_view, name='game'),
    path('<int:game_id>/view/', views.game_view, name='game_with_id'),
    path('create/', views.create_game_view, name='create_game'),
    path('<int:game_id>/', views.game_detail_view, name='game_detail'),
    path('<int:game_id>/move/', views.MakeMoveView.as_view(), name='make_move'),
]
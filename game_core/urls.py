from django.urls import path
from . import views

app_name = 'game_core'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
]

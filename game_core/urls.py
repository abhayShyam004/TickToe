from django.urls import path
from . import views

app_name = 'game_core'

urlpatterns = [
    path('', views.landing_view, name='landing'),
]

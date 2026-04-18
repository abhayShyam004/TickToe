from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('game_core.urls')),
    path('tictactoe/', include('tictactoe.urls')),
]
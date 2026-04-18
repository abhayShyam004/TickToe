from django.shortcuts import render

def landing_view(request):
    """
    Renders the platform landing page.
    """
    return render(request, 'game_core/landing.html')

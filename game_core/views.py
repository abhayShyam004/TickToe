from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from accounts.models import Profile
import json

def landing_view(request):
    """
    Renders the platform landing page.
    """
    return render(request, 'game_core/landing.html')

def leaderboard_view(request):
    """
    Renders the global leaderboard.
    """
    top_3x3 = Profile.objects.order_by('-rating_3x3')[:10]
    return render(request, 'game_core/leaderboard.html', {'top_3x3': top_3x3})

def profile_view(request, username):
    """
    Renders a player's visual dashboard.
    """
    target_user = get_object_or_404(User, username=username)
    history = target_user.match_history.all()[:10]
    
    # Prepare chart data
    chart_labels = []
    chart_data = []
    for h in reversed(history):
        chart_labels.append(h.timestamp.strftime("%b %d"))
        chart_data.append(h.new_rating)
        
    if not chart_data:
        # Fallback if no history
        chart_data = [target_user.profile.rating_3x3]
        chart_labels = ["Start"]

    context = {
        'target_user': target_user,
        'history': history,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'game_core/profile.html', context)

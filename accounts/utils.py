def calculate_elo(player_rating, opponent_rating, outcome, k_factor=32):
    """
    Calculates the new ELO rating for a player.
    outcome: 'win', 'loss', or 'draw'
    """
    expected_score = 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))
    if outcome == 'win':
        actual_score = 1
    elif outcome == 'loss':
        actual_score = 0
    else:
        actual_score = 0.5
    
    new_rating = player_rating + k_factor * (actual_score - expected_score)
    rating_diff = int(round(new_rating)) - player_rating
    
    return int(round(new_rating)), rating_diff

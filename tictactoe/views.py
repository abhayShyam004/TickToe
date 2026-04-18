from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import random
from .models import Game

def game_view(request, game_id=None):
    return render(request, 'tictactoe/game.html', {'game_id': game_id})

def create_game_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        game_type = data.get('game_type', 'two_player_offline')
        difficulty = data.get('difficulty', 'hard')
        
        hazards = '[]'
        if game_type == 'roguelike':
            # Create 1-2 random hazards
            num_hazards = random.randint(1, 2)
            hazards_list = random.sample(range(9), num_hazards)
            hazards = json.dumps(hazards_list)
            
        game = Game.objects.create(
            game_type=game_type, 
            difficulty=difficulty,
            hazards=hazards
        )
        return JsonResponse({
            'id': game.id,
            'board': game.board,
            'current_player': game.current_player,
            'status': game.status,
            'game_type': game.game_type,
            'difficulty': game.difficulty,
            'player_hp': game.player_hp,
            'enemy_hp': game.enemy_hp,
            'hazards': game.hazards
        })
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)

def game_detail_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    return JsonResponse({
        'id': game.id,
        'board': game.board,
        'current_player': game.current_player,
        'status': game.status,
        'game_type': game.game_type,
        'difficulty': game.difficulty,
        'player_hp': game.player_hp,
        'enemy_hp': game.enemy_hp,
        'hazards': game.hazards
    })

@method_decorator(csrf_exempt, name='dispatch')
class MakeMoveView(View):
    def post(self, request, game_id):
        try:
            data = json.loads(request.body)
            position = data.get('position')  # 0-8
            game = get_object_or_404(Game, id=game_id)
            hazards = []

            # Validate move
            if game.status != 'playing':
                return JsonResponse({'error': 'Game is not active'}, status=400)
            if position < 0 or position > 8:
                return JsonResponse({'error': 'Invalid position'}, status=400)
            if game.board[position] != '_':
                return JsonResponse({'error': 'Cell already occupied'}, status=400)
            
            # Check for hazards
            try:
                hazards = json.loads(game.hazards)
                if position in hazards:
                    return JsonResponse({'error': 'Cell is a hazard'}, status=400)
            except:
                pass # If hazards is not valid JSON, ignore it for now

            # Make the move
            board_list = list(game.board)
            board_list[position] = game.current_player
            new_board = ''.join(board_list)

            # Check for win or draw
            new_status = self.check_game_status(new_board, hazards)

            # Roguelike combat logic
            new_status, new_board, hit_occurred = self.handle_roguelike_combat(game, new_status, new_board)

            if new_status == 'playing':
                if game.game_type == 'roguelike' and hit_occurred:
                    new_player = 'X'
                else:
                    new_player = 'O' if game.current_player == 'X' else 'X'
            else:
                new_player = game.current_player  # Keep same player for display

            game.board = new_board
            game.current_player = new_player
            game.status = new_status
            game.save()

            # If AI needs to move
            if game.game_type in ['single_player_ai', 'roguelike'] and game.status == 'playing' and game.current_player == 'O':
                ai_move = self.get_ai_move(game)
                if ai_move is not None:
                    board_list = list(game.board)
                    board_list[ai_move] = 'O'  # AI is always 'O'
                    new_board = ''.join(board_list)
                    new_status = self.check_game_status(new_board, hazards)
                    
                    new_status, new_board, hit_occurred = self.handle_roguelike_combat(game, new_status, new_board)

                    if new_status == 'playing':
                        if game.game_type == 'roguelike' and hit_occurred:
                            new_player = 'X'
                        else:
                            new_player = 'X' # After AI move, it's player's turn (usually)
                    else:
                        new_player = 'O'
                    game.board = new_board
                    game.current_player = new_player
                    game.status = new_status
                    game.save()

            return JsonResponse({
                'id': game.id,
                'board': game.board,
                'current_player': game.current_player,
                'status': game.status,
                'game_type': game.game_type,
                'difficulty': game.difficulty,
                'player_hp': game.player_hp,
                'enemy_hp': game.enemy_hp,
                'hazards': game.hazards
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def handle_roguelike_combat(self, game, status, board):
        hit_occurred = False
        new_status = status
        new_board = board

        if game.game_type == 'roguelike':
            if status in ['X_wins', 'O_wins', 'draw']:
                hit_occurred = True
                if status == 'X_wins':
                    game.enemy_hp -= 5
                    if game.enemy_hp <= 0:
                        new_status = 'X_wins'
                    else:
                        new_status = 'playing'
                elif status == 'O_wins':
                    game.player_hp -= 5
                    if game.player_hp <= 0:
                        new_status = 'O_wins'
                    else:
                        new_status = 'playing'
                elif status == 'draw':
                    game.player_hp -= 1
                    game.enemy_hp -= 1
                    if game.enemy_hp <= 0 and game.player_hp <= 0:
                        new_status = 'draw'
                    elif game.enemy_hp <= 0:
                        new_status = 'X_wins'
                    elif game.player_hp <= 0:
                        new_status = 'O_wins'
                    else:
                        new_status = 'playing'
                
                if new_status == 'playing':
                    new_board = '_________'
        
        return new_status, new_board, hit_occurred

    def check_game_status(self, board, hazards=None):
        if hazards is None:
            hazards = []
        # Check rows
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] != '_':
                return f'{board[i]}_wins'
        # Check columns
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] != '_':
                return f'{board[i]}_wins'
        # Check diagonals
        if board[0] == board[4] == board[8] != '_':
            return f'{board[0]}_wins'
        if board[2] == board[4] == board[6] != '_':
            return f'{board[2]}_wins'
        # Check for draw
        # A draw occurs when there are no more playable cells and no one has won
        playable_cells = [i for i, cell in enumerate(board) if cell == '_' and i not in hazards]
        if not playable_cells:
            return 'draw'
        return 'playing'

    def get_ai_move(self, game):
        # game is a Game object
        board = game.board
        difficulty = game.difficulty
        try:
            hazards = json.loads(game.hazards)
        except:
            hazards = []

        if difficulty == 'easy':
            # Completely random
            available_moves = [i for i, cell in enumerate(board) if cell == '_' and i not in hazards]
            return random.choice(available_moves) if available_moves else None

        elif difficulty == 'medium':
            # 50% minimax, 50% random
            if random.random() < 0.5:
                # Same as easy
                available_moves = [i for i, cell in enumerate(board) if cell == '_' and i not in hazards]
                return random.choice(available_moves) if available_moves else None
            # Fall through to minimax

        # Hard (or medium fallback): full minimax
        best_score = float('-inf')
        best_move = None
        for i in range(9):
            if board[i] == '_' and i not in hazards:
                board_list = list(board)
                board_list[i] = 'O'
                score = self.minimax(''.join(board_list), 0, False, hazards)
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move

    def minimax(self, board, depth, is_maximizing, hazards):
        res = self.check_game_status(board, hazards)
        if res == 'O_wins':
            return 10 - depth
        elif res == 'X_wins':
            return depth - 10
        elif res == 'draw':
            return 0

        if is_maximizing:
            best_score = float('-inf')
            for i in range(9):
                if board[i] == '_' and i not in hazards:
                    board_list = list(board)
                    board_list[i] = 'O'
                    score = self.minimax(''.join(board_list), depth + 1, False, hazards)
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == '_' and i not in hazards:
                    board_list = list(board)
                    board_list[i] = 'X'
                    score = self.minimax(''.join(board_list), depth + 1, True, hazards)
                    best_score = min(score, best_score)
            return best_score
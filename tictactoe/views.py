from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import random
import uuid
from .models import Game

def game_view(request, game_id=None):
    return render(request, 'tictactoe/game.html', {'game_id': game_id})

def create_game_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        game_type = data.get('game_type', 'two_player_offline')
        difficulty = data.get('difficulty', 'hard')
        size = int(data.get('size', 3))
        win_condition = int(data.get('win_condition', 3))
        
        hazards = '[]'
        if game_type == 'roguelike':
            num_hazards = random.randint(1, 2)
            hazards_list = random.sample(range(size * size), num_hazards)
            hazards = json.dumps(hazards_list)
            
        game = Game.objects.create(
            game_type=game_type, 
            difficulty=difficulty,
            hazards=hazards,
            size=size,
            win_condition=win_condition,
            board='_' * (size * size)
        )
        return JsonResponse({
            'id': game.id,
            'uuid': str(game.uuid),
            'board': game.board,
            'current_player': game.current_player,
            'status': game.status,
            'game_type': game.game_type,
            'difficulty': game.difficulty,
            'size': game.size,
            'player_hp': game.player_hp,
            'enemy_hp': game.enemy_hp,
            'hazards': json.loads(game.hazards)
        })
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)

def game_detail_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    return JsonResponse({
        'id': game.id,
        'uuid': str(game.uuid),
        'board': game.board,
        'current_player': game.current_player,
        'status': game.status,
        'game_type': game.game_type,
        'difficulty': game.difficulty,
        'size': game.size,
        'player_hp': game.player_hp,
        'enemy_hp': game.enemy_hp,
        'hazards': json.loads(game.hazards)
    })

@method_decorator(csrf_exempt, name='dispatch')
class MakeMoveView(View):
    def post(self, request, game_id):
        try:
            data = json.loads(request.body)
            position = data.get('position')
            game = get_object_or_404(Game, id=game_id)
            hazards = json.loads(game.hazards)

            if game.status != 'playing':
                return JsonResponse({'error': 'Game is not active'}, status=400)
            if position < 0 or position >= (game.size * game.size):
                return JsonResponse({'error': 'Invalid position'}, status=400)
            if game.board[position] != '_':
                return JsonResponse({'error': 'Cell already occupied'}, status=400)
            if position in hazards:
                return JsonResponse({'error': 'Cell is a hazard'}, status=400)

            board_list = list(game.board)
            board_list[position] = game.current_player
            new_board = ''.join(board_list)

            new_status = self.check_game_status(new_board, hazards, game.size, game.win_condition)
            new_status, new_board, hit_occurred = self.handle_roguelike_combat(game, new_status, new_board)

            if new_status == 'playing':
                if game.game_type == 'roguelike' and hit_occurred:
                    new_player = 'X'
                else:
                    new_player = 'O' if game.current_player == 'X' else 'X'
            else:
                new_player = game.current_player

            game.board = new_board
            game.current_player = new_player
            game.status = new_status
            game.save()

            if game.game_type in ['single_player_ai', 'roguelike'] and game.status == 'playing' and game.current_player == 'O':
                ai_move = self.get_ai_move(game)
                if ai_move is not None:
                    board_list = list(game.board)
                    board_list[ai_move] = 'O'
                    new_board = ''.join(board_list)
                    new_status = self.check_game_status(new_board, hazards, game.size, game.win_condition)
                    new_status, new_board, hit_occurred = self.handle_roguelike_combat(game, new_status, new_board)

                    if new_status == 'playing':
                        new_player = 'X'
                    else:
                        new_player = 'O'
                    game.board = new_board
                    game.current_player = new_player
                    game.status = new_status
                    game.save()

            return JsonResponse({
                'id': game.id,
                'uuid': str(game.uuid),
                'board': game.board,
                'current_player': game.current_player,
                'status': game.status,
                'game_type': game.game_type,
                'difficulty': game.difficulty,
                'size': game.size,
                'player_hp': game.player_hp,
                'enemy_hp': game.enemy_hp,
                'hazards': hazards
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def handle_roguelike_combat(self, game, status, board):
        hit_occurred = False
        new_status = status
        new_board = board
        if game.game_type == 'roguelike' and status in ['X_wins', 'O_wins', 'draw']:
            hit_occurred = True
            if status == 'X_wins':
                game.enemy_hp -= 5
                new_status = 'X_wins' if game.enemy_hp <= 0 else 'playing'
            elif status == 'O_wins':
                game.player_hp -= 5
                new_status = 'O_wins' if game.player_hp <= 0 else 'playing'
            elif status == 'draw':
                game.player_hp -= 1
                game.enemy_hp -= 1
                if game.enemy_hp <= 0 and game.player_hp <= 0: new_status = 'draw'
                elif game.enemy_hp <= 0: new_status = 'X_wins'
                elif game.player_hp <= 0: new_status = 'O_wins'
                else: new_status = 'playing'
            if new_status == 'playing':
                new_board = '_' * (game.size * game.size)
        return new_status, new_board, hit_occurred

    def check_game_status(self, board, hazards, size, win_req):
        # Universal win check for any size and requirement
        for i in range(size * size):
            if board[i] == '_': continue
            symbol = board[i]
            # Check Horizontal, Vertical, Diagonal, Anti-Diagonal
            for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                count = 0
                for step in range(win_req):
                    nx, ny = (i % size) + step * dx, (i // size) + step * dy
                    if 0 <= nx < size and 0 <= ny < size and board[ny * size + nx] == symbol:
                        count += 1
                    else: break
                if count == win_req: return f'{symbol}_wins'
        if not [i for i, c in enumerate(board) if c == '_' and i not in hazards]: return 'draw'
        return 'playing'

    def get_ai_move(self, game):
        board, difficulty = game.board, game.difficulty
        hazards = json.loads(game.hazards)
        playable = [i for i, c in enumerate(board) if c == '_' and i not in hazards]
        if not playable: return None
        if difficulty == 'easy' or (difficulty == 'medium' and random.random() < 0.5):
            return random.choice(playable)
        # Minimax (Hard/Medium) - Scaled complexity for larger boards
        best_score, best_move = float('-inf'), random.choice(playable)
        for i in playable:
            board_list = list(board)
            board_list[i] = 'O'
            score = self.minimax(''.join(board_list), 0, False, hazards, game.size, game.win_condition)
            if score > best_score: best_score, best_move = score, i
        return best_move

    def minimax(self, board, depth, is_max, hazards, size, win_req):
        res = self.check_game_status(board, hazards, size, win_req)
        if res == 'O_wins': return 10 - depth
        if res == 'X_wins': return depth - 10
        if res == 'draw' or depth > 3: return 0 # Limit depth for large boards
        playable = [i for i, c in enumerate(board) if c == '_' and i not in hazards]
        scores = []
        for i in playable:
            bl = list(board)
            bl[i] = 'O' if is_max else 'X'
            scores.append(self.minimax(''.join(bl), depth + 1, not is_max, hazards, size, win_req))
        return max(scores) if is_max else min(scores)

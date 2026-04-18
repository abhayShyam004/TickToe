from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Game, Run, Encounter
import json
import uuid

class RoguelikeModelsTest(TestCase):
    def test_run_creation(self):
        run = Run.objects.create(player_hp=20, max_hp=20, stage=1)
        self.assertEqual(run.player_hp, 20)

    def test_encounter_creation(self):
        encounter = Encounter.objects.create(name="The Blocker", enemy_hp=15, ai_type="defensive")
        self.assertEqual(encounter.enemy_hp, 15)

    def test_game_expanded_fields(self):
        game = Game.objects.create(
            board='_________', 
            player_hp=20, 
            enemy_hp=15, 
            hazards='[1,1]' # JSON string representing blocked cells
        )
        self.assertEqual(game.player_hp, 20)

class GameCustomizationTest(TestCase):
    def test_game_customization_fields(self):
        user_x = User.objects.create_user(username='player_x', password='password123')
        user_o = User.objects.create_user(username='player_o', password='password123')
        game = Game.objects.create(
            board='_' * 25,
            size=5,
            win_condition=4,
            player_x=user_x,
            player_o=user_o
        )
        self.assertIsInstance(game.uuid, uuid.UUID)
        self.assertEqual(game.size, 5)
        self.assertEqual(game.win_condition, 4)
        self.assertEqual(game.player_x, user_x)
        self.assertEqual(game.player_o, user_o)
        self.assertEqual(len(game.board), 25)

class TicTacToeAiTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_x_wins(self):
        # Board: 
        # X X _
        # _ _ _
        # _ _ _
        game = Game.objects.create(board='XX_______', current_player='X', game_type='two_player_offline')
        response = self.client.post(f'/tictactoe/{game.id}/move/', 
                                    data=json.dumps({'position': 2}), 
                                    content_type='application/json')
        data = response.json()
        self.assertEqual(data['status'], 'X_wins')

    def test_ai_blocks_x(self):
        game = Game.objects.create(board='XX_______', current_player='X', game_type='single_player_ai')
        # X moves to 2, but wait, if X moves to 2, X wins.
        # Let's say X is at 0, 1. O is at 4.
        game = Game.objects.create(board='XX__O____', current_player='X', game_type='single_player_ai')
        # X moves to 3.
        response = self.client.post(f'/tictactoe/{game.id}/move/', 
                                    data=json.dumps({'position': 3}), 
                                    content_type='application/json')
        data = response.json()
        # Board after X move: XXX_O____ -> X wins.
        
        # Let's make X move somewhere else.
        game = Game.objects.create(board='X_X_O____', current_player='X', game_type='single_player_ai')
        response = self.client.post(f'/tictactoe/{game.id}/move/', 
                                    data=json.dumps({'position': 5}), 
                                    content_type='application/json')
        data = response.json()
        # X moved to 5. Board: X_X_OX___
        # AI (O) should have moved to 1 to block X.
        self.assertEqual(data['board'][1], 'O')

class CombatLogicTest(TestCase):
    def test_line_deals_damage(self):
        # Player X gets a line, Enemy takes damage, board resets
        game = Game.objects.create(
            board='XX_______', current_player='X', game_type='roguelike',
            player_hp=20, enemy_hp=15, hazards='[]'
        )
        response = self.client.post(f'/tictactoe/{game.id}/move/', 
                                    data=json.dumps({'position': 2}), 
                                    content_type='application/json')
        data = response.json()
        
        # In combat mode, getting a line doesn't end the game immediately, it deals damage
        self.assertEqual(data['enemy_hp'], 10) # 5 damage per line
        self.assertEqual(data['status'], 'playing') # Game continues until HP is 0
        self.assertEqual(data['board'], '_________') # Board clears after a hit

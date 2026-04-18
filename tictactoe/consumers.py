# tictoe/tictactoe/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Game

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_uuid = self.scope['url_route']['kwargs']['game_uuid']
        self.room_group_name = f'game_{self.game_uuid}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'move':
            position = data.get('position')
            game_state = await self.process_move(position)
            if 'error' not in game_state:
                # Broadcast the new state to everyone in the room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_update',
                        'game_state': game_state
                    }
                )
            else:
                # Send error back to the client who made the move
                await self.send(text_data=json.dumps(game_state))

    async def game_update(self, event):
        game_state = event['game_state']
        await self.send(text_data=json.dumps(game_state))

    @database_sync_to_async
    def process_move(self, position):
        try:
            game = Game.objects.get(uuid=self.game_uuid)
            
            if game.status != 'playing': return {'error': 'Game over'}
            if position < 0 or position >= (game.size * game.size): return {'error': 'Invalid position'}
            if game.board[position] != '_': return {'error': 'Cell occupied'}
            
            # Update board string
            board_list = list(game.board)
            board_list[position] = game.current_player
            game.board = ''.join(board_list)
            
            # Switch player (simplistic for Phase 2)
            game.current_player = 'O' if game.current_player == 'X' else 'X'
            game.save()
            
            return {
                'id': game.id, 'uuid': str(game.uuid), 'board': game.board,
                'current_player': game.current_player, 'status': game.status,
                'size': game.size
            }
        except Exception as e:
            return {'error': str(e)}

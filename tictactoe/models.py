from django.db import models

class Run(models.Model):
    player_hp = models.IntegerField(default=20)
    max_hp = models.IntegerField(default=20)
    stage = models.IntegerField(default=1)

class Encounter(models.Model):
    name = models.CharField(max_length=50)
    enemy_hp = models.IntegerField()
    ai_type = models.CharField(max_length=20)

class Game(models.Model):
    board = models.CharField(max_length=9, default='_________')
    current_player = models.CharField(max_length=1, default='X')
    status = models.CharField(max_length=10, default='playing')
    game_type = models.CharField(max_length=20, default='two_player_offline')
    difficulty = models.CharField(max_length=10, default='hard')
    # New Roguelike Fields
    run = models.ForeignKey(Run, on_delete=models.CASCADE, null=True, blank=True)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, null=True, blank=True)
    player_hp = models.IntegerField(default=20)
    enemy_hp = models.IntegerField(default=20)
    hazards = models.CharField(max_length=255, default='[]') # JSON string of blocked indices

    def __str__(self):
        return f'Game {self.id}: {self.status}'

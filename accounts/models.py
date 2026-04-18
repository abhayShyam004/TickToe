from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username_alias = models.CharField(max_length=30, blank=True)
    rating_3x3 = models.IntegerField(default=600)
    rating_4x4 = models.IntegerField(default=600)
    rating_5x5 = models.IntegerField(default=600)

    def __str__(self):
        return self.username_alias or self.user.username

class MatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_history')
    opponent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='opponent_history')
    board_size = models.IntegerField(default=3)
    result = models.CharField(max_length=10) # 'win', 'loss', 'draw'
    rating_change = models.IntegerField(default=0)
    new_rating = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

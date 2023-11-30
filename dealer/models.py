from django.db import models
from agent.models import Agent,Dealer
from adminapp.models import PlayTime

# Create your models here.

class DealerGameTest(models.Model):
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True, related_name='agent_dealergametests')
    created_by = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    customer = models.CharField(max_length=100,null=True)
    dealer = models.ForeignKey(Dealer,on_delete=models.CASCADE,null=True)
    time = models.ForeignKey(PlayTime,on_delete=models.CASCADE,null=True)
    date = models.DateField(auto_now_add=True)
    LSK = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    count = models.IntegerField()
    d_amount = models.FloatField()
    c_amount = models.FloatField()
    d_amount_admin = models.FloatField()
    c_amount_admin = models.FloatField()

    def __str__(self):
        return str(self.dealer)
    
class DealerGame(models.Model):
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    dealer = models.ForeignKey(Dealer,on_delete=models.CASCADE,null=True)
    customer = models.CharField(max_length=100,null=True)
    time = models.ForeignKey(PlayTime,on_delete=models.CASCADE,null=True)
    date = models.DateField(auto_now_add=True)
    LSK = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    count = models.IntegerField()
    d_amount = models.FloatField()
    c_amount = models.FloatField()
    d_amount_admin = models.FloatField()
    c_amount_admin = models.FloatField()
    combined = models.BooleanField()

    def __str__(self):
        return str(self.dealer)
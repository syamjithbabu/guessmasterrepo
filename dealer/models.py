from django.db import models
from agent.models import Agent,Dealer
from adminapp.models import PlayTime

# Create your models here.

class DealerGameTest(models.Model):
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    dealer = models.ForeignKey(Dealer,on_delete=models.CASCADE,null=True)
    time = models.ForeignKey(PlayTime,on_delete=models.CASCADE,null=True)
    date = models.DateField(auto_now_add=True)
    LSK = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    count = models.IntegerField()
    d_amount = models.FloatField()
    c_amount = models.FloatField()

    def __str__(self):
        return str(self.dealer)
    
class DealerGame(models.Model):
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    dealer = models.ForeignKey(Dealer,on_delete=models.CASCADE,null=True)
    time = models.ForeignKey(PlayTime,on_delete=models.CASCADE,null=True)
    date = models.DateField(auto_now_add=True)
    LSK = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    count = models.IntegerField()
    d_amount = models.FloatField()
    c_amount = models.FloatField()

    def __str__(self):
        return str(self.dealer)
    
class DealerBill(models.Model):
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    time_id = models.ForeignKey(PlayTime,on_delete=models.CASCADE,null=True)
    date = models.DateField()
    total_c_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_d_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_count = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f'Bill for {self.dealer} on {self.date}'
from django.contrib import admin
from dealer.models import DealerGameTest,DealerGame

# Register your models here.

@admin.register(DealerGameTest)
class DealerGameTest(admin.ModelAdmin):
    list_display = ('dealer', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

@admin.register(DealerGame)
class DealerGame(admin.ModelAdmin):
    list_display = ('dealer', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

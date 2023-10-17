from django.contrib import admin
from dealer.models import DealerGameTest,DealerGame,DealerBill

# Register your models here.

@admin.register(DealerGameTest)
class DealerGameTestAdmin(admin.ModelAdmin):
    list_display = ('dealer', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

@admin.register(DealerGame)
class DealerGameAdmin(admin.ModelAdmin):
    list_display = ('dealer', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

admin.site.register(DealerBill)

from django.contrib import admin
from . models import AgentGameTest,AgentGame,Bill,DealerCollectionReport

# Register your models here.

@admin.register(AgentGameTest)
class AgentGameTestAdmin(admin.ModelAdmin):
    list_display = ('agent', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

@admin.register(AgentGame)
class AgentGameAdmin(admin.ModelAdmin):
    list_display = ('agent', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

admin.site.register(Bill)
admin.site.register(DealerCollectionReport)

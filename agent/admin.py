from django.contrib import admin
from . models import AgentGameTest,AgentGame

# Register your models here.

@admin.register(AgentGameTest)
class AgentGameTestAdmin(admin.ModelAdmin):
    list_display = ('agent', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

@admin.register(AgentGame)
class AgentGameAdmin(admin.ModelAdmin):
    list_display = ('agent', 'time', 'date', 'LSK', 'number', 'count', 'd_amount', 'c_amount')

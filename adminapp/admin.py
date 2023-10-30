from django.contrib import admin
from adminapp.models import PlayTime, AgentPackage, Result, Winning, CollectionReport, Monitor, CombinedGame

# Register your models here.

admin.site.register(PlayTime)
admin.site.register(AgentPackage)
admin.site.register(Result)
admin.site.register(Winning)
admin.site.register(CollectionReport)
admin.site.register(Monitor)
admin.site.register(CombinedGame)
from . import views
from django.urls import path

app_name = 'adminapp'

urlpatterns = [

    
    path('index',views.index,name="index"),
    path('agent',views.agent,name="agent"),
    path('add-agent',views.add_agent,name="add_agent"),
    path('view-agent',views.view_agent,name="view_agent"),
    path('edit-agent/<int:id>',views.edit_agent,name="edit_agent"),
    path('delete-agent/<int:id>',views.delete_agent,name="delete_agent"),
    path('ban-agent/<int:id>',views.ban_agent,name="ban_agent"),
    path('remove-ban/<int:id>',views.remove_ban,name="remove_ban"),
    path('package',views.package,name="package"),
    path('new-package',views.new_package,name="new_package"),
    path('edit-package/<int:id>',views.edit_package,name="edit_package"),
    path('delete-package/<int:id>',views.delete_package,name="delete_package"),
    path('add-result',views.add_result,name="add_result"),
    path('republish-results',views.republish_results,name="republish_results"),
    path('sales-report',views.sales_report,name="sales_report"),
    path('add-time',views.add_time,name="add_time"),
    path('change-time',views.change_time,name="change_time"),
    path('change-game-time/<int:id>',views.change_game_time,name="change_game_time"),
    path('monitor',views.monitor,name="monitor"),
    path('set-monitor/<int:id>',views.set_monitor,name="set_monitor"),
    path('set-monitor-times',views.set_monitor_times,name="set_monitor_times"),
    path('dailyreport',views.daily_report,name="dailyreport"),
    path('countwise-report',views.countwise_report,name="countwise_report"),
    path('countsales-report',views.countsales_report,name="countsales_report"),
    path('winning_report',views.winning_report,name="winning_report"),
    path('winningcount-report',views.winningcount_report,name="winningcount_report"),
    path('blocked_numbers',views.blocked_numbers,name="blocked_numbers"),
    path('edit_bill',views.edit_bill,name="edit_bill"),
    path('delete-bill/<int:id>',views.delete_bill,name="delete_bill"),
    path('deleting-bill/<int:id>',views.deleting_bill,name="deleting_bill"),
    path('deleting-row/<int:id>/<int:bill_id>',views.delete_row,name="deleting_row"),
    path('payment_report',views.payment_report,name="payment_report"),
    path('change_password',views.change_password,name="change_password"),
    path('view-results',views.view_results,name="view_results"),
    path('add-collection',views.add_collection,name="add_collection"),
    path('balance-report',views.balance_report,name="balance_report"),
    path('set-limit',views.set_limit,name="set_limit"),
    path('view-limit',views.view_limits,name="view_limits"),
    path('edit-limit/<int:id>',views.edit_limit,name="edit_limit"),
    path('blocked-numbers',views.blocked_numbers,name="blocked_numbers"),
    path('new-block',views.new_block,name="new_block"),
    path('delete-block/<int:id>',views.delete_block,name="delete_block"),
    path('clear-limit/<int:id>',views.clear_limit,name="clear_limit"),
    path('clear-all',views.clear_all,name="clear_all"),
    path('settings',views.settings,name="settings"),
    path('lsk-limit/<int:id>',views.lsk_limit,name="lsk_limit")
    
]
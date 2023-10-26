from django.urls import path
from . import views


app_name = 'dealer'

urlpatterns = [

    path("index",views.index,name='index'),
    path('booking',views.booking,name="booking"), 
    path('result',views.result,name="result"), 
    path('edit-bill',views.edit_bill,name="edit_bill"),
    path('sales-report',views.sales_report,name="sales_report"),
    path('daily-report',views.daily_report,name="daily_report"), 
    path('winning-report',views.winning_report,name="winning_report"),
    path('count-salesreport',views.count_salereport,name="count_salereport"),
    path('winning_countreport',views.winning_countreport,name="winning_countreport"),
    path('balance-report',views.balance_report,name="balance_report"),
    path('play-game/<int:id>',views.play_game,name="play_game"),
    path('submit-data/',views.submit_data,name="submit_data"),
    path('save-data/<int:id>',views.save_data,name="save_data"),
    path('edit-bill',views.edit_bill,name="edit_bill"),
    path('delete-bill/<int:id>',views.delete_bill,name="delete_bill"),
    path('deleting-bill/<int:id>',views.deleting_bill,name="deleting_bill"),
    path('change-password',views.change_password,name="change_password"),
    path('deleting-row/<int:id>/<int:bill_id>',views.delete_row,name="deleting_row")

]
import json
from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404,redirect
import pytz
from website.decorators import dealer_required, agent_required
from django.contrib.auth.decorators import login_required
from adminapp.models import PlayTime
from agent.models import DealerPackage
from website.models import Dealer
from dealer.models import DealerGame,DealerGameTest,DealerBill
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as pytz_timezone
from collections import OrderedDict
from django.contrib import messages
from django.db.models import Sum

# Create your views here.
@dealer_required
@login_required
def index(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    play_times = PlayTime.objects.filter().all()
    play_time_availabilities = []
    for time in play_times:
        if time.start_time <= current_time <= time.end_time:
            play_time_availabilities.append(True)
        else:
            play_time_availabilities.append(False)
    zipped_play_times = zip(play_times, play_time_availabilities)
    context = {
        'play_times': play_times,
        'zipped_play_times': zipped_play_times,
    }
    return render(request,"dealer/index.html",context)

def booking(request):
    return render(request,'dealer/booking.html')

def result(request):
    return render(request,'dealer/results.html')

def edit_bill(request):
    return render(request,'dealer/edit_bill.html')

def sales_report(request):
    return render(request,'dealer/sales_report.html') 

def daily_report(request):
    return render(request,'dealer/daily_report.html')

def winning_report(request):
    return render(request,'dealer/winning_report.html') 
def count_salereport(request):
    return render(request,'dealer/count_salereport.html') 

def winning_countreport(request):
    return render(request,'dealer/winning_countreport.html') 

def balance_report(request):
    return render(request,'dealer/balance_report.html') 

def play_game(request,id):
    dealer_package = []
    time = PlayTime.objects.get(id=id)
    print(time.end_time)
    dealer_obj = Dealer.objects.get(user=request.user)
    agent_obj = dealer_obj.agent
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    if DealerPackage.objects.filter(dealer=dealer_obj).exists():
        dealer_package = DealerPackage.objects.get(dealer=dealer_obj)
        print(dealer_package.single_rate)
    else:
        messages.info(request,"There is no package for this user!")
    try:
        rows = DealerGameTest.objects.filter(agent=agent_obj,dealer=dealer_obj, time=id, date=current_date)
        total_c_amount = sum(row.c_amount for row in rows)
        total_d_amount = sum(row.d_amount for row in rows)
        total_count = sum(row.count for row in rows)
    except:
        pass
    context = {
        'time' : time,
        'agent_package' : dealer_package,
        'rows' : rows,
        'total_c_amount': total_c_amount,
        'total_d_amount': total_d_amount,
        'total_count': total_count,
    }
    return render(request,'dealer/play_game.html',context)

@csrf_exempt
def submit_data(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    dealer_obj = Dealer.objects.get(user=request.user)
    agent_obj = dealer_obj.agent
    if request.method == 'POST':
        data = json.loads(request.body, object_pairs_hook=OrderedDict)
        link_text = data.get('linkText')
        value1 = data.get('value1')
        value2 = data.get('value2')
        value3 = data.get('value3')
        value4 = data.get('value4')
        timeId = data.get('timeId')

        print(data)

        time = get_object_or_404(PlayTime,id=timeId)
        
        dealer_game_test = DealerGameTest(
            dealer=dealer_obj,
            agent=agent_obj,
            time=time,
            LSK=link_text,
            number=value1,
            count=value2,
            d_amount=value3,
            c_amount=value4
        )
        dealer_game_test.save()
        print(dealer_game_test.id,"id")
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'success'})

def save_data(request, id):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)

    dealer_obj = Dealer.objects.get(user=request.user)
    agent_obj = dealer_obj.agent
    play_time_instance = PlayTime.objects.get(id=id)

    try:
        dealer_game_test = DealerGameTest.objects.filter(agent=agent_obj,dealer=dealer_obj, time=id, date=current_date)

        for test_record in dealer_game_test:
            dealer_game_record = DealerGame(
                agent=test_record.agent,
                dealer=test_record.dealer,
                time=test_record.time,
                date=test_record.date,
                LSK=test_record.LSK,
                number=test_record.number,
                count=test_record.count,
                d_amount=test_record.d_amount,
                c_amount=test_record.c_amount
            )
            dealer_game_record.save()

        dealer_test_game_delete = DealerGameTest.objects.filter(dealer=dealer_obj)
        dealer_test_game_delete.delete()

        dealer_game_records = DealerGame.objects.filter(
            agent=agent_obj,
            dealer=dealer_obj,
            time_id=id,
            date=current_date
        )

        if not dealer_game_records.exists():
            return redirect('agent:index')

        total_c_amount = dealer_game_records.aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
        total_d_amount = dealer_game_records.aggregate(total_d_amount=Sum('d_amount'))['total_d_amount'] or 0
        total_count = dealer_game_records.aggregate(total_count=Sum('count'))['total_count'] or 0

        print(total_c_amount, "@@@@@@")

        try:
            # Check if an AgentBill already exists for the same date, time_id, and agent
            existing_bill = DealerBill.objects.filter(agent=agent_obj,dealer=dealer_obj, time_id=play_time_instance, date=current_date).first()

            if existing_bill:
                existing_bill.total_c_amount = total_c_amount
                existing_bill.total_d_amount = total_d_amount
                existing_bill.total_count = total_count
                existing_bill.save()
            else:
                # Create a new AgentBill record
                bill = DealerBill(
                    agent=agent_obj,
                    dealer=dealer_obj,
                    time_id=play_time_instance,
                    date=current_date,
                    total_c_amount=total_c_amount,
                    total_d_amount=total_d_amount,
                    total_count=total_count
                )
                bill.save()
                print("New Bill created successfully")
        except Exception as e:
            print(f"Error: {str(e)}")

    except:
        pass

    return redirect('dealer:index')
import json
from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404,redirect
import pytz
from website.decorators import dealer_required, agent_required
from django.contrib.auth.decorators import login_required
from adminapp.models import PlayTime
from agent.models import DealerPackage,Bill
from website.models import Dealer
from dealer.models import DealerGame,DealerGameTest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as pytz_timezone
from collections import OrderedDict
from django.contrib import messages
from django.db.models import Sum
from django.db.models import Q

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
    dealer_obj = Dealer.objects.get(user=request.user)
    print(dealer_obj.user,"dealer id")
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    try:
        matching_play_times = PlayTime.objects.get(start_time__lte=current_time, end_time__gte=current_time)
        print(matching_play_times.id)
    except:
        pass
    
    totals = Bill.objects.filter(user=dealer_obj.user,time_id=matching_play_times.id,date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))

    bills = Bill.objects.filter(user=dealer_obj.user,time_id=matching_play_times.id,date=current_date).all
    print (bills , "serch bill")
    context = {
        'bills':bills,
        'totals':totals

    }


    return render(request,'dealer/edit_bill.html',context)

def delete_bill(request,id):
    print(id)
    bill = Bill.objects.get(id=id)
    user_obj = bill.user
    print(user_obj)
    time_id = bill.time_id
    print(time_id,"time")
    date = bill.date
    print(date,"date")
    if DealerGame.objects.filter(dealer__user=user_obj.id,time=time_id,date=date):
        games = DealerGame.objects.filter(dealer__user=user_obj.id,time=time_id,date=date).all()
    else:
        print("error")
    context = {
        'bill' : bill,
        'games' : games
    }
    return render(request,'dealer/delete_bill.html',context) 


def deleting_bill(request,id):
    bill = get_object_or_404(Bill,id=id)
    print(bill,"deleting bill")
    bill.delete()
    return redirect('dealer:index')


def delete_row(request,id,bill_id):
    print(id,"this row")
    row_delete = get_object_or_404(DealerGame,id=id)
    row_delete.delete()
    return redirect('dealer:delete_bill',id=bill_id)


def sales_report(request):
    print("Daily report function")
    dealer_bills={}
    totals={}
    select_time={}
    dealer_games={}
    dealer_obj = Dealer.objects.get(user=request.user)
    print(dealer_obj)
    times = PlayTime.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    if request.method == 'POST':
        select_time = request.POST.get('select-time')
        lsk = request.POST.get('select-lsk')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        lsk_value = []
        dealer_bills = []
        totals = []
        if lsk == 'a_b_c':
            lsk_value = ['A','B','C']
        elif lsk == 'ab_bc_ac':
            lsk_value = ['AB','BC','AC']
        elif lsk == 'super':
            lsk_value = ['Super']
        elif lsk_value == 'box':
            lsk_value = ['Box']
        else:
            lsk_value == ['all']
        print(lsk_value,"##################")
        if select_time != 'all':
            if lsk != 'all':
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time,LSK__in=lsk_value)
                dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=dealer_obj.user.id,dealer_games__LSK__in=lsk_value).distinct()
                totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,LSK__in=lsk_value,time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                for bill in dealer_bills:
                    for game in bill.dealer_games.filter(LSK__in=lsk_value):
                        print("Game Count of",bill.id," is" , game.count)
                        print("Game D Amount of",bill.id," is" , game.d_amount)
                        print("Game C Amount of",bill.id," is" , game.c_amount)
                    bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                    bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                    bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
            else:
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time)
                dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=dealer_obj.user.id,time_id=select_time).distinct()
                totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
        else:
            if lsk != 'all':
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,LSK__in=lsk_value)
                dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=dealer_obj.user.id,dealer_games__LSK__in=lsk_value).distinct()
                totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                for bill in dealer_bills:
                    for game in bill.dealer_games.filter(LSK__in=lsk_value):
                        print("Game Count of",bill.id," is" , game.count)
                        print("Game D Amount of",bill.id," is" , game.d_amount)
                        print("Game C Amount of",bill.id," is" , game.c_amount)
                    bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                    bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                    bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
            else:
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj)
                dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=dealer_obj.user.id).distinct()
                totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
        context = {
            'times': times,
            'dealer_bills' : dealer_bills,
            'dealer_games' : dealer_games,
            'totals' : totals,
            'selected_time' : select_time,
            'selected_from' : from_date,
            'selected_to' : to_date,
            'selected_lsk' : lsk,
        }
    else:
        dealer_games = DealerGame.objects.filter(date=current_date,dealer=dealer_obj).all()
        dealer_bills = Bill.objects.filter(date=current_date,user=dealer_obj.user.id).all()
        totals = DealerGame.objects.filter(date=current_date,dealer=dealer_obj).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
        select_time = 'all'
        context = {
            'times': times,
            'dealer_bills' : dealer_bills,
            'dealer_games' : dealer_games,
            'totals' : totals,
            'selected_time' : select_time,
            'dealer_games' : dealer_games
        }
    return render(request,'dealer/sales_report.html',context)




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
    dealer_obj = Dealer.objects.get(user=request.user)
    play_time_instance = PlayTime.objects.get(id=id)

    try:
        # Filter AgentGameTest records for the agent and the specific time
        dealer_game_test = DealerGameTest.objects.filter(dealer=dealer_obj, time=play_time_instance, date=current_date)

        # Create AgentGame records based on AgentGameTest
        dealer_game_records = []
        for test_record in dealer_game_test:
            dealer_game_record = DealerGame(
                dealer=test_record.dealer,
                time=test_record.time,
                date=test_record.date,
                LSK=test_record.LSK,
                number=test_record.number,
                count=test_record.count,
                d_amount=test_record.d_amount,
                c_amount=test_record.c_amount
            )
            dealer_game_records.append(dealer_game_record)

        # Save the AgentGame records
        DealerGame.objects.bulk_create(dealer_game_records)

        # Delete the AgentGameTest records
        dealer_game_test.delete()

        # Check if there are AgentGame records
        if dealer_game_records:
            # Calculate total values
            total_c_amount = sum([record.c_amount for record in dealer_game_records])
            total_d_amount = sum([record.d_amount for record in dealer_game_records])
            total_count = sum([record.count for record in dealer_game_records])

            # Create the Bill record
            bill = Bill.objects.create(
                user=dealer_obj.user,
                time_id=play_time_instance,
                date=current_date,
                total_c_amount=total_c_amount,
                total_d_amount=total_d_amount,
                total_count=total_count,
            )
            # Add related AgentGame records to the Bill
            bill.dealer_games.add(*dealer_game_records)

    except Exception as e:
        print(e)
    print("###################")
    return redirect('dealer:index')
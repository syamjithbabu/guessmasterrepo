import json
from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404,redirect
import pytz
from website.decorators import dealer_required, agent_required
from django.contrib.auth.decorators import login_required
from adminapp.models import PlayTime, Result, Winning, BlockedNumber, GameLimit
from agent.models import DealerPackage,Bill,DealerCollectionReport,AgentGame,AgentGameTest,DealerLimit
from website.models import Dealer
from dealer.models import DealerGame,DealerGameTest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as pytz_timezone
from collections import OrderedDict
from django.contrib import messages
from django.db.models import Sum
from django.db.models import Q
from django.db.models import F
from django.contrib.auth.forms import PasswordChangeForm


# Create your views here.
@dealer_required
@login_required
def index(request):
    ist = pytz_timezone('Asia/Kolkata')
    dealer_obj = Dealer.objects.get(user=request.user)
    agent = dealer_obj.agent
    print(agent)
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    if PlayTime.objects.filter(dealerlimit__dealer=dealer_obj).all():
        play_times = PlayTime.objects.filter(dealerlimit__dealer=dealer_obj).all().order_by('id')
    else:
        play_times = PlayTime.objects.filter().all().order_by('id')
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

@dealer_required
@login_required
def booking(request):
    return render(request,'dealer/booking.html')

@dealer_required
@login_required
def result(request):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    times = PlayTime.objects.filter().all().order_by('id')
    results = Result.objects.filter(date=current_date).last()
    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        try:
            results = Result.objects.get(date=date,time=time)
        except:
            results = []
        context = {
            'times' : times,
            'results' : results,
            'selected_date' : date,
            'selected_time' : time,
        }
        return render(request,'dealer/results.html',context)
    context = {
        'times' : times,
        'results' : results
    }
    return render(request,'dealer/results.html',context)

@dealer_required
@login_required
def edit_bill_times(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    matching_play_times = PlayTime.objects.filter(Q(start_time__lte=current_time) & Q(end_time__gte=current_time)).order_by('id')
    context = {
        'times' : matching_play_times
    }
    return render(request,'dealer/edit_bill_times.html',context)

@dealer_required
@login_required
def edit_bill(request,id):
    dealer_obj = Dealer.objects.get(user=request.user)
    print(dealer_obj.user,"dealer id")
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    try:
        time = PlayTime.objects.get(id=id)
    except:
        matching_play_times = []
    try:
        totals = Bill.objects.filter(user=dealer_obj.user,time_id=time,date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
        bills = Bill.objects.filter(user=dealer_obj.user,time_id=time,date=current_date).all
        context = {
            'bills' : bills,
            'totals': totals,
        } 
    except:
        totals = []
        bills = []
        context = {
            'bills' : bills,
            'totals': totals,
        }
    return render(request,'dealer/edit_bill.html',context)

@dealer_required
@login_required
def delete_bill(request,id):
    print(id)
    bill = Bill.objects.get(id=id)
    user_obj = bill.user
    print(user_obj)
    time_id = bill.time_id
    print(time_id,"time")
    date = bill.date
    print(date,"date")
    games = DealerGame.objects.filter(dealer__user=user_obj.id,time=time_id,date=date).all()
    context = {
            'bill' : bill,
            'games' : games
        }
    return render(request,'dealer/delete_bill.html',context)  

@dealer_required
@login_required
def deleting_bill(request,id):
    bill = get_object_or_404(Bill,id=id)
    print(bill,"deleting bill")
    bill.delete()
    return redirect('dealer:index')

@dealer_required
@login_required
def delete_row(request,id,bill_id):
    print(id,"this row")
    bill = get_object_or_404(Bill, id=bill_id)
    row_delete = get_object_or_404(DealerGame,id=id)
    row_delete.delete()
    bill.update_totals_dealer()
    return redirect('dealer:delete_bill',id=bill_id)

@dealer_required
@login_required
def dealer_game_test_delete(request,id):
    row = get_object_or_404(DealerGameTest,id=id)
    row.delete()
    return JsonResponse({'status':'success'})

@dealer_required
@login_required
def dealer_game_test_update(request,id):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        edited_count = data.get('editedCount')
        print(edited_count)
        DealerGameTest.objects.filter(id=id).update(count=edited_count)
    return JsonResponse({'status':'success'})

@dealer_required
@login_required
def sales_report(request):
    print("Daily report function")
    dealer_bills={}
    totals={}
    select_time={}
    dealer_games={}
    dealer_obj = Dealer.objects.get(user=request.user)
    print(dealer_obj)
    times = PlayTime.objects.filter().all().order_by('id')
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
        elif lsk == 'box':
            lsk_value = ['Box']
        else:
            lsk_value == ['all']
        print(lsk_value,"##################")
        if select_time != 'all':
            if lsk != 'all':
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time,LSK__in=lsk_value).order_by('id')
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
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time).order_by('id')
                dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=dealer_obj.user.id,time_id=select_time).distinct()
                totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
        else:
            if lsk != 'all':
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,LSK__in=lsk_value).order_by('id')
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
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj).order_by('id')
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
        dealer_games = DealerGame.objects.filter(date=current_date,dealer=dealer_obj).all().order_by('id')
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

@dealer_required
@login_required
def daily_report(request):
    print("Daily report function")
    dealer_bills={}
    totals={}
    select_time={}
    dealer_games={}
    dealer_obj = Dealer.objects.get(user=request.user)
    print(dealer_obj)
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    total_winning = []
    total_balance = []
    if request.method == 'POST':
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        dealer_bills = []
        total_winning = []
        total_balance = []
        if select_time != 'all':
            dealer_games = DealerGame.objects.filter(date=current_date,dealer=dealer_obj,time=select_time).all()
            dealer_bills = Bill.objects.filter(date=current_date,user=dealer_obj.user.id,time_id=select_time).all()
            for bill in dealer_bills:
                winnings = Winning.objects.filter(date=current_date,dealer=dealer_obj,bill=bill.id,time=select_time)
                total_winning = sum(winning.total for winning in winnings)
                bill.win_amount += total_winning
                if winnings != 0:
                    bill.total_d_amount = bill.total_c_amount - total_winning
                else:
                    bill.total_d_amount = total_winning - bill.total_c_amount
                total_winning = sum(bill.win_amount for bill in dealer_bills)
                total_balance = sum(bill.total_d_amount for bill in dealer_bills)
            total_c_amount = DealerGame.objects.filter(date=current_date,dealer=dealer_obj,time=select_time).aggregate(total_c_amount=Sum('c_amount'))
            context = {
                'times': times,
                'dealer_bills' : dealer_bills,
                'dealer_games' : dealer_games,
                'total_c_amount' : total_c_amount,
                'total_winning' : total_winning,
                'total_balance' : total_balance,
                'selected_time' : select_time,
            }
            return render(request,'dealer/daily_report.html',context)
        else:
            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj)
            dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=dealer_obj.user.id).distinct()
            winning_for_bills = Winning.objects.filter(bill__in=dealer_bills)
            totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
            
            context = {
                'times': times,
                'dealer_bills' : dealer_bills,
                'dealer_games' : dealer_games,
                'winnings' : winning_for_bills,
                'totals' : totals,
                'selected_time' : 'all',
            }
            return render(request,'dealer/daily_report.html',context)
    else:
        dealer_games = DealerGame.objects.filter(date=current_date,dealer=dealer_obj).all()
        dealer_bills = Bill.objects.filter(date=current_date,user=dealer_obj.user.id).all()
        for bill in dealer_bills:
            winnings = Winning.objects.filter(date=current_date,dealer=dealer_obj,bill=bill.id)
            total_winning = sum(winning.total for winning in winnings)
            bill.win_amount += total_winning
            if winnings != 0:
                bill.total_d_amount = bill.total_c_amount - total_winning
            else:
                bill.total_d_amount = total_winning - bill.total_c_amount
            total_winning = sum(bill.win_amount for bill in dealer_bills)
            total_balance = sum(bill.total_d_amount for bill in dealer_bills)
        total_c_amount = DealerGame.objects.filter(date=current_date,dealer=dealer_obj).aggregate(total_c_amount=Sum('c_amount'))
        select_time = 'all'
        context = {
            'times': times,
            'dealer_bills' : dealer_bills,
            'dealer_games' : dealer_games,
            'total_c_amount' : total_c_amount,
            'total_winning' : total_winning,
            'total_balance' : total_balance,
            'selected_time' : select_time,
            'dealer_games' : dealer_games
        }
    return render(request,'dealer/daily_report.html',context)

@dealer_required
@login_required
def winning_report(request):
    times = PlayTime.objects.filter().all().order_by('id')
    print(times)
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    dealer_obj = Dealer.objects.get(user=request.user)
    winnings = []
    totals = []
    aggregated_winnings = []
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_time = request.POST.get('time')
        print(from_date,to_date,select_time)
        if select_time != 'all':
            winnings = Winning.objects.filter(dealer__user=dealer_obj.user.id,date__range=[from_date, to_date],time=select_time)
            print(winnings)
            aggregated_winnings = winnings.values('LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                dealer=F('dealer__dealer_name'),
                position=F('position'),
            )
            totals = Winning.objects.filter(dealer__user=dealer_obj.user.id,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
            context = {
                'times' : times,
                'winnings' : winnings,
                'totals' : totals,
                'aggr' : aggregated_winnings,
                'selected_time' : select_time,
                'selected_from' : from_date,
                'selected_to' : to_date,
            }
            return render(request,'dealer/winning_report.html',context)
        else:
            winnings = Winning.objects.filter(dealer__user=dealer_obj.user.id,date__range=[from_date, to_date])
            print(winnings)
            aggregated_winnings = winnings.values('LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                dealer=F('dealer__dealer_name'),
                position=F('position'),
            )
            totals = Winning.objects.filter(dealer__user=dealer_obj.user.id,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
            context = {
                'times' : times,
                'winnings' : winnings,
                'totals' : totals,
                'aggr' : aggregated_winnings,
                'selected_time' : 'all',
                'selected_from' : from_date,
                'selected_to' : to_date,
            }
            return render(request,'dealer/winning_report.html',context)
    else:
        try:
            matching_play_times = Winning.objects.filter().last()
            if matching_play_times:
                winnings = Winning.objects.filter(dealer__user=dealer_obj.user.id, date=current_date, time=matching_play_times.time)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    dealer=F('dealer__dealer_name'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(dealer__user=dealer_obj.user.id, date=current_date, time=matching_play_times.time).aggregate(total_count=Sum('count'), total_commission=Sum('commission'), total_rs=Sum('prize'), total_net=Sum('total'))
            else:
                winnings = []
                aggregated_winnings = []
                totals = {}
        except:
            winnings = []
            aggregated_winnings = []
            totals = {}
        context = {
            'times' : times,
            'winnings' : winnings,
            'totals' : totals,
            'aggr' : aggregated_winnings,
            'selected_time' : matching_play_times.time.id if matching_play_times else None,
        }
        return render(request,'dealer/winning_report.html',context) 

@dealer_required
@login_required
def count_salereport(request):
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    lsk_value1 = ['A','B','C']
    lsk_value2 = ['AB','BC','AC']
    dealer_obj = Dealer.objects.get(user=request.user)
    dealer_super = DealerGame.objects.filter(date=current_date,dealer=dealer_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_box = DealerGame.objects.filter(date=current_date,dealer=dealer_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_single = DealerGame.objects.filter(date=current_date,dealer=dealer_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_double = DealerGame.objects.filter(date=current_date,dealer=dealer_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    super_totals = {
        'total_count': (dealer_super['total_count'] or 0),
        'total_amount': (dealer_super['total_amount'] or 0)
        }
    box_totals = {
        'total_count':  (dealer_box['total_count'] or 0),
        'total_amount': (dealer_box['total_amount'] or 0)
        }
    single_totals = {
        'total_count': (dealer_single['total_count'] or 0),
        'total_amount': (dealer_single['total_amount'] or 0)
        }
    double_totals = {
        'total_count': (dealer_double['total_count'] or 0),
        'total_amount': (dealer_double['total_amount'] or 0)
        }
    totals = {
        'net_count': (super_totals['total_count'] or 0) + (box_totals['total_count'] or 0) + (single_totals['total_count'] or 0) + (double_totals['total_count'] or 0),
        'net_amount': (super_totals['total_amount'] or 0) + (box_totals['total_amount'] or 0) + (single_totals['total_amount'] or 0) + (double_totals['total_amount'] or 0)
    }
    if request.method == 'POST':
        select_time = request.POST.get('time')
        print(select_time)
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
             
        if select_time != 'all':
                    agent_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    super_totals = {
                        'total_count': (agent_super['total_count'] or 0),
                        'total_amount': (agent_super['total_amount'] or 0)
                        }
                    box_totals = {
                        'total_count': (agent_box['total_count'] or 0),
                        'total_amount': (agent_box['total_amount'] or 0)
                        }
                    single_totals = {
                        'total_count': (agent_single['total_count'] or 0),
                        'total_amount': (agent_single['total_amount'] or 0)
                        }
                    double_totals = {
                        'total_count': (agent_double['total_count'] or 0),
                        'total_amount': (agent_double['total_amount'] or 0)
                        }
                    totals = {
                        'net_count': (super_totals['total_count'] or 0) + (box_totals['total_count'] or 0) + (single_totals['total_count'] or 0) + (double_totals['total_count'] or 0),
                        'net_amount': (super_totals['total_amount'] or 0) + (box_totals['total_amount'] or 0) + (single_totals['total_amount'] or 0) + (double_totals['total_amount'] or 0)
                    }
                    context = {
                        'times' : times,
                        'dealers' : dealer_obj,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : select_time,
                        'totals' : totals
                    }
                    return render(request,'dealer/count_salereport.html',context)
        else:
                    agent_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer=dealer_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    super_totals = {
                        'total_count': (agent_super['total_count'] or 0),
                        'total_amount': (agent_super['total_amount'] or 0)
                        }
                    box_totals = {
                        'total_count': (agent_box['total_count'] or 0),
                        'total_amount': (agent_box['total_amount'] or 0)
                        }
                    single_totals = {
                        'total_count': (agent_single['total_count'] or 0),
                        'total_amount': (agent_single['total_amount'] or 0)
                        }
                    double_totals = {
                        'total_count': (agent_double['total_count'] or 0),
                        'total_amount': (agent_double['total_amount'] or 0)
                        }
                    totals = {
                        'net_count': (super_totals['total_count'] or 0) + (box_totals['total_count'] or 0) + (single_totals['total_count'] or 0) + (double_totals['total_count'] or 0),
                        'net_amount': (super_totals['total_amount'] or 0) + (box_totals['total_amount'] or 0) + (single_totals['total_amount'] or 0) + (double_totals['total_amount'] or 0)
                    }
                    context = {
                        'times' : times,
                        'dealers' : dealer_obj,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : 'all',
                        'totals' : totals
                    }
     
                    return render(request,'dealer/count_salereport.html',context)
    context = {
                        'times' : times,
                        'dealers' : dealer_obj,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : 'all',
                        'totals' : totals
                    }
     
    return render(request,'dealer/count_salereport.html',context) 
 
@dealer_required
@login_required
def winning_countreport(request):
    dealer_obj = Dealer.objects.get(user=request.user)
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    winnings = Winning.objects.filter(date=current_date).all()
    totals = Winning.objects.filter(date=current_date).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
    if request.method == 'POST':
        select_time = request.POST.get('time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_time != 'all':
            winnings = Winning.objects.filter(dealer=dealer_obj,date__range=[from_date, to_date],time=select_time)
            totals = Winning.objects.filter(dealer=dealer_obj,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
            context = {
                'times' : times,
                'winnings' : winnings,
                'totals' : totals,
                'selected_time' : select_time,
                'selected_from' : from_date,
                'selected_to' : to_date
            }
            return render(request,'dealer/winning_countreport.html',context)
        else:
            winnings = Winning.objects.filter(dealer=dealer_obj,date__range=[from_date, to_date])
            totals = Winning.objects.filter(dealer=dealer_obj,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
            context = {
                'times' : times,
                'winnings' : winnings,
                'totals' : totals,
                'selected_time' : select_time,
                'selected_from' : from_date,
                'selected_to' : to_date
            }
            return render(request,'dealer/winning_countreport.html',context)
    context = {
        'times' : times,
        'winnings' : winnings,
        'totals' : totals,
        'selected_agent' : 'all',
        'selected_time' : 'all'
    }
    return render(request,'dealer/winning_countreport.html',context) 

@dealer_required
@login_required
def balance_report(request):
    dealer_obj = Dealer.objects.get(user=request.user)
    collection = DealerCollectionReport.objects.filter().all()
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    report_data = []
    total_balance = []
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], dealer=dealer_obj)
        print(dealer_games)
        collection = DealerCollectionReport.objects.filter(date__range=[from_date, to_date], dealer=dealer_obj)
        print(collection)
        winning = Winning.objects.filter(dealer=dealer_obj,date=current_date).aggregate(total_winning=Sum('total'))['total_winning'] or 0
        dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
        from_agent = collection.filter(from_or_to='from-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        to_agent = collection.filter(from_or_to='to-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        total_collection_amount = from_agent - to_agent
        win_amount = float(winning)
        total_d_amount = dealer_total_d_amount
        balance = float(winning) - float(total_d_amount) + float(total_collection_amount)
        if total_d_amount:
            report_data.append({
                'date' : current_date,
                'total_d_amount': total_d_amount,
                'from_or_to' : total_collection_amount,
                'balance' : balance,
                'win_amount' : win_amount
            })
        total_balance = sum(entry['balance'] for entry in report_data)
        context = {
            'selected_agent' : 'all',
            'report_data': report_data,
            'total_balance' : total_balance,
            'selected_from' : from_date,
            'selected_to' : to_date
        }
    else:
        pass
    dealer_games = DealerGame.objects.filter(date=current_date, dealer=dealer_obj)
    print(dealer_games)
    collection = DealerCollectionReport.objects.filter(date=current_date, dealer=dealer_obj)
    print(collection)
    winning = Winning.objects.filter(dealer=dealer_obj,date=current_date).aggregate(total_winning=Sum('total'))['total_winning'] or 0
    dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
    from_agent = collection.filter(from_or_to='from-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    to_agent = collection.filter(from_or_to='to-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    total_collection_amount = from_agent - to_agent
    total_d_amount = dealer_total_d_amount
    win_amount = float(winning)
    balance = float(winning) - float(total_d_amount) + float(total_collection_amount)
    if total_d_amount:
        report_data.append({
            'date' : current_date,
            'total_d_amount': total_d_amount,
            'from_or_to' : total_collection_amount,
            'balance' : balance,
            'win_amount' : win_amount
        })
    total_balance = sum(entry['balance'] for entry in report_data)
    context = {
        'selected_agent' : 'all',
        'report_data': report_data,
        'total_balance' : total_balance
    }
    return render(request, 'dealer/balance_report.html',context)

@dealer_required
@login_required
def play_game(request,id):
    dealer_package = []
    time = PlayTime.objects.get(id=id)
    print(time.end_time)
    dealer_obj = Dealer.objects.get(user=request.user)
    agent_obj = dealer_obj.agent
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_date)
    if current_time > time.end_time:
        return redirect('dealer:index')
    if DealerPackage.objects.filter(dealer=dealer_obj).exists():
        dealer_package = DealerPackage.objects.get(dealer=dealer_obj)
        print(dealer_package.single_rate)
    else:
        messages.info(request,"There is no package for this user!")
    try:
        rows = DealerGameTest.objects.filter(agent=agent_obj,dealer=dealer_obj, time=id, date=current_date).order_by('-id')
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

@dealer_required
@login_required
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

        try:
            limit = DealerLimit.objects.get(dealer=dealer_obj)
            print(limit.daily_limit,"daily limit")
        except:
            pass

        try:
            blocked_numbers = BlockedNumber.objects.filter(Q(from_date__lte=current_date) & Q(to_date__gte=current_date),LSK=link_text,time=time, number=value1)
            if blocked_numbers:
                print("it is blocked")
                agent_game_count = AgentGame.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count')) or {'total_count': 0}
                dealer_game_count = DealerGame.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count')) or {'total_count': 0}
                agent_game_test_count = AgentGameTest.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count')) or {'total_count': 0}
                dealer_game_test_count = DealerGameTest.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count')) or {'total_count': 0}
                print("hello")
                print(agent_game_count)
                print(dealer_game_count)
                blocked_number_count = (agent_game_count['total_count'] or 0) + (dealer_game_count['total_count'] or 0) + (agent_game_test_count['total_count'] or 0) + (dealer_game_test_count['total_count'] or 0) + int(value2)
                print(blocked_number_count)
                for block in blocked_numbers:
                    if blocked_number_count > block.count:
                        blocked = True
                        print(blocked,"change")
                        messages.info(request,'This LSK and number is blocked!',extra_tags='blocked_message')
                        return render(request,'dealer/index.html')
                    else:
                        pass
        except:
            pass

        try:
            game_limit = GameLimit.objects.get(time=time)
            print("tried this")
            limits = {
                'Super': game_limit.super,
                'Box': game_limit.box,
                'AB' : game_limit.ab,
                'BC' : game_limit.bc,
                'AC' : game_limit.ac,
                'A' : game_limit.a,
                'B' : game_limit.b,
                'C' : game_limit.c,
            }
            print(limits)
            agent_games_super = AgentGame.objects.filter(date=current_date,time=time,LSK='Super').aggregate(total_super=Sum('count')) or {'total_super': 0}
            agent_games_test_super = AgentGameTest.objects.filter(date=current_date,time=time,LSK='Super').aggregate(total_super=Sum('count')) or {'total_super': 0}
            dealer_games_super = DealerGame.objects.filter(date=current_date,time=time,LSK='Super').aggregate(total_super=Sum('count')) or {'total_super': 0}
            dealer_games_test_super = DealerGameTest.objects.filter(date=current_date,time=time,LSK='Super').aggregate(total_super=Sum('count')) or {'total_super': 0}
            agent_games_box = AgentGame.objects.filter(date=current_date,time=time,LSK='Box').aggregate(total_box=Sum('count')) or {'total_box': 0}
            agent_games_test_box = AgentGameTest.objects.filter(date=current_date,time=time,LSK='Box').aggregate(total_box=Sum('count')) or {'total_box': 0}
            dealer_games_box = DealerGame.objects.filter(date=current_date,time=time,LSK='Box').aggregate(total_box=Sum('count')) or {'total_box': 0}
            dealer_games_test_box = DealerGameTest.objects.filter(date=current_date,time=time,LSK='Box').aggregate(total_box=Sum('count')) or {'total_box': 0}
            agent_games_ab = AgentGame.objects.filter(date=current_date,time=time,LSK='AB').aggregate(total_ab=Sum('count')) or {'total_ab': 0}
            agent_games_test_ab = AgentGameTest.objects.filter(date=current_date,time=time,LSK='AB').aggregate(total_ab=Sum('count')) or {'total_ab': 0}
            dealer_games_ab = DealerGame.objects.filter(date=current_date,time=time,LSK='AB').aggregate(total_ab=Sum('count')) or {'total_ab': 0}
            dealer_games_test_ab = DealerGameTest.objects.filter(date=current_date,time=time,LSK='AB').aggregate(total_ab=Sum('count')) or {'total_ab': 0}
            agent_games_bc = AgentGame.objects.filter(date=current_date,time=time,LSK='BC').aggregate(total_bc=Sum('count')) or {'total_bc': 0}
            agent_games_test_bc = AgentGameTest.objects.filter(date=current_date,time=time,LSK='BC').aggregate(total_bc=Sum('count')) or {'total_bc': 0}
            dealer_games_bc = DealerGame.objects.filter(date=current_date,time=time,LSK='BC').aggregate(total_bc=Sum('count')) or {'total_bc': 0}
            dealer_games_test_bc = DealerGameTest.objects.filter(date=current_date,time=time,LSK='BC').aggregate(total_bc=Sum('count')) or {'total_bc': 0}
            agent_games_ac = AgentGame.objects.filter(date=current_date,time=time,LSK='AC').aggregate(total_ac=Sum('count')) or {'total_ac': 0}
            agent_games_test_ac = AgentGameTest.objects.filter(date=current_date,time=time,LSK='AC').aggregate(total_ac=Sum('count')) or {'total_ac': 0}
            dealer_games_ac = DealerGame.objects.filter(date=current_date,time=time,LSK='AC').aggregate(total_ac=Sum('count')) or {'total_ac': 0}
            dealer_games_test_ac = DealerGameTest.objects.filter(date=current_date,time=time,LSK='AC').aggregate(total_ac=Sum('count')) or {'total_ac': 0}
            agent_games_a = AgentGame.objects.filter(date=current_date,time=time,LSK='A').aggregate(total_a=Sum('count')) or {'total_a': 0}
            agent_games_test_a = AgentGameTest.objects.filter(date=current_date,time=time,LSK='A').aggregate(total_a=Sum('count')) or {'total_a': 0}
            dealer_games_a = DealerGame.objects.filter(date=current_date,time=time,LSK='A').aggregate(total_a=Sum('count')) or {'total_a': 0}
            dealer_games_test_a = DealerGameTest.objects.filter(date=current_date,time=time,LSK='A').aggregate(total_a=Sum('count')) or {'total_a': 0}
            agent_games_b = AgentGame.objects.filter(date=current_date,time=time,LSK='B').aggregate(total_b=Sum('count')) or {'total_b': 0}
            agent_games_test_b = AgentGameTest.objects.filter(date=current_date,time=time,LSK='B').aggregate(total_b=Sum('count')) or {'total_b': 0}
            dealer_games_b = DealerGame.objects.filter(date=current_date,time=time,LSK='B').aggregate(total_b=Sum('count')) or {'total_b': 0}
            dealer_games_test_b = DealerGameTest.objects.filter(date=current_date,time=time,LSK='B').aggregate(total_b=Sum('count')) or {'total_b': 0}
            agent_games_c = AgentGame.objects.filter(date=current_date,time=time,LSK='C').aggregate(total_c=Sum('count')) or {'total_c': 0}
            agent_games_test_c = AgentGameTest.objects.filter(date=current_date,time=time,LSK='C').aggregate(total_c=Sum('count')) or {'total_c': 0}
            dealer_games_c = DealerGame.objects.filter(date=current_date,time=time,LSK='C').aggregate(total_c=Sum('count')) or {'total_c': 0}
            dealer_games_test_c = DealerGame.objects.filter(date=current_date,time=time,LSK='C').aggregate(total_c=Sum('count')) or {'total_c': 0}

            print("test",agent_games_super)
            print("test",dealer_games_super)

            games_super = (agent_games_super['total_super'] or 0) + (dealer_games_super['total_super'] or 0) + (agent_games_test_super['total_super'] or 0) + (dealer_games_test_super['total_super'] or 0)
            games_box = (agent_games_box['total_box'] or 0) + (dealer_games_box['total_box'] or 0) + (agent_games_test_box['total_box'] or 0) + (dealer_games_test_box['total_box'] or 0)
            games_ab = (agent_games_ab['total_ab'] or 0) + (dealer_games_ab['total_ab'] or 0) + (agent_games_test_ab['total_ab'] or 0) + (dealer_games_test_ab['total_ab'] or 0)
            games_bc = (agent_games_bc['total_bc'] or 0) + (dealer_games_bc['total_bc'] or 0) + (agent_games_test_bc['total_bc'] or 0) + (dealer_games_test_bc['total_bc'] or 0)
            games_ac = (agent_games_ac['total_ac'] or 0) + (dealer_games_ac['total_ac'] or 0) + (agent_games_test_ac['total_ac'] or 0) + (dealer_games_test_ac['total_ac'] or 0)
            games_a = (agent_games_a['total_a'] or 0) + (dealer_games_a['total_a'] or 0) + (agent_games_test_a['total_a'] or 0) + (dealer_games_test_a['total_a'] or 0)
            games_b = (agent_games_b['total_b'] or 0) + (dealer_games_b['total_b'] or 0) + (agent_games_test_b['total_b'] or 0) + (dealer_games_test_b['total_b'] or 0)
            games_c = (agent_games_c['total_c'] or 0) + (dealer_games_c['total_c'] or 0) + (agent_games_test_c['total_c'] or 0) + (dealer_games_test_c['total_c'] or 0)

            print("box",games_super)

            print(int(games_super)+int(value2))

            if link_text == 'Super':
                total_super = int(games_super) + int(value2)
                total = int(total_super) + int(value2)
                if total > game_limit.super:
                    print("Limit exceeded")
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'Box':
                total_box = int(games_box)+int(value2)
                total = int(total_box) + int(value2)
                if total > game_limit.box:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'AB':
                total_ab = int(games_ab)+int(value2)
                total = int(total_ab) + int(value2)
                if total > game_limit.ab:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'BC':
                total_bc = int(games_bc)+int(value2)
                total = int(total_bc) + int(value2)
                if total > game_limit.bc:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'AC':
                total_ac = int(games_ac)+int(value2)
                total = int(total_ac) + int(value2)
                if total > game_limit.ac:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'A':
                total_a = int(games_a)+int(value2)
                total = int(total_a) + int(value2)
                if total > game_limit.a:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'B':
                total_b = int(games_b)+int(value2)
                total = int(total_b) + int(value2)
                if total > game_limit.b:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
            elif link_text == 'C':
                total_c = int(games_c)+int(value2)
                total = int(total_c) + int(value2)
                if total > game_limit.c:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return render(request,'dealer/index.html')
        except:
            pass
        
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
        total_c_amount = DealerGameTest.objects.filter(dealer=dealer_obj).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
        print(total_c_amount,"@@@@@")
        try:
            dealer_total_c_amount = DealerGame.objects.filter(dealer=dealer_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
            print(dealer_total_c_amount,"$$$$$$")
            print(dealer_game_test.id,"id")
            if total_c_amount + dealer_total_c_amount > limit.daily_limit:
                print("Your daily limit is exceeded")
                dealer_game_test.delete()
                messages.info(request,'Your daily limit is exceeded!',extra_tags='limit_message')
                return render(request,'agent/index.html')
            else:
                print("You have limit balance")
        except:
            pass
        return redirect('dealer:play_game',id=timeId)
    return JsonResponse({'status': 'success'})

@dealer_required
@login_required
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
                agent=dealer_obj.agent,
                dealer=test_record.dealer,
                time=test_record.time,
                date=test_record.date,
                LSK=test_record.LSK,
                number=test_record.number,
                count=test_record.count,
                d_amount=test_record.d_amount,
                c_amount=test_record.c_amount,
                combined=False
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
    return redirect('dealer:play_game',id=id)

@dealer_required
@login_required
def change_password(request):
    if request.method== "POST":
         form= PasswordChangeForm(user=request.user,data=request.POST)
         if form.is_valid():
             form.save()
             messages.success(request,"your password changed")
             return redirect("website:login")
    else:
        form= PasswordChangeForm(user=request.user)
    return render(request,'dealer/change_password.html',{'form':form})
 
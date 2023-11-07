from audioop import reverse
import json
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
import pytz
from website.forms import LoginForm
from website.forms import DealerRegistration,UserUpdateForm
from website.models import User,Dealer,Agent
from adminapp.models import PlayTime, AgentPackage,Result,Winning,Limit,BlockedNumber,GameLimit
from .models import DealerPackage, AgentGameTest, AgentGame, Bill, DealerCollectionReport, DealerLimit
from dealer.models import DealerGame
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from website.decorators import dealer_required, agent_required
from django.utils import timezone
from pytz import timezone as pytz_timezone
from collections import OrderedDict
from django.db.models import Sum
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import F

# Create your views here.
@login_required
@agent_required
def index(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    agent_obj = Agent.objects.get(user=request.user)
    if PlayTime.objects.filter(limit__agent=agent_obj).all():
        play_times = PlayTime.objects.filter(limit__agent=agent_obj).all()
    else:
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
    return render(request,"agent/index.html",context)

@csrf_exempt
def add_dealer(request):
    login_form = LoginForm()
    dealer_form = DealerRegistration()
    agent_obj = Agent.objects.get(user=request.user)
    if request.method == "POST":
        dealer_form = DealerRegistration(request.POST)
        login_form = LoginForm(request.POST)
        print(dealer_form)
        print(login_form)
        if login_form.is_valid() and dealer_form.is_valid():
            print("loginform is working")
            user = login_form.save(commit=False)
            user.is_dealer = True
            user.save()
            dealer = dealer_form.save(commit=False)
            dealer.user = user
            dealer.agent = agent_obj  # Associate the agent_obj with the dealer
            dealer.save()
            messages.info(request, "Dealer Created Successfully")
            return redirect("agent:new_package")
    return render(request,'agent/add_dealer.html',{"login_form": login_form, "dealer_form": dealer_form})

def view_dealer(request):
    agent = Agent.objects.get(user=request.user)
    print(agent)
    dealers = Dealer.objects.filter(agent=agent).all()
    context = {
        'dealers' : dealers
    }
    return render(request,'agent/view_dealer.html',context)

def edit_dealer(request,id):
    dealer = get_object_or_404(Dealer, id=id)
    user = dealer.user
    if request.method == "POST":
        dealer_form = DealerRegistration(request.POST, instance=dealer)
        login_form = UserUpdateForm(request.POST, instance=user)
        if dealer_form.is_valid() and login_form.is_valid():
            login_form.save()
            messages.info(request, "Dealer Updated Successfully")
            return redirect("agent:view_dealer")
    else:
        dealer_form = DealerRegistration(instance=dealer)
        login_form = UserUpdateForm(instance=user)
    return render(request, 'agent/edit_dealer.html', {'dealer': dealer,'dealer_form': dealer_form,'login_form':login_form})


def delete_dealer(request,id):
    dealer = get_object_or_404(Dealer, id=id)
    dealer_user = dealer.user
    dealer_user.delete()
    return redirect('agent:view_dealer')

def ban_dealer(request,id):
    dealer = get_object_or_404(Dealer, id=id)
    user = dealer.user
    user.is_active = False
    user.save()
    return redirect('agent:view_dealer')

def remove_ban(request,id):
    dealer = get_object_or_404(Dealer,id=id)
    user = dealer.user
    user.is_active = True
    user.save()
    return redirect('agent:view_dealer')

def booking(request):
    return render(request,'agent/booking.html')

def results(request):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    times = PlayTime.objects.filter().all()
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
        return render(request,'agent/results.html',context)
    context = {
        'times' : times,
        'results' : results
    }
    return render(request,'agent/results.html',context)

def sales_report(request):
    print("Sales report function")
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    times = PlayTime.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        print(select_dealer,"selected_dealer")
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        lsk = request.POST.get('select-lsk')
        print(from_date,"fromdate")
        print(to_date,"todate")
        lsk_value = []
        agent_bills = []
        dealer_bills = []
        agent_games = []
        dealer_games = []
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
        if select_dealer != 'all':
            #a dealer selected
            if select_dealer == str(agent_obj.user):
                #agent is selected
                if select_time != 'all':
                    #time and agent is selected
                    if lsk != 'all':
                        #time, agent and lsk is selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK__in=lsk_value)
                        print(agent_games)
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).distinct()
                        print(agent_bills)
                        totals = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,agent=agent_obj,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        for bill in agent_bills:
                            for game in bill.agent_games.filter(LSK__in=lsk_value):
                                print("Game Count of",bill.id," is" , game.count)
                                print("Game D Amount of",bill.id," is" , game.d_amount)
                                print("Game C Amount of",bill.id," is" , game.c_amount)
                            bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                            bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                            bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    else:
                        #lsk not selected, agent and time selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time).all()
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time).all()
                        totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time_id=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                else:
                    #time not selected, agent selected
                    if lsk != 'all':
                        #lsk selected, time not selected, agent selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value)
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).distinct()
                        totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        for bill in agent_bills:
                            for game in bill.agent_games.filter(LSK__in=lsk_value):
                                print("Game Count of",bill.id," is" , game.count)
                                print("Game D Amount of",bill.id," is" , game.d_amount)
                                print("Game C Amount of",bill.id," is" , game.c_amount)
                            bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                            bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                            bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    else:
                        #time,lsk not selected, agent selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all()
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).distinct()
                        totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
            else:
                #dealer is selcted
                if select_time != 'all':
                    #dealer and time selected
                    if lsk != 'all':
                        #dealer,lsk and time selected
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,time=select_time,LSK__in=lsk_value)
                        dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,time_id=select_time,dealer_games__in=dealer_games).distinct()
                        totals = DealerGame.objects.filter(date__range=[from_date, to_date],time_id=select_time,dealer__user=select_dealer,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        for bill in dealer_bills:
                            for game in bill.dealer_games.filter(LSK__in=lsk_value):
                                print("Game Count of",bill.id," is" , game.count)
                                print("Game D Amount of",bill.id," is" , game.d_amount)
                                print("Game C Amount of",bill.id," is" , game.c_amount)
                            bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                            bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                            bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    else:
                        #dealer, time selcted and lsk not selected
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,time=select_time).all()
                        dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,time_id=select_time,dealer_games__in=dealer_games).distinct()
                        totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,time_id=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                else:
                    #dealer selected, time not selected
                    if lsk != 'all':
                        #dealer and lsk selected, time not selected
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,LSK__in=lsk_value)
                        dealer_bills = Bill.objecountsales_reportcts.filter(date__range=[from_date, to_date],user=select_dealer,dealer_games__in=dealer_games).distinct()
                        totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        for bill in dealer_bills:
                            for game in bill.dealer_games.filter(LSK__in=lsk_value):
                                print("Game Count of",bill.id," is" , game.count)
                                print("Game D Amount of",bill.id," is" , game.d_amount)
                                print("Game C Amount of",bill.id," is" , game.c_amount)
                            bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                            bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                            bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    else:
                        #dealer selected, time and lsk not selected
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer).all()
                        dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,dealer_games__in=dealer_games).distinct()
                        totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
        if select_dealer == 'all':
            #selected all
            if select_time != 'all':
                #all users, time is selected
                if lsk != 'all':
                    #all users, time is selected, lsk is selected
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK__in=lsk_value)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time,LSK__in=lsk_value)
                    agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).distinct()
                    dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time,dealer_games__in=dealer_games).distinct()
                    totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                        'total_c_amount': (totals_agent['total_c_amount'] or 0) + (totals_dealer['total_c_amount'] or 0),
                        'total_d_amount': (totals_agent['total_d_amount'] or 0) + (totals_dealer['total_d_amount'] or 0)
                    }
                    for bill in dealer_bills:
                        for game in bill.dealer_games.filter(LSK__in=lsk_value):
                            print("Game Count of",bill.id," is" , game.count)
                            print("Game D Amount of",bill.id," is" , game.d_amount)
                            print("Game C Amount of",bill.id," is" , game.c_amount)
                        bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                        bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                        bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    for bill in agent_bills:
                            for game in bill.agent_games.filter(LSK__in=lsk_value):
                                print("Game Count of",bill.id," is" , game.count)
                                print("Game D Amount of",bill.id," is" , game.d_amount)
                                print("Game C Amount of",bill.id," is" , game.c_amount)
                            bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                            bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                            bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                else:
                    #all users, time is selected, lsk is not selected
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time)
                    agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).distinct()
                    dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time,dealer_games__in=dealer_games).distinct()
                    totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                        'total_c_amount': (totals_agent['total_c_amount'] or 0) + (totals_dealer['total_c_amount'] or 0),
                        'total_d_amount': (totals_agent['total_d_amount'] or 0) + (totals_dealer['total_d_amount'] or 0)
                    }
            else:
                #all users, time not selected
                if lsk != 'all':
                    #all users, time not selected, lsk is selected
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK__in=lsk_value)
                    agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__LSK__in=lsk_value).distinct()
                    dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],dealer_games__LSK__in=lsk_value).distinct()
                    if not agent_bills:
                        if dealer_bills:
                            totals = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            for bill in dealer_bills:
                                for game in bill.dealer_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    else:
                        if dealer_bills:
                            for bill in agent_bills:
                                for game in bill.agent_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            for bill in dealer_bills:
                                for game in bill.dealer_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            totals = {
                                'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                                'total_c_amount': (totals_agent['total_c_amount'] or 0) + (totals_dealer['total_c_amount'] or 0),
                                'total_d_amount': (totals_agent['total_d_amount'] or 0) + (totals_dealer['total_d_amount'] or 0)
                            }
                        else:
                            totals = AgentGame.objects.filter(agent=agent_obj,date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            for bill in agent_bills:
                                for game in bill.agent_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                else:
                    #all users, time not selected, lsk not selected
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all()
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj).all()
                    agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id).distinct()
                    dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date]).distinct()
                    totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                        'total_c_amount': (totals_agent['total_c_amount'] or 0) + (totals_dealer['total_c_amount'] or 0),
                        'total_d_amount': (totals_agent['total_d_amount'] or 0) + (totals_dealer['total_d_amount'] or 0)
                        }
        context = {
            'dealers': dealers,
            'times': times,
            'agent_bills' : agent_bills,
            'dealer_bills' : dealer_bills,
            'totals' : totals,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
            'selected_from' : from_date,
            'selected_to' : to_date,
            'selected_lsk' : lsk,
            'agent_games' : agent_games,
            'dealer_games' : dealer_games,
        }
        return render(request, 'agent/sales_report.html', context)
    else:
        print("this is working")
        agent_games = AgentGame.objects.filter(date=current_date,agent=agent_obj).all()
        dealer_games = DealerGame.objects.filter(date=current_date,dealer__agent=agent_obj).all()
        agent_bills = Bill.objects.filter(date=current_date,user=agent_obj.user.id).all()
        print(agent_bills)
        dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date=current_date)
        totals = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
        select_dealer = 'all'
        select_time = 'all'
        context = {
            'dealers' : dealers,
            'times' : times,
            'agent_bills' : agent_bills,
            'dealer_bills' : dealer_bills,
            'totals' : totals,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
            'agent_games' : agent_games,
            'dealer_games' : dealer_games
        }
    return render(request,'agent/sales_report.html',context)

def daily_report(request):
    print("Daily report function")
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    print(dealers)
    times = PlayTime.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    print("this is working")
    total_winning = []
    total_balance = []
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        print(select_dealer, select_time, from_date, to_date)
        if select_dealer != 'all':
            if select_time != 'all':
                if select_dealer == str(agent_obj.user):
                    print("its agent")
                    bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time).all()
                    print(bills)
                    for bill in bills:
                        winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                        print(winnings)
                        total_winning = sum(winning.total for winning in winnings)
                        bill.win_amount += total_winning
                        if winnings != 0:
                            bill.total_d_amount = bill.total_c_amount - total_winning
                        else:
                            bill.total_d_amount = total_winning - bill.total_c_amount
                        total_winning = sum(bill.win_amount for bill in bills)
                        total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                    }
                    return render(request,'agent/daily_report.html',context)
                else:
                    print("its agent")
                    bills = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date],time_id=select_time).all()
                    print(bills)
                    for bill in bills:
                        winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                        print(winnings)
                        total_winning = sum(winning.total for winning in winnings)
                        bill.win_amount += total_winning
                        if winnings != 0:
                            bill.total_d_amount = bill.total_c_amount - total_winning
                        else:
                            bill.total_d_amount = total_winning - bill.total_c_amount
                        total_winning = sum(bill.win_amount for bill in bills)
                        total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                    }
                    return render(request,'agent/daily_report.html',context)
            else:
                if select_dealer == str(agent_obj.user):
                    print("its agent")
                    bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date]).all()
                    print(bills)
                    for bill in bills:
                        winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                        print(winnings)
                        total_winning = sum(winning.total for winning in winnings)
                        bill.win_amount += total_winning
                        if winnings != 0:
                            bill.total_d_amount = bill.total_c_amount - total_winning
                        else:
                            bill.total_d_amount = total_winning - bill.total_c_amount
                        total_winning = sum(bill.win_amount for bill in bills)
                        total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                    }
                    return render(request,'agent/daily_report.html',context)
                else:
                    print("its agent")
                    bills = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date]).all()
                    print(bills)
                    for bill in bills:
                        winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=bill.id,date__range=[from_date, to_date])
                        print(winnings)
                        total_winning = sum(winning.total for winning in winnings)
                        bill.win_amount += total_winning
                        if winnings != 0:
                            bill.total_d_amount = bill.total_c_amount - total_winning
                        else:
                            bill.total_d_amount = total_winning - bill.total_c_amount
                        total_winning = sum(bill.win_amount for bill in bills)
                        total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                    }
                    return render(request,'agent/daily_report.html',context)
        else:
            if select_time != 'all':
                print("its agent")
                bills = Bill.objects.filter(date__range=[from_date, to_date],time_id=select_time).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(bill=bill.id,date__range=[from_date, to_date],time=select_time)
                    print(winnings)
                    total_winning = sum(winning.total for winning in winnings)
                    bill.win_amount += total_winning
                    if winnings != 0:
                        bill.total_d_amount = bill.total_c_amount - total_winning
                    else:
                        bill.total_d_amount = total_winning - bill.total_c_amount
                    total_winning = sum(bill.win_amount for bill in bills)
                    total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : 'all',
                        'selected_time' : select_time,
                    }
                    return render(request,'agent/daily_report.html',context)
            else:
                print("its agent")
                bills = Bill.objects.filter(date__range=[from_date, to_date]).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(bill=bill.id,date__range=[from_date, to_date])
                    print(winnings)
                    total_winning = sum(winning.total for winning in winnings)
                    bill.win_amount += total_winning
                    if winnings != 0:
                        bill.total_d_amount = bill.total_c_amount - total_winning
                    else:
                        bill.total_d_amount = total_winning - bill.total_c_amount
                    total_winning = sum(bill.win_amount for bill in bills)
                    total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : 'all',
                        'selected_time' : 'all',
                    }
                    return render(request,'agent/daily_report.html',context)
    else:
        bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date).all()
        print(bills)
        for bill in bills:
            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=bill.id,date=current_date)
            print(winnings)
            total_winning = sum(winning.total for winning in winnings)
            bill.win_amount += total_winning
            if winnings != 0:
                bill.total_d_amount = bill.total_c_amount - total_winning
            else:
                bill.total_d_amount = total_winning - bill.total_c_amount
            total_winning = sum(bill.win_amount for bill in bills)
            total_balance = sum(bill.total_d_amount for bill in bills)
        total_c_amount = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date).aggregate(total_c_amount=Sum('total_c_amount'))
        select_dealer = 'all'
        select_time = 'all'
        context = {
            'dealers' : dealers,
            'times' : times,
            'dealer_bills' : bills,
            'total_c_amount': total_c_amount,
            'total_winning' : total_winning,
            'total_balance' : total_balance,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
        }
        return render(request,'agent/daily_report.html',context)

def winning_report(request):
    times = PlayTime.objects.filter().all()
    print(times)
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    agent_obj = Agent.objects.get(user=request.user)
    winnings = []
    totals = []
    aggregated_winnings = []
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_time = request.POST.get('time')
        print(from_date,to_date,select_time)
        if select_time != 'all':
            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time)
            print(winnings)
            aggregated_winnings = winnings.values('bill', 'LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                agent=F('agent__agent_name'),
                dealer=F('dealer__dealer_name'),
                position=F('position'),
            )
            totals = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
            context = {
                'times' : times,
                'winnings' : winnings,
                'totals' : totals,
                'aggr' : aggregated_winnings,
                'selected_time' : select_time,
                'selected_from' : from_date,
                'selected_to' : to_date,
            }
            return render(request,'agent/winning_report.html',context)
        else:
            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date])
            print(winnings)
            aggregated_winnings = winnings.values('bill', 'LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                agent=F('agent__agent_name'),
                dealer=F('dealer__dealer_name'),
                position=F('position'),
            )
            totals = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
            context = {
                'times' : times,
                'winnings' : winnings,
                'totals' : totals,
                'aggr' : aggregated_winnings,
                'selected_time' : 'all',
                'selected_from' : from_date,
                'selected_to' : to_date,
            }
            return render(request,'agent/winning_report.html',context)
    else:
        try:
            matching_play_times = Winning.objects.filter().last()
            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date=current_date,time=matching_play_times.time)
            aggregated_winnings = winnings.values('bill', 'LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                agent=F('agent__agent_name'),
                dealer=F('dealer__dealer_name'),
                position=F('position'),
            )
            totals = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date=current_date,time=matching_play_times.time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
        except:
            pass
        context = {
            'times' : times,
            'winnings' : winnings,
            'totals' : totals,
            'aggr' : aggregated_winnings,
            'selected_time' : matching_play_times.time.id,
        }
        return render(request,'agent/winning_report.html',context) 

def count_salereport(request):
    times = PlayTime.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    lsk_value1 = ['A','B','C']
    lsk_value2 = ['AB','BC','AC']
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    agent_super = AgentGame.objects.filter(date=current_date,agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_super = DealerGame.objects.filter(date=current_date,dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    agent_box = AgentGame.objects.filter(date=current_date,agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_box = DealerGame.objects.filter(date=current_date,dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    agent_single = AgentGame.objects.filter(date=current_date,agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_single = DealerGame.objects.filter(date=current_date,dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    agent_double = AgentGame.objects.filter(date=current_date,agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_double = DealerGame.objects.filter(date=current_date,dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    super_totals = {
        'total_count': (agent_super['total_count'] or 0) + (dealer_super['total_count'] or 0),
        'total_amount': (agent_super['total_amount'] or 0) + (dealer_super['total_amount'] or 0)
        }
    box_totals = {
        'total_count': (agent_box['total_count'] or 0) + (dealer_box['total_count'] or 0),
        'total_amount': (agent_box['total_amount'] or 0) + (dealer_box['total_amount'] or 0)
        }
    single_totals = {
        'total_count': (agent_single['total_count'] or 0) + (dealer_single['total_count'] or 0),
        'total_amount': (agent_single['total_amount'] or 0) + (dealer_single['total_amount'] or 0)
        }
    double_totals = {
        'total_count': (agent_double['total_count'] or 0) + (dealer_double['total_count'] or 0),
        'total_amount': (agent_double['total_amount'] or 0) + (dealer_double['total_amount'] or 0)
        }
    totals = {
        'net_count': (super_totals['total_count'] or 0) + (box_totals['total_count'] or 0) + (single_totals['total_count'] or 0) + (double_totals['total_count'] or 0),
        'net_amount': (super_totals['total_amount'] or 0) + (box_totals['total_amount'] or 0) + (single_totals['total_amount'] or 0) + (double_totals['total_amount'] or 0)
    }
    if request.method == 'POST':
        select_dealer = request.POST.get('select-agent')
        print(select_dealer)
        select_time = request.POST.get('time')
        print(select_time)
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_dealer != 'all':
            if select_dealer == str(agent_obj.user):
                if select_time != 'all':
                    agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    print(agent_super)
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
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : select_time,
                        'selected_dealer' : select_dealer,
                        'totals' : totals
                    }
                    return render(request,'agent/count_salereport.html',context)
                else:
                    agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    print(agent_super)
                    print(agent_box)
                    print(agent_single)
                    print(agent_double)
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
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : 'all',
                        'selected_dealer' : select_dealer,
                        'totals' : totals
                    }
                    return render(request,'agent/count_salereport.html',context)
            else:
                if select_time != 'all':
                    agent_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : select_time,
                        'selected_dealer' : select_dealer,
                        'totals' : totals
                    }
                    return render(request,'agent/count_salereport.html',context)
                else:
                    agent_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    agent_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : 'all',
                        'selected_dealer' : select_dealer,
                        'totals' : totals
                    }
                    return render(request,'agent/count_salereport.html',context)
        else:
            if select_time != 'all':
                agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                super_totals = {
                    'total_count': (agent_super['total_count'] or 0) + (dealer_super['total_count'] or 0),
                    'total_amount': (agent_super['total_amount'] or 0) + (dealer_super['total_amount'] or 0)
                    }
                box_totals = {
                    'total_count': (agent_box['total_count'] or 0) + (dealer_box['total_count'] or 0),
                    'total_amount': (agent_box['total_amount'] or 0) + (dealer_box['total_amount'] or 0)
                    }
                single_totals = {
                    'total_count': (agent_single['total_count'] or 0) + (dealer_single['total_count'] or 0),
                    'total_amount': (agent_single['total_amount'] or 0) + (dealer_single['total_amount'] or 0)
                    }
                double_totals = {
                    'total_count': (agent_double['total_count'] or 0) + (dealer_double['total_count'] or 0),
                    'total_amount': (agent_double['total_amount'] or 0) + (dealer_double['total_amount'] or 0)
                    }
                totals = {
                    'net_count': (super_totals['total_count'] or 0) + (box_totals['total_count'] or 0) + (single_totals['total_count'] or 0) + (double_totals['total_count'] or 0),
                    'net_amount': (super_totals['total_amount'] or 0) + (box_totals['total_amount'] or 0) + (single_totals['total_amount'] or 0) + (double_totals['total_amount'] or 0)
                }
                context = {
                    'times' : times,
                    'dealers' : dealers,
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'double_totals': double_totals,
                    'single_totals' : single_totals,
                    'selected_time' : select_time,
                    'selected_dealer' : 'all',
                    'totals' : totals
                }
                return render(request,'agent/count_salereport.html',context)
            else:
                agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                super_totals = {
                    'total_count': (agent_super['total_count'] or 0) + (dealer_super['total_count'] or 0),
                    'total_amount': (agent_super['total_amount'] or 0) + (dealer_super['total_amount'] or 0)
                    }
                box_totals = {
                    'total_count': (agent_box['total_count'] or 0) + (dealer_box['total_count'] or 0),
                    'total_amount': (agent_box['total_amount'] or 0) + (dealer_box['total_amount'] or 0)
                    }
                single_totals = {
                    'total_count': (agent_single['total_count'] or 0) + (dealer_single['total_count'] or 0),
                    'total_amount': (agent_single['total_amount'] or 0) + (dealer_single['total_amount'] or 0)
                    }
                double_totals = {
                    'total_count': (agent_double['total_count'] or 0) + (dealer_double['total_count'] or 0),
                    'total_amount': (agent_double['total_amount'] or 0) + (dealer_double['total_amount'] or 0)
                    }
                totals = {
                    'net_count': (super_totals['total_count'] or 0) + (box_totals['total_count'] or 0) + (single_totals['total_count'] or 0) + (double_totals['total_count'] or 0),
                    'net_amount': (super_totals['total_amount'] or 0) + (box_totals['total_amount'] or 0) + (single_totals['total_amount'] or 0) + (double_totals['total_amount'] or 0)
                }
                context = {
                    'times' : times,
                    'dealers' : dealers,
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'double_totals': double_totals,
                    'single_totals' : single_totals,
                    'selected_time' : 'all',
                    'selected_dealer' : 'all',
                    'totals' : totals
                }
                return render(request,'agent/count_salereport.html',context)
    context = {
        'times' : times,
        'dealers' : dealers,
        'super_totals' : super_totals,
        'box_totals' : box_totals,
        'double_totals': double_totals,
        'single_totals' : single_totals,
        'selected_time' : 'all',
        'selected_dealer' : 'all',
        'totals' : totals
    }
    return render(request,'agent/count_salereport.html',context) 

def winning_countreport(request):
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    print(dealers)
    times = PlayTime.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    winnings = Winning.objects.filter(date=current_date).all()
    totals = Winning.objects.filter(date=current_date).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
    if request.method == 'POST':
        select_time = request.POST.get('time')
        select_agent = request.POST.get('select_agent')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_time != 'all':
            if select_agent != 'all':
                if select_agent == str(agent_obj.user):
                    winnings = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date],time=select_time)
                    totals = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                    print(select_agent)
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : select_time,
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date
                    }
                    return render(request,'agent/winning_countreport.html',context)
                else:
                    winnings = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date],time=select_time)
                    totals = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                    print(winnings)
                    print(select_agent)
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : select_time,
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date
                    }
                    return render(request,'agent/winning_countreport.html',context)
            else:
                winnings = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time)
                totals = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agent_obj' : agent_obj,
                    'dealers':dealers,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : select_time,
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request,'agent/winning_countreport.html',context)
        else:
            if select_agent != 'all':
                if select_agent == str(agent_obj.user):
                    winnings = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date])
                    totals = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                    print(select_agent)
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : 'all',
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date
                    }
                    return render(request,'agent/winning_countreport.html',context)
                else:
                    winnings = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date])
                    totals = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                    print(winnings)
                    print(select_agent)
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : 'all',
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date
                    }
                    return render(request,'agent/winning_countreport.html',context)
            else:
                winnings = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date])
                totals = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agent_obj' : agent_obj,
                    'dealers':dealers,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : 'all',
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request,'agent/winning_countreport.html',context)
    context = {
        'times' : times,
        'agent_obj' : agent_obj,
        'dealers':dealers,
        'winnings' : winnings,
        'totals' : totals,
        'selected_agent' : 'all',
        'selected_time' : 'all'
    }
    return render(request,'agent/winning_countreport.html',context) 

def payment_report(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    dealers = Dealer.objects.filter().all()
    collections = DealerCollectionReport.objects.filter(date=current_date).all()
    from_dealer_total = DealerCollectionReport.objects.filter(date=current_date,from_or_to='from-dealer').aggregate(from_dealer=Sum('amount'))
    print(from_dealer_total)
    to_dealer_total = DealerCollectionReport.objects.filter(date=current_date,from_or_to='to-dealer').aggregate(to_dealer=Sum('amount'))
    print(to_dealer_total)
    from_dealer_amount = from_dealer_total['from_dealer'] if from_dealer_total['from_dealer'] else 0
    to_dealer_amount = to_dealer_total['to_dealer'] if to_dealer_total['to_dealer'] else 0
    profit_or_loss = from_dealer_amount - to_dealer_amount
    print(profit_or_loss)
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_dealer = request.POST.get('select-dealer')
        from_or_to = request.POST.get('from-to')
        if select_dealer != 'all':
            if from_or_to != 'all' and from_or_to == 'from-dealer':
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,from_or_to='from-dealer').all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                from_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = from_dealer_amount['amount'] if from_dealer_amount['amount'] else 0
                print(profit_or_loss, "hello")
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to
                }
                return render(request, 'agent/payment_report.html', context)
            if from_or_to != 'all' and from_or_to == 'to-dealer':
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,from_or_to='to-dealer').all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                to_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_dealer_amount['amount'] if to_dealer_amount['amount'] else 0
                profit_or_loss = -profit_or_loss
                print(profit_or_loss, "hello")
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to
                }
                return render(request, 'agent/payment_report.html', context)
            else:
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer).all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                to_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_dealer_amount['amount'] if to_dealer_amount['amount'] else 0
                print(profit_or_loss, "hello")
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to
                }
                return render(request, 'agent/payment_report.html', context)
        else:
            if from_or_to != 'all' and from_or_to == 'from-dealer':
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='from-dealer').all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                from_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = from_dealer_amount['amount'] if from_dealer_amount['amount'] else 0
                print(profit_or_loss, "hello")
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to
                }
                return render(request, 'agent/payment_report.html', context)
            if from_or_to != 'all' and from_or_to == 'to-dealer':
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='to-dealer').all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                to_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_dealer_amount['amount'] if to_dealer_amount['amount'] else 0
                profit_or_loss = -profit_or_loss
                print(profit_or_loss, "hello")
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to
                }
                return render(request, 'agent/payment_report.html', context)
            else:
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date]).all()
                from_dealer_total = DealerCollectionReport.objects.filter(date=current_date,from_or_to='from-dealer').aggregate(from_agent=Sum('amount'))
                print(from_dealer_total)
                to_dealer_total = DealerCollectionReport.objects.filter(date=current_date,from_or_to='to-dealer').aggregate(to_agent=Sum('amount'))
                print(to_dealer_total)
                from_dealer_amount = from_dealer_total['from_dealer'] if from_dealer_total['from_dealer'] else 0
                to_dealer_amount = to_dealer_total['to_dealer'] if to_dealer_total['to_dealer'] else 0
                profit_or_loss = from_dealer_amount - to_dealer_amount
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to
                }
                return render(request, 'agent/payment_report.html', context)
    else:
        context = {
            'dealers' : dealers,
            'collections' : collections,
            'selected_agent' : 'all',
            'profit_or_loss' : profit_or_loss,
            'from_or_to' : 'all'
        }
    return render(request,'agent/payment_report.html',context) 

def add_collection(request):
    dealers = Dealer.objects.filter().all()
    if request.method == 'POST':
        date = request.POST.get('date')
        select_dealer = request.POST.get('select-dealer')
        dealer_instance = Dealer.objects.get(id=select_dealer)
        from_or_to = request.POST.get('select-collection')
        amount = request.POST.get('amount')
        print(select_dealer,from_or_to,amount)
        collection = DealerCollectionReport.objects.create(dealer=dealer_instance,date=date,from_or_to=from_or_to,amount=amount)
        return redirect('agent:collection_report')
    context = {
        'dealers' : dealers,
    }
    return render(request,'agent/add_collection.html',context) 

def balance_report(request):
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    collection = DealerCollectionReport.objects.filter().all()
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    report_data = []
    total_balance = []
    if request.method == 'POST':
        select_agent = request.POST.get('select-agent')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_agent != 'all':
            dealer_instance = Agent.objects.get(id=select_agent)
            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], agent=select_agent)
            collection = DealerCollectionReport.objects.filter(date__range=[from_date, to_date], dealer=select_agent)
            dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('d_amount'))['dealer_total_d_amount'] or 0
            total_d_amount = dealer_total_d_amount
            from_agent = collection.filter(from_or_to='from-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            to_agent = collection.filter(from_or_to='to-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            total_collection_amount = from_agent - to_agent
            balance = float(total_collection_amount) - float(total_d_amount)
            if total_d_amount > 0:
                report_data.append({
                    'date' : current_date,
                    'dealer': dealer_instance,
                    'total_d_amount': total_d_amount,
                    'from_or_to' : total_collection_amount,
                    'balance' : balance
                })
            total_balance = sum(entry['balance'] for entry in report_data)
            context = {
                'dealers' : dealers,
                'selected_agent' : select_agent,
                'report_data': report_data,
                'total_balance' : total_balance,
                'selected_from' : from_date,
                'selected_to' : to_date
            }
            return render(request, 'agent/balance_report.html',context)
        else:
            pass
    for dealer in dealers:
        dealer_games = DealerGame.objects.filter(date=current_date, agent=agent_obj)
        print(dealer_games)
        collection = DealerCollectionReport.objects.filter(date=current_date, dealer=dealer)
        print(collection)
        dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('d_amount'))['dealer_total_d_amount'] or 0
        total_d_amount = dealer_total_d_amount
        from_agent = collection.filter(from_or_to='from-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        to_agent = collection.filter(from_or_to='to-dealer').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        total_collection_amount = from_agent - to_agent
        balance = float(total_collection_amount) - float(total_d_amount)
        if total_d_amount > 0:
            report_data.append({
                'date' : current_date,
                'dealer': dealer,
                'total_d_amount': total_d_amount,
                'from_or_to' : total_collection_amount,
                'balance' : balance
            })
    total_balance = sum(entry['balance'] for entry in report_data)
    context = {
        'dealers' : dealers,
        'selected_agent' : 'all',
        'report_data': report_data,
        'total_balance' : total_balance
    }
    return render(request, 'agent/balance_report.html',context)

def edit_bill(request):
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj.user,"agent id")
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    try:
        matching_play_times = PlayTime.objects.get(start_time__lte=current_time, end_time__gte=current_time)
        print(matching_play_times.id)
    except:
        matching_play_times = []
    if request.method == 'POST':
        search_dealer = request.POST.get('dealer-select')
        print(search_dealer,"the user id")
        if search_dealer == 'all':
            return redirect('agent:edit_bill')
        else:
            pass
        try:
            bill_search = Bill.objects.filter(user=search_dealer,time_id=matching_play_times.id,date=current_date).all()
            totals = Bill.objects.filter(user=search_dealer,time_id=matching_play_times.id,date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            print(bill_search,"search bill")
            context = {
                'dealers': dealers,
                'bills': bill_search,
                'totals' : totals
            }
            return render(request,'agent/edit_bill.html',context)
        except:
            bill_search = []
            totals = []
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            context = {
                'dealers': dealers,
                'bills': bill_search,
                'totals' : totals
            }
            return render(request,'agent/edit_bill.html',context)
    else:
        try:
            bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date,time_id=matching_play_times.id).all()
            totals = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date,time_id=matching_play_times.id).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            print(agent_obj.user,"agent id")
            context = {
                'bills':bills,
                'dealers' : dealers,
                'totals' : totals
            }
        except:
            bill_search = []
            totals = []
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            context = {
                'dealers': dealers,
                'bills': bill_search,
                'totals' : totals
            }
    return render(request,'agent/edit_bill.html',context)

def delete_bill(request,id):
    print(id)
    bill = Bill.objects.get(id=id)
    user_obj = bill.user
    print(user_obj)
    time_id = bill.time_id
    print(time_id,"time")
    date = bill.date
    print(date,"date")
    context = {
        'bill' : bill,
    }
    return render(request,'agent/delete_bill.html',context)     

def deleting_bill(request,id):
    bill = get_object_or_404(Bill,id=id)
    print(bill,"deleting bill")
    bill.delete()
    return redirect('agent:index')

def delete_row(request,id,bill_id):
    print(id,"this row")
    bill = get_object_or_404(Bill, id=bill_id)
    try:
        row_delete = get_object_or_404(AgentGame, id=id)
        row_delete.delete()
    except:
        row_delete = get_object_or_404(DealerGame, id=id)
        row_delete.delete()
    bill.update_totals()
    return redirect('agent:delete_bill',id=bill_id)

def play_game(request,id):
    agent_package = []
    time = PlayTime.objects.get(id=id)
    print(time.end_time)
    agent_obj = Agent.objects.get(user=request.user)
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_date)
    if current_time > time.end_time:
        return redirect('agent:index')
    if AgentPackage.objects.filter(agent=agent_obj).exists():
        agent_package = AgentPackage.objects.get(agent=agent_obj)
        print(agent_package.single_rate)
    else:
        messages.info(request,"There is no package for this user!")
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    try:
        rows = AgentGameTest.objects.filter(agent=agent_obj, time=id, date=current_date).order_by('-id')
        total_c_amount = sum(row.c_amount for row in rows)
        total_d_amount = sum(row.d_amount for row in rows)
        total_count = sum(row.count for row in rows)
    except:
        pass
    context = {
        'time' : time,
        'dealers' : dealers,
        'agent_package' : agent_package,
        'rows' : rows,
        'total_c_amount': total_c_amount,
        'total_d_amount': total_d_amount,
        'total_count': total_count,
    }
    return render(request,'agent/play_game.html',context)

def package(request):
    user_obj = Agent.objects.get(user=request.user)
    packages = DealerPackage.objects.filter(created_by=user_obj.user).all()
    print(packages)
    context = {
        'packages' : packages
    }
    return render(request,'agent/package.html',context)

def new_package(request):
    user_obj = Agent.objects.get(user=request.user)
    dealer = Dealer.objects.filter(agent=user_obj).all()
    if request.method == 'POST':
        dealer_obj = request.POST.get('dealer')
        package_name = request.POST.get('package_name')
        single_rate = request.POST.get('single_rate')
        single_dc = request.POST.get('single_dc')
        double_rate = request.POST.get('double_rate')
        double_dc = request.POST.get('double_dc')
        box_rate = request.POST.get('box_rate')
        box_dc = request.POST.get('box_dc')
        super_rate = request.POST.get('super_rate')
        super_dc = request.POST.get('super_dc')
        first_prize = request.POST.get('first_prize')
        first_dc = request.POST.get('first_dc')
        second_prize = request.POST.get('second_prize')
        second_dc = request.POST.get('second_dc')
        third_prize = request.POST.get('third_prize')
        third_dc = request.POST.get('third_dc')
        fourth_prize = request.POST.get('fourth_prize')
        fourth_dc = request.POST.get('fourth_dc')
        fifth_prize = request.POST.get('fifth_prize')
        fifth_dc = request.POST.get('fifth_dc')
        guarantee_prize = request.POST.get('guarantee_prize')
        guarantee_dc = request.POST.get('guarantee_dc')
        box_first_prize = request.POST.get('box_first_prize')
        box_first_prize_dc = request.POST.get('box_first_prize_dc')
        box_series_prize = request.POST.get('box_series_prize')
        box_series_dc = request.POST.get('box_series_dc')
        single1_prize = request.POST.get('single1_prize')
        single1_dc = request.POST.get('single1_dc')
        double2_prize = request.POST.get('double2_prize')
        double2_dc = request.POST.get('double2_dc')
        selected_dealer = Dealer.objects.get(id=dealer_obj)
        if DealerPackage.objects.filter(dealer=dealer_obj).exists():
            messages.info(request, "Package is not set, This dealer already have a package!")
        else:
            add_package = DealerPackage.objects.create(dealer=selected_dealer,created_by=user_obj.user,package_name=package_name,single_rate=single_rate,
                        single_dc=single_dc,double_rate=double_rate,double_dc=double_dc,box_rate=box_rate,
                        box_dc=box_dc,super_rate=super_rate,super_dc=super_dc,first_prize=first_prize,first_dc=first_dc,
                        second_prize=second_prize,second_dc=second_dc,third_prize=third_prize,third_dc=third_dc,fourth_prize=fourth_prize,
                        fourth_dc=fourth_dc,fifth_prize=fifth_prize,fifth_dc=fifth_dc,guarantee_prize=guarantee_prize,
                        guarantee_dc=guarantee_dc,box_first_prize=box_first_prize,box_first_prize_dc=box_first_prize_dc,
                        box_series_prize=box_series_prize,box_series_dc=box_series_dc,single1_prize=single1_prize,
                        single1_dc=single1_dc,double2_prize=double2_prize,double2_dc=double2_dc)
            add_package.save()
            messages.info(request, "Package created successfully!")
            return redirect('agent:set_limit')
    context = {
        'dealers' : dealer
    }
    return render(request,'agent/new_package.html',context)

def edit_package(request,id):
    package = DealerPackage.objects.get(id=id)
    user_obj = request.user
    if request.method == 'POST':
        dealer_obj = request.POST.get('dealer')
        package_name = request.POST.get('package_name')
        single_rate = request.POST.get('single_rate')
        single_dc = request.POST.get('single_dc')
        double_rate = request.POST.get('double_rate')
        double_dc = request.POST.get('double_dc')
        box_rate = request.POST.get('box_rate')
        box_dc = request.POST.get('box_dc')
        super_rate = request.POST.get('super_rate')
        super_dc = request.POST.get('super_dc')
        first_prize = request.POST.get('first_prize')
        first_dc = request.POST.get('first_dc')
        second_prize = request.POST.get('second_prize')
        second_dc = request.POST.get('second_dc')
        third_prize = request.POST.get('third_prize')
        third_dc = request.POST.get('third_dc')
        fourth_prize = request.POST.get('fourth_prize')
        fourth_dc = request.POST.get('fourth_dc')
        fifth_prize = request.POST.get('fifth_prize')
        fifth_dc = request.POST.get('fifth_dc')
        guarantee_prize = request.POST.get('guarantee_prize')
        guarantee_dc = request.POST.get('guarantee_dc')
        box_first_prize = request.POST.get('box_first_prize')
        box_first_prize_dc = request.POST.get('box_first_prize_dc')
        box_series_prize = request.POST.get('box_series_prize')
        box_series_dc = request.POST.get('box_series_dc')
        single1_prize = request.POST.get('single1_prize')
        single1_dc = request.POST.get('single1_dc')
        double2_prize = request.POST.get('double2_prize')
        double2_dc = request.POST.get('double2_dc')
        selected_dealer = Dealer.objects.get(id=dealer_obj)
        add_package = DealerPackage.objects.update(dealer=selected_dealer,created_by=user_obj,package_name=package_name,single_rate=single_rate,
                        single_dc=single_dc,double_rate=double_rate,double_dc=double_dc,box_rate=box_rate,
                        box_dc=box_dc,super_rate=super_rate,super_dc=super_dc,first_prize=first_prize,first_dc=first_dc,
                        second_prize=second_prize,second_dc=second_dc,third_prize=third_prize,third_dc=third_dc,fourth_prize=fourth_prize,
                        fourth_dc=fourth_dc,fifth_prize=fifth_prize,fifth_dc=fifth_dc,guarantee_prize=guarantee_prize,
                        guarantee_dc=guarantee_dc,box_first_prize=box_first_prize,box_first_prize_dc=box_first_prize_dc,
                        box_series_prize=box_series_prize,box_series_dc=box_series_dc,single1_prize=single1_prize,
                        single1_dc=single1_dc,double2_prize=double2_prize,double2_dc=double2_dc)
        messages.info(request, "Package updated successfully!")
        return redirect('agent:package')
    context = {
        'package' : package
    }
    return render(request,'agent/edit_package.html',context)

def delete_package(request,id):
    package = DealerPackage.objects.get(id=id)
    package.delete()
    return redirect('agent:package')

def agent_game_test_delete(request,id):
    row = get_object_or_404(AgentGameTest,id=id)
    row.delete()
    return JsonResponse({'status':'success'})

def agent_game_test_update(request,id):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        edited_count = data.get('editedCount')
        print(edited_count)
        AgentGameTest.objects.filter(id=id).update(count=edited_count)
    return JsonResponse({'status':'success'})

@csrf_exempt
def submit_data(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    agent_obj = Agent.objects.get(user=request.user)
    try:
        limit = Limit.objects.get(agent=agent_obj)
        print(limit.daily_limit)
    except:
        pass
    if request.method == 'POST':
        data = json.loads(request.body, object_pairs_hook=OrderedDict)
        select_dealer = data.get('selectDealer')
        link_text = data.get('linkText')
        value1 = data.get('value1')
        value2 = data.get('value2')
        value3 = data.get('value3')
        value4 = data.get('value4')
        timeId = data.get('timeId')

        print(select_dealer,"############")

        print(data)

        time = get_object_or_404(PlayTime,id=timeId)

        try:
            blocked_numbers = BlockedNumber.objects.filter(LSK=link_text, number=value1)
            if blocked_numbers:
                messages.info(request, "This number and LSK is blocked!")
                return redirect('agent:play_game',id=timeId)
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
            dealer_games_super = DealerGame.objects.filter(date=current_date,time=time,LSK='Super').aggregate(total_super=Sum('count')) or {'total_super': 0}
            agent_games_box = AgentGame.objects.filter(date=current_date,time=time,LSK='Box').aggregate(total_box=Sum('count')) or {'total_box': 0}
            dealer_games_box = DealerGame.objects.filter(date=current_date,time=time,LSK='Box').aggregate(total_box=Sum('count')) or {'total_box': 0}
            agent_games_ab = AgentGame.objects.filter(date=current_date,time=time,LSK='AB').aggregate(total_ab=Sum('count')) or {'total_ab': 0}
            dealer_games_ab = DealerGame.objects.filter(date=current_date,time=time,LSK='AB').aggregate(total_ab=Sum('count')) or {'total_ab': 0}
            agent_games_bc = AgentGame.objects.filter(date=current_date,time=time,LSK='BC').aggregate(total_bc=Sum('count')) or {'total_bc': 0}
            dealer_games_bc = DealerGame.objects.filter(date=current_date,time=time,LSK='BC').aggregate(total_bc=Sum('count')) or {'total_bc': 0}
            agent_games_ac = AgentGame.objects.filter(date=current_date,time=time,LSK='AC').aggregate(total_ac=Sum('count')) or {'total_ac': 0}
            dealer_games_ac = DealerGame.objects.filter(date=current_date,time=time,LSK='AC').aggregate(total_ac=Sum('count')) or {'total_ac': 0}
            agent_games_a = AgentGame.objects.filter(date=current_date,time=time,LSK='A').aggregate(total_a=Sum('count')) or {'total_a': 0}
            dealer_games_a = DealerGame.objects.filter(date=current_date,time=time,LSK='A').aggregate(total_a=Sum('count')) or {'total_a': 0}
            agent_games_b = AgentGame.objects.filter(date=current_date,time=time,LSK='B').aggregate(total_b=Sum('count')) or {'total_b': 0}
            dealer_games_b = DealerGame.objects.filter(date=current_date,time=time,LSK='B').aggregate(total_b=Sum('count')) or {'total_b': 0}
            agent_games_c = AgentGame.objects.filter(date=current_date,time=time,LSK='C').aggregate(total_c=Sum('count')) or {'total_c': 0}
            dealer_games_c = DealerGame.objects.filter(date=current_date,time=time,LSK='C').aggregate(total_c=Sum('count')) or {'total_c': 0}

            print("test",agent_games_super)
            print("test",dealer_games_super)

            games_super = (agent_games_super['total_super'] or 0) + (dealer_games_super['total_super'] or 0)
            games_box = (agent_games_box['total_box'] or 0) + (dealer_games_box['total_box'] or 0)
            games_ab = (agent_games_ab['total_ab'] or 0) + (dealer_games_ab['total_ab'] or 0)
            games_bc = (agent_games_bc['total_bc'] or 0) + (dealer_games_bc['total_bc'] or 0)
            games_ac = (agent_games_ac['total_ac'] or 0) + (dealer_games_ac['total_ac'] or 0)
            games_a = (agent_games_a['total_a'] or 0) + (dealer_games_a['total_a'] or 0)
            games_b = (agent_games_b['total_b'] or 0) + (dealer_games_b['total_b'] or 0)
            games_c = (agent_games_c['total_c'] or 0) + (dealer_games_c['total_c'] or 0)

            print("box",games_box)

            print(int(games_box)+int(value2))

            if link_text == 'Super':
                total_super = int(games_super) + int(value2)
                total = int(total_super) + int(value2)
                if total > game_limit.super:
                    print("Limit exceeded")
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game', id=timeId)
            elif link_text == 'Box':
                total_box = int(games_box)+int(value2)
                total = int(total_box) + int(value2)
                if total > game_limit.box:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
            elif link_text == 'AB':
                total_ab = int(games_ab)+int(value2)
                total = int(total_ab) + int(value2)
                if total > game_limit.ab:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
            elif link_text == 'BC':
                total_bc = int(games_bc)+int(value2)
                total = int(total_bc) + int(value2)
                if total > game_limit.bc:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
            elif link_text == 'AC':
                total_ac = int(games_ac)+int(value2)
                total = int(total_ac) + int(value2)
                if total > game_limit.ac:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
            elif link_text == 'A':
                total_a = int(games_a)+int(value2)
                total = int(total_a) + int(value2)
                if total > game_limit.a:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
            elif link_text == 'B':
                total_b = int(games_b)+int(value2)
                total = int(total_b) + int(value2)
                if total > game_limit.b:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
            elif link_text == 'C':
                total_c = int(games_c)+int(value2)
                total = int(total_c) + int(value2)
                if total > game_limit.c:
                    messages.info(request, "Limit of this LSK is exceeded!")
                    return redirect('agent:play_game',id=timeId)
        except:
            pass
        
        agent_game_test = AgentGameTest(
            agent=agent_obj,
            time=time,
            LSK=link_text,
            number=value1,
            count=value2,
            d_amount=value3,
            c_amount=value4
        )
        agent_game_test.save()
        total_c_amount = AgentGameTest.objects.filter(agent=agent_obj).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
        print(total_c_amount,"@@@@@")
        try:
            agent_total_c_amount = AgentGame.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
            print(agent_total_c_amount,"$$$$$$")
            print(agent_game_test.id,"id")
            if total_c_amount + agent_total_c_amount > limit.daily_limit:
                print("Your daily limit is exceeded")
                agent_game_test.delete()
                messages.info(request, "Your daily limit is exceeded")
            else:
                print("You have limit balance")
        except:
            pass
        try:
            blocked_numbers = BlockedNumber.objects.filter().all()
        except:
            pass
        return redirect('agent:play_game',id=timeId)
    return JsonResponse({'status': 'success'})

def save_data(request, id):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    agent_obj = Agent.objects.get(user=request.user)
    play_time_instance = PlayTime.objects.get(id=id)

    try:
        # Filter AgentGameTest records for the agent and the specific time
        agent_game_test = AgentGameTest.objects.filter(agent=agent_obj, time=play_time_instance, date=current_date)

        # Create AgentGame records based on AgentGameTest
        agent_game_records = []
        for test_record in agent_game_test:
            agent_game_record = AgentGame(
                agent=test_record.agent,
                time=test_record.time,
                date=test_record.date,
                LSK=test_record.LSK,
                number=test_record.number,
                count=test_record.count,
                d_amount=test_record.d_amount,
                c_amount=test_record.c_amount,
                combined=False
            )
            agent_game_records.append(agent_game_record)

        # Save the AgentGame records
        AgentGame.objects.bulk_create(agent_game_records)

        # Delete the AgentGameTest records
        agent_game_test.delete()

        # Check if there are AgentGame records
        if agent_game_records:
            # Calculate total values
            total_c_amount = sum([record.c_amount for record in agent_game_records])
            total_d_amount = sum([record.d_amount for record in agent_game_records])
            total_count = sum([record.count for record in agent_game_records])

            # Create the Bill record
            bill = Bill.objects.create(
                user=agent_obj.user,
                time_id=play_time_instance,
                date=current_date,
                total_c_amount=total_c_amount,
                total_d_amount=total_d_amount,
                total_count=total_count,
            )
            # Add related AgentGame records to the Bill
            bill.agent_games.add(*agent_game_records)

    except Exception as e:
        print(e)

    return redirect('agent:play_game',id=id)

def set_limit(request):
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    times = PlayTime.objects.filter().all()
    if request.method == 'POST':
        limit = request.POST.get('limit')
        print(limit)
        selected_times = request.POST.getlist('checkbox')
        print(selected_times)
        selected_agent = request.POST.get('select-agent')
        dealer_instance = Dealer.objects.get(id=selected_agent)
        print(selected_agent)
        if DealerLimit.objects.filter(agent=agent_obj,dealer=selected_agent).exists():
            messages.info(request, "Limit is not set, This dealer already have a limit!")
            context = {
                'agents' : dealers,
                'times' : times,
                'selected_agent' : selected_agent,
            }
            return render(request,'agent/set_limit.html',context)
        agent_checked_times = DealerLimit(agent=agent_obj,dealer=dealer_instance,daily_limit=limit)
        agent_checked_times.save()
        agent_checked_times.checked_times.add(*selected_times)
        return redirect('agent:index')
    context = {
        'agents' : dealers,
        'times' : times
    }
    return render(request,'agent/set_limit.html',context)

def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user,data=request.POST)
        if form.is_valid():
            form.save()
            print("password changed")
            messages.success(request,"your password changed")
            return redirect("website:login")
    else:
        form= PasswordChangeForm(user=request.user)
    return render(request,'agent/change_password.html',{'form':form})
 
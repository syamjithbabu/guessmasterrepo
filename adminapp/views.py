import datetime
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from website.decorators import dealer_required, agent_required, admin_required
from website.forms import LoginForm,UserUpdateForm
from website.forms import AgentRegistration
from website.models import User,Agent,Dealer
from agent.models import AgentGame, DealerPackage
from dealer.models import DealerGame
from .models import PlayTime, AgentPackage, Result, Winning, CollectionReport, Monitor, CombinedGame, Limit, BlockedNumber, GameLimit
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as pytz_timezone
import pytz
from django.utils import timezone
from agent.models import Bill
from django.db.models import Sum
from django.db.models import Q
import itertools
from django.db.models import F, Value, CharField, Case, When, Count
from collections import defaultdict
from django.contrib.auth.forms import AdminPasswordChangeForm,PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


# Create your views here.

@admin_required
@login_required
def index(request):
    agent_count = Agent.objects.all().count()
    dealer_count = Dealer.objects.all().count()
   

    context = {
        
        'agent_count':agent_count,
        'dealer_count':dealer_count
    }
    return render(request,'adminapp/index.html', context)

def agent(request):
    return render(request,'adminapp/customer/agent.html')

@login_required
@admin_required
@csrf_exempt
def add_agent(request):
    login_form = LoginForm()
    agent_form = AgentRegistration()
    if request.method == "POST":
        agent_form = AgentRegistration(request.POST)
        login_form = LoginForm(request.POST)
        print(agent_form)
        print(login_form)
        if login_form.is_valid() and agent_form.is_valid():
            print("loginform is not working")
            user = login_form.save(commit=False)
            user.is_agent = True
            user.save()
            c = agent_form.save(commit=False)
            c.user = user
            c.save()
            messages.info(request, "Agent Created Successfully")
            return redirect("adminapp:new_package")
    return render(request,'adminapp/add_agent.html',{"login_form": login_form, "agent_form": agent_form})

@login_required
@admin_required
def view_agent(request):
    agents = Agent.objects.filter().all()
    packages = AgentPackage.objects.filter().all()
    context = {
        'agents' : agents,
        'packages' : packages
    }
    return render(request,'adminapp/view_agent.html',context)

@login_required
@admin_required
def view_limits(request):
    limits = Limit.objects.filter().all()
    context = {
        'limits' : limits
    }
    return render(request,'adminapp/view_limits.html',context)

@login_required
@admin_required
def edit_limit(request, id):
    times = PlayTime.objects.all().order_by('id')
    if request.method == 'POST':
        limit = request.POST.get('limit')
        selected_times = request.POST.getlist('checkbox')
        selected_agent = request.POST.get('select-agent')

        # Get the selected Limit object
        limit_instance = Limit.objects.get(id=id)

        # Update the daily_limit for the selected Limit
        limit_instance.daily_limit = limit
        limit_instance.save()

        # Update the checked_times for the selected Limit
        limit_instance.checked_times.set(selected_times)

        return redirect('adminapp:index')

    context = {
        'times': times
    }
    return render(request, 'adminapp/edit_limit.html', context)

@login_required
@admin_required
def edit_agent(request, id):
    agent = get_object_or_404(Agent, id=id)
    user = agent.user
   

    if request.method == 'POST':
        form = AdminPasswordChangeForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminapp:index')
    else:
        form = AdminPasswordChangeForm(user=user)

    return render(request, 'adminapp/edit_agent.html', {'form': form})

@login_required
@admin_required
def delete_agent(request,id):
    agent = get_object_or_404(Agent, id=id)
    agent_user = agent.user
    dealers = Dealer.objects.filter(agent=agent)
    try:
        for dealer in dealers:
            dealer_user = dealer.user
            dealer_user.delete()
    except:
        pass
    agent_user.delete()
    return redirect('adminapp:view_agent')

@login_required
@admin_required
def ban_agent(request,id):
    agent = get_object_or_404(Agent, id=id)
    user = agent.user
    user.is_active = False
    user.save()
    dealers = Dealer.objects.filter(agent=agent)
    try:
        for dealer in dealers:
            dealer_user = dealer.user
            dealer_user.is_active = False
            dealer_user.save()
            print(dealer_user.is_active)
    except:
        pass
    return redirect('adminapp:view_agent')

@login_required
@admin_required
def remove_ban(request,id):
    agent = get_object_or_404(Agent, id=id)
    user = agent.user
    user.is_active = True
    user.save()
    dealers = Dealer.objects.filter(agent=agent)
    try:
        for dealer in dealers:
            dealer_user = dealer.user
            dealer_user.is_active = True
            dealer_user.save()
            print(dealer_user.is_active)
    except:
        pass
    return redirect('adminapp:view_agent')

@login_required
@admin_required
def package(request):
    packages = AgentPackage.objects.filter().all()
    print(packages)
    context = {
        'packages' : packages
    }
    return render(request,'adminapp/package.html',context)

@login_required
@admin_required
def new_package(request):
    user_obj = request.user
    try:
        agent = Agent.objects.filter().all()
    except:
        pass
    if request.method == 'POST':
        agent_obj = request.POST.get('agent')
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
        selected_agent = Agent.objects.get(id=agent_obj)
        if AgentPackage.objects.filter(agent=agent_obj).exists():
            messages.info(request, "Package is not set, This agent already have a package!")
        else:
            add_package = AgentPackage.objects.create(agent=selected_agent,created_by=user_obj,package_name=package_name,single_rate=single_rate,
                        single_dc=single_dc,double_rate=double_rate,double_dc=double_dc,box_rate=box_rate,
                        box_dc=box_dc,super_rate=super_rate,super_dc=super_dc,first_prize=first_prize,first_dc=first_dc,
                        second_prize=second_prize,second_dc=second_dc,third_prize=third_prize,third_dc=third_dc,fourth_prize=fourth_prize,
                        fourth_dc=fourth_dc,fifth_prize=fifth_prize,fifth_dc=fifth_dc,guarantee_prize=guarantee_prize,
                        guarantee_dc=guarantee_dc,box_first_prize=box_first_prize,box_first_prize_dc=box_first_prize_dc,
                        box_series_prize=box_series_prize,box_series_dc=box_series_dc,single1_prize=single1_prize,
                        single1_dc=single1_dc,double2_prize=double2_prize,double2_dc=double2_dc)
            add_package.save()
            messages.info(request, "Package created successfully!")
            return redirect('adminapp:set_limit')
    last_agent = Agent.objects.filter().last()
    print(last_agent.id)
    context = {
        'agents' : agent,
        'selected_agent' : last_agent.id,
    }
    return render(request,'adminapp/new_package.html',context)

@login_required
@admin_required
def set_limit(request):
    agents = Agent.objects.filter().all()
    times = PlayTime.objects.filter().all().order_by('id')
    if request.method == 'POST':
        limit = request.POST.get('limit')
        print(limit)
        selected_times = request.POST.getlist('checkbox')
        print(selected_times)
        selected_agent = request.POST.get('select-agent')
        agent_instance = Agent.objects.get(id=selected_agent)
        print(selected_agent)
        if Limit.objects.filter(agent=selected_agent).exists():
            messages.info(request, "Limit is not set, This agent already have a limit!")
            context = {
                'agents' : agents,
                'times' : times,
                'selected_agent' : selected_agent,
            }
            return render(request,'adminapp/set_limit.html',context)
        agent_checked_times = Limit(agent=agent_instance,daily_limit=limit)
        agent_checked_times.save()
        agent_checked_times.checked_times.add(*selected_times)
        return redirect('adminapp:index')
    last_agent = Agent.objects.filter().last()
    context = {
        'agents' : agents,
        'times' : times,
        'selected_agent' : last_agent.id,
    }
    return render(request,'adminapp/set_limit.html',context)

@login_required
@admin_required
def edit_package(request,id):
    package = AgentPackage.objects.get(id=id)
    user_obj = request.user
    if request.method == 'POST':
        agent_obj = request.POST.get('agent')
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
        selected_agent = Agent.objects.get(id=agent_obj)
        add_package = AgentPackage.objects.update(agent=selected_agent,created_by=user_obj,package_name=package_name,single_rate=single_rate,
                        single_dc=single_dc,double_rate=double_rate,double_dc=double_dc,box_rate=box_rate,
                        box_dc=box_dc,super_rate=super_rate,super_dc=super_dc,first_prize=first_prize,first_dc=first_dc,
                        second_prize=second_prize,second_dc=second_dc,third_prize=third_prize,third_dc=third_dc,fourth_prize=fourth_prize,
                        fourth_dc=fourth_dc,fifth_prize=fifth_prize,fifth_dc=fifth_dc,guarantee_prize=guarantee_prize,
                        guarantee_dc=guarantee_dc,box_first_prize=box_first_prize,box_first_prize_dc=box_first_prize_dc,
                        box_series_prize=box_series_prize,box_series_dc=box_series_dc,single1_prize=single1_prize,
                        single1_dc=single1_dc,double2_prize=double2_prize,double2_dc=double2_dc)
        messages.info(request, "Package updated successfully!")
        return redirect('adminapp:package')
    context = {
        'package' : package
    }
    return render(request,'adminapp/edit_package.html',context)

@login_required
@admin_required
def delete_package(request,id):
    package = AgentPackage.objects.get(id=id)
    package.delete()
    return redirect('adminapp:package')

@login_required
@admin_required
def add_result(request):
    timings = PlayTime.objects.filter().all().order_by('id')
    print(timings)
    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        play_time = PlayTime.objects.get(id=time)
        first = request.POST.get('first')
        second = request.POST.get('second')
        third = request.POST.get('third')
        fourth = request.POST.get('fourth')
        fifth = request.POST.get('fifth')
        field1 = request.POST.get('field1')
        field2 = request.POST.get('field2')
        field3 = request.POST.get('field3')
        field4 = request.POST.get('field4')
        field5 = request.POST.get('field5')
        field6 = request.POST.get('field6')
        field7 = request.POST.get('field7')
        field8 = request.POST.get('field8')
        field9 = request.POST.get('field9')
        field10 = request.POST.get('field10')
        field11 = request.POST.get('field11')
        field12 = request.POST.get('field12')
        field13 = request.POST.get('field13')
        field14 = request.POST.get('field14')
        field15 = request.POST.get('field15')
        field16 = request.POST.get('field16')
        field17 = request.POST.get('field17')
        field18 = request.POST.get('field18')
        field19 = request.POST.get('field19')
        field20 = request.POST.get('field20')
        field21 = request.POST.get('field21')
        field22 = request.POST.get('field22')
        field23 = request.POST.get('field23')
        field24 = request.POST.get('field24')
        field25 = request.POST.get('field25')
        field26 = request.POST.get('field26')
        field27 = request.POST.get('field27')
        field28 = request.POST.get('field28')
        field29 = request.POST.get('field29')
        field30 = request.POST.get('field30')
        already_result_check = Result.objects.filter(date=date,time=time)
        if already_result_check:
            messages.info(request, "Result already published on this date and time!")
            context = {
                'timings' : timings
            }
            return render(request,'adminapp/add_result.html',context)
        else:
            result = Result.objects.create(date=date,time=play_time,first=first,second=second,third=third,fourth=fourth,fifth=fifth,field1=field1,field2=field2,field3=field3,field4=field4,field5=field5,field6=field6,field7=field7,field8=field8,field9=field9,field10=field10,field11=field11,field12=field12,field13=field13,field14=field14,field15=field15,field16=field16,field17=field17,field18=field18,field19=field19,field20=field20,field21=field21,field22=field22,field23=field23,field24=field24,field25=field25,field26=field26,field27=field27,field28=field28,field29=field29,field30=field30)
            result.save()
            messages.info(request, "Result published!")
            agent_games = AgentGame.objects.filter(date=date,time=time).all()
            dealer_games = DealerGame.objects.filter(date=date,time=time).all()
            if agent_games:
                for game in agent_games:
                    print("Game",game)
                    print("Game id",game.id)
                    game_number = game.number
                    if game.LSK == 'Box' and game_number != result.first:
                        combinations = get_combinations(game_number)
                        print("Combinations:", combinations)
                        if len(combinations) == 6:
                            for combination in combinations:
                                if combination == result.first:
                                    print(f"Combination {combination} matches the first field for Game {game.id}")
                                    matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                                    agent_package = AgentPackage.objects.get(agent=game.agent)
                                    prize = ((agent_package.box_series_prize)*(game.count))
                                    commission = ((agent_package.box_series_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    box_series_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                        elif len(combinations) == 3:
                            for combination in combinations:
                                if combination == result.first:
                                    print(f"Combination {combination} matches the first field for Game {game.id}")
                                    matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                                    agent_package = AgentPackage.objects.get(agent=game.agent)
                                    prize = ((agent_package.box_series_prize)*(game.count))*2
                                    commission = ((agent_package.box_series_dc)*(game.count))*2
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    box_series_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif game.number in result.__dict__.values():
                        matched_field = [field for field, value in result.__dict__.items() if value == game.number]
                        if matched_field:
                            print("hello")
                            matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                            print(matching_bills.id)
                            print(f"Agent game number {game.number} matched with Result field: {matched_field[0]} for Agent: {game.agent}")
                            agent_package = AgentPackage.objects.get(agent=game.agent)
                            if game.LSK == "Super":
                                if matched_field[0] == 'first':
                                    prize = ((agent_package.first_prize)*(game.count))
                                    commission = ((agent_package.first_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    first_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'second':
                                    prize = ((agent_package.second_prize)*(game.count))
                                    commission = ((agent_package.second_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    second_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'third':
                                    prize = ((agent_package.third_prize)*(game.count))
                                    commission = ((agent_package.third_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    third_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="3",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'fourth':
                                    prize = ((agent_package.fourth_prize)*(game.count))
                                    commission = ((agent_package.fourth_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    fourth_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="4",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'fifth':
                                    prize = ((agent_package.fifth_prize)*(game.count))
                                    commission = ((agent_package.fifth_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    fifth_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="5",prize=prize,commission=commission,total=total)
                                else :
                                    prize = ((agent_package.guarantee_prize)*(game.count))
                                    commission = ((agent_package.guarantee_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    first_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="6",prize=prize,commission=commission,total=total)
                            elif game.LSK == "Box":
                                if matched_field[0] == 'first':
                                    prize = ((agent_package.box_first_prize)*(game.count))
                                    commission = ((agent_package.box_first_prize_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    box_first_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'A' and result.first.startswith(game_number[0]):
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        print(date,time,game.agent.user.id,game.id)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        prize = ((agent_package.single1_prize)*(game.count))
                        commission = ((agent_package.single1_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'B' and result.first[1] == game.number[0]:
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        prize = ((agent_package.single1_prize)*(game.count))
                        commission = ((agent_package.single1_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'C' and result.first[2] == game.number[0]:
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        prize = ((agent_package.single1_prize)*(game.count))
                        commission = ((agent_package.single1_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'AB' and result.first[:2] == game.number[:2]:
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        prize = ((agent_package.double2_prize)*(game.count))
                        commission = ((agent_package.double2_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'BC' and result.first[1] == game.number[0] and result.first[-1] == game.number[-1]:
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        prize = ((agent_package.double2_prize)*(game.count))
                        commission = ((agent_package.double2_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'AC' and result.first[0] == game.number[0] and result.first[-1] == game.number[-1]:
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        prize = ((agent_package.double2_prize)*(game.count))
                        commission = ((agent_package.double2_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
            if dealer_games:
                for game in dealer_games:
                    print("Game",game)
                    print("Game id",game.id)
                    game_number = game.number
                    if game.LSK == 'Box' and game_number != result.first:
                        combinations = get_combinations(game_number)
                        print("Combinations:", combinations)
                        if len(combinations) == 6:
                            for combination in combinations:
                                if combination == result.first:
                                    print(f"Combination {combination} matches the first field for Game {game.id}")
                                    matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                                    prize = ((dealer_package.box_series_prize)*(game.count))
                                    commission = ((dealer_package.box_series_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    box_series_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                        elif len(combinations) == 3:
                            for combination in combinations:
                                if combination == result.first:
                                    print(f"Combination {combination} matches the first field for Game {game.id}")
                                    matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                                    prize = ((dealer_package.box_series_prize)*(game.count))*2
                                    commission = ((dealer_package.box_series_dc)*(game.count))*2
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    box_series_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif game.number in result.__dict__.values():
                        matched_field = [field for field, value in result.__dict__.items() if value == game.number]
                        if matched_field:
                            print("hello")
                            matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                            print(matching_bills.id)
                            print(f"Dealer game number {game.number} matched with Result field: {matched_field[0]} for Dealer: {game.dealer}")
                            dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                            if game.LSK == "Super":
                                if matched_field[0] == 'first':
                                    prize = ((dealer_package.first_prize)*(game.count))
                                    commission = ((dealer_package.first_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    first_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'second':
                                    prize = ((dealer_package.second_prize)*(game.count))
                                    commission = ((dealer_package.second_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    second_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'third':
                                    prize = ((dealer_package.third_prize)*(game.count))
                                    commission = ((dealer_package.third_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    third_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="3",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'fourth':
                                    prize = ((dealer_package.fourth_prize)*(game.count))
                                    commission = ((dealer_package.fourth_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    fourth_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="4",prize=prize,commission=commission,total=total)
                                elif matched_field[0] == 'fifth':
                                    prize = ((dealer_package.fifth_prize)*(game.count))
                                    commission = ((dealer_package.fifth_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    fifth_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="5",prize=prize,commission=commission,total=total)
                                else :
                                    prize = ((dealer_package.guarantee_prize)*(game.count))
                                    commission = ((dealer_package.guarantee_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    first_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="6",prize=prize,commission=commission,total=total)
                            elif game.LSK == "Box":
                                if matched_field[0] == 'first':
                                    prize = ((dealer_package.box_first_prize)*(game.count))
                                    commission = ((dealer_package.box_first_prize_dc)*(game.count))
                                    total = ((prize)+(commission))
                                    print(prize,commission,total)
                                    box_first_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'A' and result.first.startswith(game_number[0]):
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        prize = ((dealer_package.single1_prize)*(game.count))
                        commission = ((dealer_package.single1_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'B' and result.first[1] == game.number[0]:
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        prize = ((dealer_package.single1_prize)*(game.count))
                        commission = ((dealer_package.single1_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'C' and result.first[2] == game.number[0]:
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        prize = ((dealer_package.single1_prize)*(game.count))
                        commission = ((dealer_package.single1_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'AB' and result.first[:2] == game.number[:2]:
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        prize = ((dealer_package.double2_prize)*(game.count))
                        commission = ((dealer_package.double2_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'BC' and result.first[1] == game.number[0] and result.first[-1] == game.number[-1]:
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        prize = ((dealer_package.double2_prize)*(game.count))
                        commission = ((dealer_package.double2_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif game.LSK == 'AC' and result.first[0] == game.number[0] and result.first[-1] == game.number[-1]:
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        matching_bills = Bill.objects.get(date=date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        prize = ((dealer_package.double2_prize)*(game.count))
                        commission = ((dealer_package.double2_dc)*(game.count))
                        total = ((prize)+(commission))
                        single_prize = Winning.objects.create(date=date,time=play_time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
    context = {
        'timings' : timings
    }
    return render(request,'adminapp/add_result.html',context)

@login_required
@admin_required
def sales_report(request):
    agents = Agent.objects.filter().all()
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        
        if select_dealer != 'all':
            agent_instance = Agent.objects.get(id=select_dealer)
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        lsk = request.POST.get('select-lsk')
        print(from_date,"fromdate")
        print(to_date,"todate")
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
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
            if select_time != 'all':
                #time and agent is selected
                if lsk != 'all':
                    print("agent,time,lsk selected")
                    print(agent_instance)
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(Q(dealer__agent=agent_instance),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    agent_games_total = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(Q(dealer__agent=agent_instance),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
                    }
                    for bill in dealer_bills:
                        for game in bill.dealer_games.filter(LSK__in=lsk_value):
                            print("Dealer Count of",bill.id," is" , game.count)
                            print("Dealer D Amount of",bill.id," is" , game.d_amount)
                            print("Dealer C Amount of",bill.id," is" , game.c_amount)
                        bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                        bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                        bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    for bill in agent_bills:
                        for game in bill.agent_games.filter(LSK__in=lsk_value):
                            print("Agent Count of",bill.id," is" , game.count)
                            print("Agent D Amount of",bill.id," is" , game.d_amount)
                            print("Agent C Amount of",bill.id," is" , game.c_amount)
                        bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                        bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                        bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                    context = {
                        'agents' : agents,
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
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,dealer__agent=agent_instance).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    agent_games_total = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,dealer__agent=agent_instance).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
                    }
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
            else:
                #time not selected, agent selected
                if lsk != 'all':
                    #lsk selected, time not selected, agent selected
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],LSK__in=lsk_value).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(dealer__agent=agent_instance,date__range=[from_date, to_date],LSK__in=lsk_value).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date]).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date]).distinct()
                    agent_games_total = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(dealer__agent=agent_instance,date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
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
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    #time,lsk not selected, agent selected
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date]).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_instance).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date]).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date]).distinct()
                    agent_games_total = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_instance).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
                    }
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
        else:
            if select_time != 'all':
                if lsk != 'all':
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    agent_games_total = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
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
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date],time_id=select_time).distinct()
                    agent_games_total = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
                    }
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
            else:
                #time not selected, agent selected
                if lsk != 'all':
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date]).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date]).distinct()
                    agent_games_total = AgentGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
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
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    #time,lsk not selected, agent selected
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date]).order_by('id')
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date]).order_by('id')
                    print(dealer_games)
                    agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date__range=[from_date, to_date]).distinct()
                    dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date__range=[from_date, to_date]).distinct()
                    agent_games_total = AgentGame.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
                    }
                    context = {
                        'agents' : agents,
                        'times': times,
                        'agent_bills' : agent_bills,
                        'dealer_bills' : dealer_bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                        'agent_games' : agent_games,
                        'dealer_games' : dealer_games,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
    else:
        print("this is working")
        agent_games = AgentGame.objects.filter(date=current_date).all().order_by('id')
        dealer_games = DealerGame.objects.filter(date=current_date).all().order_by('id')
        agent_bills = Bill.objects.filter(Q(agent_games__in=agent_games),date=current_date).distinct()
        dealer_bills = Bill.objects.filter(Q(dealer_games__in=dealer_games),date=current_date).distinct()
        totals = Bill.objects.filter(date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
        select_dealer = 'all'
        select_time = 'all'
        context = {
            'agents' : agents,
            'times' : times,
            'agent_bills' : agent_bills,
            'dealer_bills' : dealer_bills,
            'totals' : totals,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
            'agent_games' : agent_games,
            'dealer_games' : dealer_games
        }
        return render(request,'adminapp/sales_report.html',context)

@login_required
@admin_required
def add_time(request):
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        print(start_time)
        end_time = request.POST.get('end_time')
        game_time = request.POST.get('game_time')
        set_time = PlayTime.objects.create(game_time=game_time,start_time=start_time,end_time=end_time)
        set_time.save()
        return redirect('adminapp:change_time')
    return render(request,'adminapp/add_time.html')

@login_required
@admin_required
def change_time(request):
    try:
        times = PlayTime.objects.filter().all()
    except:
        pass
    context = {
        'times' : times,
    }
    return render(request,'adminapp/change_time.html',context)

@login_required
@admin_required
def change_game_time(request,id):
    time = get_object_or_404(PlayTime,id=id)
    print(time.start_time)
    print(time.end_time)
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        print(start_time)
        end_time = request.POST.get('end_time')
        print(end_time)
        set_time = PlayTime.objects.filter(id=id).update(start_time=start_time,end_time=end_time)
        return redirect('adminapp:change_time')
    return render(request,'adminapp/change_game_time.html',{'time': time})

@login_required
@admin_required
def monitor_times(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    matching_play_times = PlayTime.objects.filter(Q(start_time__lte=current_time) & Q(end_time__gte=current_time)).order_by('id')
    context = {
        'times' : matching_play_times
    }
    return render(request,'adminapp/monitor_times.html',context)

@login_required
@admin_required
def monitor(request,id):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_date)
    times = PlayTime.objects.filter().all().order_by('id')
    matching_play_times = []
    try:
        time = PlayTime.objects.get(id=id)
    except:
        pass
    if time:
        agent_games = AgentGame.objects.filter(date=current_date,time=time)
        dealer_games = DealerGame.objects.filter(date=current_date,time=time)
        monitor_game = CombinedGame.objects.filter(date=current_date,time=time).all()
        set_monitor_limit = Monitor.objects.get(time=time)
    else:
        return render(request,'adminapp/monitor.html')
    try:
        limits = {
            'Super': set_monitor_limit.super,
            'Box': set_monitor_limit.box,
            'AB' : set_monitor_limit.ab,
            'BC' : set_monitor_limit.bc,
            'AC' : set_monitor_limit.ac,
            'A' : set_monitor_limit.a,
            'B' : set_monitor_limit.b,
            'C' : set_monitor_limit.c,
        }
    except:
        pass

    combined_games = {}

    existing_combined_games = CombinedGame.objects.filter(date=current_date, time=time)

    existing_combined_games_dict = {(game.LSK, game.number): game for game in existing_combined_games}

    for agent_game in agent_games:
        if agent_game.combined == False:
            key = (agent_game.LSK, agent_game.number)
            if key in existing_combined_games_dict:
                existing_combined_game = existing_combined_games_dict[key]
                if hasattr(agent_game, 'count') and isinstance(agent_game.count, int):
                    existing_combined_game.count += agent_game.count
                    if agent_game.LSK in limits:
                        limit = limits[agent_game.LSK]
                        existing_combined_game.remaining_limit += agent_game.count - limit
                    existing_combined_game.combined = True
                    print(existing_combined_game.count)
                    print(agent_game.count)
                    existing_combined_game.save()
                    agent_game.combined = True
                    agent_game.save()
            elif key in combined_games:
                combined_games[key]['count'] += agent_game.count
                combined_games[key]['combined'] = True
            else:
                print("working this")
                combined_games[key] = {
                    'LSK': agent_game.LSK,
                    'number': agent_game.number,
                    'count': agent_game.count,
                    'combined': False,
                    'user': agent_game.agent.user,
                }
            agent_game.combined = True
            agent_game.save()

    for dealer_game in dealer_games:
        if dealer_game.combined == False:
            key = (dealer_game.LSK, dealer_game.number)
            if key in existing_combined_games_dict:
                existing_combined_game = existing_combined_games_dict[key]
                if hasattr(agent_game, 'count') and isinstance(agent_game.count, int):
                    existing_combined_game.count += dealer_game.count
                    if dealer_game.LSK in limits:
                        limit = limits[dealer_game.LSK]
                        existing_combined_game.remaining_limit += dealer_game.count - limit 
                    existing_combined_game.combined = True
                    existing_combined_game.save()
                    dealer_game.combined = True
                    dealer_game.save()
            elif key in combined_games:
                combined_games[key]['count'] += dealer_game.count
                combined_games[key]['combined'] = True
            else:
                combined_games[key] = {
                    'LSK': dealer_game.LSK,
                    'number': dealer_game.number,
                    'count': dealer_game.count,
                    'combined': False,
                    'user': dealer_game.agent.user,
                }
            dealer_game.combined = True
            dealer_game.save()
    
    total_count = 0

    for key, game_info in combined_games.items():
        print("555555555555555")
        LSK, number = key
        count = game_info['count']
        user = game_info['user']
        is_combined = game_info['combined']
        total_count += count
        print(total_count,"Total count")
        combined_game = CombinedGame(
            date=current_date,
            time=time,
            LSK=LSK,
            number=number,
            count=count,
            user=user,
            combined=is_combined,
        )

        if LSK in limits:
            limit = limits[LSK]
            remaining_limit = count - limit
            if remaining_limit <= 0:
                remaining_limit = 0
            combined_game.remaining_limit = remaining_limit
        combined_game.save()

    context = {
        'agent_games' : agent_games,
        'dealer_games' : dealer_games,
        'monitor_games' : monitor_game,
        'times' : times,
        'id' : id
    }
    if request.method == 'POST':
        print("filtering")
        checkboxes = request.POST.getlist('checkbox2')
        print(checkboxes)
        from_date = request.POST.get('from-date')
        sort = request.POST.get('sort')
        hide_zero = request.POST.get('hide-zero')
        search = request.POST.get('serch')
        selected_time = request.POST.get('time')
        print(search)
        print(hide_zero)
        filter_query = Q()
        if checkboxes:
            filter_query |= Q(LSK__in=checkboxes)
        if from_date:
            filter_query &= Q(date=from_date)
        if selected_time != 'all':
            selected_time_obj = PlayTime.objects.get(id=selected_time)
            filter_query &= Q(time=selected_time_obj)
        if search:
            search_query = Q(LSK__icontains=search) | Q(number__icontains=search)
            combined_games = CombinedGame.objects.filter(search_query)
            context = {
                'monitor_games' : combined_games,
                'agent_games' : agent_games,
                'dealers_games' : dealer_games,
                'times' : times,
                'selected_time' : selected_time,
                'id' : id
            }
            return render(request,'adminapp/monitor.html',context)

        print("Filter Query:", filter_query)
        combined_games = CombinedGame.objects.filter(filter_query)
        print("Combined Games:", combined_games)
        context = {
            'monitor_games' : combined_games,
            'agent_games' : agent_games,
            'dealers_games' : dealer_games,
            'times' : times,
            'id' : id
        }
    return render(request,'adminapp/monitor.html',context)

@login_required
@admin_required
def clear_limit(request,id,time_id):
    combined_game = get_object_or_404(CombinedGame,id=id)
    print(combined_game)
    clear_limit = CombinedGame.objects.filter(id=id).update(remaining_limit=0)
    print("cleared")
    return redirect('adminapp:monitor',id=time_id)

@login_required
@admin_required
def clear_all(request,id):
    clear_limit = CombinedGame.objects.filter().update(remaining_limit=0)
    print("cleared")
    return redirect('adminapp:monitor',id=id)

@login_required
@admin_required
def set_monitor_times(request):
    times = PlayTime.objects.filter().all().order_by('id')
    context = {
        'times' : times
    }
    return render(request,'adminapp/set_monitor_times.html',context)

@login_required
@admin_required
def set_monitor(request,id):
    time = PlayTime.objects.get(id=id)
    if request.method == 'POST':
        super = request.POST.get('super')
        box = request.POST.get('box')
        ab = request.POST.get('ab')
        bc = request.POST.get('bc')
        ac = request.POST.get('ac')
        a = request.POST.get('a')
        b = request.POST.get('b')
        c = request.POST.get('c')
        if Monitor.objects.filter(time=time):
            monitor = Monitor.objects.filter(time=time).update(super=super,box=box,ab=ab,bc=bc,ac=ac,a=a,b=b,c=c)
            print("monitor updated")
        else:
            monitor = Monitor.objects.create(time=time,super=super,box=box,ab=ab,bc=bc,ac=ac,a=a,b=b,c=c)
            print("monitor set")
        return redirect('adminapp:monitor',id=id)
    try:
        try:
            monitor = Monitor.objects.get(time=time)
        except:
            monitor = []
        context = {
            'monitor' : monitor,
        }
        return render(request,'adminapp/set_monitor.html',context)
    except:
        pass
    return render(request,'adminapp/set_monitor.html')

@login_required
@admin_required
def republish_results(request):
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    last_result = Result.objects.filter(date=current_date).last()
    time = last_result.time
    if last_result:
        field_values = {
            'first': last_result.first,
            'second': last_result.second,
            'third': last_result.third,
            'fourth': last_result.fourth,
            'fifth': last_result.fifth,
            'field1': last_result.field1,
            'field2': last_result.field2,
            'field3': last_result.field3,
            'field4': last_result.field4,
            'field5': last_result.field5,
            'field6': last_result.field6,
            'field7': last_result.field7,
            'field8': last_result.field8,
            'field9': last_result.field9,
            'field10': last_result.field10,
            'field11': last_result.field11,
            'field12': last_result.field12,
            'field13': last_result.field13,
            'field14': last_result.field14,
            'field15': last_result.field15,
            'field16': last_result.field16,
            'field17': last_result.field17,
            'field18': last_result.field18,
            'field19': last_result.field19,
            'field20': last_result.field20,
            'field21': last_result.field21,
            'field22': last_result.field22,
            'field23': last_result.field23,
            'field24': last_result.field24,
            'field25': last_result.field25,
            'field26': last_result.field26,
            'field27': last_result.field27,
            'field28': last_result.field28,
            'field29': last_result.field29,
            'field30': last_result.field30,
        }
    else:
        field_values = {
            'first': '',
            'second': '',
            'third': '',
            'fourth': '',
            'fifth': '',
            'field1': '',
            'field2': '',
            'field3': '',
            'field4': '',
            'field5': '',
            'field6': '',
            'field7': '',
            'field8': '',
            'field9': '',
            'field10': '',
            'field11': '',
            'field12': '',
            'field13': '',
            'field14': '',
            'field15': '',
            'field16': '',
            'field17': '',
            'field18': '',
            'field19': '',
            'field20': '',
            'field21': '',
            'field22': '',
            'field23': '',
            'field24': '',
            'field25': '',
            'field26': '',
            'field27': '',
            'field28': '',
            'field29': '',
            'field30': '',
        }
    if request.method == 'POST':
        first = request.POST.get('first')
        second = request.POST.get('second')
        third = request.POST.get('third')
        fourth = request.POST.get('fourth')
        fifth = request.POST.get('fifth')
        field1 = request.POST.get('field1')
        field2 = request.POST.get('field2')
        field3 = request.POST.get('field3')
        field4 = request.POST.get('field4')
        field5 = request.POST.get('field5')
        field6 = request.POST.get('field6')
        field7 = request.POST.get('field7')
        field8 = request.POST.get('field8')
        field9 = request.POST.get('field9')
        field10 = request.POST.get('field10')
        field11 = request.POST.get('field11')
        field12 = request.POST.get('field12')
        field13 = request.POST.get('field13')
        field14 = request.POST.get('field14')
        field15 = request.POST.get('field15')
        field16 = request.POST.get('field16')
        field17 = request.POST.get('field17')
        field18 = request.POST.get('field18')
        field19 = request.POST.get('field19')
        field20 = request.POST.get('field20')
        field21 = request.POST.get('field21')
        field22 = request.POST.get('field22')
        field23 = request.POST.get('field23')
        field24 = request.POST.get('field24')
        field25 = request.POST.get('field25')
        field26 = request.POST.get('field26')
        field27 = request.POST.get('field27')
        field28 = request.POST.get('field28')
        field29 = request.POST.get('field29')
        field30 = request.POST.get('field30')
        old_result_delete = Result.objects.filter(date=current_date).last()
        old_result_delete.delete()
        result = Result.objects.create(date=current_date,time=time,first=first,second=second,third=third,fourth=fourth,fifth=fifth,field1=field1,field2=field2,field3=field3,field4=field4,field5=field5,field6=field6,field7=field7,field8=field8,field9=field9,field10=field10,field11=field11,field12=field12,field13=field13,field14=field14,field15=field15,field16=field16,field17=field17,field18=field18,field19=field19,field20=field20,field21=field21,field22=field22,field23=field23,field24=field24,field25=field25,field26=field26,field27=field27,field28=field28,field29=field29,field30=field30)
        agent_games = AgentGame.objects.filter(date=current_date,time=time).all()
        dealer_games = DealerGame.objects.filter(date=current_date,time=time).all()
        delete_old_winnings = Winning.objects.filter(date=current_date,time=time).all()
        delete_old_winnings.delete()
        if agent_games:
            for game in agent_games:
                print("Game",game)
                print("Game id",game.id)
                game_number = game.number
                if game.LSK == 'Box' and game_number != result.first:
                    combinations = get_combinations(game_number)
                    print("Combinations:", combinations)
                    if len(combinations) == 6:
                        for combination in combinations:
                            if combination == result.first:
                                print(f"Combination {combination} matches the first field for Game {game.id}")
                                matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                                agent_package = AgentPackage.objects.get(agent=game.agent)
                                prize = ((agent_package.box_series_prize)*(game.count))
                                commission = ((agent_package.box_series_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                box_series_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif len(combinations) == 3:
                        for combination in combinations:
                            if combination == result.first:
                                print(f"Combination {combination} matches the first field for Game {game.id}")
                                matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                                agent_package = AgentPackage.objects.get(agent=game.agent)
                                prize = ((agent_package.box_series_prize)*(game.count))*2
                                commission = ((agent_package.box_series_dc)*(game.count))*2
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                box_series_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                elif game.number in result.__dict__.values():
                    matched_field = [field for field, value in result.__dict__.items() if value == game.number]
                    if matched_field:
                        print("hello")
                        matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                        print(matching_bills.id)
                        print(f"Agent game number {game.number} matched with Result field: {matched_field[0]} for Agent: {game.agent}")
                        agent_package = AgentPackage.objects.get(agent=game.agent)
                        if game.LSK == "Super":
                            if matched_field[0] == 'first':
                                prize = ((agent_package.first_prize)*(game.count))
                                commission = ((agent_package.first_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                first_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'second':
                                prize = ((agent_package.second_prize)*(game.count))
                                commission = ((agent_package.second_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                second_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'third':
                                prize = ((agent_package.third_prize)*(game.count))
                                commission = ((agent_package.third_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                third_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="3",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'fourth':
                                prize = ((agent_package.fourth_prize)*(game.count))
                                commission = ((agent_package.fourth_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                fourth_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="4",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'fifth':
                                prize = ((agent_package.fifth_prize)*(game.count))
                                commission = ((agent_package.fifth_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                fifth_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="5",prize=prize,commission=commission,total=total)
                            else :
                                prize = ((agent_package.guarantee_prize)*(game.count))
                                commission = ((agent_package.guarantee_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                first_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="6",prize=prize,commission=commission,total=total)
                        elif game.LSK == "Box":
                            if matched_field[0] == 'first':
                                prize = ((agent_package.box_first_prize)*(game.count))
                                commission = ((agent_package.box_first_prize_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                box_first_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'A' and result.first.startswith(game_number[0]):
                    agent_package = AgentPackage.objects.get(agent=game.agent)
                    print(time,game.agent.user.id,game.id)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                    prize = ((agent_package.single1_prize)*(game.count))
                    commission = ((agent_package.single1_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'B' and result.first[1] == game.number[0]:
                    agent_package = AgentPackage.objects.get(agent=game.agent)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                    prize = ((agent_package.single1_prize)*(game.count))
                    commission = ((agent_package.single1_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'C' and result.first[2] == game.number[0]:
                    agent_package = AgentPackage.objects.get(agent=game.agent)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                    prize = ((agent_package.single1_prize)*(game.count))
                    commission = ((agent_package.single1_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'AB' and result.first[:2] == game.number[:2]:
                    agent_package = AgentPackage.objects.get(agent=game.agent)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                    prize = ((agent_package.double2_prize)*(game.count))
                    commission = ((agent_package.double2_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                elif game.LSK == 'BC' and result.first[1] == game.number[0] and result.first[-1] == game.number[-1]:
                    agent_package = AgentPackage.objects.get(agent=game.agent)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                    prize = ((agent_package.double2_prize)*(game.count))
                    commission = ((agent_package.double2_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                elif game.LSK == 'AC' and result.first[0] == game.number[0] and result.first[-1] == game.number[-1]:
                    agent_package = AgentPackage.objects.get(agent=game.agent)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.agent.user.id,agent_games__id=game.id)
                    prize = ((agent_package.double2_prize)*(game.count))
                    commission = ((agent_package.double2_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,agent=game.agent,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
        if dealer_games:
            for game in dealer_games:
                print("Game",game)
                print("Game id",game.id)
                game_number = game.number
                if game.LSK == 'Box' and game_number != result.first:
                    combinations = get_combinations(game_number)
                    print("Combinations:", combinations)
                    if len(combinations) == 6:
                        for combination in combinations:
                            if combination == result.first:
                                print(f"Combination {combination} matches the first field for Game {game.id}")
                                matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                                dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                                prize = ((dealer_package.box_series_prize)*(game.count))
                                commission = ((dealer_package.box_series_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                box_series_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                    elif len(combinations) == 3:
                        for combination in combinations:
                            if combination == result.first:
                                print(f"Combination {combination} matches the first field for Game {game.id}")
                                matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                                dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                                prize = ((dealer_package.box_series_prize)*(game.count))*2
                                commission = ((dealer_package.box_series_dc)*(game.count))*2
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                box_series_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                elif game.number in result.__dict__.values():
                    matched_field = [field for field, value in result.__dict__.items() if value == game.number]
                    if matched_field:
                        print("hello")
                        matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                        print(matching_bills.id)
                        print(f"Dealer game number {game.number} matched with Result field: {matched_field[0]} for Dealer: {game.dealer}")
                        dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                        if game.LSK == "Super":
                            if matched_field[0] == 'first':
                                prize = ((dealer_package.first_prize)*(game.count))
                                commission = ((dealer_package.first_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                first_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'second':
                                prize = ((dealer_package.second_prize)*(game.count))
                                commission = ((dealer_package.second_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                second_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'third':
                                prize = ((dealer_package.third_prize)*(game.count))
                                commission = ((dealer_package.third_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                third_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="3",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'fourth':
                                prize = ((dealer_package.fourth_prize)*(game.count))
                                commission = ((dealer_package.fourth_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                fourth_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="4",prize=prize,commission=commission,total=total)
                            elif matched_field[0] == 'fifth':
                                prize = ((dealer_package.fifth_prize)*(game.count))
                                commission = ((dealer_package.fifth_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                fifth_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="5",prize=prize,commission=commission,total=total)
                            else :
                                prize = ((dealer_package.guarantee_prize)*(game.count))
                                commission = ((dealer_package.guarantee_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                first_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="6",prize=prize,commission=commission,total=total)
                        elif game.LSK == "Box":
                            if matched_field[0] == 'first':
                                prize = ((dealer_package.box_first_prize)*(game.count))
                                commission = ((dealer_package.box_first_prize_dc)*(game.count))
                                total = ((prize)+(commission))
                                print(prize,commission,total)
                                box_first_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'A' and result.first.startswith(game_number[0]):
                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                    prize = ((dealer_package.single1_prize)*(game.count))
                    commission = ((dealer_package.single1_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'B' and result.first[1] == game.number[0]:
                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                    prize = ((dealer_package.single1_prize)*(game.count))
                    commission = ((dealer_package.single1_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'C' and result.first[2] == game.number[0]:
                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                    prize = ((dealer_package.single1_prize)*(game.count))
                    commission = ((dealer_package.single1_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="1",prize=prize,commission=commission,total=total)
                elif game.LSK == 'AB' and result.first[:2] == game.number[:2]:
                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                    prize = ((dealer_package.double2_prize)*(game.count))
                    commission = ((dealer_package.double2_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                elif game.LSK == 'BC' and result.first[1] == game.number[0] and result.first[-1] == game.number[-1]:
                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                    prize = ((dealer_package.double2_prize)*(game.count))
                    commission = ((dealer_package.double2_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
                elif game.LSK == 'AC' and result.first[0] == game.number[0] and result.first[-1] == game.number[-1]:
                    dealer_package = DealerPackage.objects.get(dealer=game.dealer)
                    matching_bills = Bill.objects.get(date=current_date,time_id=time,user=game.dealer.user.id,dealer_games__id=game.id)
                    prize = ((dealer_package.double2_prize)*(game.count))
                    commission = ((dealer_package.double2_dc)*(game.count))
                    total = ((prize)+(commission))
                    single_prize = Winning.objects.create(date=current_date,time=time,dealer=game.dealer,bill=matching_bills.id,number=game.number,LSK=game.LSK,count=game.count,position="2",prize=prize,commission=commission,total=total)
        return redirect('adminapp:index')
    print(field_values)
    context = {
        'timings' : times,
        'result' : last_result,
        'field_values' : field_values
    }
    return render(request,'adminapp/republish_results.html',context)

@login_required
@admin_required
def view_results(request):
    times = PlayTime.objects.filter().all().order_by('id')
    results = Result.objects.filter().last()
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
            'selected_time' : time
        }
        return render(request,'adminapp/view_results.html',context)
    context = {
        'times' : times,
        'results' : results
    }
    return render(request,'adminapp/view_results.html',context)

@login_required
@admin_required
def daily_report(request):
    agents = Agent.objects.filter().all()
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    print("this is working")
    total_winning = []
    total_balance = []
    total_c_amount = []
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        if select_dealer != 'all':
            agent_instance = Agent.objects.get(id=select_dealer)
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        print(select_dealer, select_time, from_date, to_date,"@@@")
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_dealer != 'all':
            if select_time != 'all':
                print("its agent")
                bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date],time_id=select_time).all()
                print(bills)
                for bill in bills:
                    print(bill.id,"this is the id")
                    winnings = Winning.objects.filter(Q(agent=agent_instance) | Q(dealer__agent=agent_instance),date__range=[from_date, to_date],time=select_time,bill=bill.id)
                    print(winnings)
                    total_winning = sum(winning.total for winning in winnings)
                    bill.win_amount += total_winning
                    if winnings != 0:
                        bill.total_d_amount = bill.total_c_amount - total_winning
                    else:
                        bill.total_d_amount = total_winning - bill.total_c_amount
                    total_winning = sum(bill.win_amount for bill in bills)
                    total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('total_c_amount'))
                context = {
                        'agents' : agents,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                return render(request,'adminapp/daily_report.html',context)
            else:
                print("its agent")
                bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date]).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(Q(agent=agent_instance) | Q(dealer__agent=agent_instance),bill=bill.id,date__range=[from_date, to_date])
                    print(winnings)
                    print("hello")
                    total_winning = sum(winning.total for winning in winnings)
                    print(total_winning)
                    bill.win_amount += total_winning
                    if winnings != 0:
                        bill.total_d_amount = bill.total_c_amount - total_winning
                    else:
                        bill.total_d_amount = total_winning - bill.total_c_amount
                    total_winning = sum(bill.win_amount for bill in bills)
                    total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('total_c_amount'))
                context = {
                        'agents' : agents,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                return render(request,'adminapp/daily_report.html',context)
        else:
            if select_time != 'all':
                print("its agent")
                bills = Bill.objects.filter(date__range=[from_date, to_date],time_id=select_time).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(date__range=[from_date, to_date],bill=bill.id,time=select_time)
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
                        'agents' : agents,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : 'all',
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                return render(request,'adminapp/daily_report.html',context)
            else:
                bills = Bill.objects.filter(date__range=[from_date, to_date]).all()
                print(bills)
                print("***")
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
                select_dealer = 'all'
                select_time = 'all'
                context = {
                    'agents' : agents,
                    'times' : times,
                    'dealer_bills' : bills,
                    'total_c_amount': total_c_amount,
                    'total_winning' : total_winning,
                    'total_balance' : total_balance,
                    'selected_dealer' : select_dealer,
                    'selected_time' : select_time,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/daily_report.html',context)
    else:
        bills = Bill.objects.filter(date=current_date).all()
        print(bills)
        print("###")
        for bill in bills:
            winnings = Winning.objects.filter(bill=bill.id,date=current_date)
            print(winnings)
            total_winning = sum(winning.total for winning in winnings)
            bill.win_amount += total_winning
            if winnings != 0:
                bill.total_d_amount = bill.total_c_amount - total_winning
            else:
                bill.total_d_amount = total_winning - bill.total_c_amount
            total_winning = sum(bill.win_amount for bill in bills)
            total_balance = sum(bill.total_d_amount for bill in bills)
        total_c_amount = Bill.objects.filter(date=current_date).aggregate(total_c_amount=Sum('total_c_amount'))
        select_dealer = 'all'
        select_time = 'all'
        context = {
            'agents' : agents,
            'times' : times,
            'dealer_bills' : bills,
            'total_c_amount': total_c_amount,
            'total_winning' : total_winning,
            'total_balance' : total_balance,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
        }
        return render(request,'adminapp/daily_report.html',context)

@login_required
@admin_required
def countwise_report(request):
    ist = pytz.timezone('Asia/Kolkata')
    times = PlayTime.objects.filter().all().order_by('id')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    agent_games = AgentGame.objects.filter(date=current_date).all()
    dealer_games = DealerGame.objects.filter(date=current_date).all()
    totals_agent = AgentGame.objects.filter(date=current_date).aggregate(total_count=Sum('count'))
    totals_dealer = DealerGame.objects.filter(date=current_date).aggregate(total_count=Sum('count'))
    total_count = {'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0)}
    lsk_value = []
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        lsk = request.POST.get('select-lsk')
        select_time = request.POST.get('time')
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
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
        if select_time != 'all':
            if lsk != 'all':
                agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value)
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value)
                totals_agent = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'))
                totals_dealer = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'))
                total_count = {'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0)}
            else:
                agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time)
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time)
                totals_agent = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'))
                totals_dealer = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'))
                total_count = {'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0)}
            context = {
                'agent_games' : agent_games,
                'dealer_games' : dealer_games,
                'selected_lsk' : lsk,
                'selected_from' : from_date,
                'selected_to' : to_date,
                'total_count' : total_count,
                'selected_time' : select_time,
                'times' : times,
                'selected_game_time' : selected_game_time,
            }
            return render(request,'adminapp/countwise_report.html',context)
        else:
            if lsk != 'all':
                agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value)
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value)
                totals_agent = AgentGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'))
                totals_dealer = DealerGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'))
                total_count = {'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0)}
            else:
                agent_games = AgentGame.objects.filter(date__range=[from_date, to_date])
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date])
                totals_agent = AgentGame.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'))
                totals_dealer = DealerGame.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'))
                total_count = {'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0)}
            context = {
                'agent_games' : agent_games,
                'dealer_games' : dealer_games,
                'selected_lsk' : lsk,
                'selected_from' : from_date,
                'selected_to' : to_date,
                'total_count' : total_count,
                'selected_time' : select_time,
                'times' : times,
                'selected_game_time' : selected_game_time,
            }
            return render(request,'adminapp/countwise_report.html',context)
    context = {
        'agent_games' : agent_games,
        'dealer_games' : dealer_games,
        'total_count' : total_count,
        'times' : times,
        'selected_time' : 'all'
    }
    return render(request,'adminapp/countwise_report.html',context)

@login_required
@admin_required
def countsales_report(request):
    times = PlayTime.objects.filter().all().order_by('id')
    agents = Agent.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    lsk_value1 = ['A','B','C']
    lsk_value2 = ['AB','BC','AC']
    agent_super = AgentGame.objects.filter(date=current_date, LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_super = DealerGame.objects.filter(date=current_date, LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    agent_box = AgentGame.objects.filter(date=current_date, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_box = DealerGame.objects.filter(date=current_date, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    agent_single = AgentGame.objects.filter(date=current_date, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_single = DealerGame.objects.filter(date=current_date, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    agent_double = AgentGame.objects.filter(date=current_date, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
    dealer_double = DealerGame.objects.filter(date=current_date, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
        select_agent = request.POST.get('select-agent')
        select_time = request.POST.get('time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_agent != 'all':
            if select_time != 'all':
                agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_super = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),time=select_time,date__range=[from_date, to_date], LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_box = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),time=select_time,date__range=[from_date, to_date], LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_single = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),time=select_time,date__range=[from_date, to_date], LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_double = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),time=select_time,date__range=[from_date, to_date], LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
                    'agents' : agents,
                    'selected_agent' : select_agent,
                    'selected_time' : select_time,
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'single_totals' : single_totals,
                    'double_totals' : double_totals,
                    'totals' : totals,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/countsales_report.html',context)
            else:
                agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_super = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),date__range=[from_date, to_date], LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_box = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),date__range=[from_date, to_date], LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_single = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),date__range=[from_date, to_date], LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent__user=select_agent, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_double = DealerGame.objects.filter(Q(dealer__agent__user=select_agent),date__range=[from_date, to_date], LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
                    'agents' : agents,
                    'selected_agent' : select_agent,
                    'selected_time' : 'all',
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'single_totals' : single_totals,
                    'double_totals' : double_totals,
                    'totals' : totals,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/countsales_report.html',context)
        else:
            if select_time != 'all':
                agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_super = DealerGame.objects.filter(time=select_time,date__range=[from_date, to_date], LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_box = DealerGame.objects.filter(time=select_time,date__range=[from_date, to_date], LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_single = DealerGame.objects.filter(time=select_time,date__range=[from_date, to_date], LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_double = DealerGame.objects.filter(time=select_time,date__range=[from_date, to_date], LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
                    'agents' : agents,
                    'selected_agent' : 'all',
                    'selected_time' : select_time,
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'single_totals' : single_totals,
                    'double_totals' : double_totals,
                    'totals' : totals,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/countsales_report.html',context)
            else:
                agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date], LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_box = AgentGame.objects.filter(date__range=[from_date, to_date], LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date], LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_single = AgentGame.objects.filter(date__range=[from_date, to_date], LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date], LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                agent_double = AgentGame.objects.filter(date__range=[from_date, to_date], LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date], LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
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
                    'agents' : agents,
                    'selected_agent' : 'all',
                    'selected_time' : 'all',
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'single_totals' : single_totals,
                    'double_totals' : double_totals,
                    'totals' : totals,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/countsales_report.html',context)
    context = {
        'times' : times,
        'agents' : agents,
        'selected_agent' : 'all',
        'selected_time' : 'all',
        'super_totals' : super_totals,
        'box_totals' : box_totals,
        'single_totals' : single_totals,
        'double_totals' : double_totals,
        'totals' : totals,
    }
    return render(request,'adminapp/countsales_report.html',context) 

@login_required
@admin_required
def winning_report(request):
    times = PlayTime.objects.filter().all().order_by('id')
    print(times)
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    winnings = []
    totals = []
    aggregated_winnings = []
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_time = request.POST.get('time')
        select_agent = request.POST.get('select-agent')
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        print(from_date,to_date,select_time,select_agent)
        agents = Agent.objects.filter().all()
        if select_time != 'all':
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time)
                print(winnings)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'aggr' : aggregated_winnings,
                    'selected_time' : select_time,
                    'selected_agent' : select_agent,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date],time=select_time)
                print(winnings)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'aggr' : aggregated_winnings,
                    'selected_time' : select_time,
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
            return render(request,'adminapp/winning_report.html',context)
        else:
            print("time is all")
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date])
                print(winnings)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'aggr' : aggregated_winnings,
                    'selected_time' : 'all',
                    'selected_agent' : select_agent,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date])
                print(winnings)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'aggr' : aggregated_winnings,
                    'selected_time' : 'all',
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
            return render(request,'adminapp/winning_report.html',context)
    else:
        try:
            matching_play_times = Winning.objects.filter().last()
            agents = Agent.objects.filter().all()
            winnings = Winning.objects.filter(date=current_date,time=matching_play_times.time)
            aggregated_winnings = winnings.values('LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                position=F('position'),
            )
            print(aggregated_winnings)
            totals = Winning.objects.filter(date=current_date,time=matching_play_times.time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
        except:
            pass
        context = {
            'times' : times,
            'agents' : agents,
            'winnings' : winnings,
            'totals' : totals,
            'aggr' : aggregated_winnings,
            'selected_time' : 'all',
            'selected_agent' : 'all'
        }
        return render(request,'adminapp/winning_report.html',context) 

@login_required
@admin_required
def winningcount_report(request):
    times = PlayTime.objects.filter().all().order_by('id')
    agents = Agent.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    winnings = Winning.objects.filter(date=current_date).all()
    totals = Winning.objects.filter(date=current_date).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
    if request.method == 'POST':
        select_time = request.POST.get('time')
        select_agent = request.POST.get('select-agent')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_time != 'all':
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time)
                totals = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : select_time,
                    'selected_agent' : select_agent,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/winningcount_report.html',context)
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date],time=select_time)
                totals = Winning.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : select_time,
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/winningcount_report.html',context)
        else:
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date])
                totals = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : 'all',
                    'selected_agent' : select_agent,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/winningcount_report.html',context)
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date])
                totals = Winning.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : 'all',
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'adminapp/winningcount_report.html',context)
    context = {
        'times' : times,
        'agents' : agents,
        'winnings' : winnings,
        'totals' : totals,
        'selected_agent' : 'all',
        'selected_time' : 'all'
    }
    return render(request,'adminapp/winningcount_report.html',context)

@login_required
@admin_required
def blocked_number_times(request):
    times = PlayTime.objects.filter().all().order_by('id')
    context = {
        'times' : times
    }
    return render(request,'adminapp/blocked_number_times.html',context)

@login_required
@admin_required
def blocked_numbers(request,id):
    time = PlayTime.objects.get(id=id)
    blocked = BlockedNumber.objects.filter(time=time)
    context = {
        'time' : time,
        'blocked' : blocked
    }
    return render(request,'adminapp/blocked_numbers.html',context)

@login_required
@admin_required
def edit_bill_times(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    matching_play_times = PlayTime.objects.filter(Q(start_time__lte=current_time) & Q(end_time__gte=current_time)).order_by('id')
    context = {
        'times' : matching_play_times
    }
    return render(request,'adminapp/edit_bill_times.html',context)

@login_required
@admin_required
def edit_bill(request,id):
    agents = Agent.objects.filter().all()
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    try:
        time = PlayTime.objects.get(id=id)
        print(matching_play_times,"matching")
    except:
        matching_play_times = []
    if request.method == 'POST':
        search_dealer = request.POST.get('agent-select')
        print(search_dealer,"the user id")
        if search_dealer == 'all':
            bills = Bill.objects.filter(time_id=time,date=current_date).all()
            totals = Bill.objects.filter(time_id=time,date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            agents = Agent.objects.filter().all()
            context = {
                'bills' : bills,
                'agents' : agents,
                'totals': totals,
                'selected_agent' : search_dealer
            } 
            return render(request,'adminapp/edit_bill.html',context)
        else:
            agent_instance = Agent.objects.get(id=search_dealer)
        try:
            bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),time_id=time,date=current_date).all()
            totals = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),time_id=time,date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            agents = Agent.objects.filter().all()
            context = {
                'bills' : bills,
                'agents' : agents,
                'totals': totals,
                'selected_agent' : search_dealer
            } 
            return render(request,'adminapp/edit_bill.html',context)
        except:
            bills = []
            totals = []
            agents = Agent.objects.filter().all()
            context = {
                'bills' : bills,
                'agents' : agents,
                'totals': totals,
                'selected_agent' : search_dealer
            } 
            return render(request,'adminapp/edit_bill.html',context)
    else:
        try:
            print("this")
            bills = Bill.objects.filter(date=current_date,time_id=time).all()
            print(bills)
            totals = Bill.objects.filter(date=current_date,time_id=time).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            agents = Agent.objects.filter().all()
            context = {
                'bills' : bills,
                'agents' : agents,
                'totals': totals,
                'selected_agent' : 'all'
            } 
            return render(request,'adminapp/edit_bill.html',context)
        except:
            bills = []
            totals = []
            agents = Agent.objects.filter().all()
            context = {
                'bills' : bills,
                'agents' : agents,
                'totals': totals,
                'selected_agent' : 'all'
            } 
    return render(request,'adminapp/edit_bill.html',context)

@login_required
@admin_required
def delete_bill(request,id):
    print(id)
    bill = Bill.objects.get(id=id)
    user_obj = bill.user
    print(user_obj)
    time_id = bill.time_id
    print(time_id,"time")
    date = bill.date
    print(date,"date")
    if AgentGame.objects.filter(agent__user=user_obj.id,time=time_id,date=date):
        games = AgentGame.objects.filter(agent__user=user_obj.id,time=time_id,date=date).all()
    else:
        games = DealerGame.objects.filter(dealer__user=user_obj.id,time=time_id,date=date).all()
    print(games)
    context = {
        'bill' : bill,
        'games' : games
    }
    return render(request,'adminapp/delete_bill.html',context)

@login_required
@admin_required
def deleting_bill(request,id):
    bill = get_object_or_404(Bill,id=id)
    print(bill,"deleting bill")
    bill.delete()
    return redirect('adminapp:index')

@login_required
@admin_required
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
    return redirect('adminapp:delete_bill',id=bill_id)    

@login_required
@admin_required
def payment_report(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    agents = Agent.objects.filter().all()
    collections = CollectionReport.objects.filter(date=current_date).all()
    from_agent_total = CollectionReport.objects.filter(date=current_date,from_or_to='from-agent').aggregate(from_agent=Sum('amount'))
    print(from_agent_total)
    to_agent_total = CollectionReport.objects.filter(date=current_date,from_or_to='to-agent').aggregate(to_agent=Sum('amount'))
    print(to_agent_total)
    from_agent_amount = from_agent_total['from_agent'] if from_agent_total['from_agent'] else 0
    to_agent_amount = to_agent_total['to_agent'] if to_agent_total['to_agent'] else 0
    profit_or_loss = from_agent_amount - to_agent_amount
    print(profit_or_loss)
    for collection in collections:
        print(collection.from_or_to,"this is")
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_agent = request.POST.get('select-agent')
        from_or_to = request.POST.get('from-to')
        if select_agent != 'all':
            if from_or_to != 'all' and from_or_to == 'from-agent':
                collections = CollectionReport.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,from_or_to='from-agent').all()
                print(from_date, to_date, select_agent, from_or_to)
                print(collections)
                from_agent_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = from_agent_amount['amount'] if from_agent_amount['amount'] else 0
                print(profit_or_loss, "hello")
                print(from_or_to,"$$$$$$$$$")
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'adminapp/payment_report.html', context)
            if from_or_to != 'all' and from_or_to == 'to-agent':
                collections = CollectionReport.objects.filter(date__range=[from_date, to_date],agent__user=select_agent,from_or_to='to-agent').all()
                print(from_date, to_date, select_agent, from_or_to)
                print(collections)
                to_agent_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_agent_amount['amount'] if to_agent_amount['amount'] else 0
                profit_or_loss = -profit_or_loss
                print(profit_or_loss, "hello")
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'adminapp/payment_report.html', context)
            else:
                collections = CollectionReport.objects.filter(date__range=[from_date, to_date],agent__user=select_agent).all()
                print(from_date, to_date, select_agent, from_or_to)
                print(collections)
                to_agent_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_agent_amount['amount'] if to_agent_amount['amount'] else 0
                print(profit_or_loss, "hello")
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'adminapp/payment_report.html', context)
        else:
            if from_or_to != 'all' and from_or_to == 'from-agent':
                collections = CollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='from-agent').all()
                print(from_date, to_date, select_agent, from_or_to)
                print(collections)
                from_agent_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = from_agent_amount['amount'] if from_agent_amount['amount'] else 0
                print(profit_or_loss, "hello")
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'adminapp/payment_report.html', context)
            if from_or_to != 'all' and from_or_to == 'to-agent':
                collections = CollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='to-agent').all()
                print(from_date, to_date, select_agent, from_or_to)
                print(collections)
                to_agent_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_agent_amount['amount'] if to_agent_amount['amount'] else 0
                profit_or_loss = -profit_or_loss
                print(profit_or_loss, "hello")
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'adminapp/payment_report.html', context)
            else:
                collections = CollectionReport.objects.filter(date__range=[from_date, to_date]).all()
                from_agent_total = CollectionReport.objects.filter(date=current_date,from_or_to='from-agent').aggregate(from_agent=Sum('amount'))
                print(from_agent_total)
                to_agent_total = CollectionReport.objects.filter(date=current_date,from_or_to='to-agent').aggregate(to_agent=Sum('amount'))
                print(to_agent_total)
                from_agent_amount = from_agent_total['from_agent'] if from_agent_total['from_agent'] else 0
                to_agent_amount = to_agent_total['to_agent'] if to_agent_total['to_agent'] else 0
                profit_or_loss = from_agent_amount - to_agent_amount
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'adminapp/payment_report.html', context)
    else:
        context = {
            'agents' : agents,
            'collections' : collections,
            'selected_agent' : 'all',
            'profit_or_loss' : profit_or_loss,
            'from_or_to' : 'all'
        }
    return render(request,'adminapp/payment_report.html',context)

@login_required
@admin_required
def add_collection(request):
    agents = Agent.objects.filter().all()
    if request.method == 'POST':
        date = request.POST.get('date')
        select_agent = request.POST.get('select-agent')
        agent_instance = Agent.objects.get(id=select_agent)
        from_or_to = request.POST.get('select-collection')
        amount = request.POST.get('amount')
        print(select_agent,from_or_to,amount)
        collection = CollectionReport.objects.create(agent=agent_instance,date=date,from_or_to=from_or_to,amount=amount)
        return redirect('adminapp:payment_report')
    context = {
        'agents' : agents,
    }
    return render(request,'adminapp/add_collection.html',context)

@login_required
@admin_required
def balance_report(request):
    agents = Agent.objects.filter().all()
    collection = CollectionReport.objects.filter().all()
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    report_data = []
    total_balance = []
    if request.method == 'POST':
        select_agent = request.POST.get('select-agent')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_agent != 'all':
            agent_instance = Agent.objects.get(id=select_agent)
            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date], agent=select_agent)
            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], agent=select_agent)
            collection = CollectionReport.objects.filter(date__range=[from_date, to_date], agent=select_agent)
            winning = Winning.objects.filter(Q(agent=select_agent) | Q(dealer__agent=select_agent),date__range=[from_date, to_date]).aggregate(total_winning=Sum('total'))['total_winning'] or 0
            agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
            dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
            from_agent = collection.filter(from_or_to='from-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            to_agent = collection.filter(from_or_to='to-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            total_collection_amount = from_agent - to_agent
            total_d_amount = float(agent_total_d_amount + dealer_total_d_amount)
            print(total_d_amount)
            win_amount = float(winning)
            balance =  float(winning) - float(total_d_amount) + float(total_collection_amount)
            if total_d_amount:
                report_data.append({
                    'date' : current_date,
                    'agent': agent_instance,
                    'total_d_amount': total_d_amount,
                    'from_or_to' : total_collection_amount,
                    'balance' : balance,
                    'win_amount' : win_amount
                })
            total_balance = sum(entry['balance'] for entry in report_data)
            context = {
                'agents' : agents,
                'selected_agent' : select_agent,
                'report_data': report_data,
                'total_balance' : total_balance,
                'selected_from' : from_date,
                'selected_to' : to_date
            }
            return render(request, 'adminapp/balance_report.html',context)
        else:
            for agent in agents:
                print(agent)
                agent_games = AgentGame.objects.filter(date__range=[from_date, to_date], agent=agent)
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], agent=agent)
                collection = CollectionReport.objects.filter(date__range=[from_date, to_date], agent=agent)
                winning = Winning.objects.filter(Q(agent=agent) | Q(dealer__agent=agent),date__range=[from_date, to_date]).aggregate(total_winning=Sum('total'))['total_winning'] or 0
                print(winning)
                agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
                dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
                from_agent = collection.filter(from_or_to='from-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
                to_agent = collection.filter(from_or_to='to-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
                total_collection_amount = from_agent - to_agent
                print(total_collection_amount, "collection")
                total_d_amount = float(agent_total_d_amount + dealer_total_d_amount)
                print(total_d_amount)
                win_amount = float(winning)
                balance =  float(winning) - float(total_d_amount) + float(total_collection_amount)
                print(f"Agent: {agent}, Total D Amount: {total_d_amount}")
                print(balance)
                if total_d_amount:
                    report_data.append({
                        'date' : current_date,
                        'agent': agent,
                        'total_d_amount': total_d_amount,
                        'from_or_to' : total_collection_amount,
                        'balance' : balance,
                        'win_amount' : win_amount,
                    })
                    print(report_data)
            total_balance = sum(entry['balance'] for entry in report_data)
            context = {
                'agents' : agents,
                'selected_agent' : 'all',
                'report_data': report_data,
                'total_balance' : total_balance,
                'selected_from' : from_date,
                'selected_to' : to_date
            }
            return render(request, 'adminapp/balance_report.html',context)
    for agent in agents:
        print(agent)
        agent_games = AgentGame.objects.filter(date=current_date, agent=agent)
        dealer_games = DealerGame.objects.filter(date=current_date, agent=agent)
        collection = CollectionReport.objects.filter(date=current_date, agent=agent)
        winning = Winning.objects.filter(Q(agent=agent) | Q(dealer__agent=agent),date=current_date).aggregate(total_winning=Sum('total'))['total_winning'] or 0
        print(winning)
        agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
        dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
        from_agent = collection.filter(from_or_to='from-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        to_agent = collection.filter(from_or_to='to-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        total_collection_amount = from_agent - to_agent
        print(total_collection_amount, "collection")
        total_d_amount = float(agent_total_d_amount + dealer_total_d_amount)
        win_amount = float(winning)
        print(total_d_amount)
        balance = float(winning) - float(total_d_amount) + float(total_collection_amount)
        print(f"Agent: {agent}, Total D Amount: {total_d_amount}")
        print(balance)
        if total_d_amount:
            report_data.append({
                'date' : current_date,
                'agent': agent,
                'total_d_amount': total_d_amount,
                'from_or_to' : total_collection_amount,
                'balance' : balance,
                'win_amount' : win_amount
            })
            print(report_data)
    total_balance = sum(entry['balance'] for entry in report_data)
    context = {
        'agents' : agents,
        'selected_agent' : 'all',
        'report_data': report_data,
        'total_balance' : total_balance
    }
    return render(request, 'adminapp/balance_report.html',context)

@login_required
@admin_required
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
    return render(request,'adminapp/change_password.html',{'form':form})

@login_required
@admin_required
def new_block(request,id):
    time = PlayTime.objects.get(id=id)
    if request.method == 'POST':
        lsk = request.POST.get('select-lsk')
        number = request.POST.get('numberInput')
        count = request.POST.get('countInput')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        print(lsk)
        print(number)
        block_number = BlockedNumber.objects.create(time=time,from_date=from_date,to_date=to_date,LSK=lsk,number=number,count=count)
        return redirect('adminapp:blocked_numbers',id=id)
    return render(request,'adminapp/new_block.html')

@login_required
@admin_required
def edit_block(request,id,time_id):
    block = BlockedNumber.objects.get(id=id)
    time = PlayTime.objects.get(id=time_id)
    print(block)
    if request.method == 'POST':
        lsk = request.POST.get('select-lsk')
        number = request.POST.get('numberInput')
        count = request.POST.get('countInput')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        print(lsk)
        print(number)
        block_number = BlockedNumber.objects.filter(id=id).update(time=time_id,from_date=from_date,to_date=to_date,LSK=lsk,number=number,count=count)
        return redirect('adminapp:blocked_numbers',id=time_id)
    context = {
        'block' : block
    }
    return render(request,'adminapp/edit_blocked_number.html',context)

@login_required
@admin_required
def delete_block(request,id,time_id):
    block = get_object_or_404(BlockedNumber,id=id)
    time = PlayTime.objects.get(id=time_id)
    block.delete()
    return redirect('adminapp:blocked_numbers',id=time_id)

@login_required
@admin_required
def settings(request):
    times = PlayTime.objects.filter().all().order_by('id')
    context = {
        'times' : times
    }
    return render(request,'adminapp/settings.html',context)

@login_required
@admin_required
def lsk_limit(request,id):
    time = PlayTime.objects.get(id=id)
    if request.method == 'POST':
        super = request.POST.get('super')
        box = request.POST.get('box')
        ab = request.POST.get('ab')
        bc = request.POST.get('bc')
        ac = request.POST.get('ac')
        a = request.POST.get('a')
        b = request.POST.get('b')
        c = request.POST.get('c')
        if GameLimit.objects.filter(time=time):
            limit = GameLimit.objects.filter(time=time).update(super=super,box=box,ab=ab,bc=bc,ac=ac,a=a,b=b,c=c)
            print("limit updated")
        else:
            limit = GameLimit.objects.create(time=time,super=super,box=box,ab=ab,bc=bc,ac=ac,a=a,b=b,c=c)
            print("limit set")
        return redirect('adminapp:index')
    try:
        try:
            limit = GameLimit.objects.get(time=time)
        except:
            limit = []
        context = {
            'monitor' : limit,
        }
        return render(request,'adminapp/set_monitor.html',context)
    except:
        pass
    return render(request,'adminapp/LSK_limit.html')

def get_combinations(input_number):
    number_str = str(input_number).zfill(3)
    result = []
    
    if len(number_str) != 3:
        return result
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if i != j and i != k and j != k:
                    combination = number_str[i] + number_str[j] + number_str[k]
                    if combination not in result:
                        result.append(combination)
    
    return result







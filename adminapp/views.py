import datetime
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from website.decorators import dealer_required, agent_required, admin_required
from website.forms import LoginForm,UserUpdateForm
from website.forms import AgentRegistration
from website.models import User,Agent,Dealer
from agent.models import AgentGame, DealerPackage
from dealer.models import DealerGame
from .models import PlayTime, AgentPackage, Result, Winning, CollectionReport, Monitor, CombinedGame
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as pytz_timezone
import pytz
from django.utils import timezone
from agent.models import Bill
from django.db.models import Sum
from django.db.models import Q
import itertools
from django.db.models import F
from collections import defaultdict


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
            return redirect("adminapp:view_agent")
    return render(request,'adminapp/add_agent.html',{"login_form": login_form, "agent_form": agent_form})

def view_agent(request):
    agents = Agent.objects.filter().all()
  
    context = {
        'agents' : agents,
       
    }
    return render(request,'adminapp/view_agent.html',context)

def edit_agent(request,id):
    agent = get_object_or_404(Agent, id=id)
    user = agent.user
    if request.method == "POST":
        agent_form = AgentRegistration(request.POST, instance=agent)
        login_form = UserUpdateForm(request.POST, instance=user)
        if agent_form.is_valid() and login_form.is_valid():
            agent_form.save()
            messages.info(request, "Agent Updated Successfully")
            return redirect("adminapp:view_agent")
    else:
        agent_form = AgentRegistration(instance=agent)
        login_form = UserUpdateForm(instance=user)
    return render(request, 'adminapp/edit_agent.html', {'agent': agent,'agent_form': agent_form,'login_form':login_form})

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

def package(request):
    packages = AgentPackage.objects.filter().all()
    print(packages)
    context = {
        'packages' : packages
    }
    return render(request,'adminapp/package.html',context)

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
            return redirect('adminapp:package')
    context = {
        'agents' : agent
    }
    return render(request,'adminapp/new_package.html',context)

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

def delete_package(request,id):
    package = AgentPackage.objects.get(id=id)
    package.delete()
    return redirect('adminapp:package')

def add_result(request):
    timings = PlayTime.objects.filter().all()
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

def sales_report(request):
    agents = Agent.objects.filter().all()
    times = PlayTime.objects.filter().all()
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
        elif lsk_value == 'box':
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
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value)
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(Q(dealer__agent=agent_instance),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value)
                    print(dealer_games)
                    bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date],time_id=select_time).distinct()
                    print(bills)
                    agent_games_total = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    dealer_games_total = DealerGame.objects.filter(Q(dealer__agent=agent_instance),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                    totals = {
                        'total_count': (agent_games_total['total_count'] or 0) + (dealer_games_total['total_count'] or 0),
                        'total_c_amount': (agent_games_total['total_c_amount'] or 0) + (dealer_games_total['total_c_amount'] or 0),
                        'total_d_amount': (agent_games_total['total_d_amount'] or 0) + (dealer_games_total['total_d_amount'] or 0)
                    }
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],time=select_time)
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,dealer__agent=agent_instance)
                    print(dealer_games)
                    bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date],time_id=select_time).distinct()
                    print(bills)
                    totals = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date],time_id=select_time).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                    }
                    return render(request, 'adminapp/sales_report.html', context)
            else:
                #time not selected, agent selected
                if lsk != 'all':
                    #lsk selected, time not selected, agent selected
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date],LSK__in=lsk_value)
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(dealer__agent=agent_instance,date__range=[from_date, to_date],LSK__in=lsk_value)
                    print(dealer_games)
                    bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date]).distinct()
                    print(bills)
                    totals = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date]).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    #time,lsk not selected, agent selected
                    agent_games = AgentGame.objects.filter(agent=agent_instance,date__range=[from_date, to_date])
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_instance)
                    print(dealer_games)
                    bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date]).distinct()
                    print(bills)
                    totals = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date]).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : select_dealer,
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                    }
                    return render(request, 'adminapp/sales_report.html', context)
        else:
            if select_time != 'all':
                if lsk != 'all':
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value)
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value)
                    print(dealer_games)
                    bills = Bill.objects.filter(Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date],time_id=select_time).distinct()
                    print(bills)
                    totals = Bill.objects.filter(Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date],time_id=select_time).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time)
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],time=select_time)
                    print(dealer_games)
                    bills = Bill.objects.filter(date__range=[from_date, to_date],time_id=select_time).distinct()
                    print(bills)
                    totals = Bill.objects.filter(date__range=[from_date, to_date],time_id=select_time).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                    }
                    return render(request, 'adminapp/sales_report.html', context)
            else:
                #time not selected, agent selected
                if lsk != 'all':
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value)
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],LSK__in=lsk_value)
                    print(dealer_games)
                    bills = Bill.objects.filter(Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date]).distinct()
                    print(bills)
                    totals = Bill.objects.filter(Q(agent_games__LSK__in=lsk_value) | Q(dealer_games__LSK__in=lsk_value),date__range=[from_date, to_date]).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : lsk,
                    }
                    return render(request, 'adminapp/sales_report.html', context)
                else:
                    #time,lsk not selected, agent selected
                    agent_games = AgentGame.objects.filter(date__range=[from_date, to_date])
                    print(agent_games)
                    dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date])
                    print(dealer_games)
                    bills = Bill.objects.filter(date__range=[from_date, to_date]).distinct()
                    print(bills)
                    totals = Bill.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
                    context = {
                        'agents' : agents,
                        'times': times,
                        'bills' : bills,
                        'totals' : totals,
                        'selected_dealer' : 'all',
                        'selected_time' : 'all',
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_lsk' : 'all',
                    }
                    return render(request, 'adminapp/sales_report.html', context)
    else:
        print("this is working")
        agent_games = AgentGame.objects.filter(date=current_date).all()
        dealer_games = DealerGame.objects.filter(date=current_date).all()
        bills = Bill.objects.filter(date=current_date).all()
        totals = Bill.objects.filter(date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
        select_dealer = 'all'
        select_time = 'all'
        context = {
            'agents' : agents,
            'times' : times,
            'bills' : bills,
            'totals' : totals,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
            'agent_games' : agent_games,
            'dealer_games' : dealer_games
        }
        return render(request,'adminapp/sales_report.html',context)

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

def change_time(request):
    try:
        times = PlayTime.objects.filter().all()
    except:
        pass
    context = {
        'times' : times,
    }
    return render(request,'adminapp/change_time.html',context)

def change_game_time(request,id):
    time = get_object_or_404(PlayTime,id=id)

    print(time)
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        print(start_time)
        end_time = request.POST.get('end_time')
        print(end_time)
        set_time = PlayTime.objects.filter(id=id).update(start_time=start_time,end_time=end_time)
        return redirect('adminapp:change_time')
    return render(request,'adminapp/change_game_time.html')



def monitor(request):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_date)
    matching_play_times = []
    try:
        matching_play_times = PlayTime.objects.get(start_time__lte=current_time, end_time__gte=current_time)
        print(matching_play_times.id)
    except:
        pass
    agent_games = AgentGame.objects.filter(date=current_date,time=matching_play_times)
    dealer_games = DealerGame.objects.filter(date=current_date,time=matching_play_times)
    set_monitor_limit = Monitor.objects.filter().last()
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

    combined_games = {}

    # Iterate through agent games
    for agent_game in agent_games:
        key = (agent_game.LSK, agent_game.number)
        if key in combined_games:
            combined_games[key]['count'] += agent_game.count
            combined_games[key]['combined'] = True
        else:
            combined_games[key] = {
                'LSK': agent_game.LSK,
                'number': agent_game.number,
                'count': agent_game.count,
                'combined': False,
                'user': agent_game.agent.user,
            }

    # Combine dealer games
    for dealer_game in dealer_games:
        key = (dealer_game.LSK, dealer_game.number)
        if key in combined_games:
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

    # Calculate remaining_limit and handle clearing
    for game in combined_games.values():
        LSK = game['LSK']
        if LSK in limits:
            limit = limits[LSK]
            count = game['count']
            game['remaining_limit'] = count - limit
            if game['remaining_limit'] <= 0:
                game['remaining_limit'] = 0

    print(combined_games)

    context = {
        'agent_games' : agent_games,
        'dealer_games' : dealer_games,
    }
    return render(request,'adminapp/monitor.html',context)

def set_monitor(request):
    if request.method == 'POST':
        super = request.POST.get('super')
        box = request.POST.get('box')
        ab = request.POST.get('ab')
        bc = request.POST.get('bc')
        ac = request.POST.get('ac')
        a = request.POST.get('a')
        b = request.POST.get('b')
        c = request.POST.get('c')
        monitor = Monitor.objects.create(super=super,box=box,ab=ab,bc=bc,ac=ac,a=a,b=b,c=c)
        print("monitor set")
        return redirect('adminapp:monitor')
    try:
        monitor = Monitor.objects.filter().last()
        context = {
            'monitor' : monitor
        }
        return render(request,'adminapp/set_monitor.html',context)
    except:
        pass
    return render(request,'adminapp/set_monitor.html')

def republish_results(request):
    times = PlayTime.objects.filter().all()
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
            'feild1': last_result.field1,
            'feild2': last_result.field2,
            'feild3': last_result.field3,
            'feild4': last_result.field4,
            'feild5': last_result.field5,
            'feild6': last_result.field6,
            'feild7': last_result.field7,
            'feild8': last_result.field8,
            'feild9': last_result.field9,
            'feild10': last_result.field10,
            'feild11': last_result.field11,
            'feild12': last_result.field12,
            'feild13': last_result.field13,
            'feild14': last_result.field14,
            'feild15': last_result.field15,
            'feild16': last_result.field16,
            'feild17': last_result.field17,
            'feild18': last_result.field18,
            'feild19': last_result.field19,
            'feild20': last_result.field20,
            'feild21': last_result.field21,
            'feild22': last_result.field22,
            'feild23': last_result.field23,
            'feild24': last_result.field24,
            'feild25': last_result.field25,
            'feild26': last_result.field26,
            'feild27': last_result.field27,
            'feild28': last_result.field28,
            'feild29': last_result.field29,
            'feild30': last_result.field30,
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
        result = Result.objects.update(date=current_date,time=time,first=first,second=second,third=third,fourth=fourth,fifth=fifth,field1=field1,field2=field2,field3=field3,field4=field4,field5=field5,field6=field6,field7=field7,field8=field8,field9=field9,field10=field10,field11=field11,field12=field12,field13=field13,field14=field14,field15=field15,field16=field16,field17=field17,field18=field18,field19=field19,field20=field20,field21=field21,field22=field22,field23=field23,field24=field24,field25=field25,field26=field26,field27=field27,field28=field28,field29=field29,field30=field30)
        messages.info(request, "Result re-published!")
        return redirect('adminapp:index')
    context = {
        'timings' : times,
        'result' : last_result,
        'field_values' : field_values
    }
    return render(request,'adminapp/republish_results.html',context)

def view_results(request):
    times = PlayTime.objects.filter().all()
    results = Result.objects.filter().last()
    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        results = Result.objects.filter(date=date,time=time).last()
        context = {
            'times' : times,
            'results' : results,
            'selected_date' : date,
        }
        return render(request,'adminapp/view_results.html',context)
    context = {
        'times' : times,
        'results' : results
    }
    return render(request,'adminapp/view_results.html',context)

def daily_report(request):
    agents = Agent.objects.filter().all()
    times = PlayTime.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    print("this is working")
    total_winning = []
    total_balance = []
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        agent_instance = Agent.objects.get(id=select_dealer)
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        print(select_dealer, select_time, from_date, to_date)
        if select_dealer != 'all':
            if select_time != 'all':
                print("its agent")
                bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date],time_id=select_time).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(Q(agent__user=select_dealer) | Q(dealer__agent__user=select_dealer),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                    print(winnings)
                    total_winning = sum(winning.prize for winning in winnings)
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
                    }
                    return render(request,'adminapp/daily_report.html',context)
            else:
                print("its agent")
                bills = Bill.objects.filter(Q(user__agent=agent_instance) | Q(user__dealer__agent=agent_instance),date__range=[from_date, to_date]).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(Q(agent__user=select_dealer) | Q(dealer__agent__user=select_dealer),bill=bill.id,date__range=[from_date, to_date])
                    print(winnings)
                    total_winning = sum(winning.prize for winning in winnings)
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
                    }
                    return render(request,'adminapp/daily_report.html',context)
        else:
            if select_time != 'all':
                print("its agent")
                bills = Bill.objects.filter(date__range=[from_date, to_date],time_id=select_time).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(bill=bill.id,date__range=[from_date, to_date],time=select_time)
                    print(winnings)
                    total_winning = sum(winning.prize for winning in winnings)
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
                    }
                    return render(request,'adminapp/daily_report.html',context)
            else:
                print("its agent")
                bills = Bill.objects.filter(date__range=[from_date, to_date]).all()
                print(bills)
                for bill in bills:
                    winnings = Winning.objects.filter(bill=bill.id,date__range=[from_date, to_date])
                    print(winnings)
                    total_winning = sum(winning.prize for winning in winnings)
                    bill.win_amount += total_winning
                    if winnings != 0:
                        bill.total_d_amount = bill.total_c_amount - total_winning
                    else:
                        bill.total_d_amount = total_winning - bill.total_c_amount
                    total_winning = sum(bill.win_amount for bill in bills)
                    total_balance = sum(bill.total_d_amount for bill in bills)
                    total_c_amount = Bill.objects.filter(date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('total_c_amount'))
                    context = {
                        'agents' : agents,
                        'times' : times,
                        'dealer_bills' : bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : 'all',
                        'selected_time' : 'all',
                    }
                    return render(request,'adminapp/daily_report.html',context)
    else:
        bills = Bill.objects.filter(date=current_date).all()
        print(bills)
        for bill in bills:
            winnings = Winning.objects.filter(bill=bill.id,date=current_date)
            print(winnings)
            total_winning = sum(winning.prize for winning in winnings)
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

def countwise_report(request):
    ist = pytz.timezone('Asia/Kolkata')
    times = PlayTime.objects.filter().all()
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
                'times' : times
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
                'times' : times
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

def countsales_report(request):
    times = PlayTime.objects.filter().all()
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
                    'selected_to' : to_date
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
                    'selected_to' : to_date
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
                    'selected_to' : to_date
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
                    'selected_to' : to_date
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

def winning_report(request):
    times = PlayTime.objects.filter().all()
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
        print(from_date,to_date,select_time,select_agent)
        agents = Agent.objects.filter().all()
        if select_time != 'all':
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time)
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
                }
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date],time=select_time)
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
                }
            return render(request,'adminapp/winning_report.html',context)
        else:
            print("time is all")
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date])
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
                }
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date])
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
                }
            return render(request,'adminapp/winning_report.html',context)
    else:
        try:
            matching_play_times = Winning.objects.filter().last()
            agents = Agent.objects.filter().all()
            winnings = Winning.objects.filter(date=current_date,time=matching_play_times.time)
            aggregated_winnings = winnings.values('bill', 'LSK', 'number').annotate(
                total_count=Sum('count'),
                total_commission=Sum('commission'),
                total_prize=Sum('prize'),
                total_net=Sum('total'),
                agent=F('agent__agent_name'),
                dealer=F('dealer__dealer_name'),
                position=F('position'),
            )
            totals = Winning.objects.filter(date=current_date,time=matching_play_times.time).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
        except:
            pass
        context = {
            'times' : times,
            'agents' : agents,
            'winnings' : winnings,
            'totals' : totals,
            'aggr' : aggregated_winnings,
            'selected_time' : matching_play_times.time.id,
            'selected_agent' : 'all'
        }
        return render(request,'adminapp/winning_report.html',context) 


def winningcount_report(request):
    times = PlayTime.objects.filter().all()
    agents = Agent.objects.filter().all()
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    winnings = Winning.objects.filter(date=current_date).all()
    totals = Winning.objects.filter(date=current_date).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
    if request.method == 'POST':
        select_time = request.POST.get('time')
        select_agent = request.POST.get('select-agent')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_time != 'all':
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time)
                totals = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : select_time,
                    'selected_agent' : select_agent,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request,'adminapp/winningcount_report.html',context)
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date],time=select_time)
                totals = Winning.objects.filter(date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : select_time,
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request,'adminapp/winningcount_report.html',context)
        else:
            if select_agent != 'all':
                winnings = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date])
                totals = Winning.objects.filter(Q(agent__user=select_agent) | Q(dealer__agent__user=select_agent),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : 'all',
                    'selected_agent' : select_agent,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request,'adminapp/winningcount_report.html',context)
            else:
                winnings = Winning.objects.filter(date__range=[from_date, to_date])
                totals = Winning.objects.filter(date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                context = {
                    'times' : times,
                    'agents' : agents,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : 'all',
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date
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

def blocked_numbers(request):
    return render(request,'adminapp/blocked_numbers.html')

def edit_bill(request):
    bill = Agent.objects.all()
    bill_agent = bill
    bill= Dealer.objects.all()
    bill_dealer=bill
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    bill_search = {}
    totals = {}

    try:
        matching_play_times = PlayTime.objects.get(start_time__lte=current_time, end_time__gte=current_time)
        print(matching_play_times.id)
    except:
        pass
    if request.method == 'POST':
        search_select = request.POST.get('select')
        print(search_select,"the user id")
        if search_select == 'all':
            return redirect('adminapp:edit_bill')
        else :
            bill_search = Bill.objects.filter(user=search_select,date=current_date,time_id=matching_play_times.id).all()
            totals = Bill.objects.filter(user=search_select,date=current_date,time_id=matching_play_times.id).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            print(bill_search,"search bill")
            print(totals,"get total")
            print(bill_search,"search bill")
    context = {
        'bills': bill_search,
        'totals' : totals,
        'bill_dealer':bill_dealer,
    }
    return render(request,'adminapp/edit_bill.html',context)

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
                context = {
                    'agents': agents,
                    'collections': collections,
                    'profit_or_loss': profit_or_loss,
                    'selected_agent' : select_agent,
                    'from_or_to' : from_or_to
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
                    'from_or_to' : from_or_to
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
                    'from_or_to' : from_or_to
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
                    'from_or_to' : from_or_to
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
                    'from_or_to' : from_or_to
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
                    'from_or_to' : from_or_to
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
            agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('d_amount'))['agent_total_d_amount'] or 0
            dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('d_amount'))['dealer_total_d_amount'] or 0
            total_d_amount = agent_total_d_amount + dealer_total_d_amount
            from_agent = collection.filter(from_or_to='from-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            to_agent = collection.filter(from_or_to='to-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            total_collection_amount = from_agent - to_agent
            balance = float(total_collection_amount) - float(total_d_amount)
            if total_d_amount > 0:
                report_data.append({
                    'date' : current_date,
                    'agent': agent_instance,
                    'total_d_amount': total_d_amount,
                    'from_or_to' : total_collection_amount,
                    'balance' : balance
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
            pass
    for agent in agents:
        agent_games = AgentGame.objects.filter(date=current_date, agent=agent)
        dealer_games = DealerGame.objects.filter(date=current_date, agent=agent)
        collection = CollectionReport.objects.filter(date=current_date, agent=agent)
        agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('d_amount'))['agent_total_d_amount'] or 0
        dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('d_amount'))['dealer_total_d_amount'] or 0
        total_d_amount = agent_total_d_amount + dealer_total_d_amount
        from_agent = collection.filter(from_or_to='from-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        to_agent = collection.filter(from_or_to='to-agent').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        total_collection_amount = from_agent - to_agent
        balance = float(total_collection_amount) - float(total_d_amount)
        print(f"Agent: {agent}, Total D Amount: {total_d_amount}")
        if total_d_amount > 0:
            report_data.append({
                'date' : current_date,
                'agent': agent,
                'total_d_amount': total_d_amount,
                'from_or_to' : total_collection_amount,
                'balance' : balance
            })
    total_balance = sum(entry['balance'] for entry in report_data)
    context = {
        'agents' : agents,
        'selected_agent' : 'all',
        'report_data': report_data,
        'total_balance' : total_balance
    }
    return render(request, 'adminapp/balance_report.html',context)

def change_password(request):
    return render(request,'adminapp/change_password.html')

def settings(request):
    return render(request,'adminapp/settings.html')



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







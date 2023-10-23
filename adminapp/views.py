from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from website.decorators import dealer_required, agent_required, admin_required
from website.forms import LoginForm,UserUpdateForm
from website.forms import AgentRegistration
from website.models import User,Agent,Dealer
from .models import PlayTime, AgentPackage, Result
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as pytz_timezone
import pytz
from django.utils import timezone
from agent.models import Bill
from django.db.models import Sum
from django.db.models import Q

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
    context = {
        'timings' : timings
    }
    return render(request,'adminapp/add_result.html',context)

def sales_report(request):
    return render(request,'adminapp/sales_report.html')

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
        'times' : times
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
    return render(request,'adminapp/monitor.html')

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
    return render(request,'adminapp/dailyreport.html')

def countwise_report(request):
    return render(request,'adminapp/countwise_report.html')

def countsales_report(request):
    return render(request,'adminapp/countsales_report.html') 

def winning_report(request):
    return render(request,'adminapp/winning_report.html') 

def winningcount_report(request):
    return render(request,'adminapp/winningcount_report.html')

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
    return render(request,'adminapp/payment_report.html')

def change_password(request):
    return render(request,'adminapp/change_password.html')
def settings(request):
    return render(request,'adminapp/settings.html')

def change_password(request):
    return render(request,'adminapp/change_password.html')


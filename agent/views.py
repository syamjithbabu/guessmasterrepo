from audioop import reverse
import json
from urllib import response
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
import pytz
from website.forms import LoginForm
from website.forms import DealerRegistration,UserUpdateForm
from website.models import User,Dealer,Agent
from adminapp.models import PlayTime, AgentPackage,Result,Winning,Limit,BlockedNumber,GameLimit,CollectionReport
from .models import DealerPackage, AgentGameTest, AgentGame, Bill, DealerCollectionReport, DealerLimit
from dealer.models import DealerGame, DealerGameTest
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from website.decorators import dealer_required, agent_required
from django.utils import timezone
from pytz import timezone as pytz_timezone
from collections import OrderedDict
from django.db.models import Sum
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import PasswordChangeForm,AdminPasswordChangeForm
from django.db.models import F
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from django.http import HttpResponse
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from datetime import datetime, timedelta

# Create your views here.
@login_required
@agent_required
def index(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    agent_obj = Agent.objects.get(user=request.user)
    if PlayTime.objects.filter(limit__agent=agent_obj).all():
        play_times = PlayTime.objects.filter(limit__agent=agent_obj).all().order_by('id')
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
    return render(request,"agent/index.html",context)

@login_required
@agent_required
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

@login_required
@agent_required
def view_dealer(request):
    agent = Agent.objects.get(user=request.user)
    print(agent)
    dealers = Dealer.objects.filter(agent=agent).all()
    packages = DealerPackage.objects.filter().all()
    context = {
        'dealers' : dealers,
        'packages' : packages
    }
    return render(request,'agent/view_dealer.html',context)

@login_required
@agent_required
def edit_dealer(request,id):
    dealer = get_object_or_404(Dealer, id=id)
    user = dealer.user
    if request.method == 'POST':
        form = AdminPasswordChangeForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect("agent:view_dealer")
    else:
        form = AdminPasswordChangeForm(user=user)

    return render(request, 'agent/edit_dealer.html', {'form': form})


@login_required
@agent_required
def delete_dealer(request,id):
    dealer = get_object_or_404(Dealer, id=id)
    dealer_user = dealer.user
    dealer_user.delete()
    return redirect('agent:view_dealer')

@login_required
@agent_required
def ban_dealer(request,id):
    dealer = get_object_or_404(Dealer, id=id)
    user = dealer.user
    user.is_active = False
    user.save()
    return redirect('agent:view_dealer')

@login_required
@agent_required
def remove_ban(request,id):
    dealer = get_object_or_404(Dealer,id=id)
    user = dealer.user
    user.is_active = True
    user.save()
    return redirect('agent:view_dealer')

@login_required
@agent_required
def booking(request):
    return render(request,'agent/booking.html')

@login_required
@agent_required
def results(request):
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
        return render(request,'agent/results.html',context)
    context = {
        'times' : times,
        'results' : results
    }
    return render(request,'agent/results.html',context)

@login_required
@agent_required
def sales_report(request):
    print("Sales report function")
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    day_of_week = current_date.strftime('%A')
    print(day_of_week)
    print(current_date)
    items_per_page = 15
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        print(select_dealer,"selected_dealer")
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
            if str(select_dealer) != str(agent_obj.user) and not str(select_dealer).isdigit():
                if select_time != 'all':
                    selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                    #time and agent is selected
                    if lsk != 'all':
                        #time, agent and lsk is selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK__in=lsk_value,customer=select_dealer).order_by('id')
                        print(agent_games)
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games,customer=select_dealer).distinct().order_by('-id')
                        print(agent_bills)
                        totals = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,agent=agent_obj,LSK__in=lsk_value,customer=select_dealer).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        customers_list = []
                        customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).exclude(customer='').order_by('-id')
                        for cust in customers:
                            if cust.customer not in customers_list:
                                customers_list.append(cust.customer)
                        combined_queryset = agent_bills
                        paginator = Paginator(combined_queryset, 100)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        for bill in agent_bills:
                            for game in bill.agent_games.filter(LSK__in=lsk_value):
                                print("Game Count of",bill.id," is" , game.count)
                                print("Game D Amount of",bill.id," is" , game.d_amount)
                                print("Game C Amount of",bill.id," is" , game.c_amount)
                            bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                            bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                            bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                        if 'pdfButton' in request.POST:
                            pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +selected_time+ ".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                            title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                                # Add a line break after the title
                            story.append(Spacer(1, 12))

                                # Add table headers
                            headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                            data = [headers]

                            for bill in combined_queryset:
                                user = bill.user

                                display_user = bill.customer

                                display_d_amount = bill.total_d_amount

                                display_c_amount = bill.total_c_amount

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{bill.id}",
                                    f"{bill.total_count}",
                                    f"{display_d_amount:.2f}",
                                    f"{display_c_amount:.2f}",
                                ])

                                for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                    data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])
                                # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            total_count_text = f"Total Count: {totals['total_count']}"
                            total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                            total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                            total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        context = {   
                                'dealers' : dealers,
                                'times' : times,
                                'combined_bills' : combined_bills,
                                'totals' : totals,
                                'selected_dealer' : select_dealer,
                                'selected_time' : select_time,
                                'agent_games' : agent_games,
                                'dealer_games' : dealer_games,  
                                'selected_game_time' : selected_game_time, 
                                'customers' : customers_list,
                                'selected_lsk' : lsk,
                            }
                        return render(request, 'agent/sales_report.html', context)
                    else:
                        #lsk not selected, agent and time selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,customer=select_dealer).all().order_by('id')
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,customer=select_dealer).all().order_by('-id')
                        totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time_id=select_time,customer=select_dealer).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        customers_list = []
                        customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time).exclude(customer='').order_by('-id')
                        for cust in customers:
                            if cust.customer not in customers_list:
                                customers_list.append(cust.customer)
                        combined_queryset = agent_bills
                        paginator = Paginator(combined_queryset, 100)
                        page = request.POST.get('page', 1)
                        print("this worked")
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        if 'pdfButton' in request.POST:
                            pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +selected_time+ ".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                                # Add a line break after the title
                            story.append(Spacer(1, 12))

                                # Add table headers
                            headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                            data = [headers]

                            for bill in combined_queryset:
                                user = bill.user

                                display_user = bill.customer

                                display_d_amount = bill.total_d_amount

                                display_c_amount = bill.total_c_amount

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{bill.id}",
                                    f"{bill.total_count}",
                                    f"{display_d_amount:.2f}",
                                    f"{display_c_amount:.2f}",
                                ])

                                for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                    data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])
                                # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            total_count_text = f"Total Count: {totals['total_count']}"
                            total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                            total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                            total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        context = {   
                                'dealers' : dealers,
                                'times' : times,
                                'combined_bills' : combined_bills,
                                'totals' : totals,
                                'selected_dealer' : select_dealer,
                                'selected_time' : select_time,
                                'agent_games' : agent_games,
                                'dealer_games' : dealer_games,  
                                'selected_game_time' : selected_game_time, 
                                'customers' : customers_list,
                            }
                        return render(request, 'agent/sales_report.html', context)
                else:
                    #time not selected, agent selected
                    if lsk != 'all':
                            #lsk selected, time not selected, agent selected
                            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value,customer=select_dealer).order_by('id')
                            agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games,customer=select_dealer).distinct().order_by('-id')
                            totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value,customer=select_dealer).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            customers_list = []
                            customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).exclude(customer='').order_by('-id')
                            for cust in customers:
                                if cust.customer not in customers_list:
                                    customers_list.append(cust.customer)
                            combined_queryset = agent_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            for bill in agent_bills:
                                for game in bill.agent_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.customer

                                    display_d_amount = bill.total_d_amount

                                    display_c_amount = bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                            context = {   
                                'dealers' : dealers,
                                'times' : times,
                                'combined_bills' : combined_bills,
                                'totals' : totals,
                                'selected_dealer' : select_dealer,
                                'selected_time' : select_time,
                                'agent_games' : agent_games,
                                'dealer_games' : dealer_games,  
                                'selected_game_time' : selected_game_time, 
                                'customers' : customers_list,
                                'selected_lsk' : lsk,
                            }
                            return render(request, 'agent/sales_report.html', context)
                    else:
                            #time,lsk not selected, agent selected
                            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,customer=select_dealer).all().order_by('id')
                            agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games,customer=select_dealer).distinct().order_by('-id')
                            totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,customer=select_dealer).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            customers_list = []
                            customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).exclude(customer='').order_by('-id')
                            for cust in customers:
                                if cust.customer not in customers_list:
                                    customers_list.append(cust.customer)
                            combined_queryset = agent_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            if 'customer-search' in request.POST:
                                print("customer")
                            else:
                                print("no customer")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.customer

                                    display_d_amount = bill.total_d_amount

                                    display_c_amount = bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                            context = {   
                                'dealers' : dealers,
                                'times' : times,
                                'combined_bills' : combined_bills,
                                'totals' : totals,
                                'selected_dealer' : select_dealer,
                                'selected_time' : select_time,
                                'agent_games' : agent_games,
                                'dealer_games' : dealer_games,  
                                'selected_game_time' : selected_game_time, 
                                'customers' : customers_list
                            }
                            return render(request, 'agent/sales_report.html', context)
            else:
                if select_dealer == str(agent_obj.user):
                    #agent is selected
                    if select_time != 'all':
                        selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                        #time and agent is selected
                        if lsk != 'all':
                            #time, agent and lsk is selected
                            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK__in=lsk_value).order_by('id')
                            print(agent_games)
                            agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).distinct().order_by('-id')
                            print(agent_bills)
                            totals = AgentGame.objects.filter(date__range=[from_date, to_date],time=select_time,agent=agent_obj,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            customers_list = []
                            customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).exclude(customer='').order_by('-id')
                            for cust in customers:
                                if cust.customer not in customers_list:
                                    customers_list.append(cust.customer)
                            combined_queryset = agent_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            for bill in agent_bills:
                                for game in bill.agent_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +selected_time+ ".pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                        else:
                            #lsk not selected, agent and time selected
                            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time).all().order_by('id')
                            agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time).all().order_by('-id')
                            totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time_id=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            customers_list = []
                            customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time).exclude(customer='').order_by('-id')
                            for cust in customers:
                                if cust.customer not in customers_list:
                                    customers_list.append(cust.customer)
                            combined_queryset = agent_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +selected_time+ ".pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                    else:
                        #time not selected, agent selected
                        if lsk != 'all':
                            #lsk selected, time not selected, agent selected
                            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value).order_by('id')
                            agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).distinct().order_by('-id')
                            totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            customers_list = []
                            customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).exclude(customer='').order_by('-id')
                            for cust in customers:
                                if cust.customer not in customers_list:
                                    customers_list.append(cust.customer)
                            combined_queryset = agent_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            for bill in agent_bills:
                                for game in bill.agent_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.agent_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                        else:
                            #time,lsk not selected, agent selected
                            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all().order_by('id')
                            agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).distinct().order_by('-id')
                            totals = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            customers_list = []
                            customers = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__in=agent_games).exclude(customer='').order_by('-id')
                            for cust in customers:
                                if cust.customer not in customers_list:
                                    customers_list.append(cust.customer)
                            combined_queryset = agent_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            if 'customer-search' in request.POST:
                                print("customer")
                            else:
                                print("no customer")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                else:
                    #dealer is selcted
                    if select_time != 'all':
                        selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                        #dealer and time selected
                        if lsk != 'all':
                            print("here")
                            #dealer,lsk and time selected
                            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,time=select_time,LSK__in=lsk_value).order_by('id')
                            dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,time_id=select_time,dealer_games__in=dealer_games).distinct().order_by('-id')
                            totals = DealerGame.objects.filter(date__range=[from_date, to_date],time_id=select_time,dealer__user=select_dealer,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            combined_queryset = dealer_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            for bill in dealer_bills:
                                for game in bill.dealer_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +selected_time+ ".pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount:.2f}", f"{dealer_game.c_amount:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                        else:
                            #dealer, time selcted and lsk not selected
                            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,time=select_time).all().order_by('id')
                            dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,time_id=select_time,dealer_games__in=dealer_games).distinct().order_by('-id')
                            totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,time_id=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            combined_queryset = dealer_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +selected_time+ ".pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount:.2f}", f"{dealer_game.c_amount:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                    else:
                        #dealer selected, time not selected
                        if lsk != 'all':
                            #dealer and lsk selected, time not selected
                            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,LSK__in=lsk_value).order_by('id')
                            dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,dealer_games__in=dealer_games).distinct().order_by('-id')
                            totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            combined_queryset = dealer_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            for bill in dealer_bills:
                                for game in bill.dealer_games.filter(LSK__in=lsk_value):
                                    print("Game Count of",bill.id," is" , game.count)
                                    print("Game D Amount of",bill.id," is" , game.d_amount)
                                    print("Game C Amount of",bill.id," is" , game.c_amount)
                                bill.total_count = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_count=Sum('count'))['total_count']
                                bill.total_d_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_d_amount=Sum('d_amount'))['total_d_amount']
                                bill.total_c_amount = bill.dealer_games.filter(LSK__in=lsk_value).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount']
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +"All Times.pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount:.2f}", f"{dealer_game.c_amount:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                        else:
                            #dealer selected, time and lsk not selected
                            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer).all().order_by('id')
                            dealer_bills = Bill.objects.filter(date__range=[from_date, to_date],user=select_dealer,dealer_games__in=dealer_games).distinct().order_by('-id')
                            print(dealer_bills)
                            combined_queryset = dealer_bills
                            paginator = Paginator(combined_queryset, 100)
                            page = request.POST.get('page', 1)
                            print("this worked")
                            try:
                                combined_bills = paginator.page(page)
                            except PageNotAnInteger:
                                combined_bills = paginator.page(1)
                            except EmptyPage:
                                combined_bills = paginator.page(paginator.num_pages)
                            for bills in dealer_bills:
                                print(bills.total_c_amount)
                            totals = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                            if 'pdfButton' in request.POST:
                                pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " +"All Times.pdf"
                                response = HttpResponse(content_type='application/pdf')
                                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                                story = []

                                title_style = ParagraphStyle(
                                    'Title',
                                    parent=ParagraphStyle('Normal'),
                                    fontSize=12,
                                    textColor=colors.black,
                                    spaceAfter=16,
                                )
                                title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                                title_paragraph = Paragraph(title_text, title_style)
                                story.append(title_paragraph)

                                # Add a line break after the title
                                story.append(Spacer(1, 12))

                                # Add table headers
                                headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                                data = [headers]

                                for bill in combined_queryset:
                                    user = bill.user

                                    display_user = bill.user.username

                                    display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount

                                    display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                    formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                    # Add bill information to the table data
                                    data.append([
                                        formatted_date_time,
                                        display_user,
                                        f"{bill.id}",
                                        f"{bill.total_count}",
                                        f"{display_d_amount:.2f}",
                                        f"{display_c_amount:.2f}",
                                    ])

                                    for agent_game in bill.agent_games.all():
                                        # Add agent game information to the table data
                                        data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                    for dealer_game in bill.dealer_games.all():
                                        # Add dealer game information to the table data
                                        data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount:.2f}", f"{dealer_game.c_amount:.2f}"])

                                # Create the table and apply styles
                                table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))

                                story.append(table)

                                total_count_text = f"Total Count: {totals['total_count']}"
                                total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                                total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                                total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                                story.append(total_paragraph)

                                pdf.build(story)
                                return response
                context = {
                    'dealers': dealers,
                    'times': times,
                    'combined_bills' : combined_bills,
                    'totals' : totals,
                    'selected_dealer' : select_dealer,
                    'selected_time' : select_time,
                    'selected_game_time' : selected_game_time,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_lsk' : lsk,
                    'agent_games' : agent_games,
                    'dealer_games' : dealer_games,
                    'day_of_week':day_of_week,
                }
                return render(request, 'agent/sales_report.html', context)
        if select_dealer == 'all':
            if select_time != 'all':
                selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                    #all users, time is selected
                if lsk != 'all':
                        #all users, time is selected, lsk is selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK__in=lsk_value).order_by('id')
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time,LSK__in=lsk_value).order_by('id')
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).distinct().order_by('-id')
                        dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time,dealer_games__in=dealer_games).distinct().order_by('-id')
                        totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time,LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount_admin'),total_d_amount=Sum('d_amount_admin'))
                        combined_queryset = agent_bills | dealer_bills
                        paginator = Paginator(combined_queryset, 100)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
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
                        if 'pdfButton' in request.POST:
                            pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " + selected_time +".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                            data = [headers]

                            for bill in combined_queryset:
                                user = bill.user

                                display_user = bill.user.username

                                display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount_admin

                                display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                # Add bill information to the table data
                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{bill.id}",
                                    f"{bill.total_count}",
                                    f"{display_d_amount:.2f}",
                                    f"{display_c_amount:.2f}",
                                ])

                                for agent_game in bill.agent_games.all():
                                    # Add agent game information to the table data
                                    data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                for dealer_game in bill.dealer_games.all():
                                    # Add dealer game information to the table data
                                    data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            total_count_text = f"Total Count: {totals['total_count']}"
                            total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                            total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                            total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                else:
                        #all users, time is selected, lsk is not selected
                        selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time).order_by('id')
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,time=select_time).order_by('id')
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,time_id=select_time,agent_games__in=agent_games).distinct().order_by('-id')
                        dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time,dealer_games__in=dealer_games).distinct().order_by('-id')
                        totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount_admin'),total_d_amount=Sum('d_amount_admin'))
                        combined_queryset = agent_bills | dealer_bills
                        paginator = Paginator(combined_queryset, 100)
                        page = request.POST.get('page', 1)
                        print("this worked")
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        totals = {
                            'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                            'total_c_amount': (totals_agent['total_c_amount'] or 0) + (totals_dealer['total_c_amount'] or 0),
                            'total_d_amount': (totals_agent['total_d_amount'] or 0) + (totals_dealer['total_d_amount'] or 0)
                        }
                        if 'pdfButton' in request.POST:
                            pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + " - " + selected_time +".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                            data = [headers]

                            for bill in combined_queryset:
                                user = bill.user

                                display_user = bill.user.username

                                display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount_admin

                                display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                # Add bill information to the table data
                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{bill.id}",
                                    f"{bill.total_count}",
                                    f"{display_d_amount:.2f}",
                                    f"{display_c_amount:.2f}",
                                ])

                                for agent_game in bill.agent_games.all():
                                    # Add agent game information to the table data
                                    data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                for dealer_game in bill.dealer_games.all():
                                    # Add dealer game information to the table data
                                    data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            total_count_text = f"Total Count: {totals['total_count']}"
                            total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                            total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                            total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
            else:
                    #all users, time not selected
                    if lsk != 'all':
                        #all users, time not selected, lsk is selected
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK__in=lsk_value).order_by('id')
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK__in=lsk_value).order_by('id')
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id,agent_games__LSK__in=lsk_value).distinct().order_by('-id')
                        dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],dealer_games__LSK__in=lsk_value).distinct().order_by('-id')
                        combined_queryset = agent_bills | dealer_bills
                        paginator = Paginator(combined_queryset, 100)
                        page = request.POST.get('page', 1)
                        print("this worked")
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
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
                                totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date],LSK__in=lsk_value).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount_admin'),total_d_amount=Sum('d_amount_admin'))
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
                        if 'pdfButton' in request.POST:
                            pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + "- All Times.pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + " - All Times"
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                            data = [headers]

                            for bill in combined_queryset:
                                user = bill.user

                                display_user = bill.user.username

                                display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount_admin

                                display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                # Add bill information to the table data
                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{bill.id}",
                                    f"{bill.total_count}",
                                    f"{display_d_amount:.2f}",
                                    f"{display_c_amount:.2f}",
                                ])

                                for agent_game in bill.agent_games.all():
                                    # Add agent game information to the table data
                                    data.append(["#",f"{agent_game.LSK}", agent_game.number, agent_game.count, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                for dealer_game in bill.dealer_games.all():
                                    # Add dealer game information to the table data
                                    data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            total_count_text = f"Total Count: {totals['total_count']}"
                            total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                            total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                            total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                    else:
                        #all users, time not selected, lsk not selected
                        print("request here")
                        agent_games = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all().order_by('id')
                        dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj).all().order_by('id')
                        agent_bills = Bill.objects.filter(date__range=[from_date, to_date],user=agent_obj.user.id).distinct().order_by('-id')
                        dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date]).distinct().order_by('-id')
                        totals_agent = AgentGame.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount'),total_d_amount=Sum('d_amount'))
                        totals_dealer = DealerGame.objects.filter(Q(dealer__agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_c_amount=Sum('c_amount_admin'),total_d_amount=Sum('d_amount_admin'))
                        combined_queryset = agent_bills | dealer_bills
                        paginator = Paginator(combined_queryset, 100)
                        page = request.POST.get('page', 1)
                        print("this worked")
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        totals = {
                            'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                            'total_c_amount': (totals_agent['total_c_amount'] or 0) + (totals_dealer['total_c_amount'] or 0),
                            'total_d_amount': (totals_agent['total_d_amount'] or 0) + (totals_dealer['total_d_amount'] or 0)
                            }
                        if 'pdfButton' in request.POST:
                            pdf_filename = "Sales_Report" + "-" + from_date + "-" + to_date + "- All Times.pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Sales Report" + "( " + from_date + " - " + to_date + " )" + " - All Times"
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Dealer", "Bill", "Count", "S.Amt", "C.Amt"]
                            data = [headers]

                            for bill in combined_queryset:
                                user = bill.user

                                display_user = bill.user.username

                                display_d_amount = bill.total_d_amount if user.is_agent else bill.total_d_amount_admin

                                display_c_amount = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                # Add bill information to the table data
                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{bill.id}",
                                    f"{bill.total_count}",
                                    f"{display_d_amount:.2f}",
                                    f"{display_c_amount:.2f}",
                                ])

                                for agent_game in bill.agent_games.all():
                                    # Add agent game information to the table data
                                    data.append(["#",f"{agent_game.LSK}", agent_game.number, f"{agent_game.d_amount:.2f}", f"{agent_game.c_amount:.2f}"])

                                for dealer_game in bill.dealer_games.all():
                                    # Add dealer game information to the table data
                                    data.append(["#",f"{dealer_game.LSK}", dealer_game.number, dealer_game.count, f"{dealer_game.d_amount_admin:.2f}", f"{dealer_game.c_amount_admin:.2f}"])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            total_count_text = f"Total Count: {totals['total_count']}"
                            total_d_amount_text = f"A.Amount: {totals['total_d_amount']:.2f}"
                            total_s_amount_text = f"C.Amount: {totals['total_c_amount']:.2f}"

                            total_paragraph = Paragraph(f"{total_count_text}<br/>{total_d_amount_text}<br/>{total_s_amount_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
            for_agent = 'yes'
            context = {
                'dealers': dealers,
                'times': times,
                'combined_bills' : combined_bills,
                'totals' : totals,
                'selected_dealer' : select_dealer,
                'selected_time' : select_time,
                'selected_game_time' : selected_game_time,
                'selected_from' : from_date,
                'selected_to' : to_date,
                'selected_lsk' : lsk,
                'agent_games' : agent_games,
                'dealer_games' : dealer_games,
                'day_of_week':day_of_week,
                'for_agent' : for_agent
            }
            return render(request, 'agent/sales_report.html', context)
    else:
        agent_games = AgentGame.objects.filter(date=current_date,agent=agent_obj).all().order_by('id')
        dealer_games = DealerGame.objects.filter(date=current_date,dealer__agent=agent_obj).all().order_by('id')
        agent_bills = Bill.objects.filter(date=current_date,user=agent_obj.user.id).all().order_by('-id')
        dealer_bills = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date=current_date).order_by('-id')
        agent_bills_totals = Bill.objects.filter(Q(user=agent_obj.user),date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
        dealer_bills_totals = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount_admin'),total_d_amount=Sum('total_d_amount_admin'))
        customers_list = []
        customers = Bill.objects.filter(date=current_date,user=agent_obj.user.id).exclude(customer='').order_by('-id')
        for cust in customers:
            if cust.customer not in customers_list:
                customers_list.append(cust.customer)
        totals = {
            'total_count': (agent_bills_totals['total_count'] or 0) + (dealer_bills_totals['total_count'] or 0),
            'total_c_amount': (agent_bills_totals['total_c_amount'] or 0) + (dealer_bills_totals['total_c_amount'] or 0),
            'total_d_amount': (agent_bills_totals['total_d_amount'] or 0) + (dealer_bills_totals['total_d_amount'] or 0)
            }
        combined_queryset = agent_bills | dealer_bills
        paginator = Paginator(combined_queryset, 100)
        page = request.POST.get('page', 1)

        try:
            combined_bills = paginator.page(page)
        except PageNotAnInteger:
            combined_bills = paginator.page(1)
        except EmptyPage:
            combined_bills = paginator.page(paginator.num_pages)

        select_dealer = 'all'
        select_time = 'all'
        selected_game_time = 'all times'
        for_agent = 'yes'
        context = {   
            'dealers' : dealers,
            'times' : times,
            'combined_bills' : combined_bills,
            'totals' : totals,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
            'agent_games' : agent_games,
            'dealer_games' : dealer_games,  
            'selected_game_time' : selected_game_time, 
            'for_agent' : for_agent,
            'customers' : customers_list
        }
    return render(request,'agent/sales_report.html',context)

@login_required
@agent_required
def daily_report(request):
    print("Daily report function")
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    print(dealers)
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    print(current_date)
    print("this is working")
    items_per_page = 15
    total_winning = []
    total_balance = []
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        select_time = request.POST.get('select-time')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        print(select_dealer, select_time, from_date, to_date)
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_dealer != 'all':
            if str(select_dealer) != str(agent_obj.user) and not str(select_dealer).isdigit():
                if select_time != 'all':
                        print("its agent")
                        selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                        bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time,customer=select_dealer).all()
                        customers_list = []
                        customers = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time).exclude(customer='')
                        for cust in customers:
                            if cust.customer not in customers_list:
                                customers_list.append(cust.customer)
                        paginator = Paginator(bills, 15)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        print(bills)
                        for bill in combined_bills:
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                            print(winnings)
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            if winnings != 0:
                                bill.total_d_amount =  bill.total_c_amount - total_winning 
                            else:
                                bill.total_d_amount =  bill.total_c_amount - total_winning
                        if bills:
                            for b in bills:
                                user = b.user
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=b.id,date__range=[from_date, to_date],time=select_time)
                                if user.is_agent:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                    print(b.win_amount,"agent")
                                else:
                                    total_winning = sum(winning.total_admin for winning in winnings)
                                    b.win_amount = total_winning
                                    print(b.win_amount,"dealer")
                                if winnings != 0 and user.is_agent:
                                    b.total_d_amount =  b.total_c_amount - total_winning
                                elif winnings != 0 and user.is_dealer:
                                    b.total_d_amount = b.total_c_amount_admin - total_winning
                                else:
                                    b.total_d_amount = total_winning - b.total_c_amount
                                total_winning = sum(b.win_amount for b in bills)
                        else:
                            total_winning = 0
                        total_c_amount = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time,customer=select_dealer).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
                        total_balance =  float(total_c_amount) - float(total_winning)
                        if 'pdfButton' in request.POST:
                            print("pdf working")
                            pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - " + selected_time +".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                            data = [headers]

                            # Fetch bills within the date range
                            bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time,customer=select_dealer).all()

                            # Populate data for each bill
                            for bill in bills:
                                user = bill.customer
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                                total_win = sum(winning.total for winning in winnings)
                                balance = bill.total_c_amount - total_win

                                display_user = bill.customer

                                display_sale = bill.total_c_amount

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{display_sale:.2f}",
                                    f"{total_win:.2f}",
                                    f"{balance:.2f}",
                                ])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            story.append(Spacer(1, 12))
                            
                            total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                            total_win_text = f"Total Win Amount: {total_winning:.2f}"
                            total_balance_text = f"Total Balance: {total_balance:.2f}"

                            total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : select_dealer,
                            'selected_time' : select_time,
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                            'customers' : customers_list
                        }
                        return render(request,'agent/daily_report.html',context)
                else:
                    bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],customer=select_dealer).all()
                    customers_list = []
                    customers = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date]).exclude(customer='')
                    for cust in customers:
                        if cust.customer not in customers_list:
                            customers_list.append(cust.customer)
                    paginator = Paginator(bills, 15)
                    page = request.POST.get('page', 1)
                    try:
                        combined_bills = paginator.page(page)
                    except PageNotAnInteger:
                        combined_bills = paginator.page(1)
                    except EmptyPage:
                        combined_bills = paginator.page(paginator.num_pages)
                    print(bills)
                    for bill in combined_bills:
                        winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                        print(winnings)
                        total_winning = sum(winning.total for winning in winnings)
                        bill.win_amount = total_winning
                        if winnings != 0:
                            bill.total_d_amount = bill.total_c_amount - total_winning
                        else:
                            bill.total_d_amount = total_winning - bill.total_c_amount
                    if bills:
                        for b in bills:
                            user = b.user
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=b.id,date__range=[from_date, to_date])
                            if user.is_agent:
                                total_winning = sum(winning.total for winning in winnings)
                                b.win_amount = total_winning
                                print(b.win_amount,"agent")
                            else:
                                total_winning = sum(winning.total_admin for winning in winnings)
                                b.win_amount = total_winning
                                print(b.win_amount,"dealer")
                            if winnings != 0 and user.is_agent:
                                b.total_d_amount = b.total_c_amount - total_winning
                            elif winnings != 0 and user.is_dealer:
                                b.total_d_amount = b.total_c_amount_admin - total_winning
                            else:
                                b.total_d_amount = total_winning - b.total_c_amount
                            total_winning = sum(b.win_amount for b in bills)
                    else:
                        total_winning = 0
                    total_c_amount = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],customer=select_dealer).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
                    total_balance = float(total_c_amount) - float(total_winning)
                    if 'pdfButton' in request.POST:
                            print("pdf working")
                            pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                            data = [headers]

                            # Fetch bills within the date range
                            bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],customer=select_dealer).all()

                            # Populate data for each bill
                            for bill in bills:
                                user = bill.user
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                                total_win = sum(winning.total for winning in winnings)
                                balance = bill.total_c_amount - total_win

                                display_user = bill.customer

                                display_sale = bill.total_c_amount

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{display_sale:.2f}",
                                    f"{total_win:.2f}",
                                    f"{balance:.2f}",
                                ])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            story.append(Spacer(1, 12))
                            
                            total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                            total_win_text = f"Total Win Amount: {total_winning:.2f}"
                            total_balance_text = f"Total Balance: {total_balance:.2f}"

                            total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                    context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : select_dealer,
                            'selected_time' : 'all',
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                            'customers' : customers_list
                        }
                    return render(request,'agent/daily_report.html',context)
            else:
                if select_time != 'all':
                    if select_dealer == str(agent_obj.user):
                        print("its agent")
                        selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                        bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time).all()
                        paginator = Paginator(bills, 15)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        print(bills)
                        for bill in combined_bills:
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                            print(winnings)
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            if winnings != 0:
                                bill.total_d_amount = total_winning - bill.total_c_amount
                            else:
                                bill.total_d_amount = total_winning - bill.total_c_amount
                        if bills:
                            for b in bills:
                                user = b.user
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=b.id,date__range=[from_date, to_date],time=select_time)
                                if user.is_agent:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                    print(b.win_amount,"agent")
                                else:
                                    total_winning = sum(winning.total_admin for winning in winnings)
                                    b.win_amount = total_winning
                                    print(b.win_amount,"dealer")
                                if winnings != 0 and user.is_agent:
                                    b.total_d_amount = b.total_c_amount - total_winning
                                elif winnings != 0 and user.is_dealer:
                                    b.total_d_amount = b.total_c_amount_admin - total_winning
                                else:
                                    b.total_d_amount = total_winning - b.total_c_amount
                                total_winning = sum(b.win_amount for b in bills)
                        else:
                            total_winning = 0
                        total_c_amount = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
                        total_balance = float(total_winning) - float(total_c_amount)
                        if 'pdfButton' in request.POST:
                            print("pdf working")
                            pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - " + selected_time +".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                            data = [headers]

                            # Fetch bills within the date range
                            bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date],time_id=select_time).all()

                            # Populate data for each bill
                            for bill in bills:
                                user = bill.user
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                                total_win = sum(winning.total if user.is_agent else winning.total_admin for winning in winnings)
                                balance = total_win - bill.total_c_amount  if user.is_agent else bill.total_c_amount_admin - total_win

                                display_user = bill.user.username

                                display_sale = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{display_sale:.2f}",
                                    f"{total_win:.2f}",
                                    f"{balance:.2f}",
                                ])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            story.append(Spacer(1, 12))
                            
                            total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                            total_win_text = f"Total Win Amount: {total_winning:.2f}"
                            total_balance_text = f"Total Balance: {total_balance:.2f}"

                            total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : select_dealer,
                            'selected_time' : select_time,
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                        }
                        return render(request,'agent/daily_report.html',context)
                    else:
                        print("its agent")
                        selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                        bills = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date],time_id=select_time).all()
                        paginator = Paginator(bills, 15)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        for bill in combined_bills:
                            winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            print(bill.win_amount,"win")
                            if winnings != 0:
                                bill.total_d_amount = bill.total_c_amount - total_winning
                            else:
                                bill.total_d_amount = total_winning - bill.total_c_amount
                        if bills:
                            for b in bills:
                                user = b.user
                                winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=b.id,date__range=[from_date, to_date],time=select_time)
                                if user.is_agent:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                else:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                if winnings != 0 and user.is_agent:
                                    b.total_d_amount = b.total_c_amount - total_winning
                                elif winnings != 0 and user.is_dealer:
                                    b.total_d_amount = b.total_c_amount - total_winning
                                else:
                                    b.total_d_amount = total_winning - b.total_c_amount
                                total_winning = sum(b.win_amount for b in bills)
                        else:
                            total_winning = 0
                        total_c_amount = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('dealer_games__c_amount'))['total_c_amount'] or 0
                        total_balance = float(total_c_amount) - float(total_winning)
                        for_agent = 'yes'
                        if 'pdfButton' in request.POST:
                            print("pdf working")
                            pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - " + selected_time + ".pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                            data = [headers]

                            # Fetch bills within the date range
                            bills = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date],time_id=select_time).all()

                            # Populate data for each bill
                            for bill in bills:
                                user = bill.user
                                winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                                total_win = sum(winning.total if user.is_agent else winning.total for winning in winnings)
                                balance = total_win - bill.total_c_amount  if user.is_agent else bill.total_c_amount - total_win

                                display_user = bill.user.username

                                display_sale = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{display_sale:.2f}",
                                    f"{total_win:.2f}",
                                    f"{balance:.2f}",
                                ])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            story.append(Spacer(1, 12))
                            
                            total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                            total_win_text = f"Total Win Amount: {total_winning:.2f}"
                            total_balance_text = f"Total Balance: {total_balance:.2f}"

                            total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : select_dealer,
                            'selected_time' : select_time,
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                            'for_agent' : for_agent,
                        }
                        return render(request,'agent/daily_report.html',context)
                else:
                    if select_dealer == str(agent_obj.user):
                        print("its agent")
                        bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date]).all()
                        paginator = Paginator(bills, 15)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        print(bills)
                        for bill in combined_bills:
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                            print(winnings)
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            if winnings != 0:
                                bill.total_d_amount = total_winning - bill.total_c_amount
                            else:
                                bill.total_d_amount = total_winning - bill.total_c_amount
                        if bills:
                            for b in bills:
                                user = b.user
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=b.id,date__range=[from_date, to_date])
                                if user.is_agent:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                    print(b.win_amount,"agent")
                                else:
                                    total_winning = sum(winning.total_admin for winning in winnings)
                                    b.win_amount = total_winning
                                    print(b.win_amount,"dealer")
                                if winnings != 0 and user.is_agent:
                                    b.total_d_amount = b.total_c_amount - total_winning
                                elif winnings != 0 and user.is_dealer:
                                    b.total_d_amount = b.total_c_amount_admin - total_winning
                                else:
                                    b.total_d_amount = total_winning - b.total_c_amount
                                total_winning = sum(b.win_amount for b in bills)
                        else:
                            total_winning = 0
                        total_c_amount = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
                        total_balance = float(total_winning) - float(total_c_amount)
                        if 'pdfButton' in request.POST:
                            print("pdf working")
                            pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                            data = [headers]

                            # Fetch bills within the date range
                            bills = Bill.objects.filter(Q(user=agent_obj.user.id),date__range=[from_date, to_date]).all()

                            # Populate data for each bill
                            for bill in bills:
                                user = bill.user
                                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                                total_win = sum(winning.total if user.is_agent else winning.total_admin for winning in winnings)
                                balance = total_win - bill.total_c_amount  if user.is_agent else bill.total_c_amount_admin - total_win

                                display_user = bill.user.username

                                display_sale = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{display_sale:.2f}",
                                    f"{total_win:.2f}",
                                    f"{balance:.2f}",
                                ])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            story.append(Spacer(1, 12))
                            
                            total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                            total_win_text = f"Total Win Amount: {total_winning:.2f}"
                            total_balance_text = f"Total Balance: {total_balance:.2f}"

                            total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : select_dealer,
                            'selected_time' : 'all',
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                        }
                        return render(request,'agent/daily_report.html',context)
                    else:
                        print("its agent")
                        bills = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date]).all()
                        paginator = Paginator(bills, 15)
                        page = request.POST.get('page', 1)
                        try:
                            combined_bills = paginator.page(page)
                        except PageNotAnInteger:
                            combined_bills = paginator.page(1)
                        except EmptyPage:
                            combined_bills = paginator.page(paginator.num_pages)
                        print(bills)
                        for bill in combined_bills:
                            winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=bill.id,date__range=[from_date, to_date])
                            print(winnings)
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            if winnings != 0:
                                bill.total_d_amount = bill.total_c_amount - total_winning
                            else:
                                bill.total_d_amount = total_winning - bill.total_c_amount
                        if bills:
                            for b in bills:
                                user = b.user
                                winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=b.id,date__range=[from_date, to_date])
                                if user.is_agent:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                else:
                                    total_winning = sum(winning.total for winning in winnings)
                                    b.win_amount = total_winning
                                if winnings != 0 and user.is_agent:
                                    b.total_d_amount = b.total_c_amount - total_winning
                                elif winnings != 0 and user.is_dealer:
                                    b.total_d_amount = b.total_c_amount - total_winning
                                else:
                                    b.total_d_amount = total_winning - b.total_c_amount
                                total_winning = sum(b.win_amount for b in bills)
                        else:
                            total_winning = 0
                        total_c_amount = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('dealer_games__c_amount'))['total_c_amount'] or 0
                        total_balance = float(total_c_amount) - float(total_winning)
                        if 'pdfButton' in request.POST:
                            print("pdf working")
                            pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - "  + "All Times.pdf"
                            response = HttpResponse(content_type='application/pdf')
                            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                            pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                            story = []

                            title_style = ParagraphStyle(
                                'Title',
                                parent=ParagraphStyle('Normal'),
                                fontSize=12,
                                textColor=colors.black,
                                spaceAfter=16,
                            )
                            title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                            title_paragraph = Paragraph(title_text, title_style)
                            story.append(title_paragraph)

                            # Add a line break after the title
                            story.append(Spacer(1, 12))

                            # Add table headers
                            headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                            data = [headers]

                            # Fetch bills within the date range
                            bills = Bill.objects.filter(Q(user=select_dealer),date__range=[from_date, to_date]).all()

                            # Populate data for each bill
                            for bill in bills:
                                user = bill.user
                                winnings = Winning.objects.filter(Q(dealer__user=select_dealer),bill=bill.id,date__range=[from_date, to_date])
                                total_win = sum(winning.total if user.is_agent else winning.total for winning in winnings)
                                balance = total_win - bill.total_c_amount  if user.is_agent else bill.total_c_amount - total_win

                                display_user = bill.user.username

                                display_sale = bill.total_c_amount if user.is_agent else bill.total_c_amount

                                formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                                data.append([
                                    formatted_date_time,
                                    display_user,
                                    f"{display_sale:.2f}",
                                    f"{total_win:.2f}",
                                    f"{balance:.2f}",
                                ])

                            # Create the table and apply styles
                            table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ]))

                            story.append(table)

                            story.append(Spacer(1, 12))
                            
                            total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                            total_win_text = f"Total Win Amount: {total_winning:.2f}"
                            total_balance_text = f"Total Balance: {total_balance:.2f}"

                            total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                            story.append(total_paragraph)

                            pdf.build(story)
                            return response
                        for_agent = 'yes'
                        context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : select_dealer,
                            'selected_time' : 'all',
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                            'for_agent' : for_agent
                        }
                        return render(request,'agent/daily_report.html',context)
        else:
                if select_time != 'all':
                    print("daily report issue")
                    selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                    bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time).all()
                    paginator = Paginator(bills, 15)
                    page = request.POST.get('page', 1)
                    try:
                        combined_bills = paginator.page(page)
                    except PageNotAnInteger:
                        combined_bills = paginator.page(1)
                    except EmptyPage:
                        combined_bills = paginator.page(paginator.num_pages)
                    print(bills)
                    for bill in combined_bills:
                        user = bill.user
                        winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                        print(winnings)
                        total_winning = sum(winning.total for winning in winnings)
                        if user.is_agent:
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            print(bill.win_amount,"***")
                        else:
                            total_winning = sum(winning.total_admin for winning in winnings)
                            bill.win_amount = total_winning
                            print(bill.win_amount,"winn")
                        if winnings != 0 and user.is_agent:
                            bill.total_d_amount = total_winning - bill.total_c_amount
                            print(bill.total_d_amount)
                        elif winnings != 0 and user.is_dealer:
                            bill.total_d_amount = bill.total_c_amount_admin - total_winning
                            print(bill.total_d_amount)
                    if bills:
                        for b in bills:
                            user = b.user
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=b.id,date__range=[from_date, to_date],time=select_time)
                            if user.is_agent:
                                total_winning = sum(winning.total for winning in winnings)
                                b.win_amount = total_winning
                            else:
                                total_winning = sum(winning.total_admin for winning in winnings)
                                b.win_amount = total_winning
                            if winnings != 0 and user.is_agent:
                                b.total_d_amount = b.total_c_amount - total_winning
                            elif winnings != 0 and user.is_dealer:
                                b.total_d_amount = b.total_c_amount - total_winning
                            else:
                                b.total_d_amount = total_winning - b.total_c_amount
                            total_winning = sum(b.win_amount for b in bills)
                    else:
                        total_winning = 0
                    agent_total_c_amount = Bill.objects.filter(Q(user=agent_obj.user),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
                    dealer_total_c_amount = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time).aggregate(total_c_amount=Sum('dealer_games__c_amount_admin'))['total_c_amount'] or 0
                    total_c_amount = agent_total_c_amount + dealer_total_c_amount
                    total_balance = float(total_winning) - float(total_c_amount)
                    if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + " - " + selected_time +".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                        data = [headers]

                        # Fetch bills within the date range
                        bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date],time_id=select_time).all()

                        # Populate data for each bill
                        for bill in bills:
                            user = bill.user
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date],time=select_time)
                            total_win = sum(winning.total if user.is_agent else winning.total_admin for winning in winnings)
                            balance = total_win - bill.total_c_amount  if user.is_agent else bill.total_c_amount_admin - total_win

                            display_user = bill.user.username

                            display_sale = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                            formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                            data.append([
                                formatted_date_time,
                                display_user,
                                f"{display_sale:.2f}",
                                f"{total_win:.2f}",
                                f"{balance:.2f}",
                            ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                        total_win_text = f"Total Win Amount: {total_winning:.2f}"
                        total_balance_text = f"Total Balance: {total_balance:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                            'dealers' : dealers,
                            'times' : times,
                            'combined_bills' : combined_bills,
                            'total_c_amount': total_c_amount,
                            'total_winning' : total_winning,
                            'total_balance' : total_balance,
                            'selected_dealer' : 'all',
                            'selected_time' : select_time,
                            'selected_from' : from_date,
                            'selected_to' : to_date,
                            'selected_game_time' : selected_game_time,
                        }
                    return render(request,'agent/daily_report.html',context)
                else:
                    print("this pdf")
                    bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date]).all()
                    paginator = Paginator(bills, 15)
                    page = request.POST.get('page', 1)
                    try:
                        combined_bills = paginator.page(page)
                    except PageNotAnInteger:
                        combined_bills = paginator.page(1)
                    except EmptyPage:
                        combined_bills = paginator.page(paginator.num_pages)
                    for bill in combined_bills:
                        winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                        user = bill.user
                        if user.is_agent:
                            total_winning = sum(winning.total for winning in winnings)
                            bill.win_amount = total_winning
                            bill.total_d_amount = total_winning - bill.total_c_amount
                        else:
                            total_winning = sum(winning.total_admin for winning in winnings)
                            bill.win_amount = total_winning
                            bill.total_d_amount = bill.total_c_amount_admin - total_winning
                    if bills:
                        for b in bills:
                            user = b.user
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=b.id,date__range=[from_date, to_date])
                            if user.is_agent:
                                total_winning = sum(winning.total for winning in winnings)
                                b.win_amount = total_winning
                            else:
                                total_winning = sum(winning.total_admin for winning in winnings)
                                b.win_amount = total_winning
                            if winnings != 0 and user.is_agent:
                                b.total_d_amount = b.total_c_amount - total_winning
                            elif winnings != 0 and user.is_dealer:
                                b.total_d_amount = b.total_c_amount - total_winning
                            else:
                                b.total_d_amount = total_winning - b.total_c_amount
                            total_winning = sum(b.win_amount for b in bills)
                    else:
                        total_winning = 0
                    agent_total_c_amount = Bill.objects.filter(Q(user=agent_obj.user),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
                    dealer_total_c_amount = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_c_amount=Sum('dealer_games__c_amount_admin'))['total_c_amount'] or 0
                    total_c_amount = agent_total_c_amount + dealer_total_c_amount
                    total_balance = float(total_winning) - float(total_c_amount)
                    select_dealer = 'all'
                    select_time = 'all'
                    if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Daily_Report" + "-" + from_date + "-" + to_date + "- All Times.pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Daily Report" + "( " + from_date + " - " + to_date + " )" + " - All Times"
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Date", "Agent", "T.Sale", "T.W.Amount", "Balance"]
                        data = [headers]

                        # Fetch bills within the date range
                        bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date]).all()

                        # Populate data for each bill
                        for bill in bills:
                            user = bill.user
                            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=bill.id,date__range=[from_date, to_date])
                            total_win = sum(winning.total if user.is_agent else winning.total_admin for winning in winnings)
                            balance = total_win - bill.total_c_amount  if user.is_agent else bill.total_c_amount_admin - total_win

                            display_user = bill.user.username

                            display_sale = bill.total_c_amount if user.is_agent else bill.total_c_amount_admin

                            formatted_date_time = bill.created_at.astimezone(timezone.get_current_timezone()).strftime("%b. %d, %Y %H:%M")

                            data.append([
                                formatted_date_time,
                                display_user,
                                f"{display_sale:.2f}",
                                f"{total_win:.2f}",
                                f"{balance:.2f}",
                            ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {total_c_amount:.2f}"
                        total_win_text = f"Total Win Amount: {total_winning:.2f}"
                        total_balance_text = f"Total Balance: {total_balance:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}<br/>{total_balance_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                        'dealers' : dealers,
                        'times' : times,
                        'combined_bills' : combined_bills,
                        'total_c_amount': total_c_amount,
                        'total_winning' : total_winning,
                        'total_balance' : total_balance,
                        'selected_dealer' : select_dealer,
                        'selected_time' : select_time,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request,'agent/daily_report.html',context)
    else:
        bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date).all()
        customers_list = []
        customers = Bill.objects.filter(Q(user=agent_obj.user),date=current_date).exclude(customer='')
        for cust in customers:
            if cust.customer not in customers_list:
                customers_list.append(cust.customer)
        paginator = Paginator(bills, 15)
        page = request.GET.get('page', 1)
        try:
            combined_bills = paginator.page(page)
        except PageNotAnInteger:
            combined_bills = paginator.page(1)
        except EmptyPage:
            combined_bills = paginator.page(paginator.num_pages)
        for bill in combined_bills:
            winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=bill.id,date=current_date)
            user = bill.user
            if user.is_agent:
                total_winning = sum(winning.total for winning in winnings)
                bill.win_amount = total_winning
                bill.total_d_amount = total_winning - bill.total_c_amount
            else:
                total_winning = sum(winning.total_admin for winning in winnings)
                bill.win_amount = total_winning
                bill.total_d_amount = bill.total_c_amount_admin - total_winning
            print(bill.total_d_amount,"balance amount")
        if bills:
            for b in bills:
                user = b.user
                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),bill=b.id,date=current_date)
                if user.is_agent:
                    total_winning = sum(winning.total for winning in winnings)
                    b.win_amount = total_winning
                else:
                    total_winning = sum(winning.total_admin for winning in winnings)
                    b.win_amount = total_winning
                if winnings != 0 and user.is_agent:
                    b.total_d_amount = b.total_c_amount - total_winning
                elif winnings != 0 and user.is_dealer:
                    b.total_d_amount = b.total_c_amount - total_winning
                else:
                    b.total_d_amount = total_winning - b.total_c_amount
                total_winning = sum(b.win_amount for b in bills)
        else:
            total_winning = 0
        agent_total_c_amount = Bill.objects.filter(Q(user=agent_obj.user),date=current_date).aggregate(total_c_amount=Sum('agent_games__c_amount'))['total_c_amount'] or 0
        dealer_total_c_amount = Bill.objects.filter(Q(user__dealer__agent=agent_obj),date=current_date).aggregate(total_c_amount=Sum('dealer_games__c_amount_admin'))['total_c_amount'] or 0
        total_c_amount = agent_total_c_amount + dealer_total_c_amount
        total_balance = float(total_winning) - float(total_c_amount)
        select_dealer = 'all'
        select_time = 'all'
        selected_game_time = 'all times'
        context = {
            'dealers' : dealers,
            'times' : times,
            'combined_bills' : combined_bills,
            'total_c_amount': total_c_amount,
            'total_winning' : total_winning,
            'total_balance' : total_balance,
            'selected_dealer' : select_dealer,
            'selected_time' : select_time,
            'selected_game_time' : selected_game_time,
            'customers' : customers_list,
        }
        return render(request,'agent/daily_report.html',context)

@login_required
@agent_required
def winning_report(request):
    winning = None
    times = PlayTime.objects.filter().all().order_by('id')
    print(times)
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    winnings = []
    totals = []
    aggregated_winnings = []
    customers_list = []
    customers = Bill.objects.filter(user=agent_obj.user.id,date=current_date)
    for customer in customers:
        if customer.customer != '':
            if customer.customer not in customers_list:
                customers_list.append(customer.customer)
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_time = request.POST.get('time')
        customer = request.POST.get('customer')
        print(customer,"customer")
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_time != 'all':
            if str(customer) != str(agent_obj.user) and str(customer)!='all' and not str(customer).isdigit():
                selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                bills = Bill.objects.filter(user=agent_obj.user.id, customer=customer, date__range=[from_date, to_date], time_id=select_time)
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + selected_time + ".pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : select_time,
                    'customers' : customers_list,
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
            elif str(customer) != str(agent_obj.user) and str(customer).isdigit():
                selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                bills = Bill.objects.filter(user=customer,date__range=[from_date, to_date], time_id=select_time)
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(dealer__user=customer),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(dealer__user=customer),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + selected_time + ".pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(dealer__user=customer),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : select_time,
                    'customers' : customers_list,
                    'dealer_only' : 'yes',
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
            elif str(customer) == str(agent_obj.user):
                selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                bills = Bill.objects.filter(Q(user=agent_obj.user),date__range=[from_date, to_date], time_id=select_time)
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)
                print(winnings)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals_agent = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                totals = {
                    'total_count': (totals_agent['total_count'] or 0),
                    'total_commission': (totals_agent['total_commission'] or 0),
                    'total_rs': (totals_agent['total_rs'] or 0),
                    'total_net': (totals_agent['total_net'] or 0),
                }
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + selected_time + ".pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : select_time,
                    'customers' : customers_list,
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
            else:
                selected_time = selected_game_time.game_time.strftime("%I:%M %p")
                bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date__range=[from_date, to_date], time_id=select_time)
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals_agent = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                totals_dealer = Winning.objects.filter(Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission_admin'),total_rs=Sum('prize_admin'),total_net=Sum('total_admin'))
                totals = {
                    'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                    'total_commission': (totals_agent['total_commission'] or 0) + (totals_dealer['total_commission'] or 0),
                    'total_rs': (totals_agent['total_rs'] or 0) + (totals_dealer['total_rs'] or 0),
                    'total_net': (totals_agent['total_net'] or 0) + (totals_dealer['total_net'] or 0),
                }
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + selected_time + ".pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],time=select_time,bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : select_time,
                    'customers' : customers_list,
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
        else:
            if str(customer) != str(agent_obj.user) and str(customer)!='all' and not str(customer).isdigit():
                bills = Bill.objects.filter(user=agent_obj.user.id, customer=customer, date__range=[from_date, to_date])
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],bill__in=bill_ids)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + "All Times.pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date],bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : 'all',
                    'customers' : customers_list,
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : 'all',
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
            elif str(customer) != str(agent_obj.user) and str(customer).isdigit():
                bills = Bill.objects.filter(user=customer,date__range=[from_date, to_date])
                print(bills)
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(dealer__user=customer),date__range=[from_date, to_date],bill__in=bill_ids)
                print(winnings)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(dealer__user=customer),date__range=[from_date, to_date],bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + "All Times.pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(dealer__user=customer),date__range=[from_date, to_date],bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : 'all',
                    'customers' : customers_list,
                    'dealer_only' : 'yes',
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : 'all',
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
            elif str(customer) == str(agent_obj.user):
                bills = Bill.objects.filter(user=agent_obj.user,date__range=[from_date, to_date])
                bill_ids = [bill.id for bill in bills]
                winnings = Winning.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],bill__in=bill_ids)
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals = Winning.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],bill__in=bill_ids).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + "All Times.pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent=agent_obj),date__range=[from_date, to_date],bill__in=bill_ids)

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission
                            prize = win.prize
                            total = win.total

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'dealers' : dealers,
                    'aggr' : aggregated_winnings,
                    'selected_time' : 'all',
                    'customers' : customers_list,
                    'dealer_only' : 'yes',
                    'selected_customer' : customer, 
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : 'all',
                    'bill': winning.bill if winning else None
                }
                return render(request,'agent/winning_report.html',context)
            else:
                winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date])
                for winning in winnings:
                    winning.bill = Bill.objects.get(pk=winning.bill)
                aggregated_winnings = winnings.values('LSK', 'number').annotate(
                    total_count=Sum('count'),
                    total_commission=Sum('commission'),
                    total_prize=Sum('prize'),
                    total_net=Sum('total'),
                    position=F('position'),
                )
                totals_agent = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
                totals_dealer = Winning.objects.filter(Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_commission=Sum('commission_admin'),total_rs=Sum('prize_admin'),total_net=Sum('total_admin'))
                totals = {
                    'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
                    'total_commission': (totals_agent['total_commission'] or 0) + (totals_dealer['total_commission'] or 0),
                    'total_rs': (totals_agent['total_rs'] or 0) + (totals_dealer['total_rs'] or 0),
                    'total_net': (totals_agent['total_net'] or 0) + (totals_dealer['total_net'] or 0),
                }
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Report" + "-" + from_date + "-" + to_date + "- " + "All Times.pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                        # Add table headers
                    headers = ["Bill", "User", "T", "PN", "C", "PP", "SU", "RS", "Net"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date__range=[from_date, to_date])

                    # Populate data for each bill
                    for win in winnings:
                        if win.agent:
                            bill_instance = Bill.objects.get(pk=win.bill)
                            if bill_instance.customer == '':
                                agent_dealer = bill_instance.user
                            else:
                                agent_dealer = bill_instance.customer
                            commission = win.commission
                            prize = win.prize
                            total = win.total
                        else:
                            agent_dealer = win.dealer.user
                            commission = win.commission_admin
                            prize = win.prize_admin
                            total = win.total_admin

                        print(win.bill,"bill id")

                        data.append([
                            win.bill,
                            agent_dealer,
                            win.LSK,
                            win.number,
                            win.count,
                            win.position,
                            commission,
                            prize,
                            total,
                        ])

                    # Create the table and apply styles
                    table = Table(data, colWidths=[60, 60, 60, 60, 60])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    story.append(Spacer(1, 12))
                        
                    total_count_text = f"Count: {totals['total_count']}"
                    total_comm_text = f"Comm: {totals['total_commission']:.2f}"
                    total_win_text = f"Total: {totals['total_rs']:.2f}"
                    total_net_text = f"Net: {totals['total_net']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_comm_text}<br/>{total_win_text}<br/>{total_net_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'winnings' : winnings,
                    'totals' : totals,
                    'aggr' : aggregated_winnings,
                    'selected_customer' : 'all',
                    'selected_time' : 'all',
                    'customers' : customers_list,
                    'dealers' : dealers,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                    'bill' : winning.bill
                }
                return render(request,'agent/winning_report.html',context)
    else:
        winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id) | Q(dealer__agent__user=agent_obj.user.id),date=current_date)
        agent_winnings = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date=current_date)
        dealer_winnings = Winning.objects.filter(Q(dealer__agent__user=agent_obj.user.id),date=current_date)
        for winning in winnings:
            winning.bill = Bill.objects.get(pk=winning.bill)
        agent_aggregated = agent_winnings.values('LSK', 'number').annotate(
            total_count=Sum('count'),
            total_commission=Sum('commission'),
            total_prize=Sum('prize'),
            total_net=Sum('total'),
            position=F('position'),
        )
        dealer_aggregated = dealer_winnings.values('LSK', 'number').annotate(
            total_count=Sum('count'),
            total_commission=Sum('commission_admin'),
            total_prize=Sum('prize_admin'),
            total_net=Sum('total_admin'),
            position=F('position'),
        )
        aggregated_winnings = agent_aggregated | dealer_aggregated
        totals_agent = Winning.objects.filter(Q(agent__user=agent_obj.user.id),date=current_date).aggregate(total_count=Sum('count'),total_commission=Sum('commission'),total_rs=Sum('prize'),total_net=Sum('total'))
        totals_dealer = Winning.objects.filter(Q(dealer__agent__user=agent_obj.user.id),date=current_date).aggregate(total_count=Sum('count'),total_commission=Sum('commission_admin'),total_rs=Sum('prize_admin'),total_net=Sum('total_admin'))
        totals = {
            'total_count': (totals_agent['total_count'] or 0) + (totals_dealer['total_count'] or 0),
            'total_commission': (totals_agent['total_commission'] or 0) + (totals_dealer['total_commission'] or 0),
            'total_rs': (totals_agent['total_rs'] or 0) + (totals_dealer['total_rs'] or 0),
            'total_net': (totals_agent['total_net'] or 0) + (totals_dealer['total_net'] or 0),
        }
        selected_game_time = 'all times'
        selected_time = 'all'
        context = {
            'customers' : customers_list,
            'dealers' : dealers,
            'selected_customer' : 'all',
            'times' : times,
            'winnings' : winnings,
            'totals' : totals,
            'aggr' : aggregated_winnings,
            'selected_time' : selected_time,
            'selected_game_time' : selected_game_time,
            'bill': winning.bill if winning else None
        }
        return render(request,'agent/winning_report.html',context) 

@login_required
@agent_required
def count_salereport(request):
    times = PlayTime.objects.filter().all().order_by('id')
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
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_dealer != 'all':
            if select_dealer == str(agent_obj.user):
                if select_time != 'all':
                    selected_time = selected_game_time.game_time.strftime("%I:%M %p")

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
                    if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Sales_Count_Report" + "-" + from_date + "-" +to_date + " - " + selected_time +".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Sales Count Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Position", "Count", "Amount"]
                        data = [headers]

                        agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,time=select_time, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                    
                        data.append([
                            "Super",
                            super_totals['total_count'],
                            super_totals['total_amount'],

                        ])

                        data.append([
                            "Box",
                            box_totals['total_count'],
                            box_totals['total_amount'],

                        ])

                        data.append([
                            "Single",
                            single_totals['total_count'],
                            single_totals['total_amount'],
                        ])
                        data.append([
                            "Double",
                            double_totals['total_count'],
                            double_totals['total_amount'],
                          
                        ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {totals['net_count']:.2f}"
                        total_win_text = f"Total Win Amount: {totals['net_amount']:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                        'times' : times,
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : select_time,
                        'selected_dealer' : select_dealer,
                        'totals' : totals,
                        'selected_game_time' : selected_game_time,
                        
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
                    if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Sales_Count_Report" + "-" + from_date + "-" + to_date + " - " +"All Times" +".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Sales Count Report" + "( " + from_date + " - " + to_date + " )" + "All Times  "
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Position", "Count", "Amount"]
                        data = [headers]

                        # Populate data for each bill
                        agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                
                        data.append([
                            "Super",
                            super_totals['total_count'],
                            super_totals['total_amount'],

                        ])

                        data.append([
                            "Box",
                            box_totals['total_count'],
                            box_totals['total_amount'],

                        ])

                        data.append([
                            "Single",
                            single_totals['total_count'],
                            single_totals['total_amount'],
                        ])
                        data.append([
                            "Double",
                            double_totals['total_count'],
                            double_totals['total_amount'],
                          
                        ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {totals['net_count']:.2f}"
                        total_win_text = f"Total Win Amount: {totals['net_amount']:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                        'times' : times,
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : 'all',
                        'selected_dealer' : select_dealer,
                        'totals' : totals,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request,'agent/count_salereport.html',context)
            else:
                if select_time != 'all':
                    selected_time = selected_game_time.game_time.strftime("%I:%M %p")
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
                    if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Sales_Count_Report" + "-" + from_date + "-" + to_date + " - " + selected_time +".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Sales Count Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Position", "Count", "Amount"]
                        data = [headers]

                        # Populate data for each bill
                        agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                
                        data.append([
                            "Super",
                            super_totals['total_count'],
                            super_totals['total_amount'],

                        ])

                        data.append([
                            "Box",
                            box_totals['total_count'],
                            box_totals['total_amount'],

                        ])

                        data.append([
                            "Single",
                            single_totals['total_count'],
                            single_totals['total_amount'],
                        ])
                        data.append([
                            "Double",
                            double_totals['total_count'],
                            double_totals['total_amount'],
                          
                        ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {totals['net_count']:.2f}"
                        total_win_text = f"Total Win Amount: {totals['net_amount']:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response

                    context = {
                        'times' : times,
                        'dealers' : dealers,
                        'super_totals' : super_totals,
                        'box_totals' : box_totals,
                        'double_totals': double_totals,
                        'single_totals' : single_totals,
                        'selected_time' : select_time,
                        'selected_dealer' : select_dealer,
                        'totals' : totals,
                        'selected_game_time' : selected_game_time,
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
                        'totals' : totals,
                        'selected_game_time' : selected_game_time,
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
                if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Sales_Count_Report" + "-" + from_date + "-" + to_date + " - " +"All Times" +".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Sales Count Report" + "( " + from_date + " - " + to_date + " )" + "All Times  "
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Position", "Count", "Amount"]
                        data = [headers]

                        # Populate data for each bill
                        agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                
                        data.append([
                            "Super",
                            super_totals['total_count'],
                            super_totals['total_amount'],

                        ])

                        data.append([
                            "Box",
                            box_totals['total_count'],
                            box_totals['total_amount'],

                        ])

                        data.append([
                            "Single",
                            single_totals['total_count'],
                            single_totals['total_amount'],
                        ])
                        data.append([
                            "Double",
                            double_totals['total_count'],
                            double_totals['total_amount'],
                          
                        ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {totals['net_count']:.2f}"
                        total_win_text = f"Total Win Amount: {totals['net_amount']:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response

                context = {
                    'times' : times,
                    'dealers' : dealers,
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'double_totals': double_totals,
                    'single_totals' : single_totals,
                    'selected_time' : select_time,
                    'selected_dealer' : 'all',
                    'totals' : totals,
                    'selected_game_time' : selected_game_time,
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
                if 'pdfButton' in request.POST:
                        print("pdf working")
                        pdf_filename = "Sales_Count_Report" + "-" + from_date + "-" + to_date + " - " +"All Times" +".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Sales Count Report" + "( " + from_date + " - " + to_date + " )" + "All Times  "
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                        # Add table headers
                        headers = ["Position", "Count", "Amount"]
                        data = [headers]

                        # Populate data for each bill
                        agent_super = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_box = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_single = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        agent_double = AgentGame.objects.filter(date__range=[from_date, to_date],agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_super = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj,LSK='Super').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_box = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK='Box').aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_single = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value1).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                        dealer_double = DealerGame.objects.filter(date__range=[from_date, to_date],dealer__agent=agent_obj, LSK__in=lsk_value2).aggregate(total_count=Sum('count'),total_amount=Sum('c_amount'))
                
                        data.append([
                            "Super",
                            super_totals['total_count'],
                            super_totals['total_amount'],

                        ])

                        data.append([
                            "Box",
                            box_totals['total_count'],
                            box_totals['total_amount'],

                        ])

                        data.append([
                            "Single",
                            single_totals['total_count'],
                            single_totals['total_amount'],
                        ])
                        data.append([
                            "Double",
                            double_totals['total_count'],
                            double_totals['total_amount'],
                          
                        ])

                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        story.append(Spacer(1, 12))
                        
                        total_sale_text = f"Total Sale: {totals['net_count']:.2f}"
                        total_win_text = f"Total Win Amount: {totals['net_amount']:.2f}"

                        total_paragraph = Paragraph(f"{total_sale_text}<br/>{total_win_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response


                context = {
                    'times' : times,
                    'dealers' : dealers,
                    'super_totals' : super_totals,
                    'box_totals' : box_totals,
                    'double_totals': double_totals,
                    'single_totals' : single_totals,
                    'selected_time' : 'all',
                    'selected_time':'selected_time',
                    'selected_dealer' : 'all',
                    'totals' : totals,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'agent/count_salereport.html',context)
    selected_game_time = 'all times'
    context = {
        'times' : times,
        'dealers' : dealers,
        'super_totals' : super_totals,
        'box_totals' : box_totals,
        'double_totals': double_totals,
        'single_totals' : single_totals,
        'selected_time' : 'all',
        'selected_dealer' : 'all',
        'totals' : totals,
        'selected_game_time' : selected_game_time
    }
    return render(request,'agent/count_salereport.html',context) 

@login_required
@agent_required
def winning_countreport(request):
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    print(dealers)
    times = PlayTime.objects.filter().all().order_by('id')
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    winnings = Winning.objects.filter(date=current_date).all()
    totals = Winning.objects.filter(date=current_date).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
    for_agent = 'yes'
    if request.method == 'POST':
        select_time = request.POST.get('time')
        select_agent = request.POST.get('select_agent')
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        try:
            selected_game_time = PlayTime.objects.get(id=select_time)
        except:
            selected_game_time = 'all times'
        if select_time != 'all':
            selected_time = selected_game_time.game_time.strftime("%I:%M %p")
            if select_agent != 'all':
                if select_agent == str(agent_obj.user):
                    winnings = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date],time=select_time)
                    totals = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                    if 'pdfButton' in request.POST:
                        pdf_filename = "Winning Count Report" + "-" + from_date + "-" + to_date + " - " + selected_time + ".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Winning Count Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                                            # Add a line break after the title
                        story.append(Spacer(1, 12))

                                            # Add table headers
                        headers = ["Particular", "Number", "Count"]
                        data = [headers]

                        winnings = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date],time=select_time)

                        for win in winnings:

                            if win.agent:
                                amount = win.total
                            else:
                                amount = win.total
                                                # Add bill information to the table data
                            data.append([
                                win.position,
                                win.count,
                                amount
                            ])

                                            # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        total_count_text = f"Total Count: {totals['total_count']:.2f}"
                        total_amount_text = f"Total Amount: {totals['total_prize']:.2f}"

                        total_paragraph = Paragraph(f"{total_count_text}<br/>{total_amount_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : select_time,
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request,'agent/winning_countreport.html',context)
                else:
                    winnings = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date],time=select_time)
                    totals = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                    if 'pdfButton' in request.POST:
                        pdf_filename = "Winning Count Report" + "-" + from_date + "-" + to_date + " - " + selected_time + ".pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Winning Count Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                                            # Add a line break after the title
                        story.append(Spacer(1, 12))

                                            # Add table headers
                        headers = ["Particular", "Number", "Count"]
                        data = [headers]

                        winnings = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date],time=select_time)

                        for win in winnings:

                            if win.agent:
                                amount = win.total
                            else:
                                amount = win.total
                                                # Add bill information to the table data
                            data.append([
                                win.position,
                                win.count,
                                amount
                            ])

                                            # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        total_count_text = f"Total Count: {totals['total_count']:.2f}"
                        total_amount_text = f"Total Amount: {totals['total_prize']:.2f}"

                        total_paragraph = Paragraph(f"{total_count_text}<br/>{total_amount_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
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
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request,'agent/winning_countreport.html',context)
            else:
                winnings = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time)
                totals = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time).aggregate(total_count=Sum('count'),total_prize=Sum('total'))
                print(select_agent)
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Count Report" + "-" + from_date + "-" + to_date + " - " + selected_time + ".pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Count Report" + "( " + from_date + " - " + to_date + " )" + selected_time
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                                        # Add a line break after the title
                    story.append(Spacer(1, 12))

                                        # Add table headers
                    headers = ["Particular", "Number", "Count"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date],time=select_time)

                    for win in winnings:

                        if win.agent:
                            amount = win.total
                        else:
                            amount = win.total
                                            # Add bill information to the table data
                        data.append([
                            win.position,
                            win.count,
                            amount
                        ])

                                        # Create the table and apply styles
                    table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    total_count_text = f"Total Count: {totals['total_count']:.2f}"
                    total_amount_text = f"Total Amount: {totals['total_prize']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_amount_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'agent_obj' : agent_obj,
                    'dealers':dealers,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : select_time,
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'agent/winning_countreport.html',context)
        else:
            if select_agent != 'all':
                if select_agent == str(agent_obj.user):
                    winnings = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date])
                    totals = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                    print(select_agent)
                    if 'pdfButton' in request.POST:
                        pdf_filename = "Winning Count Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Winning Count Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                                        # Add table headers
                        headers = ["Particular", "Number", "Count"]
                        data = [headers]

                        winnings = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date])

                        for win in winnings:

                            if win.agent:
                                amount = win.total
                            else:
                                amount = win.total
                                            # Add bill information to the table data
                            data.append([
                                win.position,
                                win.count,
                                amount
                            ])

                                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        total_count_text = f"Total Count: {totals['total_count']:.2f}"
                        total_amount_text = f"Total Amount: {totals['total_prize']:.2f}"

                        total_paragraph = Paragraph(f"{total_count_text}<br/>{total_amount_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : 'all',
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request,'agent/winning_countreport.html',context)
                else:
                    winnings = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date])
                    totals = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                    print(winnings)
                    print(select_agent)
                    if 'pdfButton' in request.POST:
                        pdf_filename = "Winning Count Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                        story = []

                        title_style = ParagraphStyle(
                            'Title',
                            parent=ParagraphStyle('Normal'),
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=16,
                        )
                        title_text = "Winning Count Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                        title_paragraph = Paragraph(title_text, title_style)
                        story.append(title_paragraph)

                                        # Add a line break after the title
                        story.append(Spacer(1, 12))

                                        # Add table headers
                        headers = ["Particular", "Number", "Count"]
                        data = [headers]

                        winnings = Winning.objects.filter(dealer__user=select_agent,date__range=[from_date, to_date])

                        for win in winnings:

                            if win.agent:
                                amount = win.total
                            else:
                                amount = win.total
                                            # Add bill information to the table data
                            data.append([
                                win.position,
                                win.count,
                                amount
                            ])

                                        # Create the table and apply styles
                        table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        story.append(table)

                        total_count_text = f"Total Count: {totals['total_count']:.2f}"
                        total_amount_text = f"Total Amount: {totals['total_prize']:.2f}"

                        total_paragraph = Paragraph(f"{total_count_text}<br/>{total_amount_text}", title_style)
                        story.append(total_paragraph)

                        pdf.build(story)
                        return response
                    context = {
                        'times' : times,
                        'agent_obj' : agent_obj,
                        'dealers':dealers,
                        'winnings' : winnings,
                        'totals' : totals,
                        'selected_time' : 'all',
                        'selected_agent' : select_agent,
                        'selected_from' : from_date,
                        'selected_to' : to_date,
                        'selected_game_time' : selected_game_time,
                    }
                    return render(request,'agent/winning_countreport.html',context)
            else:
                winnings = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date])
                totals = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date]).aggregate(total_count=Sum('count'),total_prize=Sum('prize'))
                print(select_agent)
                if 'pdfButton' in request.POST:
                    pdf_filename = "Winning Count Report" + "-" + from_date + "-" + to_date + " - " + "All Times.pdf"
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                    pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                    story = []

                    title_style = ParagraphStyle(
                        'Title',
                        parent=ParagraphStyle('Normal'),
                        fontSize=12,
                        textColor=colors.black,
                        spaceAfter=16,
                    )
                    title_text = "Winning Count Report" + "( " + from_date + " - " + to_date + " )" + "All Times"
                    title_paragraph = Paragraph(title_text, title_style)
                    story.append(title_paragraph)

                                    # Add a line break after the title
                    story.append(Spacer(1, 12))

                                    # Add table headers
                    headers = ["Particular", "Number", "Count"]
                    data = [headers]

                    winnings = Winning.objects.filter(Q(agent=agent_obj) | Q(dealer__agent=agent_obj),date__range=[from_date, to_date])

                    for win in winnings:

                        if win.agent:
                            amount = win.total
                        else:
                            amount = win.total
                                        # Add bill information to the table data
                        data.append([
                            win.position,
                            win.count,
                            amount
                        ])

                                    # Create the table and apply styles
                    table = Table(data, colWidths=[120, 100, 80, 80, 80])  # Adjust colWidths as needed
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))

                    story.append(table)

                    total_count_text = f"Total Count: {totals['total_count']:.2f}"
                    total_amount_text = f"Total Amount: {totals['total_prize']:.2f}"

                    total_paragraph = Paragraph(f"{total_count_text}<br/>{total_amount_text}", title_style)
                    story.append(total_paragraph)

                    pdf.build(story)
                    return response
                context = {
                    'times' : times,
                    'agent_obj' : agent_obj,
                    'dealers':dealers,
                    'winnings' : winnings,
                    'totals' : totals,
                    'selected_time' : 'all',
                    'selected_agent' : 'all',
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'selected_game_time' : selected_game_time,
                }
                return render(request,'agent/winning_countreport.html',context)
    selected_game_time = 'all times'
    context = {
        'times' : times,
        'agent_obj' : agent_obj,
        'dealers':dealers,
        'winnings' : winnings,
        'totals' : totals,
        'selected_agent' : 'all',
        'selected_time' : 'all',
        'selected_game_time' : selected_game_time,
        'for_agent' : for_agent
    }
    return render(request,'agent/winning_countreport.html',context) 

@login_required
@agent_required
def payment_report(request):
    agent_obj = Agent.objects.get(user=request.user)
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    collections = DealerCollectionReport.objects.filter(date=current_date,dealer__agent=agent_obj).all()
    from_dealer_total = DealerCollectionReport.objects.filter(date=current_date,from_or_to='received',dealer__agent=agent_obj).aggregate(from_dealer=Sum('amount'))
    print(from_dealer_total)
    to_dealer_total = DealerCollectionReport.objects.filter(date=current_date,from_or_to='paid',dealer__agent=agent_obj).aggregate(to_dealer=Sum('amount'))
    print(to_dealer_total)
    from_dealer_amount = from_dealer_total['from_dealer'] if from_dealer_total['from_dealer'] else 0
    to_dealer_amount = to_dealer_total['to_dealer'] if to_dealer_total['to_dealer'] else 0
    profit_or_loss_dealer = from_dealer_amount - to_dealer_amount
    print(profit_or_loss_dealer,"dealer collection")
    #agent collection
    agent_collection = CollectionReport.objects.filter(date=current_date,agent=agent_obj).all()
    from_agent_total = CollectionReport.objects.filter(date=current_date,from_or_to='received',agent=agent_obj).aggregate(from_agent=Sum('amount'))
    to_agent_total = CollectionReport.objects.filter(date=current_date,from_or_to='paid',agent=agent_obj).aggregate(to_agent=Sum('amount'))
    from_agent_amount = from_agent_total['from_agent'] if from_agent_total['from_agent'] else 0
    to_agent_amount = to_agent_total['to_agent'] if to_agent_total['to_agent'] else 0
    profit_or_loss_of_agent =  to_agent_amount - from_agent_amount
    print(profit_or_loss_of_agent,"agent collection")
    print(from_agent_total, to_agent_total)
    profit_or_loss = profit_or_loss_of_agent + profit_or_loss_dealer
    if request.method == 'POST':
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        select_dealer = request.POST.get('select-dealer')
        from_or_to = request.POST.get('from-to')
        
        if select_dealer != 'all':
            if from_or_to != 'all' and from_or_to == 'received':
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,from_or_to='received').all()
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
            if from_or_to != 'all' and from_or_to == 'paid':
                collections = DealerCollectionReport.objects.filter(date__range=[from_date, to_date],dealer__user=select_dealer,from_or_to='paid').all()
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
            if from_or_to != 'all' and from_or_to == 'received':

                agent_collection = CollectionReport.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all()
                to_agent_total = CollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='paid',agent=agent_obj).aggregate(to_agent=Sum('amount'))
                to_agent_amount = to_agent_total['to_agent'] if to_agent_total['to_agent'] else 0
                profit_or_loss_of_agent =  to_agent_amount
                agent_profit_or_loss = profit_or_loss_of_agent

                collections = DealerCollectionReport.objects.filter(dealer__agent=agent_obj,date__range=[from_date, to_date],from_or_to='received').all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                from_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = from_dealer_amount['amount'] if from_dealer_amount['amount'] else 0
                print(profit_or_loss, "hello")
                total_profit = profit_or_loss + agent_profit_or_loss
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'agent_collection' : agent_collection,
                    'profit_or_loss': total_profit,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'agent/payment_report.html', context)
            if from_or_to != 'all' and from_or_to == 'paid':

                agent_collection = CollectionReport.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all()
                from_agent_total = CollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='received',agent=agent_obj).aggregate(from_agent=Sum('amount'))
                from_agent_amount = from_agent_total['from_agent'] if from_agent_total['from_agent'] else 0
                profit_or_loss_of_agent =  from_agent_amount
                agent_profit_or_loss = profit_or_loss_of_agent

                collections = DealerCollectionReport.objects.filter(dealer__agent=agent_obj,date__range=[from_date, to_date],from_or_to='paid').all()
                print(from_date, to_date, select_dealer, from_or_to)
                print(collections)
                to_dealer_amount = collections.aggregate(amount=Sum('amount'))
                profit_or_loss = to_dealer_amount['amount'] if to_dealer_amount['amount'] else 0
                profit_or_loss = -profit_or_loss
                print(profit_or_loss, "hello")
                total_profit = profit_or_loss + agent_profit_or_loss
                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'profit_or_loss': total_profit,
                    'agent_collection' : agent_collection,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'agent/payment_report.html', context)
            else:

                agent_collection = CollectionReport.objects.filter(date__range=[from_date, to_date],agent=agent_obj).all()
                from_agent_total = CollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='received',agent=agent_obj).aggregate(from_agent=Sum('amount'))
                to_agent_total = CollectionReport.objects.filter(date__range=[from_date, to_date],from_or_to='paid',agent=agent_obj).aggregate(to_agent=Sum('amount'))
                from_agent_amount = from_agent_total['from_agent'] if from_agent_total['from_agent'] else 0
                to_agent_amount = to_agent_total['to_agent'] if to_agent_total['to_agent'] else 0
                profit_or_loss_of_agent =  to_agent_amount - from_agent_amount
                agent_profit_or_loss = profit_or_loss_of_agent

                collections = DealerCollectionReport.objects.filter(dealer__agent=agent_obj,date__range=[from_date, to_date]).all()
                from_dealer_total = DealerCollectionReport.objects.filter(dealer__agent=agent_obj,date__range=[from_date, to_date],from_or_to='received').aggregate(from_agent=Sum('amount'))
                print(from_dealer_total,"from")
                to_dealer_total = DealerCollectionReport.objects.filter(dealer__agent=agent_obj,date__range=[from_date, to_date],from_or_to='paid').aggregate(to_agent=Sum('amount'))
                print(to_dealer_total,"to")
                from_dealer_amount = from_dealer_total['from_agent'] if from_dealer_total['from_agent'] else 0
                to_dealer_amount = to_dealer_total['to_agent'] if to_dealer_total['to_agent'] else 0
                profit_or_loss = from_dealer_amount - to_dealer_amount

                total_profit = profit_or_loss + agent_profit_or_loss

                context = {
                    'dealers': dealers,
                    'collections': collections,
                    'agent_collection' : agent_collection,
                    'profit_or_loss': total_profit,
                    'selected_agent' : select_dealer,
                    'from_or_to' : from_or_to,
                    'selected_from' : from_date,
                    'selected_to' : to_date
                }
                return render(request, 'agent/payment_report.html', context)
    else:
        context = {
            'dealers' : dealers,
            'collections' : collections,
            'agent_collection' : agent_collection,
            'selected_agent' : 'all',
            'profit_or_loss' : profit_or_loss,
            'from_or_to' : 'all',
        }
    return render(request,'agent/payment_report.html',context) 

@login_required
@agent_required
def add_collection(request):
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
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

@login_required
@agent_required
def balance_report(request):
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    collection = DealerCollectionReport.objects.filter().all()
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    report_data = []
    total_balance = []
    admin_report = []
    date_wise_data = []
    if request.method == 'POST':
        select_agent = request.POST.get('select-agent')
        print(select_agent)
        from_date = request.POST.get('from-date')
        to_date = request.POST.get('to-date')
        if select_agent != 'all':
            dealer_instance = Dealer.objects.get(id=select_agent)
            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], dealer=select_agent)
            collection = DealerCollectionReport.objects.filter(date__range=[from_date, to_date], dealer=select_agent)
            winning = Winning.objects.filter(dealer=select_agent,date__range=[from_date, to_date]).aggregate(total_winning=Sum('total'))['total_winning'] or 0
            dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
            total_d_amount = dealer_total_d_amount
            from_agent = collection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            to_agent = collection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            total_collection_amount = from_agent - to_agent
            win_amount = float(winning)
            print(win_amount,"winnn")
            balance = float(winning) - float(total_d_amount) - float(total_collection_amount)
            if total_d_amount > 0:
                report_data.append({
                    'date' : current_date,
                    'dealer': dealer_instance,
                    'total_d_amount': total_d_amount,
                    'from_or_to' : total_collection_amount,
                    'balance' : balance,
                    'win_amount' : win_amount
                })

            from_day = datetime.strptime(request.POST.get('from-date'), '%Y-%m-%d').date()
            to_day = datetime.strptime(request.POST.get('to-date'), '%Y-%m-%d').date()

            date_range = [from_day + timedelta(days=x) for x in range((to_day - from_day).days + 1)]

            for date in date_range:
                dealer_games = DealerGame.objects.filter(date=date, dealer=select_agent)
                collection = DealerCollectionReport.objects.filter(date=date, dealer=select_agent)
                winning = Winning.objects.filter(dealer=select_agent, date=date).aggregate(total_winning=Sum('total'))['total_winning'] or 0
                dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
                total_d_amount = dealer_total_d_amount
                from_agent = collection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
                to_agent = collection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
                total_collection_amount = from_agent - to_agent
                win_amount = float(winning)
                balance = float(winning) - float(total_d_amount) - float(total_collection_amount)

                date_wise_data.append({
                    'date': date,
                    'dealer': dealer_instance,
                    'total_d_amount': total_d_amount,
                    'from_or_to': total_collection_amount,
                    'balance': balance,
                    'win_amount': win_amount
                })
            total_balance = sum(entry['balance'] for entry in report_data)
            if 'pdfButton' in request.POST:
                pdf_filename = "Balance Report" + "-" + from_date + "-" + to_date + ".pdf"
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                story = []

                title_style = ParagraphStyle(
                    'Title',
                    parent=ParagraphStyle('Normal'),
                    fontSize=12,
                    textColor=colors.black,
                    spaceAfter=16,
                )
                title_text = "Balance Report" + "( " + from_date + " - " + to_date + " )"
                title_paragraph = Paragraph(title_text, title_style)
                story.append(title_paragraph)

                                # Add a line break after the title
                story.append(Spacer(1, 12))

                                # Add table headers
                headers = ["Date","Dealer", "Sales Amount", "Win Amount", "Collection Amount", "Balance"]
                data = [headers]

                for datas in report_data:
                    data.append([
                        datas['date'],
                        datas['dealer'].user,
                        f"{float(datas['total_d_amount'] or 0):.2f}",
                        f"{float(datas['win_amount'] or 0):.2f}",
                        f"{float(datas['from_or_to'] or 0):.2f}",
                        f"{float(datas['balance'] or 0):.2f}"
                    ])
                table = Table(data, colWidths=[80, 80, 80, 80,100,80])  # Adjust colWidths as needed
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                story.append(table)

                total_balance_text = f"Balance: {total_balance:.2f}"

                total_paragraph = Paragraph(f"{total_balance_text}", title_style)
                story.append(total_paragraph)

                pdf.build(story)
                return response
            context = {
                'dealers' : dealers,
                'selected_agent' : select_agent,
                'report_data': report_data,
                'date_wise_data': date_wise_data,
                'total_balance' : total_balance,
                'selected_from' : from_date,
                'selected_to' : to_date,
                'dealer_only' : 'yes'
            }
            return render(request, 'agent/balance_report.html',context)
        else:
            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date], agent=agent_obj)
            print(agent_games)
            agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
            collection = CollectionReport.objects.filter(date__range=[from_date, to_date], agent=agent_obj)
            winning = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date]).aggregate(total_winning=Sum('total'))['total_winning'] or 0
            from_agent = collection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            to_agent = collection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            total_collection_amount = to_agent - from_agent
            total_d_amount = agent_total_d_amount
            win_amount = float(winning)
            balance = float(winning) - float(total_d_amount) - float(total_collection_amount)
            if total_d_amount:
                report_data.append({
                    'date' : current_date,
                    'dealer': agent_obj,
                    'total_d_amount': total_d_amount,
                    'from_or_to' : total_collection_amount,
                    'balance' : balance,
                    'selected_from' : from_date,
                    'selected_to' : to_date,
                    'win_amount' : win_amount
                })
            total_balance = sum(entry['balance'] for entry in report_data)
            if 'pdfButton' in request.POST:
                pdf_filename = "Balance Report" + "-" + from_date + "-" + to_date + ".pdf"
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                story = []

                title_style = ParagraphStyle(
                    'Title',
                    parent=ParagraphStyle('Normal'),
                    fontSize=12,
                    textColor=colors.black,
                    spaceAfter=16,
                )
                title_text = "Balance Report" + "( " + from_date + " - " + to_date + " )"
                title_paragraph = Paragraph(title_text, title_style)
                story.append(title_paragraph)

                                # Add a line break after the title
                story.append(Spacer(1, 12))

                                # Add table headers
                headers = ["Date","Dealer", "Sales Amount", "Win Amount", "Collection Amount", "Balance"]
                data = [headers]

                for datas in report_data:
                    data.append([
                        datas['date'],
                        datas['dealer'].user,
                        f"{float(datas['total_d_amount'] or 0):.2f}",
                        f"{float(datas['win_amount'] or 0):.2f}",
                        f"{float(datas['from_or_to'] or 0):.2f}",
                        f"{float(datas['balance'] or 0):.2f}"
                    ])
                table = Table(data, colWidths=[80, 80, 80, 80,100,80])  # Adjust colWidths as needed
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                story.append(table)

                total_balance_text = f"Balance: {total_balance:.2f}"

                total_paragraph = Paragraph(f"{total_balance_text}", title_style)
                story.append(total_paragraph)

                pdf.build(story)
                return response
            context = {
                'dealers' : dealers,
                'selected_agent' : 'all',
                'report_data': report_data,
                'total_balance' : total_balance
            }
            for dealer in dealers:
                dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], agent=agent_obj,dealer=dealer)
                print(dealer_games)
                collection = DealerCollectionReport.objects.filter(date__range=[from_date, to_date], dealer=dealer)
                print(collection)
                winning = Winning.objects.filter(dealer=dealer,date__range=[from_date, to_date]).aggregate(total_winning=Sum('total_admin'))['total_winning'] or 0
                dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
                total_d_amount = dealer_total_d_amount
                from_agent = collection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
                to_agent = collection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
                total_collection_amount = from_agent - to_agent
                win_amount = float(winning)
                balance = float(total_d_amount) - float(total_collection_amount) - float(winning)
                if total_d_amount:
                    report_data.append({
                        'date' : current_date,
                        'dealer': dealer,
                        'total_d_amount': total_d_amount,
                        'from_or_to' : total_collection_amount,
                        'balance' : balance,
                        'win_amount' : win_amount
                    })
            total_balance = sum(entry['balance'] for entry in report_data)

            agent_games = AgentGame.objects.filter(date__range=[from_date, to_date], agent=agent_obj)
            dealer_games = DealerGame.objects.filter(date__range=[from_date, to_date], agent=agent_obj)
            agent_total_d_amount_admin = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
            dealer_total_d_amount_admin = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount_admin'))['dealer_total_d_amount'] or 0
            print(dealer_total_d_amount_admin,"dealer")
            collection_admin = CollectionReport.objects.filter(date__range=[from_date, to_date], agent=agent_obj)
            winning_agent_admin = Winning.objects.filter(agent=agent_obj,date__range=[from_date, to_date]).aggregate(total_winning=Sum('total'))['total_winning'] or 0
            winning_dealer_admin = Winning.objects.filter(dealer__agent=agent_obj,date__range=[from_date, to_date]).aggregate(total_winning=Sum('total_admin'))['total_winning'] or 0
            from_agent = collection_admin.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            to_agent = collection_admin.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
            total_collection_amount = to_agent - from_agent
            win_amount_admin = float(winning_agent_admin) + float(winning_dealer_admin)
            total_d_amount_admin = agent_total_d_amount_admin + dealer_total_d_amount_admin
            balance_admin = float(win_amount_admin) - float(total_d_amount_admin) - float(total_collection_amount)

            admin_report.append({
                'date' : current_date,
                'admin': 'admin',
                'total_d_amount_admin': total_d_amount_admin,
                'from_or_to' : total_collection_amount,
                'balance_admin' : balance_admin,
                'win_amount_admin' : win_amount_admin
            })
                
            total_balance_admin = sum(entry['balance_admin'] for entry in admin_report)
            
            if 'pdfButton' in request.POST:
                pdf_filename = "Balance Report" + "-" + from_date + "-" + to_date + ".pdf"
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

                pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
                story = []

                title_style = ParagraphStyle(
                    'Title',
                    parent=ParagraphStyle('Normal'),
                    fontSize=12,
                    textColor=colors.black,
                    spaceAfter=16,
                )
                title_text = "Balance Report" + "( " + from_date + " - " + to_date + " )"
                title_paragraph = Paragraph(title_text, title_style)
                story.append(title_paragraph)

                                # Add a line break after the title
                story.append(Spacer(1, 12))

                                # Add table headers
                headers = ["Date","Dealer", "Sales Amount", "Win Amount", "Collection Amount", "Balance"]
                data = [headers]

                for datas in report_data:
                    data.append([
                        datas['date'],
                        datas['dealer'].user,
                        f"{float(datas['total_d_amount'] or 0):.2f}",
                        f"{float(datas['win_amount'] or 0):.2f}",
                        f"{float(datas['from_or_to'] or 0):.2f}",
                        f"{float(datas['balance'] or 0):.2f}"
                    ])
                table = Table(data, colWidths=[80, 80, 80, 80,100,80])  # Adjust colWidths as needed
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                story.append(table)

                total_balance_text = f"Balance: {total_balance:.2f}"

                total_paragraph = Paragraph(f"{total_balance_text}", title_style)
                story.append(total_paragraph)

                pdf.build(story)
                return response
            context = {
                'dealers' : dealers,
                'selected_agent' : 'all',
                'report_data': report_data,
                'total_balance' : total_balance,
                'admin_report' : admin_report,
                'total_balance_admin' : total_balance_admin,
                'selected_from' : from_date,
                'selected_to' : to_date
            }
            return render(request, 'agent/balance_report.html',context)
    agent_games = AgentGame.objects.filter(date=current_date, agent=agent_obj)
    print(agent_games)
    agent_total_d_amount = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
    collection = CollectionReport.objects.filter(date=current_date, agent=agent_obj)
    winning = Winning.objects.filter(agent=agent_obj,date=current_date).aggregate(total_winning=Sum('total'))['total_winning'] or 0
    from_agent = collection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    to_agent = collection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    total_collection_amount =  to_agent - from_agent
    win_amount = float(winning)
    total_d_amount = agent_total_d_amount
    balance = float(winning) - float(total_d_amount) - float(total_collection_amount)
    if total_d_amount:
        report_data.append({
            'date' : current_date,
            'dealer': agent_obj,
            'total_d_amount': total_d_amount,
            'from_or_to' : total_collection_amount,
            'balance' : balance,
            'win_amount' : win_amount,
        })
    for dealer in dealers:
        dealer_games = DealerGame.objects.filter(date=current_date, agent=agent_obj,dealer=dealer)
        print(dealer_games)
        collection = DealerCollectionReport.objects.filter(date=current_date, dealer=dealer)
        print(collection)
        winning = Winning.objects.filter(dealer=dealer,date=current_date).aggregate(total_winning=Sum('total_admin'))['total_winning'] or 0
        dealer_total_d_amount = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount'))['dealer_total_d_amount'] or 0
        total_d_amount = dealer_total_d_amount
        from_agent = collection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        to_agent = collection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        total_collection_amount = from_agent - to_agent
        win_amount = float(winning)
        balance = float(total_d_amount) - float(total_collection_amount) - float(winning) 
        if total_d_amount:
            report_data.append({
                'date' : current_date,
                'dealer': dealer,
                'total_d_amount': total_d_amount,
                'from_or_to' : total_collection_amount,
                'balance' : balance,
                'win_amount' : win_amount
            })
    total_balance = sum(entry['balance'] for entry in report_data)

    #for admin

    agent_games = AgentGame.objects.filter(date=current_date, agent=agent_obj)
    dealer_games = DealerGame.objects.filter(date=current_date, agent=agent_obj)
    agent_total_d_amount_admin = agent_games.aggregate(agent_total_d_amount=Sum('c_amount'))['agent_total_d_amount'] or 0
    dealer_total_d_amount_admin = dealer_games.aggregate(dealer_total_d_amount=Sum('c_amount_admin'))['dealer_total_d_amount'] or 0
    print(dealer_total_d_amount_admin,"dealer")
    collection_admin = CollectionReport.objects.filter(date=current_date, agent=agent_obj)
    winning_agent_admin = Winning.objects.filter(agent=agent_obj,date=current_date).aggregate(total_winning=Sum('total'))['total_winning'] or 0
    winning_dealer_admin = Winning.objects.filter(dealer__agent=agent_obj,date=current_date).aggregate(total_winning=Sum('total_admin'))['total_winning'] or 0
    from_agent = collection_admin.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    to_agent = collection_admin.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    total_collection_amount = to_agent - from_agent
    win_amount_admin = float(winning_agent_admin) + float(winning_dealer_admin)
    total_d_amount_admin = agent_total_d_amount_admin + dealer_total_d_amount_admin
    balance_admin = float(win_amount_admin) - float(total_d_amount_admin) - float(total_collection_amount)

    admin_report.append({
        'date' : current_date,
        'admin': 'admin',
        'total_d_amount_admin': total_d_amount_admin,
        'from_or_to' : total_collection_amount,
        'balance_admin' : balance_admin,
        'win_amount_admin' : win_amount_admin
    })
        
    total_balance_admin = sum(entry['balance_admin'] for entry in admin_report)

    print(admin_report)

    context = {
        'dealers' : dealers,
        'selected_agent' : 'all',
        'report_data': report_data,
        'admin_report': admin_report,
        'total_balance' : total_balance,
        'total_balance_admin' : total_balance_admin,
    }
    return render(request, 'agent/balance_report.html',context)

@login_required
@agent_required
def edit_bill_times(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist).time()
    matching_play_times = PlayTime.objects.filter(Q(start_time__lte=current_time) & Q(end_time__gte=current_time)).order_by('id')
    context = {
        'times' : matching_play_times
    }
    return render(request,'agent/edit_bill_times.html',context)

@login_required
@agent_required
def edit_bill(request,id):
    agent_obj = Agent.objects.get(user=request.user)
    print(agent_obj.user,"agent id")
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_time)
    try:
        time = PlayTime.objects.get(id=id)
    except:
        matching_play_times = []
    if request.method == 'POST':
        search_dealer = request.POST.get('dealer-select')
        print(search_dealer,"the user id")
        if search_dealer == 'all':
            return redirect('agent:edit_bill',id=id)
        else:
            pass
        try:
            bills = Bill.objects.filter(user=search_dealer,time_id=time,date=current_date).all().order_by('-id')
            totals = Bill.objects.filter(user=search_dealer,time_id=time,date=current_date).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            context = {
                'bills' : bills,
                'dealers' : dealers,
                'totals': totals,
            } 
            return render(request,'agent/edit_bill.html',context)
        except:
            bills = []
            totals = []
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            context = {
                'bills' : bills,
                'dealers' : dealers,
                'totals': totals,
            } 
            return render(request,'agent/edit_bill.html',context)
    else:
        try:
            bills = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date,time_id=time).all().order_by('-id')
            print(bills,"time is",time.game_time)
            totals = Bill.objects.filter(Q(user=agent_obj.user) | Q(user__dealer__agent=agent_obj),date=current_date,time_id=time).aggregate(total_count=Sum('total_count'),total_c_amount=Sum('total_c_amount'),total_d_amount=Sum('total_d_amount'))
            dealers = Dealer.objects.filter(agent=agent_obj).all()
            print(agent_obj.user,"agent id")
            context = {
                'bills' : bills,
                'dealers' : dealers,
                'totals': totals,
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

@login_required
@agent_required
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

@login_required
@agent_required
def deleting_bill(request,id):
    bill = get_object_or_404(Bill,id=id)
    print(bill,"deleting bill")
    bill.delete()
    return redirect('agent:index')

@login_required
@agent_required
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

@login_required
@agent_required
def play_game(request,id):
    agent_package = []
    time = PlayTime.objects.get(id=id)
    print(time.end_time)
    agent_obj = Agent.objects.get(user=request.user)
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    current_time = timezone.now().astimezone(ist).time()
    print(current_date)
    bill_id = Bill.objects.filter().last()
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    if current_time > time.end_time:
        return redirect('agent:index')
    if current_time < time.start_time:
        return redirect('agent:index')
    try:
        limit = Limit.objects.get(agent=agent_obj)
        checked_times = limit.checked_times.all()
        if time not in checked_times:
            return redirect('agent:index')
    except:
        pass
    if request.method == 'POST':
        select_dealer = request.POST.get('select-dealer')
        print(select_dealer)
        if select_dealer == 'False':
            return redirect('agent:play_game',id=id)
        if DealerPackage.objects.filter(dealer=select_dealer).exists():
            agent_package = DealerPackage.objects.get(dealer=select_dealer)
            print(agent_package.single_rate)
        else:
            messages.info(request,"There is no package for this user!",extra_tags='package_message')
        try:
            dealer_rows = DealerGameTest.objects.filter(agent=agent_obj,created_by=agent_obj,dealer=select_dealer,time=id,date=current_date).order_by('-id')
            total_c_amount = sum(row.c_amount for row in dealer_rows)
            total_d_amount = sum(row.d_amount for row in dealer_rows)
            total_count = sum(row.count for row in dealer_rows)
        except:
            pass
        context = {
            'time' : time,
            'dealers' : dealers,
            'selected_dealer' : select_dealer,
            'agent_package' : agent_package,
            'dealer_rows' : dealer_rows,
            'total_c_amount': total_c_amount,
            'total_d_amount': total_d_amount,
            'total_count': total_count,
            'bill_id' : bill_id
        }
        return render(request,'agent/play_game.html',context)
    else:
        if AgentPackage.objects.filter(agent=agent_obj).exists():
            agent_package = AgentPackage.objects.get(agent=agent_obj)
            print(agent_package.single_rate)
        else:
            messages.info(request,"There is no package for this user!",extra_tags='package_message')
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
            'selected_dealer' : 'False',
            'bill_id' : bill_id
        }
        return render(request,'agent/play_game.html',context)

@login_required
@agent_required
def package(request):
    user_obj = Agent.objects.get(user=request.user)
    packages = DealerPackage.objects.filter(created_by=user_obj.user).all()
    print(packages)
    context = {
        'packages' : packages
    }
    return render(request,'agent/package.html',context)

@login_required
@agent_required
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
    last_dealer = Dealer.objects.filter(agent=user_obj).last()
    context = {
        'dealers' : dealer,
        'selected_dealer' : last_dealer.id
    }
    return render(request,'agent/new_package.html',context)

@login_required
@agent_required
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
        add_package = DealerPackage.objects.filter(dealer=selected_dealer).update(package_name=package_name,single_rate=single_rate,
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

@login_required
@agent_required
def delete_package(request,id):
    package = DealerPackage.objects.get(id=id)
    package.delete()
    return redirect('agent:package')

@login_required
@agent_required
def agent_game_test_delete(request,id):
    select_dealer = request.GET.get('selectDealer', None)
    print(select_dealer,"the dealer")
    if select_dealer == 'False':
        row = get_object_or_404(AgentGameTest,id=id)
        row.delete()
    else:
        row = get_object_or_404(DealerGameTest,id=id)
        row.delete()
    return JsonResponse({'status':'success'})

@login_required
@agent_required
def agent_game_test_update(request,id):
    agent_obj = Agent.objects.get(user=request.user)
    agent_package = AgentPackage.objects.get(agent=agent_obj)
    amounts = {
        "A": agent_package.single_rate,
        "B": agent_package.single_rate,
        "C": agent_package.single_rate,
        "AB": agent_package.double_rate,
        "BC": agent_package.double_rate,
        "AC": agent_package.double_rate,
        "Super": agent_package.super_rate,
        "Box": agent_package.box_rate,
    }
    dcs = {
        "A": agent_package.single_dc,
        "B": agent_package.single_dc,
        "C": agent_package.single_dc,
        "AB": agent_package.double_dc,
        "BC": agent_package.double_dc,
        "AC": agent_package.double_dc,
        "Super": agent_package.super_dc,
        "Box": agent_package.box_dc,
    }
    print(amounts)
    print(dcs)
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        edited_count = data.get('editedCount')
        print(edited_count)
        select_dealer = data.get('selectDealer')
        if select_dealer == 'False':
            test_game = AgentGameTest.objects.get(id=id)
            lsk = test_game.LSK
            print(lsk)
            updated_d_amount = amounts[lsk] * float(edited_count)
            updated_c_amount = (amounts[lsk] + dcs[lsk]) * float(edited_count)
            AgentGameTest.objects.filter(id=id).update(count=edited_count,d_amount=updated_d_amount,c_amount=updated_c_amount)
            return JsonResponse({'status':'success'})
        else:
            dealer = Dealer.objects.get(id=select_dealer)
            dealer_package = DealerPackage.objects.get(dealer=dealer)
            amounts_dealer = {
                "A": dealer_package.single_rate,
                "B": dealer_package.single_rate,
                "C": dealer_package.single_rate,
                "AB": dealer_package.double_rate,
                "BC": dealer_package.double_rate,
                "AC": dealer_package.double_rate,
                "Super": dealer_package.super_rate,
                "Box": dealer_package.box_rate,
            }
            dcs_dealer = {
                "A": dealer_package.single_dc,
                "B": dealer_package.single_dc,
                "C": dealer_package.single_dc,
                "AB": dealer_package.double_dc,
                "BC": dealer_package.double_dc,
                "AC": dealer_package.double_dc,
                "Super": dealer_package.super_dc,
                "Box": dealer_package.box_dc,
            }
            test_game = DealerGameTest.objects.get(id=id)
            lsk = test_game.LSK
            updated_d_amount = amounts_dealer[lsk] * float(edited_count)
            updated_c_amount = (amounts_dealer[lsk] + dcs_dealer[lsk]) * float(edited_count)
            updated_d_amount_admin = amounts[lsk] * float(edited_count)
            updated_c_amount_admin = (amounts[lsk] + dcs[lsk]) * float(edited_count)
            DealerGameTest.objects.filter(id=id).update(count=edited_count,d_amount=updated_d_amount,c_amount=updated_c_amount,d_amount_admin=updated_d_amount_admin,c_amount_admin=updated_c_amount_admin)
            return JsonResponse({'status':'success'})

def get_total_count(model, date, time, link_text, number):
    return model.objects.filter(date=date, time=time, LSK=link_text, number=number).aggregate(total_count=Sum('count'))['total_count'] or 0

def get_game_totals(model, date, time, link_text):
    return {
        'total_super': model.objects.filter(date=date, time=time, LSK='Super').aggregate(total_super=Sum('count'))['total_super'] or 0,
        'total_box': model.objects.filter(date=date, time=time, LSK='Box').aggregate(total_box=Sum('count'))['total_box'] or 0,
        'total_ab': model.objects.filter(date=date, time=time, LSK='AB').aggregate(total_ab=Sum('count'))['total_ab'] or 0,
        'total_bc': model.objects.filter(date=date, time=time, LSK='BC').aggregate(total_bc=Sum('count'))['total_bc'] or 0,
        'total_ac': model.objects.filter(date=date, time=time, LSK='AC').aggregate(total_ac=Sum('count'))['total_ac'] or 0,
        'total_a': model.objects.filter(date=date, time=time, LSK='A').aggregate(total_a=Sum('count'))['total_a'] or 0,
        'total_b': model.objects.filter(date=date, time=time, LSK='B').aggregate(total_b=Sum('count'))['total_b'] or 0,
        'total_c': model.objects.filter(date=date, time=time, LSK='C').aggregate(total_c=Sum('count'))['total_c'] or 0,
    }

def check_limit(request):
    ist = pytz_timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    agent_obj = Agent.objects.get(user=request.user)
    if request.method == 'POST':
        data = json.loads(request.body, object_pairs_hook=OrderedDict)
        print(data)
        select_dealer = data.get('selectDealer')
        customer = data.get('customer', '').strip().lower()
        link_text = data.get('linkText')
        value1 = data.get('value1')
        value2 = data.get('value2')
        value3 = data.get('value3')
        value4 = data.get('value4')
        timeId = data.get('timeId')
        time = get_object_or_404(PlayTime,id=timeId)
        current_time = timezone.now().astimezone(ist).time()
        if current_time > time.end_time:
            print("time over")
            return JsonResponse({'message': 'time over'})
        else:
            print("time not over")
        if select_dealer == 'False':
            try:
                agent_test_total_c_amount = AgentGameTest.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
                dealer_test_total_c_amount = DealerGameTest.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount_admin'))['total_c_amount'] or 0
                agent_total_c_amount = AgentGame.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
                dealer_total_c_amount = DealerGame.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount_admin'))['total_c_amount'] or 0
                limit = Limit.objects.get(agent=agent_obj)
                add = float(value4) + float(agent_total_c_amount) + float(agent_test_total_c_amount) + float(dealer_test_total_c_amount) + float(dealer_total_c_amount)
                try:
                    blocked_numbers = BlockedNumber.objects.filter(Q(from_date__lte=current_date) & Q(to_date__gte=current_date),time=time, LSK=link_text, number=value1)
                    if blocked_numbers:
                        agent_game_count = AgentGame.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        dealer_game_count = DealerGame.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        agent_game_test_count = AgentGameTest.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        dealer_game_test_count = DealerGameTest.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        blocked_number_count = (agent_game_count) + (dealer_game_count) + (agent_game_test_count) + (dealer_game_test_count) + int(value2)
                        sale_count = (agent_game_count) + (dealer_game_count)
                        for block in blocked_numbers:
                            if blocked_number_count > block.count:
                                return JsonResponse({'message': 'Blocked number'})
                            else:
                                pass
                except:
                    pass

                try:
                    game_limit = GameLimit.objects.get(time=time)
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
                    agent_games = AgentGame.objects.filter(date=current_date, time=time, LSK=link_text,number=value1)
                    agent_games_test = AgentGameTest.objects.filter(date=current_date, time=time, LSK=link_text,number=value1)
                    dealer_games = DealerGame.objects.filter(date=current_date, time=time, LSK=link_text,number=value1)
                    dealer_games_test = DealerGameTest.objects.filter(date=current_date, time=time, LSK=link_text,number=value1)
                    total_counts = {
                        'agent_game_count': agent_games.aggregate(total_count=Sum('count'))['total_count'] or 0,
                        'dealer_game_count': dealer_games.aggregate(total_count=Sum('count'))['total_count'] or 0,
                        'agent_game_test_count': agent_games_test.aggregate(total_count=Sum('count'))['total_count'] or 0,
                        'dealer_game_test_count': dealer_games_test.aggregate(total_count=Sum('count'))['total_count'] or 0,
                    }
                    games_total = sum([
                        agent_games.aggregate(total=Sum('count'))['total'] or 0,
                        dealer_games.aggregate(total=Sum('count'))['total'] or 0,
                        agent_games_test.aggregate(total=Sum('count'))['total'] or 0,
                        dealer_games_test.aggregate(total=Sum('count'))['total'] or 0,
                    ])
                    total_count_key = limits.get(link_text, None)
                    if total_count_key is not None:
                        print("limit checking")
                        total = games_total + int(value2)
                        if total > getattr(game_limit, link_text.lower(), value1):
                            return JsonResponse({'message': 'LSK blocked'})
                except:
                    pass
                
                if add > limit.daily_limit:
                    return JsonResponse({'message': 'Limit exceeded'})
                else:
                    agent_game_test = AgentGameTest.objects.create(
                        agent=agent_obj,
                        customer=customer,
                        time=time,
                        LSK=link_text,
                        number=value1,
                        count=value2,
                        d_amount=value3,
                        c_amount=value4
                    )
                    print(agent_game_test.id)
                    return JsonResponse({'message': 'Data saved','row_id':agent_game_test.id})
            except:
                pass
        else:
            dealer = Dealer.objects.get(id=select_dealer)
            agent_package = AgentPackage.objects.get(agent=agent_obj)
            amounts = {
                "A" : agent_package.single_rate,
                "B" : agent_package.single_rate,
                "C" : agent_package.single_rate,
                "AB" : agent_package.double_rate,
                "BC" : agent_package.double_rate,
                "AC" : agent_package.double_rate,
                "Super" : agent_package.super_rate,
                "Box" : agent_package.box_rate,
            }
            dcs = {
                "A" : agent_package.single_dc,
                "B" : agent_package.single_dc,
                "C" : agent_package.single_dc,
                "AB" : agent_package.double_dc,
                "BC" : agent_package.double_dc,
                "AC" : agent_package.double_dc,
                "Super" : agent_package.super_dc,
                "Box" : agent_package.box_dc,
            }
            value3_agent = float(value2) * float(amounts[link_text])
            value4_agent = float(value2) * float(amounts[link_text] + dcs[link_text])
            try:
                agent_test_total_c_amount = AgentGameTest.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
                dealer_test_total_c_amount = DealerGameTest.objects.filter(agent=agent_obj,dealer=dealer,date=current_date).aggregate(total_c_amount=Sum('c_amount_admin'))['total_c_amount'] or 0
                agent_total_c_amount = AgentGame.objects.filter(agent=agent_obj, date=current_date).aggregate(total_c_amount=Sum('c_amount'))['total_c_amount'] or 0
                dealer_total_c_amount = DealerGame.objects.filter(agent=agent_obj,dealer=dealer, date=current_date).aggregate(total_c_amount=Sum('c_amount_admin'))['total_c_amount'] or 0
                limit = Limit.objects.get(agent=agent_obj)
                add = float(value4) + float(agent_total_c_amount) + float(agent_test_total_c_amount) + float(dealer_test_total_c_amount) + float(dealer_total_c_amount)
                try:
                    blocked_numbers = BlockedNumber.objects.filter(Q(from_date__lte=current_date) & Q(to_date__gte=current_date),time=time, LSK=link_text, number=value1)
                    if blocked_numbers:
                        agent_game_count = AgentGame.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        dealer_game_count = DealerGame.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        agent_game_test_count = AgentGameTest.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        dealer_game_test_count = DealerGameTest.objects.filter(date=current_date,time=time,LSK=link_text,number=value1).aggregate(total_count=Sum('count'))['total_count'] or 0
                        blocked_number_count = (agent_game_count) + (dealer_game_count) + (agent_game_test_count) + (dealer_game_test_count) + int(value2)
                        sale_count = (agent_game_count) + (dealer_game_count)
                        for block in blocked_numbers:
                            if blocked_number_count > block.count:
                                return JsonResponse({'message': 'Blocked number'})
                            else:
                                pass
                except:
                    pass
                
                try:
                    game_limit = GameLimit.objects.get(time=time)
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
                    agent_games = AgentGame.objects.filter(date=current_date, time=time, LSK=link_text)
                    agent_games_test = AgentGameTest.objects.filter(date=current_date, time=time, LSK=link_text)
                    dealer_games = DealerGame.objects.filter(date=current_date, time=time, LSK=link_text)
                    dealer_games_test = DealerGameTest.objects.filter(date=current_date, time=time, LSK=link_text)
                    total_counts = {
                        'agent_game_count': agent_games.aggregate(total_count=Sum('count'))['total_count'] or 0,
                        'dealer_game_count': dealer_games.aggregate(total_count=Sum('count'))['total_count'] or 0,
                        'agent_game_test_count': agent_games_test.aggregate(total_count=Sum('count'))['total_count'] or 0,
                        'dealer_game_test_count': dealer_games_test.aggregate(total_count=Sum('count'))['total_count'] or 0,
                    }
                    games_total = sum([
                        agent_games.aggregate(total=Sum('count'))['total'] or 0,
                        dealer_games.aggregate(total=Sum('count'))['total'] or 0,
                        agent_games_test.aggregate(total=Sum('count'))['total'] or 0,
                        dealer_games_test.aggregate(total=Sum('count'))['total'] or 0,
                    ])
                    total_count_key = limits.get(link_text, None)
                    if total_count_key is not None:
                        print("limit checking")
                        total = games_total + int(value2)
                        if total > getattr(game_limit, link_text.lower(), value1):
                            return JsonResponse({'message': 'LSK blocked'})
                except:
                    pass
                
                if add > limit.daily_limit:
                    return JsonResponse({'message': 'Limit exceeded'})
                else:
                    dealer_game_test = DealerGameTest.objects.create(
                        agent=agent_obj,
                        created_by=agent_obj,
                        dealer=dealer,
                        time=time,
                        LSK=link_text,
                        number=value1,
                        count=value2,
                        d_amount=value3,
                        c_amount=value4,
                        d_amount_admin=value3_agent,
                        c_amount_admin=value4_agent,
                    )
                    return JsonResponse({'message': 'Data saved','row_id':dealer_game_test.id})
            except:
                pass
    return JsonResponse({'message': 'Data saved successfully'})

@login_required
@agent_required
def save_data(request):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    agent_obj = Agent.objects.get(user=request.user)

    if request.method == 'POST':
        data = json.loads(request.body, object_pairs_hook=OrderedDict)
        print(data)
        select_dealer = data.get('selectDealer')
        customer = data.get('customer', '').strip().lower()
        play_time = data.get('timeId')
        time = PlayTime.objects.get(id=play_time)
        print(select_dealer)
        print(customer)

    try:
        if select_dealer == 'False':
            agent_game_test = AgentGameTest.objects.filter(agent=agent_obj, time=time, date=current_date).order_by('id')

            # Create AgentGame records based on AgentGameTest
            agent_game_records = []

            for test_record in agent_game_test:
                agent_game_record = AgentGame(
                    agent=test_record.agent,
                    customer=test_record.customer,
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

            AgentGame.objects.bulk_create(agent_game_records)

            agent_game_test.delete()

            if agent_game_records:
                # Calculate total values
                total_c_amount = sum([record.c_amount for record in agent_game_records])
                total_d_amount = sum([record.d_amount for record in agent_game_records])
                total_count = sum([record.count for record in agent_game_records])

                # Create the Bill record
                bill = Bill.objects.create(
                    user=agent_obj.user,
                    customer=customer,
                    time_id=time,
                    date=current_date,
                    total_c_amount=total_c_amount,
                    total_d_amount=total_d_amount,
                    total_count=total_count,
                )
                # Add related AgentGame records to the Bill
                bill.agent_games.add(*agent_game_records)

        else:

            dealer_game_test = DealerGameTest.objects.filter(agent=agent_obj,created_by=agent_obj,time=time, date=current_date).order_by('id')

            dealer_game_records = []

            for test_record in dealer_game_test:
                dealer_game_record = DealerGame(
                    agent=agent_obj,
                    dealer=test_record.dealer,
                    time=test_record.time,
                    date=test_record.date,
                    LSK=test_record.LSK,
                    number=test_record.number,
                    count=test_record.count,
                    d_amount=test_record.d_amount,
                    c_amount=test_record.c_amount,
                    d_amount_admin=test_record.d_amount_admin,
                    c_amount_admin=test_record.c_amount_admin,
                    combined=False
                )
                dealer_game_records.append(dealer_game_record)
        

            # Save the AgentGame records
            

            DealerGame.objects.bulk_create(dealer_game_records)

            # Delete the AgentGameTest records
            

            dealer_game_test.delete()

            # Check if there are AgentGame records
            

            if dealer_game_records:
                print(dealer_game_records,"dealer games")
                # Calculate total values
                total_c_amount = sum([record.c_amount for record in dealer_game_records])
                total_d_amount = sum([record.d_amount for record in dealer_game_records])
                total_count = sum([record.count for record in dealer_game_records])

                total_c_amount_admin = sum([record.c_amount_admin for record in dealer_game_records])
                total_d_amount_admin = sum([record.d_amount_admin for record in dealer_game_records])

                dealer_obj = dealer_game_records[0].dealer.user

                # Create the Bill record
                bill = Bill.objects.create(
                    user=dealer_obj,
                    time_id=time,
                    date=current_date,
                    total_c_amount=total_c_amount,
                    total_d_amount=total_d_amount,
                    total_count=total_count,
                    total_c_amount_admin=total_c_amount_admin,
                    total_d_amount_admin=total_d_amount_admin,
                )
                # Add related AgentGame records to the Bill
                bill.dealer_games.add(*dealer_game_records)

    except Exception as e:
        print(e)

    return JsonResponse({'message':'Bill saved'})

@login_required
@agent_required
def set_limit(request):
    agent_obj = Agent.objects.get(user=request.user)
    dealers = Dealer.objects.filter(agent=agent_obj).all()
    times = PlayTime.objects.filter().all().order_by('id')
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
    last_dealer = Dealer.objects.filter(agent=agent_obj).last()
    context = {
        'agents' : dealers,
        'times' : times,
        'selected_dealer' : last_dealer.id
    }
    return render(request,'agent/set_limit.html',context)

@login_required
@agent_required
def view_limits(request):
    agent_obj = Agent.objects.get(user=request.user)
    limits = DealerLimit.objects.filter(agent=agent_obj).all()
    context = {
        'limits' : limits
    }
    return render(request,'agent/view_limits.html',context)

@login_required
@agent_required
def edit_limit(request, id):
    times = PlayTime.objects.all().order_by('id')
    limit_instance = DealerLimit.objects.get(id=id)

    if request.method == 'POST':
        limit = request.POST.get('limit')
        selected_times = request.POST.getlist('checkbox')
        selected_agent = request.POST.get('select-agent')

        # Update the daily_limit for the selected Limit
        limit_instance.daily_limit = limit
        limit_instance.save()

        # Update the checked_times for the selected Limit
        limit_instance.checked_times.set(selected_times)

        return redirect('agent:index')

    context = {
        'times': times,
        'limit_instance': limit_instance,
    }
    return render(request, 'agent/edit_limit.html', context)

@login_required
@agent_required
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


def total_balance(request):
    ist = pytz.timezone('Asia/Kolkata')
    current_date = timezone.now().astimezone(ist).date()
    agent_obj = Agent.objects.get(user=request.user)

    dealers = Dealer.objects.filter(agent=agent_obj,).all()
    report_data = []

    agent_sale_amount = AgentGame.objects.filter(agent=agent_obj,).aggregate(total_sale_amount=Sum('c_amount'))['total_sale_amount'] or 0
    agentcollection = CollectionReport.objects.filter(agent=agent_obj)
    winning = Winning.objects.filter(agent=agent_obj).aggregate(total_winning=Sum('total'))['total_winning'] or 0
    sale_amount =  agent_sale_amount
    from_agent = agentcollection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    to_agent = agentcollection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
    total_collection_amount = to_agent - from_agent
    print(total_collection_amount, "collection")
    win_amount = float(winning)
    balance = float(winning) - float(sale_amount) - float(total_collection_amount)
    report_data.append({
            'dealer' : 'Myself',
            'sale_amount' : balance,
            'total_balance' : balance
        })
    for dealer in dealers:
        dealer_sale_amount = DealerGame.objects.filter(dealer=dealer).aggregate(total_sale_amount=Sum('c_amount'))['total_sale_amount'] or 0
        dealer_sale_amount_admin = DealerGame.objects.filter(dealer=dealer).aggregate(total_sale_amount=Sum('c_amount_admin'))['total_sale_amount'] or 0
        dealercollection = DealerCollectionReport.objects.filter(dealer=dealer)

        winning = Winning.objects.filter(dealer=dealer).aggregate(total_winning=Sum('total'))['total_winning'] or 0
        winning_admin = Winning.objects.filter(dealer=dealer).aggregate(total_winning_admin=Sum('total'))['total_winning_admin'] or 0
        sale_amount =  dealer_sale_amount
        from_dealer = dealercollection.filter(from_or_to='received').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        to_dealer = dealercollection.filter(from_or_to='paid').aggregate(collection_amount=Sum('amount'))['collection_amount'] or 0
        total_collection_amount = from_dealer - to_dealer
        print(total_collection_amount, "collection")
        win_amount = float(winning)
        balance = float(sale_amount)  - float(winning) - float(total_collection_amount)
        admin_balance = float(winning_admin) - float(dealer_sale_amount_admin)
        print(winning_admin)
        print(dealer_sale_amount_admin)
        print(admin_balance)
        report_data.append({
            'dealer' : dealer,
            'sale_amount' : balance,
            'total_balance' : admin_balance
        })

    total_balance = sum(entry['total_balance'] for entry in report_data)

    if 'pdfButton' in request.POST:
        print("total pdf")
        pdf_filename = "Total_Balance" + " - " + str(current_date) + ".pdf"
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'

        pdf = SimpleDocTemplate(response, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        story = []

        title_style = ParagraphStyle(
            'Title',
            parent=ParagraphStyle('Normal'),
            fontSize=12,
            textColor=colors.black,
            spaceAfter=16,
        )
        title_text = "Total Balance" + " - " + str(current_date)
        title_paragraph = Paragraph(title_text, title_style)
        story.append(title_paragraph)

        # Add a line break after the title
        story.append(Spacer(1, 12))

        # Add table headers
        headers = ["Agent", "Balance"]
        data = [headers]
        
        for entry in report_data:
            data.append([
                entry['dealer'],
                f"{float(entry['sale_amount'] or 0):.2f}",
            ])

        # Create the table and apply styles
        table = Table(data, colWidths=[120, 100])  # Adjust colWidths as needed
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(table)

        story.append(Spacer(1, 12))

        total_balance_text = f"Total Balance: {total_balance:.2f}"
        total_paragraph = Paragraph(total_balance_text, title_style)
        story.append(total_paragraph)

        pdf.build(story)
        return response
    context = {
        'report_data' : report_data,
        'total_balance' : total_balance,
        'agent_balance':balance
    }
    return render(request,'agent/total_balance.html',context)


 
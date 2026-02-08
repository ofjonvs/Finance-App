from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Portfolio, Holding
from .forms import HoldingForm, BudgetForm
import mstarpy
from datetime import datetime, timedelta
from .util import *
import yfinance as yf
from decimal import Decimal
from collections import defaultdict
import calendar

# Create your views here.
def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful.')
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Logout successful.')
    return redirect('index')

@login_required
def portfolio(request):
    portfolio, created = Portfolio.objects.get_or_create(
        user=request.user,
        defaults={'name': f"{request.user.username}'s Portfolio"}
    )

    if request.method == 'POST':
        form = HoldingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                fund = getFund(data.get('symbol'))
                holding, _ = Holding.objects.get_or_create(portfolio=portfolio, fund=fund)
                holding.shares += data.get('shares') or Decimal(data['dollars_invested'])/Decimal(fund.nav)
                holding.save()

                messages.success(request, 'Holding added successfully.')
            except Exception as e:
                print(e)
                messages.error(request, f'Error adding holding: {str(e)}. Please check the fund symbol and try again.')
            
            return redirect('portfolio')
    else:
        form = HoldingForm()

    updateFunds(request.user)

    holdings = portfolio.holdings.all()
    total_dollars = sum((h.shares or 0) * (h.fund.nav or 0) for h in holdings)
    vt, vxus = getFund('VT'), getFund('VXUS')

    regions = defaultdict(lambda: Decimal(0))
    intl_alloc = defaultdict(lambda: Decimal(0))
    allocs = defaultdict(lambda: Decimal(0))
    sectors = defaultdict(lambda: Decimal(0))
    total_invested = 0
    total_invested = sum(round(holding.fund.nav*holding.shares, 2) for holding in holdings)
    for holding in holdings:
        for region in holding.fund.region_allocations.all():
            regions[region.region] += region.percentage*holding.fund.nav*holding.shares
        for allocAttr in CAP_ATTRS:
            allocs[allocAttr] += getattr(holding.fund, allocAttr)*holding.fund.nav*holding.shares
        for sector in holding.fund.sector_allocations.all():
            sectors[sector.sector] += sector.percentage*holding.fund.nav*holding.shares
        dollars_invested = round(holding.fund.nav*holding.shares, 2)
        holding.dollars_invested = f'{dollars_invested:,}'
        holding.percent = round(dollars_invested/total_invested*100, 2)
    regions = {r: round(p/Decimal(total_dollars), 2) for r, p in regions.items()}
    total_regions = [vt.region_allocations.get(region=region).percentage for region in regions]
    intl_regions = {r: round(p/(100-regions['United States'])*100, 2) for r, p in regions.items() if r != 'United States'}
    intl_total_regions = [vxus.region_allocations.get(region=region).percentage for region in intl_regions]
    allocs = {alloc.replace('_', ' ').replace('cap ', '').title(): round(p/Decimal(total_dollars), 2) for alloc, p in allocs.items()}
    total_allocs = [getattr(vt, allocAttr) for allocAttr in CAP_ATTRS]
    sectors = {s: round(p/Decimal(total_dollars), 2) for s, p in sectors.items()}
    total_sectors = [vt.sector_allocations.get(sector=sector).percentage for sector in sectors]

    return render(request, 'portfolio.html', {'portfolio': portfolio, 'form': form, 'holdings': holdings, 'regions': regions, 'total_regions': total_regions, 'intl_regions': intl_regions, 'total_intl_regions': intl_total_regions, 'allocs': allocs, 'total_allocs': total_allocs, 'sectors': sectors, 'total_sectors': total_sectors, 'total_invested': f'{total_invested:,}'})

@login_required
def delete_holding(request, pk):
    holding = get_object_or_404(Holding, pk=pk)
    if holding.portfolio.user == request.user:
        holding.delete()
        messages.success(request, 'Holding removed successfully.')
    else:
        messages.error(request, 'You do not have permission to remove this holding.')
    return redirect('portfolio')

@login_required
def update_nav(request, holding_id):
    holding = get_object_or_404(Holding, id=holding_id, portfolio__user=request.user)
    if request.method == 'POST':
        try:
            nav = request.POST.get('custom_nav')
            holding.nav = float(nav) if nav else None
            holding.save()
            messages.success(request, f"NAV for {holding.fund_name} updated successfully.")
        except ValueError:
            messages.error(request, "Invalid NAV value provided.")
    return redirect('portfolio')

@login_required
def budget(request, year=None):
    # budget = MonthlyBudget(user=request.user)
    year = year or datetime.datetime.today().year
    print(year)
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget_item = form.save(commit=False)
            budget_item.user = request.user
            budget_item.item = budget_item.item.title()
            budget_item.subcategory = budget_item.subcategory.title()
            budget_item.date = datetime.date(year, int(form.cleaned_data['month']), 1)
            budget_item.save()
            messages.success(request, 'Expense added successfully.')
            return redirect('budget')
        else:
            messages.error(request, 'Error adding expense. Please check the form.')
    else:
        form = BudgetForm()
    
    items = BudgetItem.objects.filter(user=request.user)
    monthlyBudgets = {calendar.month_name[month]: MonthlyBudget(request.user, month, year) for month in sorted(set(item.date.month for item in items.filter(date__year=year)) - {'Recurring'})}

    # all_month_expenses = {month: budget.expenses.to_html(classes='table table-striped', index=False) for month, budget in monthlyBudgets.items()}
    months = {month: {
        'expenses': budget.expenses.to_dict(orient="records"),
        'total_spent': round(budget.totalExpenses(), 2),
        'total_needs': round(budget.totalNeeds(), 2),
        'total_wants': round(budget.totalWants(), 2),
        'savings': round(budget.savings(), 2),
        } for month, budget in monthlyBudgets.items()}
    # wants_table = budget.wants().to_html(classes='table table-striped', index=False)
    # needs_table = budget.needs().to_html(classes='table table-striped', index=False)
    
    context = {
        'form': form,
        'income': request.user.portfolio.monthly_income,
        'all_months': months,
        'needs_summary': getBudgetAverages(monthlyBudgets.values(), 'Needs').to_html(classes='table table-striped', index=False),
        'wants_summary': getBudgetAverages(monthlyBudgets.values(), 'Wants').to_html(classes='table table-striped', index=False),
        'savings': round(sum(m['savings'] for m in months.values())/len(months) if months else 0, 2),
        'year': year,
        'avail_years': sorted({datetime.datetime.today().year}|{item.date.year for item in items}, reverse=True),
        # 'total_wants': budget.totalWants(),
        # 'total_needs': budget.totalNeeds(),
        # 'expenses_table': expenses_table,
        # 'wants_table': wants_table,
        # 'needs_table': needs_table
    }
    # print(request.user)
    return render(request, 'budget.html', context)

def set_income(request):
    if request.method == 'POST':
        request.user.portfolio.monthly_income = request.POST.get('income')
        request.user.portfolio.save()

    return redirect('budget')

def delete_expense(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(BudgetItem, pk=pk)
        if item.user == request.user:
            item.delete()
            messages.success(request, 'Holding removed successfully.')
        else:
            messages.error(request, 'You do not have permission to remove this holding.')
    return redirect('budget')
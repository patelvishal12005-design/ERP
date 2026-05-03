from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import Employee, InventoryItem, FinanceRecord, SaleRecord, Attendance


# ─── LOGIN / LOGOUT ───────────────────────────────────────────
def html_login(request):
    if request.user.is_authenticated:
        return redirect('html_dashboard')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            login(request, user)
            return redirect('html_dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'ERP/login.html')


def html_logout(request):
    logout(request)
    return redirect('html_login')


# ─── DASHBOARD ────────────────────────────────────────────────
@login_required(login_url='/')
def html_dashboard(request):
    total_income  = FinanceRecord.objects.filter(user=request.user, type='income').aggregate(t=Sum('amount'))['t'] or 0
    total_expense = FinanceRecord.objects.filter(user=request.user, type='expense').aggregate(t=Sum('amount'))['t'] or 0
    sales_qs      = SaleRecord.objects.filter(user=request.user)
    sales_revenue = sum(s.quantity * s.unit_price for s in sales_qs)

    stats = {
        'employees':    Employee.objects.filter(user=request.user).count(),
        'products':     InventoryItem.objects.filter(user=request.user).count(),
        'total_sales':  sales_qs.count(),
        'sales_revenue': sales_revenue,
        'total_income':  total_income,
        'total_expense': total_expense,
        'net_profit':    total_income - total_expense,
    }
    recent_sales = sales_qs.order_by('-id')[:5]
    return render(request, 'ERP/dashboard.html', {'stats': stats, 'recent_sales': recent_sales})


# ─── EMPLOYEES ────────────────────────────────────────────────
@login_required(login_url='/')
def html_employees(request):
    today = timezone.now().date()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Employee.objects.filter(user=request.user, id=request.POST.get('emp_id')).delete()
            messages.success(request, 'Employee deleted.')
        elif action == 'mark_attendance':
            emp_id = request.POST.get('emp_id')
            status = request.POST.get('status')
            try:
                emp = Employee.objects.get(user=request.user, id=emp_id)
                Attendance.objects.update_or_create(
                    employee=emp,
                    date=today,
                    defaults={'status': status}
                )
                messages.success(request, f"Attendance marked as {status} for {emp.name}.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            try:
                Employee.objects.create(
                    user=request.user,
                    name=request.POST['name'],
                    email=request.POST['email'],
                    role=request.POST['role'],
                    department=request.POST['department'],
                    salary=request.POST['salary'],
                )
                messages.success(request, f"Employee '{request.POST['name']}' added.")
            except Exception as e:
                messages.error(request, str(e))
        return redirect('html_employees')

    employees = Employee.objects.filter(user=request.user).order_by('-id')
    for emp in employees:
        att = emp.attendance_records.filter(date=today).first()
        emp.today_status = att.status if att else None

    return render(request, 'ERP/employees.html', {'employees': employees})


# ─── INVENTORY ────────────────────────────────────────────────
@login_required(login_url='/')
def html_inventory(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            InventoryItem.objects.filter(user=request.user, id=request.POST.get('item_id')).delete()
            messages.success(request, 'Item deleted.')
        else:
            try:
                InventoryItem.objects.create(
                    user=request.user,
                    name=request.POST['name'],
                    category=request.POST['category'],
                    quantity=request.POST['quantity'],
                    unit_price=request.POST['unit_price'],
                    supplier=request.POST.get('supplier', ''),
                )
                messages.success(request, f"Item '{request.POST['name']}' added.")
            except Exception as e:
                messages.error(request, str(e))
        return redirect('html_inventory')

    items = InventoryItem.objects.filter(user=request.user).order_by('-id')
    total_value = sum(i.quantity * i.unit_price for i in items)
    return render(request, 'ERP/inventory.html', {'items': items, 'total_value': total_value})


# ─── FINANCE ──────────────────────────────────────────────────
@login_required(login_url='/')
def html_finance(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            FinanceRecord.objects.filter(user=request.user, id=request.POST.get('record_id')).delete()
            messages.success(request, 'Record deleted.')
        else:
            try:
                FinanceRecord.objects.create(
                    user=request.user,
                    title=request.POST['title'],
                    amount=request.POST['amount'],
                    type=request.POST['type'],
                    notes=request.POST.get('notes', ''),
                )
                messages.success(request, 'Finance record added.')
            except Exception as e:
                messages.error(request, str(e))
        return redirect('html_finance')

    records      = FinanceRecord.objects.filter(user=request.user).order_by('-id')
    total_income  = records.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
    total_expense = records.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'ERP/finance.html', {
        'records': records,
        'total_income':  total_income,
        'total_expense': total_expense,
        'net_balance':   total_income - total_expense,
    })


# ─── SALES ────────────────────────────────────────────────────
@login_required(login_url='/')
def html_sales(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            SaleRecord.objects.filter(user=request.user, id=request.POST.get('sale_id')).delete()
            messages.success(request, 'Sale deleted.')
        else:
            try:
                product_id = request.POST.get('product_id')
                quantity = int(request.POST['quantity'])
                
                if product_id:
                    inventory_item = InventoryItem.objects.get(user=request.user, id=product_id)
                    if inventory_item.quantity < quantity:
                        messages.error(request, f'Insufficient stock! Only {inventory_item.quantity} available.')
                        return redirect('html_sales')
                    
                    inventory_item.quantity -= quantity
                    inventory_item.save()
                    product_name = inventory_item.name
                    unit_price = inventory_item.unit_price
                else:
                    product_name = request.POST['product_name']
                    unit_price = request.POST['unit_price']
                
                SaleRecord.objects.create(
                    user=request.user,
                    product_name=product_name,
                    customer=request.POST['customer'],
                    quantity=quantity,
                    unit_price=unit_price,
                )
                messages.success(request, 'Sale recorded.')
            except Exception as e:
                messages.error(request, str(e))
        return redirect('html_sales')

    sales = SaleRecord.objects.filter(user=request.user).order_by('-id')
    items = InventoryItem.objects.filter(user=request.user).order_by('name')
    total_revenue = sum(s.quantity * s.unit_price for s in sales)
    return render(request, 'ERP/sales.html', {'sales': sales, 'items': items, 'total_revenue': total_revenue})

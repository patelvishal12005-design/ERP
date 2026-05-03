from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Sum
from django.utils import timezone
import calendar
from datetime import datetime

from .models import Employee, InventoryItem, FinanceRecord, SaleRecord, Attendance
from .serializers import (
    EmployeeSerializer,
    InventoryItemSerializer,
    FinanceRecordSerializer,
    SaleRecordSerializer,
    UserRegisterSerializer,
)
from rest_framework.permissions import AllowAny
from rest_framework import generics
from django.contrib.auth.models import User

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by('-id')
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        print("perform_create called with data:", serializer.validated_data)
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_attendance(self, request, pk=None):
        employee = self.get_object()
        status = request.data.get('status')
        today = timezone.now().date()
        Attendance.objects.update_or_create(
            employee=employee,
            date=today,
            defaults={'status': status}
        )
        return Response({'status': 'success', 'today_status': status})


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all().order_by('-id')
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        inventory_item = serializer.save(user=self.request.user)
        total_cost = inventory_item.quantity * inventory_item.unit_price
        FinanceRecord.objects.create(
            user=self.request.user,
            title=f"Purchase: {inventory_item.name}",
            amount=total_cost,
            type='expense',
            notes=f"Added {inventory_item.quantity} units of {inventory_item.name} at ₹{inventory_item.unit_price} each"
        )


class FinanceViewSet(viewsets.ModelViewSet):
    queryset = FinanceRecord.objects.all().order_by('-id')
    serializer_class = FinanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SaleViewSet(viewsets.ModelViewSet):
    queryset = SaleRecord.objects.all().order_by('-id')
    serializer_class = SaleRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 0))
        
        if product_id:
            try:
                from bson import ObjectId
                inventory_item = InventoryItem.objects.get(user=request.user, id=ObjectId(product_id))
                if inventory_item.quantity < quantity:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'detail': f'Insufficient stock! Only {inventory_item.quantity} available.'})
                
                inventory_item.quantity -= quantity
                inventory_item.save()
                
                data = request.data.copy()
                data['product_name'] = inventory_item.name
                data['unit_price'] = inventory_item.unit_price
                
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                sale_record = serializer.save(user=self.request.user)
                
                total_sale = sale_record.quantity * sale_record.unit_price
                FinanceRecord.objects.create(
                    user=self.request.user,
                    title=f"Sale: {sale_record.product_name} to {sale_record.customer}",
                    amount=total_sale,
                    type='income',
                    notes=f"Sold {sale_record.quantity} units of {sale_record.product_name} at ₹{sale_record.unit_price} each to {sale_record.customer}"
                )
                
                headers = self.get_success_headers(serializer.data)
                from rest_framework.response import Response
                return Response(serializer.data, status=201, headers=headers)
                
            except InventoryItem.DoesNotExist:
                pass
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        sale_record = serializer.save(user=self.request.user)
        total_sale = sale_record.quantity * sale_record.unit_price
        FinanceRecord.objects.create(
            user=self.request.user,
            title=f"Sale: {sale_record.product_name} to {sale_record.customer}",
            amount=total_sale,
            type='income',
            notes=f"Sold {sale_record.quantity} units of {sale_record.product_name} at ₹{sale_record.unit_price} each to {sale_record.customer}"
        )


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_employees = len(Employee.objects.filter(user=request.user))
        total_products = len(InventoryItem.objects.filter(user=request.user))

        total_income = sum(
            r.amount for r in FinanceRecord.objects.filter(user=request.user, type='income')
        )

        total_expense = sum(
            r.amount for r in FinanceRecord.objects.filter(user=request.user, type='expense')
        )

        user_sales = SaleRecord.objects.filter(user=request.user)
        total_sales = len(user_sales)
        sales_revenue = sum(
            s.quantity * s.unit_price for s in user_sales
        )

        recent_sales = user_sales.order_by('-id')[:5]
        recent_sales_data = SaleRecordSerializer(recent_sales, many=True).data

        return Response({
            'employees': total_employees,
            'products': total_products,
            'total_sales': total_sales,
            'sales_revenue': float(sales_revenue),
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net_profit': float(total_income) - float(total_expense),
            'recent_sales': recent_sales_data,
        })


class MonthlyAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        now = timezone.now()
        year = int(year) if year else now.year
        month = int(month) if month else now.month
        
        _, days_in_month = calendar.monthrange(year, month)
        
        employees = Employee.objects.filter(user=request.user).order_by('name')
        records = []
        
        for emp in employees:
            att_records = emp.attendance_records.filter(date__year=year, date__month=month)
            att_dict = {str(att.date.day): att.status for att in att_records}
            records.append({
                'employee_id': str(emp.id),
                'employee_name': emp.name,
                'attendance': att_dict
            })
            
        return Response({
            'year': year,
            'month': month,
            'days_in_month': days_in_month,
            'records': records
        })


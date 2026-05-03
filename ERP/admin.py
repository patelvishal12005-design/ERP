from django.contrib import admin
from .models import Employee, InventoryItem, FinanceRecord, SaleRecord

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'role', 'department', 'salary', 'date_joined']
    search_fields = ['name', 'email', 'department']

@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'quantity', 'unit_price', 'supplier']
    search_fields = ['name', 'category']

@admin.register(FinanceRecord)
class FinanceAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'amount', 'date']
    list_filter = ['type']

@admin.register(SaleRecord)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'customer', 'quantity', 'unit_price', 'date']

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django_mongodb_backend.fields import ObjectIdAutoField

class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('Engineering', 'Engineering'),
        ('Sales', 'Sales'),
        ('HR', 'HR'),
        ('Finance', 'Finance'),
        ('Operations', 'Operations'),
        ('Marketing', 'Marketing'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=100)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='Engineering')
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'email')

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics'),
        ('Furniture', 'Furniture'),
        ('Stationery', 'Stationery'),
        ('Raw Material', 'Raw Material'),
        ('Finished Good', 'Finished Good'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class FinanceRecord(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type}: {self.title}"


class SaleRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    customer = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    @property
    def total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product_name} → {self.customer}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.status}"

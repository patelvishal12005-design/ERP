from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet,
    InventoryViewSet,
    FinanceViewSet,
    SaleViewSet,
    DashboardStatsView,
    MonthlyAttendanceView,
    RegisterView,
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'inventory', InventoryViewSet)
router.register(r'finance', FinanceViewSet)
router.register(r'sales', SaleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('attendance/monthly/', MonthlyAttendanceView.as_view(), name='monthly-attendance'),
    path('register/', RegisterView.as_view(), name='register'),
]

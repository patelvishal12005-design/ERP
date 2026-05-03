from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from ERP.html_views import (
    html_login, html_logout,
    html_dashboard, html_employees,
    html_inventory, html_finance, html_sales,
)

urlpatterns = [
    # ── HTML Admin Panel ──────────────────────────────────────
    path('', html_login, name='html_login'),
    path('logout/', html_logout, name='html_logout'),
    path('dashboard/', html_dashboard, name='html_dashboard'),
    path('employees/', html_employees, name='html_employees'),
    path('inventory/', html_inventory, name='html_inventory'),
    path('finance/', html_finance, name='html_finance'),
    path('sales/', html_sales, name='html_sales'),

    # ── REST API (for React frontend) ─────────────────────────
    path('api/', include('ERP.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
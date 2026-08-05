from django.urls import path
from . import dashboardservice

urlpatterns = [
    path('', dashboardservice.dashboard_view, name='dashboard'),
    path('report-portal/', dashboardservice.report_portal, name='report_portal'),
    path('report-portal/csv/', dashboardservice.export_csv, name='export_csv'),
    path('report-portal/pdf/', dashboardservice.export_pdf, name='export_pdf'),
]


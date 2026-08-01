from django.urls import path
from . import firereportservice, firereportapi

urlpatterns = [
    path('', firereportservice.report_fire, name='report_fire'),
    # Fire Report CRUD
    path('fire-reports/', firereportservice.fire_report_list, name='fire_report_list'),
    path('fire-reports/create/', firereportservice.fire_report_create, name='fire_report_create'),
    path('fire-reports/update/<int:pk>/', firereportservice.fire_report_update, name='fire_report_update'),
    path('fire-reports/delete/<int:pk>/', firereportservice.fire_report_delete, name='fire_report_delete'),

    # API endpoints
    path('api/fire-reports/', firereportapi.firereport_list_create, name='api_firereport_list_create'),
    path('api/fire-reports/<int:pk>/', firereportapi.firereport_detail, name='api_firereport_detail'),
]
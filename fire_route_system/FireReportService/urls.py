from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_fire, name='report_fire'),
    # Fire Report CRUD
    path('fire-reports/', views.fire_report_list, name='fire_report_list'),
    path('fire-reports/create/', views.fire_report_create, name='fire_report_create'),
    path('fire-reports/update/<int:pk>/', views.fire_report_update, name='fire_report_update'),
    path('fire-reports/delete/<int:pk>/', views.fire_report_delete, name='fire_report_delete'),
]
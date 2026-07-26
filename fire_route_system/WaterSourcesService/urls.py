from django.urls import path
from . import views, api_views

urlpatterns = [
    path('', views.water_list, name='water_list'),
    path('add/', views.water_add, name='water_add'),
    path('edit/<int:pk>/', views.water_edit, name='water_edit'),
    path('delete/<int:pk>/', views.water_delete, name='water_delete'),

    # API endpoints
    path('api/water-sources/', api_views.watersource_list_create, name='api_watersource_list_create'),
    path('api/water-sources/<int:pk>/', api_views.watersource_detail, name='api_watersource_detail'),
]
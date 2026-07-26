from django.urls import path
from . import views, api_views

urlpatterns = [

    path('', views.firestation_list, name='firestation_list'),

    path('create/', views.firestation_create, name='firestation_create'),

    path('update/<int:station_id>/',
         views.firestation_update,
         name='firestation_update'),

    path('delete/<int:station_id>/',
         views.firestation_delete,
         name='firestation_delete'),

    # API endpoints
    path('api/firestations/', api_views.firestation_list_create, name='api_firestation_list_create'),
    path('api/firestations/<int:station_id>/', api_views.firestation_detail, name='api_firestation_detail'),

]
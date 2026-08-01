from django.urls import path
from . import firestationservice, firestationapi

urlpatterns = [

    path('', firestationservice.firestation_list, name='firestation_list'),

    path('create/', firestationservice.firestation_create, name='firestation_create'),

    path('update/<int:station_id>/',
         firestationservice.firestation_update,
         name='firestation_update'),

    path('delete/<int:station_id>/',
         firestationservice.firestation_delete,
         name='firestation_delete'),

    # API endpoints
    path('api/firestations/', firestationapi.firestation_list_create, name='api_firestation_list_create'),
    path('api/firestations/<int:station_id>/', firestationapi.firestation_detail, name='api_firestation_detail'),

]
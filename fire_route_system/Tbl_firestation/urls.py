from django.urls import path
from . import views

urlpatterns = [

    path('', views.firestation_list, name='firestation_list'),

    path('create/', views.firestation_create, name='firestation_create'),

    path('update/<int:station_id>/',
         views.firestation_update,
         name='firestation_update'),

    path('delete/<int:station_id>/',
         views.firestation_delete,
         name='firestation_delete'),

]
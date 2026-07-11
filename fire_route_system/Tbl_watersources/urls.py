from django.urls import path
from . import views

urlpatterns = [
    path('', views.water_list, name='water_list'),
    path('add/', views.water_add, name='water_add'),
    path('edit/<int:pk>/', views.water_edit, name='water_edit'),
    path('delete/<int:pk>/', views.water_delete, name='water_delete'),
]
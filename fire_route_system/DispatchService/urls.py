from django.urls import path
from . import views

urlpatterns = [
    path('dispatch/', views.dispatch_list, name='dispatch_list'),
    path('dispatch/create/', views.dispatch_create, name='dispatch_create'),
    path('dispatch/update/<int:pk>/', views.dispatch_update, name='dispatch_update'),
    path('dispatch/delete/<int:pk>/', views.dispatch_delete, name='dispatch_delete'),
]
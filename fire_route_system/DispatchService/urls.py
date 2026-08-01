from django.urls import path
from . import dispatchservice, dispatchapi

urlpatterns = [
    path('dispatch/', dispatchservice.dispatch_list, name='dispatch_list'),
    path('dispatch/create/', dispatchservice.dispatch_create, name='dispatch_create'),
    path('dispatch/update/<int:pk>/', dispatchservice.dispatch_update, name='dispatch_update'),
    path('dispatch/delete/<int:pk>/', dispatchservice.dispatch_delete, name='dispatch_delete'),

    # API endpoints
    path('api/dispatches/', dispatchapi.dispatch_list_create, name='api_dispatch_list_create'),
    path('api/dispatches/<int:pk>/', dispatchapi.dispatch_detail, name='api_dispatch_detail'),
]
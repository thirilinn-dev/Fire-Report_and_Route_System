from django.urls import path
from . import userservice, userapi

urlpatterns = [

    # Role
    path('roles/create/', userservice.role_create, name='role_create'),
    path('roles/update/<int:pk>/', userservice.role_update, name='role_update'),
    path('roles/delete/<int:pk>/', userservice.role_delete, name='role_delete'),

    # User
    path('users/', userservice.user_list, name='user_list'),
    path('users/create/', userservice.user_create, name='user_create'),
    path('users/update/<int:pk>/', userservice.user_update, name='user_update'),
    path('users/delete/<int:pk>/', userservice.user_delete, name='user_delete'),

    # API endpoints
    path('api/roles/', userapi.role_list_create, name='api_role_list_create'),
    path('api/roles/<int:pk>/', userapi.role_detail, name='api_role_detail'),
    path('api/users/', userapi.user_list_create, name='api_user_list_create'),
    path('api/users/<int:pk>/', userapi.user_detail, name='api_user_detail'),

]
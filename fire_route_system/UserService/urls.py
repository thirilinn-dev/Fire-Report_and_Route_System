from django.urls import path
from . import views, api_views

urlpatterns = [

    # Role
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/update/<int:pk>/', views.role_update, name='role_update'),
    path('roles/delete/<int:pk>/', views.role_delete, name='role_delete'),

    # User
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/update/<int:pk>/', views.user_update, name='user_update'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),

    # API endpoints
    path('api/roles/', api_views.role_list_create, name='api_role_list_create'),
    path('api/roles/<int:pk>/', api_views.role_detail, name='api_role_detail'),
    path('api/users/', api_views.user_list_create, name='api_user_list_create'),
    path('api/users/<int:pk>/', api_views.user_detail, name='api_user_detail'),

]
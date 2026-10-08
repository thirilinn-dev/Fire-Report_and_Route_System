from django.urls import path
from . import views,api

app_name='emergency'
urlpatterns=[
    path('',views.dashboard,name='dashboard'),path('register/',views.register,name='register'),
    path('posts/',views.posts,name='posts'),path('report/',views.report,name='report'),
    path('queue/',views.incident_queue,name='queue'),
    path('incidents/',views.incidents,name='incidents'),path('incidents/',views.incidents,name='incident_list'),path('incidents/<int:pk>/',views.incident,name='incident'),
    path('incidents/<int:pk>/pdf/',views.incident_pdf,name='incident_pdf'),
    path('incidents/<int:pk>/<str:action>/',views.action,name='action'),
    path('deployments/<int:pk>/<str:action>/',views.deployment_action,name='deployment_action'),
    path('leaves/<int:pk>/review/',views.leave_review,name='leave_review'),
    path('map/',views.map_view,name='map'),path('reports/',views.reports,name='reports'),
    path('api/incidents/',api.incidents,name='api_incidents'),path('api/incidents/<int:pk>/',api.incident_detail,name='api_incident'),
    path('api/map/',api.map_data,name='map_data'),path('api/poll/',api.poll,name='poll'),
    path('api/plan-preview/',api.plan_preview,name='plan_preview'),
    path('manage/<str:kind>/',views.listing,name='list'),path('manage/<str:kind>/new/',views.edit,name='create'),path('manage/<str:kind>/<int:pk>/',views.edit,name='edit'),
]

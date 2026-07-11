from django.urls import path
from . import views

urlpatterns =[
    path ('', views.report_fire , name='report_fire'),
]
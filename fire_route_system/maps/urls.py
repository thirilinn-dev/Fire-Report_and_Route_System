from django.urls import path
from . import mapservice

urlpatterns = [
    path('', mapservice.map_view, name='map_view'),
]


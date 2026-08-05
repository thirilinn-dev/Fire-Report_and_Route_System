from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('FireStationService.urls')),
    path('report/', include('FireReportService.urls')),
    path('', include('UserService.urls')),
    path('', include('DispatchService.urls')),
    path('map/', include('maps.urls')),
    path('dashboard/', include('dashboard.urls')),
]
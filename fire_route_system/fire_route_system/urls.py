from django.contrib import admin
<<<<<<< HEAD
=======
<<<<<<< HEAD
from django.urls import path , include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('report/', include ('Tbl_firereport.urls')),
=======

>>>>>>> 86f2bc5074330786ea1e171c3a53cbb01ed70e8f
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< HEAD
    path('', include('FireStationService.urls')),
    path('report/', include('FireReportService.urls')),
    path('', include('UserService.urls')),
    path('waters/', include('WaterSourcesService.urls')),
    path('', include('DispatchService.urls')),
=======
    path('', include('Tbl_firestation.urls')),
]


from django.urls import path
from Tbl_firereport import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('report/',include('Tbl_firereport.urls')),
>>>>>>> 8411e2b0841025dabce418887528ea5942e93fad
]


from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Tbl_user.urls')),
]
from django.urls import path, include

urlpatterns = [
    path('waters/', include('Tbl_watersources.urls')),
>>>>>>> 86f2bc5074330786ea1e171c3a53cbb01ed70e8f
]
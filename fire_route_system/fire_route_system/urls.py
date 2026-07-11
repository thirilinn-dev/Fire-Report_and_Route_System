from django.contrib import admin
<<<<<<< HEAD
from django.urls import path , include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('report/', include ('Tbl_firereport.urls')),
=======

from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
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
]
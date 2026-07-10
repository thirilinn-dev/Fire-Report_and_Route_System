from django.contrib import admin

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
]


from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Tbl_user.urls')),
]
<<<<<<< HEAD


from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Tbl_dispatch.urls')),
=======
from django.urls import path, include

urlpatterns = [
    path('waters/', include('Tbl_watersources.urls')),
>>>>>>> 3c336186c4198495487cc52719eeff576e6f6583
]
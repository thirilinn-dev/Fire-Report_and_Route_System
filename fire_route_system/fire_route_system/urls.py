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
    path('report/',views.report_fire,name='report_fire'),
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
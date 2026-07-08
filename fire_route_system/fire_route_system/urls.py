from django.contrib import admin
<<<<<<< HEAD
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('firestation.urls')),
]
=======
from django.urls import path
from Tbl_firereport import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('report/',views.report_fire,name='report_fire'),
]
>>>>>>> 81f10ca2afee6271e0ff571967e62f586f43af53

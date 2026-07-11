from django.contrib import admin

from .models import FireReport

@admin.register(FireReport)
class FireReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'fire_scale', 'status', 'reported_at', 'latitude', 'longitude')
    list_filter = ('status', 'fire_scale')
    search_fields = ('reporter_phone', 'user_id')
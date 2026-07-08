from django.db import models

class FireReport(models.Model):
    # Django automatically creates an auto-incrementing integer primary key named 'id'
    # report_id = models.AutoField(primary_key=True) # Uncomment if you explicitly need it named 'report_id'

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Dispatched', 'Dispatched'),
        ('Under Control', 'Under Control'),
        ('Resolved', 'Resolved'),
        ('False Alarm', 'False Alarm'),
    ]

    user_id = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Null if anonymous 1-click report; filled if logged-in citizen reports"
    )
    reporter_phone = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        help_text="Captured manual phone input if available"
    )
    latitude = models.FloatField(
        help_text="Captured via HTML5 Geolocation API"
    )
    longitude = models.FloatField(
        help_text="Captured via HTML5 Geolocation API"
    )
    fire_scale = models.IntegerField(
        help_text="Severity Scale: 1, 2, or 3"
    )
    photo_url = models.URLField(
        max_length=255, 
        null=True, 
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Current status of the fire incident response"
    )
    reported_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the report was created"
    )

    def __str__(self):
        return f"Report {self.id} - Scale {self.fire_scale} ({self.status})"


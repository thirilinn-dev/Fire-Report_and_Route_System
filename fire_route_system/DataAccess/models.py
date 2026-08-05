from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.role_name


class User(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Inactive', 'Inactive'),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class FireStation(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Maintenance", "Maintenance"),
    ]

    station_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    latitude = models.FloatField(help_text="For Leaflet/Google Maps routing")
    longitude = models.FloatField(help_text="For Leaflet/Google Maps routing")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fire_stations" 

    def __str__(self):
        return self.name


class FireReport(models.Model):
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
        null=True,
        blank=True,
        help_text="Captured via HTML5 Geolocation API"
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Captured via HTML5 Geolocation API"
    )
    address = models.TextField(
        null=True,
        blank=True,
        help_text="Manual address input if GPS is disabled"
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

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if not self.address and (self.latitude is None or self.longitude is None):
            raise ValidationError("Either GPS location coordinates or a manual address must be provided.")

    def __str__(self):
        return f"Report {self.id} - Scale {self.fire_scale} ({self.status})"


class Dispatch(models.Model):
    report = models.ForeignKey(FireReport, on_delete=models.CASCADE)
    station = models.ForeignKey(FireStation, on_delete=models.CASCADE)
    operator = models.ForeignKey(User, on_delete=models.CASCADE)

    dispatched_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resources_deployed = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Dispatch {self.id}"


class Location(models.Model):
    name = models.CharField(max_length=150)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Tbl_Notification(models.Model):
    report = models.ForeignKey(FireReport, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_notifications"

    def __str__(self):
        return f"Notification {self.id} for Report {self.report_id}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=FireReport)
def create_notification_on_pending_report(sender, instance, created, **kwargs):
    if created and instance.status == 'Pending':
        Tbl_Notification.objects.create(report=instance)



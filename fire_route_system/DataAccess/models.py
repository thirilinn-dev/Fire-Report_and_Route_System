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


class WaterSource(models.Model):
    SOURCE_TYPES = [
        ('Hydrant', 'Hydrant'),
        ('Pond', 'Pond'),
        ('River', 'River'),
        ('Water Tank', 'Water Tank'),
    ]

    STATUS_CHOICES = [
        ('Operational', 'Operational'),
        ('Under Maintenance', 'Under Maintenance'),
        ('Unavailable', 'Unavailable'),
    ]

    source_id = models.AutoField(primary_key=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Operational')
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "water_sources"

    def __str__(self):
        return self.source_type


class Dispatch(models.Model):
    report = models.ForeignKey(FireReport, on_delete=models.CASCADE)
    station = models.ForeignKey(FireStation, on_delete=models.CASCADE)
    source = models.ForeignKey(WaterSource, on_delete=models.CASCADE)
    operator = models.ForeignKey(User, on_delete=models.CASCADE)

    dispatched_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resources_deployed = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Dispatch {self.id}"

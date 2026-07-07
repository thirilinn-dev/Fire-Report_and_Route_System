from django.db import models


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
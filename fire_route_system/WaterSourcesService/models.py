from django.db import models

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
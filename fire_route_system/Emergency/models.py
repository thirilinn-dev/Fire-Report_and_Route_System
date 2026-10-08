from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from DataAccess.models import User, FireStation, FireReport


class MyanmarLocation(models.Model):
    pcode = models.CharField(max_length=20, unique=True)
    kind = models.CharField(max_length=10, choices=[('township', 'Township'), ('town', 'Town')])
    name_en = models.CharField(max_length=150)
    name_my = models.CharField(max_length=150, blank=True)
    region_pcode = models.CharField(max_length=20)
    region_name_en = models.CharField(max_length=100)
    district_pcode = models.CharField(max_length=20)
    district_name_en = models.CharField(max_length=100)
    township_pcode = models.CharField(max_length=20)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    source_data = models.JSONField(default=dict)

    class Meta:
        ordering = ['kind', 'name_en']

    def __str__(self):
        return f'{self.name_my or self.name_en} ({self.pcode})'


class VehicleType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name


class Vehicle(models.Model):
    station = models.ForeignKey(FireStation, on_delete=models.PROTECT)
    kind = models.ForeignKey(VehicleType, on_delete=models.PROTECT)
    registration = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=[(s, s) for s in ['Available', 'Reserved', 'Deployed', 'Maintenance', 'Inactive']], default='Available')
    def __str__(self): return f'{self.registration} — {self.kind} ({self.station})'


class ResponsePlan(models.Model):
    home_station = models.ForeignKey(FireStation, on_delete=models.PROTECT, related_name='response_plans')
    level = models.PositiveSmallIntegerField(choices=FireReport.FIRE_SCALE_CHOICES)
    lead_station = models.ForeignKey(FireStation, on_delete=models.PROTECT, related_name='+')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['home_station', 'level'], name='unique_home_level')]
    def __str__(self): return f'{self.home_station} / {self.level}'


class PlanRequirement(models.Model):
    plan = models.ForeignKey(ResponsePlan, on_delete=models.CASCADE, related_name='requirements')
    station = models.ForeignKey(FireStation, on_delete=models.PROTECT)
    kind = models.ForeignKey(VehicleType, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['plan', 'station', 'kind'], name='unique_plan_resource'), models.CheckConstraint(condition=Q(quantity__gt=0), name='positive_plan_quantity')]
    def __str__(self): return f'{self.plan}: {self.station} / {self.kind} × {self.quantity}'


class Duty(models.Model):
    employee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='duties')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    task = models.CharField(max_length=200)
    def clean(self):
        if self.starts_at and self.ends_at:
            if self.ends_at <= self.starts_at: raise ValidationError('ပြီးဆုံးချိန်သည် စတင်ချိန်နောက်တွင် ဖြစ်ရမည်။')
            if Duty.objects.filter(employee=self.employee, starts_at__lt=self.ends_at, ends_at__gt=self.starts_at).exclude(pk=self.pk).exists(): raise ValidationError('တာဝန်ချိန်ထပ်နေသည်။')
            if Leave.objects.filter(employee=self.employee, status='Approved', starts_at__lt=self.ends_at, ends_at__gt=self.starts_at).exists(): raise ValidationError('ခွင့်အတည်ပြုထားသော အချိန်ဖြစ်သည်။')
    def __str__(self): return f'{self.employee} — {self.task} / {self.starts_at}'


class Leave(models.Model):
    employee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='leaves')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[(s,s) for s in ['Pending','Approved','Rejected']], default='Pending')
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    review_note = models.TextField(blank=True)
    def clean(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at: raise ValidationError('ခွင့်အချိန်အပိုင်းအခြား မမှန်ပါ။')
    def __str__(self): return f'{self.employee} / {self.status} / {self.starts_at}'


class ActingAssignment(models.Model):
    leave = models.OneToOneField(Leave, on_delete=models.PROTECT)
    employee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='acting_assignments')
    station = models.ForeignKey(FireStation, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()


class Deployment(models.Model):
    incident = models.ForeignKey(FireReport, on_delete=models.PROTECT, related_name='deployments')
    station = models.ForeignKey(FireStation, on_delete=models.PROTECT)
    state = models.CharField(max_length=20, choices=[(s,s) for s in ['Ordered','Accepted','Departed','Arrived','Returned','Cancelled']], default='Ordered')
    route = models.JSONField(default=dict, blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.incident_id} / {self.station} / {self.state}'


class VehicleParticipation(models.Model):
    deployment = models.ForeignKey(Deployment, on_delete=models.PROTECT, related_name='vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    actual = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)


class StaffParticipation(models.Model):
    deployment = models.ForeignKey(Deployment, on_delete=models.PROTECT, related_name='personnel')
    employee = models.ForeignKey(User, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    actual = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)


class IncidentUpdate(models.Model):
    incident = models.ForeignKey(FireReport, on_delete=models.PROTECT, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    station = models.ForeignKey(FireStation, null=True, blank=True, on_delete=models.PROTECT)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class StationReport(models.Model):
    deployment = models.OneToOneField(Deployment, on_delete=models.PROTECT, related_name='station_report')
    narrative = models.TextField()
    water_gallons = models.DecimalField(max_digits=12, decimal_places=2)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT)
    submitted_at = models.DateTimeField(auto_now=True)
    def clean(self):
        if self.water_gallons is not None and self.water_gallons < 0: raise ValidationError('ရေဂါလန် အနုတ်တန်ဖိုး မဖြစ်ရပါ။')


class FinalReport(models.Model):
    incident = models.OneToOneField(FireReport, on_delete=models.PROTECT, related_name='final_report')
    narrative = models.TextField()
    snapshot = models.JSONField(default=dict)
    state = models.CharField(max_length=20, default='Submitted', choices=[(s,s) for s in ['Submitted','Revision','Approved']])
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    review_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now=True)


class Notice(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.PROTECT)
    incident = models.ForeignKey(FireReport, on_delete=models.PROTECT)
    message = models.CharField(max_length=255)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    station = models.ForeignKey(FireStation, null=True, blank=True, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=[('Public','လူတိုင်း'),('Staff','ဝန်ထမ်းအားလုံး'),('Station','မိမိစခန်း')])
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title


class Audit(models.Model):
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class RoadNode(models.Model):
    osm_id = models.BigIntegerField(unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()


class RoadEdge(models.Model):
    source = models.ForeignKey(RoadNode, on_delete=models.CASCADE, related_name='outgoing')
    target = models.ForeignKey(RoadNode, on_delete=models.CASCADE, related_name='incoming')
    metres = models.FloatField()
    name = models.CharField(max_length=255, blank=True)

from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_name(self):
        role_burmese_map = {
            'admin': 'စနစ်အုပ်ချုပ်သူ (Administrator)',
            'administrator': 'စနစ်အုပ်ချုပ်သူ (Administrator)',
            'dispatcher': 'အရေးပေါ်ကွပ်ကဲရေးမှူး (Dispatcher)',
            'operator': 'အရေးပေါ်ကွပ်ကဲရေးမှူး (Dispatcher)',
            'firefighter': 'မီးသတ်တပ်ဖွဲ့ဝင် (Firefighter)',
            'responder': 'မီးသတ်တပ်ဖွဲ့ဝင် (Firefighter)',
            'citizen': 'သတင်းပို့သူ ပြည်သူ (Citizen)',
            'reporter': 'သတင်းပို့သူ ပြည်သူ (Citizen)',
        }
        return role_burmese_map.get(self.role_name.lower().strip(), self.role_name)

    def __str__(self):
        return self.role_name


import hmac
import hashlib
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    STATUS_CHOICES = [
        ('Active', 'အသုံးပြုဆဲ'),
        ('Suspended', 'ယာယီရပ်ဆိုင်း'),
        ('Inactive', 'ပိတ်ထား'),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    password_hash = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    nrc = models.CharField(max_length=50, blank=True)
    rank = models.CharField(max_length=100, blank=True)
    station = models.ForeignKey('FireStation', null=True, blank=True, on_delete=models.PROTECT, related_name='staff')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ── Django Authentication Protocol Support ────────────────────────────
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self.status == 'Active'

    def get_username(self):
        return self.username

    def get_session_auth_hash(self):
        key_salt = "DataAccess.models.User.get_session_auth_hash"
        return hmac.new(
            settings.SECRET_KEY.encode(),
            f"{self.password_hash}:{key_salt}".encode(),
            hashlib.sha256
        ).hexdigest()

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        # Dual-support: verify Django PBKDF2 hash or plaintext fallback
        if check_password(raw_password, self.password_hash):
            return True
        elif self.password_hash == raw_password:
            # Upgrade legacy/plaintext password to PBKDF2 hash automatically
            self.set_password(raw_password)
            if self.pk:
                User.objects.filter(pk=self.pk).update(password_hash=self.password_hash)
            return True
        return False

    # ── Role-Based Authorization Helpers ─────────────────────────────────
    @property
    def role_name(self):
        return self.role.role_name if self.role else ""

    @property
    def role_display(self):
        return self.role.display_name if self.role else ""

    def has_role(self, *role_names):
        """
        Check if user's role matches any of the specified roles or aliases.
        Aliases:
          Admin <-> Administrator
          Operator <-> Dispatcher
          Responder <-> Firefighter
          Reporter <-> Citizen
        """
        if not self.role:
            return False
        current_role = self.role.role_name.lower().strip()
        role_map = {
            'admin': {'admin', 'administrator'},
            'administrator': {'admin', 'administrator'},
            'dispatcher': {'dispatcher', 'operator', 'station admin'},
            'operator': {'dispatcher', 'operator', 'station admin'},
            'station admin': {'station admin', 'dispatcher', 'operator'},
            'firefighter': {'firefighter', 'responder'},
            'responder': {'firefighter', 'responder'},
            'citizen': {'citizen', 'reporter'},
            'reporter': {'citizen', 'reporter'},
        }

        for target in role_names:
            t = target.lower().strip()
            aliases = role_map.get(t, {t})
            if current_role in aliases:
                return True
        return False

    @property
    def is_admin(self):
        return self.has_role('Admin', 'Administrator')

    @property
    def is_dispatcher(self):
        return self.has_role('Dispatcher', 'Operator')

    @property
    def is_firefighter(self):
        return self.has_role('Firefighter', 'Responder')

    @property
    def is_citizen(self):
        return self.has_role('Citizen', 'Reporter')

    @property
    def is_station_admin(self):
        if self.has_role('Station Admin') and self.station_id:
            return True
        from django.utils import timezone
        return self.acting_assignments.filter(starts_at__lte=timezone.now(), ends_at__gt=timezone.now(), leave__status='Approved').exists()

    # ── Django Permissions Compatibility ─────────────────────────────────
    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def __str__(self):
        return f"{self.username} ({self.role_name})"


class FireStation(models.Model):
    STATUS_CHOICES = [
        ("Active", "အသင့်ရှိ"),
        ("Unknown", "အသင့်ရှိမှု မစစ်ဆေးရသေး"),
        ("Inactive", "ယာယီပိတ်ထား"),
        ("Maintenance", "ပြုပြင်ထိန်းသိမ်းဆဲ"),
    ]

    @property
    def status_display(self):
        status_map = {
            'Active': 'အသင့်ရှိ',
            'Inactive': 'ယာယီပိတ်ထား',
            'Maintenance': 'ပြုပြင်ထိန်းသိမ်းဆဲ',
        }
        return status_map.get(self.status, self.get_status_display() or self.status)

    station_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    township = models.CharField('မြို့နယ်', max_length=100, blank=True)
    source_key = models.CharField(max_length=80, unique=True, null=True, blank=True)
    source_data = models.JSONField(default=dict, blank=True)
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
    source_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    source_data = models.JSONField(default=dict, blank=True)
    home_station = models.ForeignKey(FireStation, null=True, blank=True, on_delete=models.PROTECT, related_name='local_incidents')
    lead_station = models.ForeignKey(FireStation, null=True, blank=True, on_delete=models.PROTECT, related_name='led_incidents')
    reporter_latitude = models.FloatField(null=True, blank=True)
    reporter_longitude = models.FloatField(null=True, blank=True)
    coordinates_confirmed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    STATUS_CHOICES = [
        ('Pending', 'ဆိုင်းငံ့ / စိစစ်ဆဲ'),
        ('Confirmed', 'အတည်ပြုပြီး'),
        ('Dispatched', 'တပ်ဖွဲ့စေလွှတ်ပြီး'),
        ('Under Control', 'မီးထိန်းချုပ်နိုင်ပြီ'),
        ('Resolved', 'ငြှိမ်းသတ်ပြီးစီး'),
        ('False Alarm', 'သတင်းမှား'),
    ]

    FIRE_SCALE_CHOICES = [
        (0, 'နယ်မြေခံ'),
        (1, 'အဆင့် ၁'),
        (2, 'အဆင့် ၂'),
        (3, 'အဆင့် ၃'),
        (4, 'အဆင့် ၄'),
        (5, 'အဆင့် ၅'),
    ]

    @property
    def scale_display(self):
        scale_map = {
            0: 'နယ်မြေခံ',
            1: 'အဆင့် ၁',
            2: 'အဆင့် ၂',
            3: 'အဆင့် ၃',
            4: 'အဆင့် ၄',
            5: 'အဆင့် ၅',
        }
        return scale_map.get(self.fire_scale, f"အဆင့် {self.fire_scale}")

    @property
    def status_display(self):
        status_map = {
            'Pending': 'ဆိုင်းငံ့ / စိစစ်ဆဲ',
            'Confirmed': 'အတည်ပြုပြီး',
            'Dispatched': 'တပ်ဖွဲ့စေလွှတ်ပြီး',
            'Under Control': 'မီးထိန်းချုပ်နိုင်ပြီ',
            'Resolved': 'ငြှိမ်းသတ်ပြီးစီး',
            'False Alarm': 'သတင်းမှား',
        }
        return status_map.get(self.status, self.get_status_display() or self.status)

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
        choices=FIRE_SCALE_CHOICES,
        null=True,
        help_text="Severity Scale: 0=နယ်မြေခံ, 1=Level 1, 2=Level 2, 3=Level 3, 4=Level 4, 5=Level 5"
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

    def delete(self, *args, **kwargs):
        if self.status != 'Resolved':
            from django.core.exceptions import ValidationError
            raise ValidationError("Incident reports cannot be deleted unless they are resolved.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Report {self.id} - Scale {self.fire_scale} ({self.status})"


class Dispatch(models.Model):
    report = models.ForeignKey(FireReport, on_delete=models.CASCADE)
    station = models.ForeignKey(FireStation, on_delete=models.CASCADE)
    operator = models.ForeignKey(User, on_delete=models.CASCADE)

    dispatched_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, default='Dispatched')
    resources_deployed = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Dispatch {self.id} ({self.status})"


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



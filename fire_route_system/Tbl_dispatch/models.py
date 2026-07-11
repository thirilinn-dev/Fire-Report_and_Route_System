from django.db import models

class Dispatch(models.Model):
    report = models.ForeignKey("Tbl_firereport.FireReport", on_delete=models.CASCADE)
    station = models.ForeignKey("Tbl_firestation.FireStation", on_delete=models.CASCADE)
    source = models.ForeignKey("Tbl_watersources.WaterSource", on_delete=models.CASCADE)
    operator = models.ForeignKey("Tbl_user.User", on_delete=models.CASCADE)

    dispatched_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resources_deployed = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Dispatch {self.id}"
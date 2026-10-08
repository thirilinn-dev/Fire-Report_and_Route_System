from django import forms
from DataAccess.models import FireReport

class FireReportForm(forms.ModelForm):
    class Meta:
        model = FireReport
        fields = '__all__'

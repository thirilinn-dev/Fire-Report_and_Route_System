from django import forms
from .models import WaterSource

class WaterSourceForm(forms.ModelForm):
    class Meta:
        model = WaterSource
        fields = '__all__'
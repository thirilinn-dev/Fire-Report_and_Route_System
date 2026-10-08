from django import forms
from .models import Dispatch

class DispatchForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = '__all__'
import re
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from DataAccess.models import User, Role, FireReport, FireStation
from .models import *


class RegisterForm(forms.Form):
    full_name=forms.CharField(label='အမည်',max_length=150)
    phone_number=forms.CharField(label='ဖုန်းနံပါတ်',max_length=20)
    nrc=forms.CharField(label='မှတ်ပုံတင်အမှတ်',max_length=50)
    email=forms.EmailField(label='Email (မဖြည့်လည်းရသည်)',required=False,max_length=100)
    password=forms.CharField(label='စကားဝှက်',widget=forms.PasswordInput)
    confirmation=forms.CharField(label='စကားဝှက် ထပ်ဖြည့်ပါ',widget=forms.PasswordInput)
    def clean_phone_number(self):
        phone=re.sub(r'[\s-]','',self.cleaned_data['phone_number'])
        if not re.fullmatch(r'\+?\d{7,15}',phone): raise ValidationError('ဖုန်းနံပါတ် မမှန်ပါ။')
        if User.objects.filter(phone_number=phone).exists(): raise ValidationError('ဖုန်းနံပါတ် အသုံးပြုပြီးဖြစ်သည်။')
        return phone
    def clean(self):
        data=super().clean()
        if data.get('password')!=data.get('confirmation'): self.add_error('confirmation','စကားဝှက် မတူပါ။')
        if data.get('password'): validate_password(data['password'])
        return data
    def clean_email(self):
        email=self.cleaned_data.get('email') or None
        if email and User.objects.filter(email__iexact=email).exists():raise ValidationError('Email အသုံးပြုပြီးဖြစ်သည်။')
        return email
    def save(self):
        import uuid
        role,_=Role.objects.get_or_create(role_name='Citizen')
        user=User(role=role,username='citizen_'+uuid.uuid4().hex[:20],email=self.cleaned_data.get('email'),**{k:self.cleaned_data[k] for k in ['full_name','phone_number','nrc']})
        user.set_password(self.cleaned_data['password']);user.save();return user


class StaffForm(forms.ModelForm):
    password=forms.CharField(label='စကားဝှက် (ပြင်မည်ဆိုမှဖြည့်ပါ)',required=False,widget=forms.PasswordInput)
    class Meta:
        model=User
        fields=['full_name','username','phone_number','email','nrc','rank','station','role','status']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['role'].queryset=Role.objects.filter(role_name__in=['Administrator','Station Admin','Firefighter','Citizen'])
    def clean(self):
        data=super().clean()
        role=data.get('role')
        if role and role.role_name in ['Station Admin','Firefighter'] and not data.get('station'): self.add_error('station','စခန်းရွေးပါ။')
        if not self.instance.pk and not data.get('password'): self.add_error('password','စကားဝှက် ဖြည့်ပါ။')
        if data.get('password'): validate_password(data['password'])
        data['email']=data.get('email') or None
        data['phone_number']=data.get('phone_number') or None
        return data
    def save(self,commit=True):
        user=super().save(commit=False)
        if self.cleaned_data.get('password'): user.set_password(self.cleaned_data['password'])
        if commit:user.save()
        return user


class IncidentForm(forms.ModelForm):
    class Meta:
        model=FireReport
        fields=['address','latitude','longitude','reporter_latitude','reporter_longitude']
        labels={'address':'မီးလောင်ရာလိပ်စာ','latitude':'မီးလောင်ရာ Latitude','longitude':'မီးလောင်ရာ Longitude','reporter_latitude':'သတင်းပို့သူ Latitude','reporter_longitude':'သတင်းပို့သူ Longitude'}
        help_texts={'address':'GPS မရှိလျှင် လိပ်စာသီးသန့်ဖြင့်တင်နိုင်ပါသည်။','latitude':'မီးလောင်ရာ Map pin','longitude':'မီးလောင်ရာ Map pin'}
    def clean(self):
        data=super().clean()
        for prefix in ['', 'reporter_']:
            lat,lng=data.get(prefix+'latitude'),data.get(prefix+'longitude')
            if (lat is None)!=(lng is None): raise ValidationError('Latitude နှင့် Longitude နှစ်ခုလုံး ဖြည့်ပါ။')
            if lat is not None and (not -90<=lat<=90 or not -180<=lng<=180):raise ValidationError('Coordinate မမှန်ပါ။')
        return data


class ConfirmForm(forms.ModelForm):
    class Meta:
        model = FireReport
        fields = ['fire_scale']
        labels = {'fire_scale': 'မီးလောင်မှုအဆင့် (Fire Level)'}
        widgets = {
            'fire_scale': forms.Select(attrs={'class': 'cad-select', 'id': 'id_fire_scale', 'style': 'font-size: 1rem; padding: 0.5rem 1rem; font-weight: 600; min-width: 200px;'})
        }


def model_form(model,fields):
    form=forms.modelform_factory(model,fields=fields,widgets={
        name:forms.DateTimeInput(attrs={'placeholder':'DD-MM-YYYY HH:MM AM/PM','class':'cad-datetimepicker','autocomplete':'off'},format='%d-%m-%Y %I:%M %p')
        for name in ['starts_at','ends_at'] if name in fields})
    for name in ['starts_at','ends_at']:
        if name in form.base_fields:form.base_fields[name].input_formats=['%d-%m-%Y %I:%M %p','%d-%m-%Y %H:%M','%d/%m/%Y %I:%M %p','%d/%m/%Y %H:%M','%Y-%m-%dT%H:%M']
    return form


FORM_TYPES={
    'stations':(FireStation,model_form(FireStation,['name','township','address','contact_number','latitude','longitude','status'])),
    'staff':(User,StaffForm),
    'vehicle-types':(VehicleType,model_form(VehicleType,['name'])),
    'vehicles':(Vehicle,model_form(Vehicle,['station','kind','registration','status'])),
    'plans':(ResponsePlan,model_form(ResponsePlan,['home_station','level','lead_station'])),
    'requirements':(PlanRequirement,model_form(PlanRequirement,['plan','station','kind','quantity'])),
    'duties':(Duty,model_form(Duty,['employee','starts_at','ends_at','task'])),
    'leaves':(Leave,model_form(Leave,['starts_at','ends_at','reason'])),
    'posts':(Post,model_form(Post,['title','body','station','audience','published'])),
}

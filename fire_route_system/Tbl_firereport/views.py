from django.shortcuts import render
from django.http import HttpResponse
from .models import FireReport

def report_fire(request):

    if request.method == "POST":
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        scale = request.POST.get('fire_scale')
        phone = request.POST.get('reporter_phone')
        image_file=request.FILES.get('fire_image')

       
        FireReport.objects.create(
            latitude=lat,
            longitude=lng,
            fire_scale=scale,
            reporter_phone=phone,
            status='Pending'
        )
        return HttpResponse("<h2>မီးလောင်မှု သတင်းပို့ခြင်း အောင်မြင်ပါသည်။ မီးသတ်ကားများ ချက်ချင်း စေလွှတ်ပါမည်။</h2>")

    
    return render(request, 'report_form.html')
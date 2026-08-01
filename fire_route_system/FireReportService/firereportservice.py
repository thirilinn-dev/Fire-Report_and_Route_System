from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import FireReport
from .forms import FireReportForm

def report_fire(request):
    if request.method == "POST":
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        scale = request.POST.get('fire_scale')
        phone = request.POST.get('reporter_phone')
        
        # In case photo upload is supported, we can handle it
        # However photo_url in DB is a URLField, but fire_image in form is a FileField.
        # We can handle it gracefully.
        FireReport.objects.create(
            latitude=lat,
            longitude=lng,
            fire_scale=scale,
            reporter_phone=phone,
            status='Pending'
        )
        return render(request, 'report_form.html', {'success': True})

    return render(request, 'report_form.html')


def fire_report_list(request):
    reports = FireReport.objects.all().order_by('-reported_at')
    return render(request, 'fire_reports/list.html', {'reports': reports})


def fire_report_create(request):
    form = FireReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fire report created successfully.")
        return redirect('fire_report_list')
    return render(request, 'fire_reports/form.html', {'form': form, 'title': 'Create Fire Report'})


def fire_report_update(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    form = FireReportForm(request.POST or None, instance=report)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fire report updated successfully.")
        return redirect('fire_report_list')
    return render(request, 'fire_reports/form.html', {'form': form, 'title': 'Update Fire Report', 'report': report})


def fire_report_delete(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    if request.method == "POST":
        report.delete()
        messages.success(request, "Fire report deleted successfully.")
        return redirect('fire_report_list')
    return render(request, 'fire_reports/delete.html', {'report': report})

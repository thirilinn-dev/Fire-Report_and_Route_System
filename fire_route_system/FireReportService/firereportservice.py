from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import FireReport
from .forms import FireReportForm

def report_fire(request):
    if request.method == "POST":
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        phone = request.POST.get('reporter_phone')
        addr = request.POST.get('address', '').strip()

        # Parse coordinates
        lat_val = float(lat) if (lat and lat.strip()) else None
        lng_val = float(lng) if (lng and lng.strip()) else None
        phone_val = phone.strip() if phone else None

        # Validation: Either GPS (lat & lng) OR address must be provided
        if not addr and (lat_val is None or lng_val is None):
            return render(request, 'report_form.html', {
                'error': 'Either GPS location coordinates or a manual address description must be provided.',
                'latitude': lat,
                'longitude': lng,
                'reporter_phone': phone,
                'address': addr
            })

        FireReport.objects.create(
            latitude=lat_val,
            longitude=lng_val,
            address=addr if addr else None,
            fire_scale=0,
            reporter_phone=phone_val,
            status='Pending'
        )
        return render(request, 'report_form.html', {'success': True})

    return render(request, 'report_form.html')


def fire_report_list(request):
    from django.db.models import Q
    from django.utils import timezone
    import datetime

    # Read GET parameters
    query = request.GET.get('q', '').strip()
    date_str = request.GET.get('date', '').strip()
    status_filter = request.GET.get('status', '').strip()
    scale_filter = request.GET.get('scale', '').strip()

    # Base query excluding 'Pending'
    reports = FireReport.objects.exclude(status='Pending')

    # Apply date search or default 7-day window
    if date_str:
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            reports = reports.filter(reported_at__date=parsed_date)
        except ValueError:
            pass
    else:
        seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        reports = reports.filter(reported_at__gte=seven_days_ago)

    # Filter dropdowns
    if status_filter:
        reports = reports.filter(status=status_filter)
    if scale_filter:
        reports = reports.filter(fire_scale=scale_filter)

    # Preserve search query
    if query:
        filters = Q(reporter_phone__icontains=query) | Q(status__icontains=query)
        if query.isdigit():
            filters |= Q(id=int(query))
        reports = reports.filter(filters)

    reports = reports.order_by('-reported_at')

    import json
    reports_json = json.dumps([
        {
            'id': r.id,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'fire_scale': r.fire_scale,
            'status': r.status,
            'reporter_phone': r.reporter_phone or 'Anonymous',
            'reported_at': r.reported_at.strftime('%d-%m-%Y %I:%M %p'),
        }
        for r in reports
        if r.latitude is not None and r.longitude is not None
    ])

    return render(request, 'fire_reports/incident_list.html', {
        'reports': reports,
        'reports_json': reports_json,
        'query': query,
        'selected_date': date_str,
        'selected_status': status_filter,
        'selected_scale': scale_filter
    })


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
    if report.status != 'Resolved':
        messages.error(request, "Incident reports cannot be deleted unless they are resolved.")
        return redirect('fire_report_list')
    if request.method == "POST":
        try:
            report.delete()
            messages.success(request, "Fire report deleted successfully.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect('fire_report_list')
    return render(request, 'fire_reports/delete.html', {'report': report})


def triage_queue(request):
    from DataAccess.models import Tbl_Notification
    unread = Tbl_Notification.objects.filter(is_read=False).select_related('report').order_by('-created_at')
    return render(request, 'fire_reports/triage_queue.html', {
        'notifications': unread
    })


from django.views.decorators.http import require_POST

@require_POST
def confirm_incident(request, notification_id):
    from DataAccess.models import Tbl_Notification
    notification = get_object_or_404(Tbl_Notification, pk=notification_id)
    notification.is_read = True
    notification.save()

    report = notification.report
    report.status = 'Confirmed'
    report.save()

    return redirect('triage_queue')

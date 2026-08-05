import json
from django.shortcuts import render
from django.utils import timezone
from DataAccess.models import FireReport, FireStation, Dispatch

def dashboard_view(request):
    # Active statuses list
    active_statuses = ['Pending', 'Dispatched']
    
    # 1. Top Row (KPI Cards)
    # Total Active Fires
    total_active_fires = FireReport.objects.filter(status__in=active_statuses).count()
    # High Severity Fires (Active fires of severity scale 3)
    high_severity_fires = FireReport.objects.filter(status__in=active_statuses, fire_scale=3).count()
    # Available Stations (Count of active stations)
    available_stations = FireStation.objects.filter(status='Active').count()
    # Total Dispatches today
    today = timezone.now().date()
    total_dispatches_today = Dispatch.objects.filter(dispatched_at__date=today).count()

    # 2. Bottom Row (Actionable Tables)
    # Pending Reports (Need immediate operator action)
    pending_reports = FireReport.objects.filter(status='Pending').order_by('-reported_at')
    # Active Dispatches (Station handling which report, unresolved dispatches)
    active_dispatches = Dispatch.objects.filter(resolved_at__isnull=True).select_related('report', 'station', 'operator').order_by('-dispatched_at')

    # 3. Leaflet.js Active Pins
    # Active Fire Pins
    active_fires = FireReport.objects.filter(status__in=active_statuses).order_by('-reported_at')
    fire_pins = []
    for report in active_fires:
        fire_pins.append({
            'id': report.id,
            'latitude': report.latitude,
            'longitude': report.longitude,
            'fire_scale': report.fire_scale,
            'status': report.status,
            'reported_at': report.reported_at.strftime('%I:%M %p') if report.reported_at else ''
        })

    # Active Station Pins
    active_stations_list = FireStation.objects.filter(status='Active')
    station_pins = []
    for station in active_stations_list:
        station_pins.append({
            'station_id': station.station_id,
            'name': station.name,
            'latitude': station.latitude,
            'longitude': station.longitude,
            'contact_number': station.contact_number,
            'status': station.status
        })

    # 4. Severity Breakdown Charts (Chart.js counts)
    # Get count of all active fires grouped by severity scale (1, 2, 3)
    severity_breakdown = {
        'scale_1': FireReport.objects.filter(fire_scale=1).count(),
        'scale_2': FireReport.objects.filter(fire_scale=2).count(),
        'scale_3': FireReport.objects.filter(fire_scale=3).count(),
    }
    
    context = {
        'total_active_fires': total_active_fires,
        'high_severity_fires': high_severity_fires,
        'available_stations': available_stations,
        'total_dispatches_today': total_dispatches_today,
        'pending_reports': pending_reports,
        'active_dispatches': active_dispatches,
        'fire_pins_json': json.dumps(fire_pins),
        'station_pins_json': json.dumps(station_pins),
        'severity_breakdown_json': json.dumps(severity_breakdown),
    }
    
    return render(request, 'dashboard/dashboard.html', context)


import csv
import datetime
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa

def get_filtered_reports(request):
    reports = FireReport.objects.all().order_by('-reported_at')
    
    # 1. Filter by Level (fire_scale)
    level = request.GET.get('level', '').strip()
    if level and level != 'All':
        try:
            reports = reports.filter(fire_scale=int(level))
        except ValueError:
            pass

    # 2. Filter by Period or custom date range
    period = request.GET.get('period', '').strip()
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()

    now = timezone.now()

    if start_date_str or end_date_str:
        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
                reports = reports.filter(reported_at__gte=start_date)
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                end_date = timezone.make_aware(end_date)
                reports = reports.filter(reported_at__lte=end_date)
            except ValueError:
                pass
    elif period:
        if period == 'Daily':
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            reports = reports.filter(reported_at__gte=today_start)
        elif period == 'Monthly':
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            reports = reports.filter(reported_at__gte=month_start)
        elif period == 'Yearly':
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            reports = reports.filter(reported_at__gte=year_start)

    return reports


def report_portal(request):
    reports = get_filtered_reports(request)
    
    context = {
        'reports': reports,
        'level': request.GET.get('level', 'All'),
        'period': request.GET.get('period', 'All'),
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
    }
    return render(request, 'dashboard/report_preview.html', context)


def export_csv(request):
    reports = get_filtered_reports(request)
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="fire_reports.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['No', 'Reporter Phone', 'Fire Scale', 'Status', 'Location', 'Logged At'])
    
    for idx, report in enumerate(reports, 1):
        loc = f"{report.latitude}, {report.longitude}" if (report.latitude and report.longitude) else (report.address or 'N/A')
        writer.writerow([
            idx,
            report.reporter_phone or 'Anonymous',
            f"Level {report.fire_scale}",
            report.status,
            loc,
            report.reported_at.strftime('%Y-%m-%d %H:%M')
        ])
        
    return response


def export_pdf(request):
    reports = get_filtered_reports(request)
    
    template = get_template('dashboard/pdf_report.html')
    
    total_count = reports.count()
    level_1 = reports.filter(fire_scale=1).count()
    level_2 = reports.filter(fire_scale=2).count()
    level_3 = reports.filter(fire_scale=3).count()
    
    context = {
        'reports': reports,
        'total_count': total_count,
        'level_1': level_1,
        'level_2': level_2,
        'level_3': level_3,
        'filter_level': request.GET.get('level', 'All'),
        'filter_period': request.GET.get('period', 'All'),
        'filter_start': request.GET.get('start_date', 'N/A'),
        'filter_end': request.GET.get('end_date', 'N/A'),
        'generated_at': timezone.now()
    }
    
    html = template.render(context)
    result = BytesIO()
    
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result, encoding='utf-8')
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="fire_report.pdf"'
        return response
        
    return HttpResponse('Errors encountered while rendering the PDF report.', status=400)

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
    # High Severity Fires (Active fires of severity scale 5 — the highest level)
    high_severity_fires = FireReport.objects.filter(status__in=active_statuses, fire_scale=5).count()
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
    # Get count of all active fires grouped by severity scale (0–5)
    severity_breakdown = {
        'scale_0': FireReport.objects.filter(fire_scale=0).count(),
        'scale_1': FireReport.objects.filter(fire_scale=1).count(),
        'scale_2': FireReport.objects.filter(fire_scale=2).count(),
        'scale_3': FireReport.objects.filter(fire_scale=3).count(),
        'scale_4': FireReport.objects.filter(fire_scale=4).count(),
        'scale_5': FireReport.objects.filter(fire_scale=5).count(),
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

import json
from django.shortcuts import render
from DataAccess.models import FireStation

def map_view(request):
    stations = FireStation.objects.all().order_by('name')

    stations_list = []
    for station in stations:
        stations_list.append({
            'id': station.station_id,
            'name': station.name,
            'latitude': float(station.latitude) if station.latitude else None,
            'longitude': float(station.longitude) if station.longitude else None,
            'address': station.address or '',
            'contact_number': station.contact_number or '',
            'status': station.status or ''
        })

    stations_json = json.dumps([
        s for s in stations_list
        if s['latitude'] is not None and s['longitude'] is not None
    ])

    context = {
        'stations': stations,
        'stations_json': stations_json,
    }
    return render(request, 'maps/map.html', context)

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from DataAccess.models import FireStation

def serialize_firestation(station):
    return {
        'station_id': station.station_id,
        'name': station.name,
        'address': station.address,
        'contact_number': station.contact_number,
        'latitude': station.latitude,
        'longitude': station.longitude,
        'status': station.status,
        'created_at': station.created_at.isoformat() if station.created_at else None,
    }

@csrf_exempt
def firestation_list_create(request):
    if request.method == 'GET':
        stations = FireStation.objects.all()
        return JsonResponse([serialize_firestation(s) for s in stations], safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        required_fields = ['name', 'address', 'contact_number', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'{field} is required'}, status=400)

        try:
            station = FireStation.objects.create(
                name=data['name'],
                address=data['address'],
                contact_number=data['contact_number'],
                latitude=float(data['latitude']),
                longitude=float(data['longitude']),
                status=data.get('status', 'Active')
            )
            return JsonResponse(serialize_firestation(station), status=201)
        except ValueError:
            return JsonResponse({'error': 'latitude and longitude must be valid numbers'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def firestation_detail(request, station_id):
    try:
        station = FireStation.objects.get(pk=station_id)
    except FireStation.DoesNotExist:
        return JsonResponse({'error': 'FireStation not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_firestation(station))

    elif request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if request.method == 'PUT':
            required_fields = ['name', 'address', 'contact_number', 'latitude', 'longitude']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'{field} is required for PUT'}, status=400)

            try:
                station.name = data['name']
                station.address = data['address']
                station.contact_number = data['contact_number']
                station.latitude = float(data['latitude'])
                station.longitude = float(data['longitude'])
                station.status = data.get('status', 'Active')
            except ValueError:
                return JsonResponse({'error': 'latitude and longitude must be valid numbers'}, status=400)
        else: # PATCH
            if 'name' in data:
                station.name = data['name']
            if 'address' in data:
                station.address = data['address']
            if 'contact_number' in data:
                station.contact_number = data['contact_number']
            if 'latitude' in data:
                try:
                    station.latitude = float(data['latitude'])
                except ValueError:
                    return JsonResponse({'error': 'latitude must be a valid number'}, status=400)
            if 'longitude' in data:
                try:
                    station.longitude = float(data['longitude'])
                except ValueError:
                    return JsonResponse({'error': 'longitude must be a valid number'}, status=400)
            if 'status' in data:
                station.status = data['status']

        try:
            station.save()
            return JsonResponse(serialize_firestation(station))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            station.delete()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

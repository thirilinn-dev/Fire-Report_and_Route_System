import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from DataAccess.models import WaterSource

def serialize_watersource(source):
    return {
        'source_id': source.source_id,
        'source_type': source.source_type,
        'description': source.description,
        'latitude': source.latitude,
        'longitude': source.longitude,
        'status': source.status,
        'last_checked': source.last_checked.isoformat() if source.last_checked else None,
    }

@csrf_exempt
def watersource_list_create(request):
    if request.method == 'GET':
        sources = WaterSource.objects.all()
        return JsonResponse([serialize_watersource(s) for s in sources], safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        required_fields = ['source_type', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'{field} is required'}, status=400)

        try:
            source = WaterSource.objects.create(
                source_type=data['source_type'],
                description=data.get('description'),
                latitude=float(data['latitude']),
                longitude=float(data['longitude']),
                status=data.get('status', 'Operational')
            )
            return JsonResponse(serialize_watersource(source), status=201)
        except ValueError:
            return JsonResponse({'error': 'latitude and longitude must be valid numbers'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def watersource_detail(request, pk):
    try:
        source = WaterSource.objects.get(pk=pk)
    except WaterSource.DoesNotExist:
        return JsonResponse({'error': 'WaterSource not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_watersource(source))

    elif request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if request.method == 'PUT':
            required_fields = ['source_type', 'latitude', 'longitude']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'{field} is required for PUT'}, status=400)

            try:
                source.source_type = data['source_type']
                source.description = data.get('description')
                source.latitude = float(data['latitude'])
                source.longitude = float(data['longitude'])
                source.status = data.get('status', 'Operational')
            except ValueError:
                return JsonResponse({'error': 'latitude and longitude must be valid numbers'}, status=400)
        else: # PATCH
            if 'source_type' in data:
                source.source_type = data['source_type']
            if 'description' in data:
                source.description = data['description']
            if 'latitude' in data:
                try:
                    source.latitude = float(data['latitude'])
                except ValueError:
                    return JsonResponse({'error': 'latitude must be a valid number'}, status=400)
            if 'longitude' in data:
                try:
                    source.longitude = float(data['longitude'])
                except ValueError:
                    return JsonResponse({'error': 'longitude must be a valid number'}, status=400)
            if 'status' in data:
                source.status = data['status']

        try:
            source.save()
            return JsonResponse(serialize_watersource(source))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            source.delete()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

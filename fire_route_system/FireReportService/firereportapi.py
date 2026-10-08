import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from DataAccess.models import FireReport

def serialize_firereport(report):
    return {
        'id': report.id,
        'user_id': report.user_id,
        'reporter_phone': report.reporter_phone,
        'latitude': report.latitude,
        'longitude': report.longitude,
        'fire_scale': report.fire_scale,
        'photo_url': report.photo_url,
        'status': report.status,
        'reported_at': report.reported_at.isoformat() if report.reported_at else None,
    }

@csrf_exempt
def firereport_list_create(request):
    if request.method == 'GET':
        reports = FireReport.objects.all()
        return JsonResponse([serialize_firereport(r) for r in reports], safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        required_fields = ['latitude', 'longitude', 'fire_scale']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'{field} is required'}, status=400)

        try:
            scale = int(data['fire_scale'])
            if scale not in (0, 1, 2, 3, 4, 5):
                return JsonResponse({'error': 'fire_scale must be 0, 1, 2, 3, 4, or 5'}, status=400)
            
            report = FireReport.objects.create(
                user_id=data.get('user_id'),
                reporter_phone=data.get('reporter_phone'),
                latitude=float(data['latitude']),
                longitude=float(data['longitude']),
                fire_scale=scale,
                photo_url=data.get('photo_url'),
                status=data.get('status', 'Pending')
            )
            return JsonResponse(serialize_firereport(report), status=201)
        except ValueError:
            return JsonResponse({'error': 'latitude, longitude, and fire_scale must be valid numbers'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def firereport_detail(request, pk):
    try:
        report = FireReport.objects.get(pk=pk)
    except FireReport.DoesNotExist:
        return JsonResponse({'error': 'FireReport not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_firereport(report))

    elif request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if request.method == 'PUT':
            required_fields = ['latitude', 'longitude', 'fire_scale']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'{field} is required for PUT'}, status=400)

            try:
                scale = int(data['fire_scale'])
                if scale not in (0, 1, 2, 3, 4, 5):
                    return JsonResponse({'error': 'fire_scale must be 0, 1, 2, 3, 4, or 5'}, status=400)

                report.user_id = data.get('user_id')
                report.reporter_phone = data.get('reporter_phone')
                report.latitude = float(data['latitude'])
                report.longitude = float(data['longitude'])
                report.fire_scale = scale
                report.photo_url = data.get('photo_url')
                report.status = data.get('status', 'Pending')
            except ValueError:
                return JsonResponse({'error': 'latitude, longitude, and fire_scale must be valid numbers'}, status=400)
        else: # PATCH
            if 'user_id' in data:
                report.user_id = data['user_id']
            if 'reporter_phone' in data:
                report.reporter_phone = data['reporter_phone']
            if 'latitude' in data:
                try:
                    report.latitude = float(data['latitude'])
                except ValueError:
                    return JsonResponse({'error': 'latitude must be a valid number'}, status=400)
            if 'longitude' in data:
                try:
                    report.longitude = float(data['longitude'])
                except ValueError:
                    return JsonResponse({'error': 'longitude must be a valid number'}, status=400)
            if 'fire_scale' in data:
                try:
                    scale = int(data['fire_scale'])
                    if scale not in (0, 1, 2, 3, 4, 5):
                        return JsonResponse({'error': 'fire_scale must be 0, 1, 2, 3, 4, or 5'}, status=400)
                    report.fire_scale = scale
                except ValueError:
                    return JsonResponse({'error': 'fire_scale must be a valid integer'}, status=400)
            if 'photo_url' in data:
                report.photo_url = data['photo_url']
            if 'status' in data:
                report.status = data['status']

        try:
            report.save()
            return JsonResponse(serialize_firereport(report))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        if report.status != 'Resolved':
            return JsonResponse({'error': 'Incident report cannot be deleted unless it is resolved'}, status=400)
        try:
            report.delete()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

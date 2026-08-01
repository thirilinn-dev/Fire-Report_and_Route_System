import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from DataAccess.models import Dispatch, FireReport, FireStation, User

def serialize_dispatch(dispatch):
    return {
        'id': dispatch.id,
        'report_id': dispatch.report_id,
        'station_id': dispatch.station_id,
        'operator_id': dispatch.operator_id,
        'dispatched_at': dispatch.dispatched_at.isoformat() if dispatch.dispatched_at else None,
        'resolved_at': dispatch.resolved_at.isoformat() if dispatch.resolved_at else None,
        'resources_deployed': dispatch.resources_deployed,
    }

@csrf_exempt
def dispatch_list_create(request):
    if request.method == 'GET':
        dispatches = Dispatch.objects.all()
        return JsonResponse([serialize_dispatch(d) for d in dispatches], safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        required_fields = ['report_id', 'station_id', 'operator_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'{field} is required'}, status=400)

        # Validate existence of relationships
        try:
            report = FireReport.objects.get(pk=data['report_id'])
        except FireReport.DoesNotExist:
            return JsonResponse({'error': f"FireReport with id {data['report_id']} does not exist"}, status=400)

        try:
            station = FireStation.objects.get(pk=data['station_id'])
        except FireStation.DoesNotExist:
            return JsonResponse({'error': f"FireStation with id {data['station_id']} does not exist"}, status=400)

        try:
            operator = User.objects.get(pk=data['operator_id'])
        except User.DoesNotExist:
            return JsonResponse({'error': f"User (Operator) with id {data['operator_id']} does not exist"}, status=400)

        try:
            resolved_at_val = None
            if data.get('resolved_at'):
                resolved_at_val = parse_datetime(data['resolved_at'])
                if not resolved_at_val:
                    return JsonResponse({'error': 'resolved_at must be in valid ISO 8601 format'}, status=400)

            dispatch = Dispatch.objects.create(
                report=report,
                station=station,
                operator=operator,
                resolved_at=resolved_at_val,
                resources_deployed=data.get('resources_deployed')
            )
            return JsonResponse(serialize_dispatch(dispatch), status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def dispatch_detail(request, pk):
    try:
        dispatch = Dispatch.objects.get(pk=pk)
    except Dispatch.DoesNotExist:
        return JsonResponse({'error': 'Dispatch not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_dispatch(dispatch))

    elif request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if request.method == 'PUT':
            required_fields = ['report_id', 'station_id', 'operator_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'{field} is required for PUT'}, status=400)

            try:
                report = FireReport.objects.get(pk=data['report_id'])
                station = FireStation.objects.get(pk=data['station_id'])
                operator = User.objects.get(pk=data['operator_id'])
            except (FireReport.DoesNotExist, FireStation.DoesNotExist, User.DoesNotExist) as e:
                return JsonResponse({'error': str(e)}, status=400)

            resolved_at_val = None
            if data.get('resolved_at'):
                resolved_at_val = parse_datetime(data['resolved_at'])
                if not resolved_at_val:
                    return JsonResponse({'error': 'resolved_at must be in valid ISO 8601 format'}, status=400)

            dispatch.report = report
            dispatch.station = station
            dispatch.operator = operator
            dispatch.resolved_at = resolved_at_val
            dispatch.resources_deployed = data.get('resources_deployed')
        else: # PATCH
            if 'report_id' in data:
                try:
                    dispatch.report = FireReport.objects.get(pk=data['report_id'])
                except FireReport.DoesNotExist:
                    return JsonResponse({'error': f"FireReport with id {data['report_id']} does not exist"}, status=400)
            if 'station_id' in data:
                try:
                    dispatch.station = FireStation.objects.get(pk=data['station_id'])
                except FireStation.DoesNotExist:
                    return JsonResponse({'error': f"FireStation with id {data['station_id']} does not exist"}, status=400)
            if 'operator_id' in data:
                try:
                    dispatch.operator = User.objects.get(pk=data['operator_id'])
                except User.DoesNotExist:
                    return JsonResponse({'error': f"User with id {data['operator_id']} does not exist"}, status=400)
            if 'resolved_at' in data:
                if data['resolved_at'] is None:
                    dispatch.resolved_at = None
                else:
                    resolved_at_val = parse_datetime(data['resolved_at'])
                    if not resolved_at_val:
                        return JsonResponse({'error': 'resolved_at must be in valid ISO 8601 format'}, status=400)
                    dispatch.resolved_at = resolved_at_val
            if 'resources_deployed' in data:
                dispatch.resources_deployed = data['resources_deployed']

        try:
            dispatch.save()
            return JsonResponse(serialize_dispatch(dispatch))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            dispatch.delete()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

from collections import Counter
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from DataAccess.models import User, FireReport, FireStation
from .models import *
from .permissions import managed_station_ids
from .routing import route_between, distance


def audit(actor, action, obj, **detail):
    Audit.objects.create(actor=actor, action=action, object_type=type(obj).__name__, object_id=obj.pk, detail=detail)


def preview(incident):
    plan=ResponsePlan.objects.filter(home_station=incident.home_station,level=incident.fire_scale).first()
    active=Counter(VehicleParticipation.objects.filter(deployment__incident=incident,active=True).values_list('vehicle__station_id','vehicle__kind_id'))
    rows=[]
    if plan:
        for requirement in plan.requirements.select_related('station','kind'):
            current=active[requirement.station_id,requirement.kind_id]
            available=Vehicle.objects.filter(station=requirement.station,kind=requirement.kind,status='Available',station__status='Active').count()
            rows.append({'station':requirement.station,'kind':requirement.kind,'total':requirement.quantity,'current':current,'needed':max(0,requirement.quantity-current),'available':available})
    return plan,rows


@transaction.atomic
def dispatch(actor, incident_id, vehicle_ids, reason='', manual_reason=''):
    if not actor.is_admin: raise PermissionDenied
    incident=FireReport.objects.select_for_update().get(pk=incident_id)
    if incident.closed_at or incident.status in ['Pending','False Alarm','Resolved']: raise ValidationError('စေလွှတ်ရန် ဖြစ်စဉ်ကို စိစစ်အတည်ပြုပါ။')
    if not incident.home_station_id or not incident.lead_station_id: raise ValidationError('နယ်မြေခံနှင့် ဦးဆောင်စခန်း ရွေးပါ။')
    vehicles=list(Vehicle.objects.select_for_update().filter(pk__in=vehicle_ids).order_by('pk'))
    if len(vehicles)!=len(set(vehicle_ids)) or not vehicles: raise ValidationError('ယာဉ်ရွေးပါ။')
    if any(v.status!='Available' or v.station.status!='Active' for v in vehicles): raise ValidationError('ရွေးထားသောယာဉ် အခြားဖြစ်စဉ်တွင်ပါဝင်နေသည် သို့မဟုတ် အသင့်မဖြစ်ပါ။')
    plan,rows=preview(incident)
    selected=Counter((v.station_id,v.kind_id) for v in vehicles)
    if (not plan or any(r['current']+selected[r['station'].pk,r['kind'].pk]<r['total'] for r in rows)) and not reason.strip(): raise ValidationError('အစီအစဉ်မပြည့်မီပါက အကြောင်းပြချက်ထည့်ပါ။')
    for station_id in sorted({v.station_id for v in vehicles}):
        station=FireStation.objects.get(pk=station_id)
        route=route_between(station,incident)
        if route.get('error') and not manual_reason.strip(): raise ValidationError('Route မရပါ။ Manual စေလွှတ်မှုအကြောင်းပြချက် ထည့်ပါ။')
        deployment=Deployment.objects.filter(incident=incident,station=station,state__in=['Ordered','Accepted']).first()
        if deployment is None:deployment=Deployment.objects.create(incident=incident,station=station)
        deployment.route=route
        deployment.save()
        for vehicle in [v for v in vehicles if v.station_id==station_id]:
            VehicleParticipation.objects.create(deployment=deployment,vehicle=vehicle)
            vehicle.status='Reserved'; vehicle.save(update_fields=['status'])
        for user in User.objects.filter(station=station,status='Active',role__role_name='Station Admin'):
            Notice.objects.create(recipient=user,incident=incident,message=f'ဖြစ်စဉ် {incident.pk} စေလွှတ်အမိန့်')
        for assignment in ActingAssignment.objects.filter(station=station,leave__status='Approved',starts_at__lte=timezone.now(),ends_at__gt=timezone.now()):
            Notice.objects.create(recipient=assignment.employee,incident=incident,message=f'ဖြစ်စဉ် {incident.pk} စေလွှတ်အမိန့်')
    incident.status='Dispatched';incident.save(update_fields=['status'])
    audit(actor,'dispatch',incident,vehicles=vehicle_ids,reason=reason,manual_reason=manual_reason)


def eligible_staff(deployment):
    now=timezone.now()
    on_leave=Leave.objects.filter(status='Approved',starts_at__lte=now,ends_at__gt=now).values('employee_id')
    return User.objects.filter(station=deployment.station,status='Active',role__role_name='Firefighter',duties__starts_at__lte=now,duties__ends_at__gt=now).exclude(pk__in=on_leave).exclude(pk__in=StaffParticipation.objects.filter(active=True).values('employee_id')).distinct()


@transaction.atomic
def assign_staff(actor,deployment_id,employee_ids):
    deployment=Deployment.objects.select_for_update().get(pk=deployment_id)
    if not actor.is_admin and deployment.station_id not in managed_station_ids(actor): raise PermissionDenied
    if deployment.state not in ['Accepted','Departed','Arrived']: raise ValidationError('စေလွှတ်အမိန့်ကို အရင်လက်ခံပါ။')
    employees=list(User.objects.select_for_update().filter(pk__in=employee_ids).order_by('pk'))
    eligible=set(eligible_staff(deployment).values_list('pk',flat=True))
    if len(employees)!=len(set(employee_ids)) or not set(employee_ids)<=eligible: raise ValidationError('ဝန်ထမ်းသည် တာဝန်ကျ/ခွင့်/ဖြစ်စဉ်အခြေအနေ မကိုက်ညီပါ။')
    for employee in employees: StaffParticipation.objects.create(deployment=deployment,employee=employee,actual=deployment.state in ['Departed','Arrived'])
    audit(actor,'assign_staff',deployment,employees=employee_ids)


@transaction.atomic
def deployment_state(actor,deployment_id,state):
    deployment=Deployment.objects.select_for_update().get(pk=deployment_id)
    if not actor.is_admin and deployment.station_id not in managed_station_ids(actor): raise PermissionDenied
    transitions={'Ordered':'Accepted','Accepted':'Departed','Departed':'Arrived','Arrived':'Returned'}
    if transitions.get(deployment.state)!=state: raise ValidationError('အခြေအနေပြောင်းလဲမှု အစီအစဉ်မမှန်ပါ။')
    if state=='Departed':
        if not deployment.vehicles.filter(active=True).exists():raise ValidationError('ထွက်ခွာရန် ယာဉ်မရှိပါ။')
        if not deployment.personnel.filter(active=True).exists(): raise ValidationError('လိုက်ပါမည့်ဝန်ထမ်း ရွေးပါ။')
        now=timezone.now()
        people=list(User.objects.select_for_update().filter(pk__in=deployment.personnel.filter(active=True).values('employee_id')).order_by('pk'))
        for person in people:
            if not person.is_active or not person.duties.filter(starts_at__lte=now,ends_at__gt=now).exists() or person.leaves.filter(status='Approved',starts_at__lte=now,ends_at__gt=now).exists():raise ValidationError('ဝန်ထမ်းတာဝန်/ခွင့် ပြောင်းလဲထားသည်။ ထွက်ခွာမီ ပြန်ရွေးပါ။')
        deployment.personnel.filter(active=True).update(actual=True)
        deployment.vehicles.filter(active=True).update(actual=True)
        Vehicle.objects.filter(pk__in=deployment.vehicles.filter(active=True).values('vehicle_id')).update(status='Deployed')
    if state=='Returned':
        vehicles=list(Vehicle.objects.select_for_update().filter(pk__in=deployment.vehicles.filter(active=True).values('vehicle_id')).order_by('pk'))
        for vehicle in vehicles: vehicle.status='Available';vehicle.save(update_fields=['status'])
        deployment.vehicles.filter(active=True).update(active=False,returned_at=timezone.now())
        deployment.personnel.filter(active=True).update(active=False,released_at=timezone.now())
    deployment.state=state;deployment.save(update_fields=['state'])
    IncidentUpdate.objects.create(incident=deployment.incident,author=actor,station=deployment.station,message=state)
    for admin in User.objects.filter(role__role_name__in=['Administrator','Admin'],status='Active'):
        Notice.objects.create(recipient=admin,incident=deployment.incident,message=f'{deployment.station.name[:100]}: {state}')
    audit(actor,'deployment_state',deployment,state=state)


@transaction.atomic
def review_leave(actor,leave_id,approved,replacement=None,note=''):
    leave=Leave.objects.select_for_update().select_related('employee').get(pk=leave_id)
    employee=User.objects.select_for_update().get(pk=leave.employee_id)
    if employee.has_role('Station Admin'):
        if not actor.is_admin: raise PermissionDenied
    elif not actor.is_admin and (employee.station_id not in managed_station_ids(actor) or actor.pk==employee.pk): raise PermissionDenied
    if leave.status!='Pending': raise ValidationError('စိစစ်ပြီးသော ခွင့်စာဖြစ်သည်။')
    if approved:
        if ActingAssignment.objects.filter(employee=employee,starts_at__lt=leave.ends_at,ends_at__gt=leave.starts_at).exists():raise ValidationError('ယာယီတာဝန်ခံကာလနှင့် ခွင့်ရက် တိုက်နေသည်။')
        if Leave.objects.filter(employee=employee,status='Approved',starts_at__lt=leave.ends_at,ends_at__gt=leave.starts_at).exists(): raise ValidationError('ခွင့်ချိန်ထပ်နေသည်။')
        if StaffParticipation.objects.filter(employee=employee,active=True).exists(): raise ValidationError('ဝန်ထမ်းသည် ဖြစ်စဉ်တွင် ပါဝင်နေသည်။')
        if employee.has_role('Station Admin'):
            if not replacement: raise ValidationError('ယာယီတာဝန်ခံ ရွေးပါ။')
            replacement=User.objects.select_for_update().get(pk=replacement)
            if replacement.station_id!=employee.station_id or not replacement.is_firefighter or not replacement.is_active: raise ValidationError('မိမိစခန်းရှိ အသုံးပြုဆဲဝန်ထမ်း ရွေးပါ။')
            if replacement.leaves.filter(status='Approved',starts_at__lt=leave.ends_at,ends_at__gt=leave.starts_at).exists(): raise ValidationError('ယာယီတာဝန်ခံ ခွင့်ယူထားသည်။')
            if ActingAssignment.objects.filter(employee=replacement,starts_at__lt=leave.ends_at,ends_at__gt=leave.starts_at).exists(): raise ValidationError('ယာယီတာဝန် ထပ်နေသည်။')
            ActingAssignment.objects.create(leave=leave,employee=replacement,station=employee.station,starts_at=leave.starts_at,ends_at=leave.ends_at)
    leave.status='Approved' if approved else 'Rejected';leave.reviewed_by=actor;leave.review_note=note;leave.save()
    audit(actor,'review_leave',leave,status=leave.status)


def aggregate(incident):
    rows=[]
    for deployment in incident.deployments.exclude(state='Cancelled').select_related('station'):
        try: report=deployment.station_report
        except StationReport.DoesNotExist: raise ValidationError('ပါဝင်စခန်းအားလုံး၏ အစီရင်ခံစာ လိုအပ်သည်။')
        rows.append({'station':deployment.station.name,'water_gallons':str(report.water_gallons),'narrative':report.narrative,'staff':list(deployment.personnel.filter(actual=True).values('employee_id','employee__full_name','employee__username')),'vehicles':list(deployment.vehicles.filter(actual=True).values('vehicle_id','vehicle__registration','vehicle__kind__name'))})
    if not rows: raise ValidationError('စခန်းစေလွှတ်မှု မရှိပါ။')
    return {'stations':rows,'water_gallons':str(sum(StationReport.objects.filter(deployment__incident=incident).exclude(deployment__state='Cancelled').values_list('water_gallons',flat=True)))}


@transaction.atomic
def calculate_all_routes_and_dispatch(incident, actor=None, fire_scale=None):
    """
    Automatic Dijkstra Route Calculation and Responding Station Selection:
    1. Incident Location (verifies coordinates)
    2. Eligible/Active Fire Stations
    3. Dijkstra Road calculation for ALL active stations
    4. Vehicle/Engine availability check for each station
    5. Compare valid routes and select shortest with available engine
    6. Deterministic tie-breaking
    7. Assign responding station and engine
    8. Idempotently create/update Deployment and Dispatch
    """
    import math
    from DataAccess.models import Dispatch

    if fire_scale is not None:
        incident.fire_scale = int(fire_scale)
        incident.save(update_fields=['fire_scale'])

    # Ensure coordinates exist
    if incident.latitude is None or incident.longitude is None:
        return {
            'success': False,
            'error': 'မီးလောင်ရာ တည်နေရာ Coordinates မရှိပါ။',
            'routes': [],
            'selected_station': None,
            'selected_route': None,
            'selected_engine': None,
        }

    # Ensure coordinates_confirmed is set
    if not incident.coordinates_confirmed:
        incident.coordinates_confirmed = True
        incident.save(update_fields=['coordinates_confirmed'])

    # Find all eligible / active Fire Stations
    active_stations = list(FireStation.objects.filter(status='Active').order_by('pk'))
    if not active_stations:
        return {
            'success': False,
            'error': 'No active fire station is currently available. (အသင့်ရှိသော မီးသတ်စခန်း မရှိပါ)',
            'routes': [],
            'selected_station': None,
            'selected_route': None,
            'selected_engine': None,
        }

    # Calculate routes from ALL active stations to Incident
    calculated_routes = []
    for station in active_stations:
        # Check engine availability (Available or already assigned to this incident's deployment)
        already_participating_ids = VehicleParticipation.objects.filter(
            deployment__incident=incident,
            deployment__station=station,
            active=True
        ).values_list('vehicle_id', flat=True)
        available_engine = Vehicle.objects.filter(
            Q(station=station, status='Available') | Q(pk__in=already_participating_ids)
        ).select_related('kind').first()
        available_engines_count = Vehicle.objects.filter(
            Q(station=station, status='Available') | Q(pk__in=already_participating_ids)
        ).count()

        # Calculate road Dijkstra route
        route_res = route_between(station, incident)
        is_valid_route = not route_res.get('error') and bool(route_res.get('coordinates'))
        total_metres = route_res.get('total_metres') or route_res.get('metres') if is_valid_route else math.inf

        route_item = {
            'station_id': station.pk,
            'station_name': station.name,
            'station_address': station.address,
            'station_lat': station.latitude,
            'station_lng': station.longitude,
            'metres': route_res.get('metres', 0) if is_valid_route else 0,
            'total_metres': total_metres,
            'distance_km': round(total_metres / 1000.0, 2) if is_valid_route and total_metres != math.inf else None,
            'coordinates': route_res.get('coordinates', []),
            'instructions': route_res.get('instructions', []),
            'start_connector_metres': route_res.get('start_connector_metres', 0),
            'end_connector_metres': route_res.get('end_connector_metres', 0),
            'has_engine': available_engines_count > 0,
            'engine_id': available_engine.pk if available_engine else None,
            'engine_name': f"{available_engine.registration} ({available_engine.kind.name})" if available_engine else None,
            'engine_available_count': available_engines_count,
            'error': route_res.get('error', '') if not is_valid_route else '',
            'is_valid': is_valid_route,
            'is_selected': False,
        }
        calculated_routes.append(route_item)

    # Filter eligible stations with valid route and available engine
    valid_candidates = [
        r for r in calculated_routes if r['is_valid'] and r['has_engine']
    ]

    # Error handling per specification
    if not any(r['is_valid'] for r in calculated_routes):
        return {
            'success': False,
            'error': 'No valid road route could be calculated. (သွားနိုင်သော လမ်းကြောင်း မရှိပါ)',
            'routes': calculated_routes,
            'selected_station': None,
            'selected_route': None,
            'selected_engine': None,
        }

    if not valid_candidates:
        return {
            'success': False,
            'error': 'No available fire engine is currently available for dispatch. (စေလွှတ်ရန် အသင့်ရှိသော မီးသတ်ယာဉ် မရှိပါ)',
            'routes': calculated_routes,
            'selected_station': None,
            'selected_route': None,
            'selected_engine': None,
        }

    # Deterministic tie-breaking:
    # Sort by: (total_metres, station_id)
    valid_candidates.sort(key=lambda r: (r['total_metres'], r['station_id']))
    selected_item = valid_candidates[0]
    selected_item['is_selected'] = True

    # Mark the selected route in calculated_routes
    for r in calculated_routes:
        if r['station_id'] == selected_item['station_id']:
            r['is_selected'] = True

    selected_station = FireStation.objects.get(pk=selected_item['station_id'])
    selected_engine = Vehicle.objects.get(pk=selected_item['engine_id'])

    # Update Incident
    incident.home_station = selected_station
    incident.lead_station = selected_station
    if incident.status in ['Pending', 'Confirmed']:
        incident.status = 'Dispatched'
    incident.save(update_fields=['home_station', 'lead_station', 'status'])

    # Response Route Data Dictionary
    selected_route_dict = {
        'station_id': selected_station.pk,
        'station_name': selected_station.name,
        'coordinates': selected_item['coordinates'],
        'metres': selected_item['metres'],
        'total_metres': selected_item['total_metres'],
        'start_connector_metres': selected_item['start_connector_metres'],
        'end_connector_metres': selected_item['end_connector_metres'],
        'instructions': selected_item['instructions'],
        'all_routes': calculated_routes,
    }

    # Idempotent Deployment creation / update
    deployment = Deployment.objects.filter(
        incident=incident,
        station=selected_station
    ).exclude(state__in=['Returned', 'Cancelled']).first()

    if deployment is None:
        deployment = Deployment.objects.create(
            incident=incident,
            station=selected_station,
            state='Ordered',
            route=selected_route_dict
        )
    else:
        deployment.route = selected_route_dict
        deployment.save(update_fields=['route'])

    # Vehicle assignment (idempotent)
    participation = VehicleParticipation.objects.filter(
        deployment=deployment,
        active=True
    ).first()
    if not participation:
        VehicleParticipation.objects.create(
            deployment=deployment,
            vehicle=selected_engine
        )
        selected_engine.status = 'Reserved'
        selected_engine.save(update_fields=['status'])
    else:
        selected_engine = participation.vehicle

    # Idempotent Dispatch record
    operator_user = actor if (actor and actor.is_authenticated) else User.objects.filter(role__role_name__in=['Administrator', 'Admin']).first()
    if operator_user:
        Dispatch.objects.update_or_create(
            report=incident,
            defaults={
                'station': selected_station,
                'operator': operator_user,
                'resources_deployed': f"{selected_engine.registration} ({selected_engine.kind.name})"
            }
        )

    # Notice notifications
    for st_admin in User.objects.filter(station=selected_station, status='Active', role__role_name='Station Admin'):
        Notice.objects.get_or_create(
            recipient=st_admin,
            incident=incident,
            defaults={'message': f'ဖြစ်စဉ် {incident.pk} အလိုအလျောက် စေလွှတ်အမိန့် ({selected_item["distance_km"]} km)'}
        )
    for ff in User.objects.filter(station=selected_station, status='Active', role__role_name='Firefighter'):
        Notice.objects.get_or_create(
            recipient=ff,
            incident=incident,
            defaults={'message': f'ဖြစ်စဉ် {incident.pk} အလိုအလျောက် စေလွှတ်အမိန့် ({selected_item["distance_km"]} km)'}
        )

    if actor and actor.is_authenticated:
        audit(actor, 'auto_dispatch', incident,
              station=selected_station.pk,
              vehicle=selected_engine.pk,
              distance_km=selected_item['distance_km'])

    return {
        'success': True,
        'error': '',
        'selected_station': selected_station,
        'selected_engine': selected_engine,
        'selected_route': selected_item,
        'routes': calculated_routes,
    }

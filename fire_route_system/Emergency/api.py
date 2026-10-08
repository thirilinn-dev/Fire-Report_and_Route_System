import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from DataAccess.models import FireReport,FireStation
from .forms import IncidentForm
from .permissions import incidents_for
from .models import Notice,ResponsePlan


def serialize(incident,private=False):
    data={k:getattr(incident,k) for k in ['id','latitude','longitude','address','fire_scale','status']}
    data['closed']=bool(incident.closed_at)
    data['status_display']=incident.status_display
    data['scale_display']=incident.scale_display
    if incident.source_key and incident.source_key.startswith('history:'):
        data['historical']=True
        data['source_url']=incident.source_data.get('url')
    if private:data.update(reporter_phone=incident.reporter_phone,user_id=incident.user_id)
    return data


@csrf_protect
def incidents(request):
    if not request.user.is_authenticated:return JsonResponse({'error':'Login required'},status=401)
    if request.method=='GET':
        page=Paginator(incidents_for(request.user).order_by('-reported_at'),20).get_page(request.GET.get('page'))
        return JsonResponse({'results':[serialize(i,request.user.is_admin) for i in page],'count':page.paginator.count})
    if request.method=='POST':
        try:data=json.loads(request.body)
        except (ValueError,TypeError):return JsonResponse({'error':'Invalid JSON'},status=400)
        if not isinstance(data,dict):return JsonResponse({'error':'Expected a JSON object'},status=400)
        form=IncidentForm(data)
        if not form.is_valid():return JsonResponse({'errors':form.errors},status=400)
        incident=form.save(commit=False);incident.user_id=request.user.pk;incident.reporter_phone=request.user.phone_number;incident.fire_scale=0;incident.status='Pending';incident.save()
        from DataAccess.models import User
        for admin in User.objects.filter(role__role_name__in=['Administrator','Admin'],status='Active'):
            Notice.objects.create(recipient=admin,incident=incident,message=f'မီးသတင်းအသစ် {incident.pk}')
        from .services import audit
        audit(request.user,'report_fire',incident)
        return JsonResponse(serialize(incident),status=201)
    return JsonResponse({'error':'Method not allowed'},status=405)


@csrf_protect
def incident_detail(request,pk):
    if not request.user.is_authenticated:return JsonResponse({'error':'Login required'},status=401)
    incident=incidents_for(request.user).filter(pk=pk).first()
    if not incident:return JsonResponse({'error':'Not found'},status=404)
    if request.method!='GET':return JsonResponse({'error':'Use the audited incident workflow'},status=405)
    return JsonResponse(serialize(incident,request.user.is_admin))


def map_payload():
    incidents=FireReport.objects.exclude(status__in=['Pending','False Alarm','Resolved']).filter(latitude__isnull=False,longitude__isnull=False,coordinates_confirmed=True,closed_at__isnull=True)
    return {'incidents':[serialize(i) for i in incidents],'stations':list(FireStation.objects.filter(status='Active').values('station_id','name','latitude','longitude','address','contact_number','status'))}


def map_data(request):
    if not request.user.is_authenticated:return JsonResponse({'error':'Login required'},status=401)
    return JsonResponse(map_payload())


@csrf_protect
def poll(request):
    if not request.user.is_authenticated:return JsonResponse({'error':'Login required'},status=401)
    scope=request.GET.get('scope','dashboard')
    if scope not in ['notifications','dashboard','incident','queue']:
        return JsonResponse({'error':'Invalid poll scope'},status=400)
    if scope=='queue' and not request.user.is_admin:
        return JsonResponse({'error':'Forbidden'},status=403)
    notices=Notice.objects.filter(recipient=request.user)
    if request.method=='POST':
        from django.utils import timezone
        notices.filter(pk=request.POST.get('notice')).update(read_at=timezone.now())
    result={'unread':notices.filter(read_at=None).count()}
    if scope=='dashboard':
        result.update(notices=list(notices.order_by('-pk').values('id','incident_id','message','read_at')[:20]),incidents=[serialize(i) for i in incidents_for(request.user).order_by('-reported_at')[:20]])
    if scope=='queue':
        from copy import copy
        from django.template.loader import render_to_string
        from .views import queue_context
        queue_request=copy(request)
        queue_request.GET=request.GET.copy()
        for key in ['scope','map','incident']:queue_request.GET.pop(key,None)
        result['queue_html']=render_to_string('emergency/queue_results.html',queue_context(queue_request),request=queue_request)
    obj=incidents_for(request.user).filter(pk=request.GET.get('incident')).first() if request.GET.get('incident','').isdigit() else None
    if obj:
        result['incident']=serialize(obj)
        if request.user.is_admin or request.user.is_station_admin or request.user.is_firefighter:
            from .permissions import managed_station_ids
            deployments=obj.deployments.all()
            updates=obj.updates.all()
            if not request.user.is_admin:
                ids=managed_station_ids(request.user)+[request.user.station_id]
                deployments=deployments.filter(station_id__in=ids)
                updates=updates.filter(station_id__in=ids)
            result['deployments']=list(deployments.values('id','state','station__name'))
            result['updates']=list(updates.order_by('-pk').values('id','created_at','message','station__name')[:50])
    if request.GET.get('map') == '1':
        result['map'] = map_payload()
    return JsonResponse(result)


def plan_preview(request):
    if not request.user.is_authenticated or not request.user.is_admin:return JsonResponse({'error':'Forbidden'},status=403)
    home=request.GET.get('station','');level=request.GET.get('level','')
    if not home.isdigit() or level not in ['0','1','2','3','4','5']:return JsonResponse({'error':'Invalid selection'},status=400)
    plan=ResponsePlan.objects.filter(home_station_id=home,level=int(level)).first()
    return JsonResponse({'lead_station':plan.lead_station_id if plan else None})

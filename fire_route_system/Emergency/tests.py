import json
from datetime import timedelta
from unittest.mock import patch
from io import BytesIO
from django.test import TestCase,TransactionTestCase,Client
from django.core.exceptions import ValidationError,PermissionDenied
from django.utils import timezone
from django.core.management import call_command
from django.urls import reverse
from DataAccess.models import User,Role,FireStation,FireReport
from .models import *
from .forms import RegisterForm,IncidentForm
from .permissions import managed_station_ids
from .services import dispatch,preview,assign_staff,deployment_state,review_leave
from .routing import dijkstra


class EmergencyTests(TestCase):
    def setUp(self):
        self.roles={n:Role.objects.get_or_create(role_name=n)[0] for n in ['Administrator','Station Admin','Firefighter','Citizen']}
        self.station=FireStation.objects.create(name='A',address='Mandalay',contact_number='1',latitude=21.97,longitude=96.08)
        self.other=FireStation.objects.create(name='B',address='Mandalay',contact_number='2',latitude=21.98,longitude=96.09)
        self.admin=self.user('admin','Administrator')
        self.station_admin=self.user('station','Station Admin',self.station)
        self.firefighter=self.user('ff','Firefighter',self.station)
        self.citizen=self.user('citizen','Citizen')
        self.outsider=self.user('other','Station Admin',self.other)
        self.kind=VehicleType.objects.create(name='Engine')
        self.vehicles=[Vehicle.objects.create(registration=f'V{i}',station=self.station,kind=self.kind) for i in range(3)]
        self.plan=ResponsePlan.objects.create(home_station=self.station,lead_station=self.station,level=1)
        PlanRequirement.objects.create(plan=self.plan,station=self.station,kind=self.kind,quantity=2)
        self.incident=FireReport.objects.create(user_id=self.citizen.pk,fire_scale=1,address='မီးလောင်ရာ',latitude=21.975,longitude=96.083,status='Confirmed',home_station=self.station,lead_station=self.station,coordinates_confirmed=True)
        self.now=timezone.now()
        Duty.objects.create(employee=self.firefighter,starts_at=self.now-timedelta(hours=1),ends_at=self.now+timedelta(hours=2),task='Respond')
    def user(self,name,role,station=None):
        user=User.objects.create(username=name,role=self.roles[role],station=station,email=None,phone_number=None)
        user.set_password('StrongDemo2026!');user.save();return user
    def auth(self,user):self.client.force_login(user,backend='DataAccess.backends.RoleAuthBackend')
    def send(self,vehicles=None,reason=''):
        with patch('Emergency.services.route_between',return_value={'coordinates':[[21.97,96.08],[21.975,96.083]],'metres':700,'instructions':[]}):
            dispatch(self.admin,self.incident.pk,[v.pk for v in vehicles or self.vehicles[:2]],reason)
        return Deployment.objects.get(incident=self.incident)
    def test_phone_login_and_optional_email_registration(self):
        form=RegisterForm({'full_name':'ကိုကို','phone_number':'09912345678','nrc':'Demo','password':'StrongDemo2026!','confirmation':'StrongDemo2026!'})
        self.assertTrue(form.is_valid(),form.errors);user=form.save();self.assertIsNone(user.email)
        from django.contrib.auth import authenticate
        self.assertEqual(authenticate(username='09912345678',password='StrongDemo2026!'),user)
        duplicate=RegisterForm({'full_name':'ထပ်','phone_number':'09912345678','nrc':'Demo','password':'StrongDemo2026!','confirmation':'StrongDemo2026!'})
        self.assertFalse(duplicate.is_valid())
    def test_anonymous_reporting_and_api_blocked(self):
        self.assertEqual(self.client.get('/emergency/report/').status_code,302)
        self.assertEqual(self.client.post('/report/api/fire-reports/',data='{}',content_type='application/json').status_code,401)
        self.assertEqual(self.client.get('/api/users/').status_code,302)
    def test_report_identity_cannot_be_spoofed(self):
        self.auth(self.citizen)
        response=self.client.post('/emergency/api/incidents/',data=json.dumps({'address':'မီးသတင်း','user_id':self.admin.pk,'status':'Resolved','fire_scale':5}),content_type='application/json')
        self.assertEqual(response.status_code,201)
        report=FireReport.objects.get(pk=response.json()['id']);self.assertEqual(report.user_id,self.citizen.pk);self.assertEqual(report.fire_scale,0);self.assertEqual(report.status,'Pending')
    def test_coordinates_validation(self):
        self.assertFalse(IncidentForm({'latitude':'nan','longitude':'96','address':'x'}).is_valid())
        self.assertFalse(IncidentForm({'latitude':100,'longitude':96}).is_valid())
        self.assertFalse(IncidentForm({'latitude':21}).is_valid())
        self.assertTrue(IncidentForm({'address':'manual address'}).is_valid())
    def test_csrf_protected_legacy_intake(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.citizen,backend='DataAccess.backends.RoleAuthBackend')
        self.assertEqual(client.post('/report/api/fire-reports/',data='{}',content_type='application/json').status_code,403)
    def test_station_scope_and_legacy_permissions(self):
        self.auth(self.station_admin)
        self.assertEqual(self.client.get(f'/emergency/manage/staff/{self.outsider.pk}/').status_code,404)
        self.assertEqual(self.client.get('/api/users/').status_code,403)
        self.assertEqual(self.client.post('/emergency/manage/staff/new/',{'username':'hack','full_name':'hack','role':self.roles['Administrator'].pk,'station':self.station.pk,'status':'Active','password':'StrongDemo2026!'}).status_code,200)
        self.assertFalse(User.objects.filter(username='hack').exists())
    def test_overnight_duty_and_overlap(self):
        duty=Duty(employee=self.firefighter,starts_at=self.now+timedelta(hours=3),ends_at=self.now+timedelta(hours=15),task='Night');duty.full_clean();duty.save()
        conflict=Duty(employee=self.firefighter,starts_at=self.now+timedelta(hours=14),ends_at=self.now+timedelta(hours=16),task='Overlap')
        with self.assertRaises(ValidationError):conflict.full_clean()
    def test_leave_requires_admin_for_station_manager(self):
        leave=Leave.objects.create(employee=self.station_admin,starts_at=self.now-timedelta(minutes=1),ends_at=self.now+timedelta(hours=2),reason='Leave')
        with self.assertRaises(PermissionDenied):review_leave(self.outsider,leave.pk,True,self.firefighter.pk)
        with self.assertRaises(ValidationError):review_leave(self.admin,leave.pk,True)
        review_leave(self.admin,leave.pk,True,self.firefighter.pk)
        self.assertIn(self.station.pk,managed_station_ids(self.firefighter))
        ActingAssignment.objects.filter(employee=self.firefighter).update(ends_at=self.now-timedelta(seconds=1))
        self.assertNotIn(self.station.pk,managed_station_ids(self.firefighter))
    def test_approved_leave_excludes_staff(self):
        leave=Leave.objects.create(employee=self.firefighter,starts_at=self.now-timedelta(minutes=1),ends_at=self.now+timedelta(hours=1),reason='Leave')
        review_leave(self.station_admin,leave.pk,True)
        deployment=self.send();deployment_state(self.station_admin,deployment.pk,'Accepted')
        with self.assertRaises(ValidationError):assign_staff(self.station_admin,deployment.pk,[self.firefighter.pk])
        duty=Duty(employee=self.firefighter,starts_at=self.now,ends_at=self.now+timedelta(minutes=30),task='Conflict')
        with self.assertRaises(ValidationError):duty.full_clean()
    def test_preview_and_level_total(self):
        deployment=self.send()
        rows=preview(self.incident)[1];self.assertEqual(rows[0]['current'],2);self.assertEqual(rows[0]['needed'],0)
        plan=ResponsePlan.objects.create(home_station=self.station,lead_station=self.station,level=2)
        PlanRequirement.objects.create(plan=plan,station=self.station,kind=self.kind,quantity=3)
        self.incident.fire_scale=2;self.incident.save()
        self.assertEqual(preview(self.incident)[1][0]['needed'],1)
        with patch('Emergency.services.route_between',return_value={'error':'No route'}):
            with self.assertRaises(ValidationError):dispatch(self.admin,self.incident.pk,[self.vehicles[2].pk])
            dispatch(self.admin,self.incident.pk,[self.vehicles[2].pk],manual_reason='Manual navigation')
        self.assertEqual(deployment.vehicles.filter(active=True).count(),3)
    def test_shortage_requires_reason_and_atomic_rollback(self):
        with self.assertRaises(ValidationError):self.send([self.vehicles[0]])
        self.vehicles[0].refresh_from_db();self.assertEqual(self.vehicles[0].status,'Available');self.assertEqual(Deployment.objects.count(),0)
        self.send([self.vehicles[0]],reason='Only one ready')
    def test_vehicle_cannot_be_reserved_twice(self):
        self.send()
        with self.assertRaises(ValidationError):self.send()
    def test_staff_scope_and_reservation(self):
        deployment=self.send();deployment_state(self.station_admin,deployment.pk,'Accepted')
        with self.assertRaises(PermissionDenied):assign_staff(self.outsider,deployment.pk,[self.firefighter.pk])
        assign_staff(self.station_admin,deployment.pk,[self.firefighter.pk])
        with self.assertRaises(ValidationError):assign_staff(self.station_admin,deployment.pk,[self.firefighter.pk])
    def test_end_to_end_with_actual_staff_and_closure(self):
        deployment=self.send();deployment_state(self.station_admin,deployment.pk,'Accepted')
        assign_staff(self.station_admin,deployment.pk,[self.firefighter.pk])
        deployment_state(self.station_admin,deployment.pk,'Departed');deployment_state(self.station_admin,deployment.pk,'Arrived')
        self.assertTrue(deployment.personnel.get().actual)
        deployment_state(self.station_admin,deployment.pk,'Returned')
        self.vehicles[0].refresh_from_db();self.assertEqual(self.vehicles[0].status,'Available')
        self.assertFalse(deployment.personnel.filter(active=True).exists())
        self.auth(self.station_admin)
        response=self.client.post(f'/emergency/deployments/{deployment.pk}/report/',{'narrative':'ဆောင်ရွက်ပြီး','water_gallons':'250'})
        self.assertEqual(response.status_code,302)
        self.auth(self.admin);self.client.post(f'/emergency/incidents/{self.incident.pk}/state/',{'status':'Resolved'})
        self.auth(self.station_admin);self.client.post(f'/emergency/incidents/{self.incident.pk}/final/',{'narrative':'နောက်ဆုံးအစီရင်ခံစာ'})
        final=FinalReport.objects.get(incident=self.incident);self.assertEqual(final.snapshot['water_gallons'],'250.00')
        self.assertEqual(len(final.snapshot['stations'][0]['staff']),1)
        self.auth(self.admin);self.client.post(f'/emergency/incidents/{self.incident.pk}/review-final/',{'decision':'Revision','note':'ပြန်စစ်'})
        final.refresh_from_db();self.assertEqual(final.state,'Revision')
        self.auth(self.station_admin);self.client.post(f'/emergency/incidents/{self.incident.pk}/final/',{'narrative':'ပြန်ပြင်ပြီး'})
        self.auth(self.admin);self.client.post(f'/emergency/incidents/{self.incident.pk}/review-final/',{'decision':'Approved'})
        self.incident.refresh_from_db();self.assertIsNotNone(self.incident.closed_at)
    def test_final_review_without_submission_redirects_and_hides_controls(self):
        self.auth(self.admin)
        url=f'/emergency/incidents/{self.incident.pk}/'
        response=self.client.get(url)
        self.assertNotContains(response,'name="decision"')
        response=self.client.post(url+'review-final/',{'decision':'Approved'},follow=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'နောက်ဆုံးအစီရင်ခံစာ တင်သွင်းပြီးမှ')
        self.incident.refresh_from_db()
        self.assertIsNone(self.incident.closed_at)
        self.assertFalse(FinalReport.objects.filter(incident=self.incident).exists())

    def test_final_review_requires_resubmission_after_revision(self):
        self.auth(self.admin)
        final=FinalReport.objects.create(incident=self.incident,narrative='Report',snapshot={},submitted_by=self.station_admin,state='Revision')
        url=f'/emergency/incidents/{self.incident.pk}/'
        self.assertNotContains(self.client.get(url),'name="decision"')
        response=self.client.post(url+'review-final/',{'decision':'Approved'},follow=True)
        self.assertEqual(response.status_code,200)
        final.refresh_from_db()
        self.assertEqual(final.state,'Revision')
        self.incident.refresh_from_db()
        self.assertIsNone(self.incident.closed_at)

    def test_plans_filter_by_township_and_level(self):
        self.station.township='ချမ်းမြသာစည်မြို့နယ်';self.station.save()
        self.other.township='အမရပူရမြို့နယ်';self.other.save()
        ResponsePlan.objects.create(home_station=self.other,lead_station=self.other,level=1)
        ResponsePlan.objects.create(home_station=self.station,lead_station=self.station,level=2)
        self.auth(self.admin)
        response=self.client.get('/emergency/manage/plans/',{'township':self.station.township,'level':'1'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(list(response.context['page_obj']),[self.plan])
        self.assertContains(response,'မြို့နယ်')
        self.assertNotContains(response,'တိုင်းဒေသကြီး / ပြည်နယ်')

    def test_incident_list_actions_and_day_first_date(self):
        self.auth(self.admin)
        response=self.client.get('/emergency/incidents/')
        self.assertContains(response,'စီမံရန်')
        self.assertContains(response,timezone.localtime(self.incident.reported_at).strftime('%d-%m-%Y %I:%M %p'))
        self.auth(self.citizen)
        response=self.client.get('/emergency/incidents/')
        self.assertContains(response,'အသေးစိတ်ကြည့်ရန်')
        self.assertNotContains(response,'စီမံရန်</a>')

    def test_pending_queue_fifo_and_admin_permission(self):
        self.incident.status='Pending';self.incident.save()
        newer=FireReport.objects.create(user_id=self.citizen.pk,address='New pending',status='Pending',fire_scale=0)
        FireReport.objects.create(user_id=self.citizen.pk,address='Already confirmed',status='Confirmed',fire_scale=0)
        self.auth(self.admin)
        response=self.client.get('/emergency/queue/')
        self.assertEqual(response.status_code,200)
        self.assertEqual([i.pk for i in response.context['page_obj']],[self.incident.pk,newer.pk])
        self.assertContains(response,'စိစစ် / အတည်ပြုရန်')
        self.incident.status='Confirmed';self.incident.save()
        response=self.client.get('/emergency/queue/')
        self.assertEqual([i.pk for i in response.context['page_obj']],[newer.pk])
        for user in [self.citizen,self.firefighter,self.station_admin]:
            self.auth(user)
            self.assertEqual(self.client.get('/emergency/queue/').status_code,403)

    def test_duty_form_accepts_am_pm(self):
        from .forms import FORM_TYPES
        form=FORM_TYPES['duties'][1]({'employee':self.firefighter.pk,'starts_at':'20/10/2026 09:00 PM','ends_at':'21/10/2026 06:00 AM','task':'Night duty'})
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.cleaned_data['starts_at'].hour,21)
        self.assertEqual(form.cleaned_data['ends_at'].hour,6)

    def test_route_preview_without_dispatch_and_missing_coordinates(self):
        self.auth(self.admin)
        with patch('Emergency.services.route_between',return_value={'coordinates':[[21.97,96.08],[21.98,96.09]],'metres':1000}):
            response=self.client.get(f'/emergency/incidents/{self.incident.pk}/')
        self.assertContains(response,'route-data')
        self.assertFalse(Deployment.objects.exists())
        self.incident.coordinates_confirmed=False;self.incident.save()
        response=self.client.get(f'/emergency/incidents/{self.incident.pk}/')
        self.assertContains(response,'Admin အတည်ပြုရန်လိုသည်')

    def test_map_privacy_and_pending_excluded(self):
        self.auth(self.citizen);data=self.client.get('/emergency/api/map/').json()
        self.assertEqual(len(data['incidents']),1);self.assertNotIn('reporter_phone',data['incidents'][0]);self.assertNotIn('user_id',data['incidents'][0])
        self.incident.status='Pending';self.incident.save();self.assertEqual(self.client.get('/emergency/api/map/').json()['incidents'],[])
    def test_citizen_detail_has_no_staff(self):
        self.send();self.auth(self.citizen);response=self.client.get(f'/emergency/incidents/{self.incident.pk}/')
        self.assertEqual(response.status_code,200);self.assertNotContains(response,'V0');self.assertNotContains(response,'တာဝန်ကျဝန်ထမ်းရွေးရန်')
    def test_posts_audience_and_public_access(self):
        for audience,title in [('Public','PUBLIC'),('Staff','STAFF'),('Station','PRIVATE')]:Post.objects.create(author=self.station_admin,station=self.station,title=title,body='Demo',audience=audience)
        self.assertContains(self.client.get('/emergency/posts/'),'PUBLIC');self.assertNotContains(self.client.get('/emergency/posts/'),'STAFF')
        self.auth(self.outsider);response=self.client.get('/emergency/posts/');self.assertContains(response,'STAFF');self.assertNotContains(response,'PRIVATE')
    def test_station_post_cannot_target_another_station(self):
        self.auth(self.station_admin)
        response=self.client.post('/emergency/manage/posts/new/',{'title':'Outside','body':'Demo','audience':'Station','station':self.other.pk,'published':'on'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(Post.objects.filter(title='Outside').exists())
    def test_station_manager_can_edit_own_unpublished_post(self):
        post=Post.objects.create(author=self.station_admin,station=self.station,title='Draft',body='Demo',audience='Station',published=False)
        self.auth(self.station_admin)
        self.assertContains(self.client.get('/emergency/manage/posts/'),'Draft')
        self.assertEqual(self.client.get(f'/emergency/manage/posts/{post.pk}/').status_code,200)
        self.auth(self.outsider)
        self.assertEqual(self.client.get(f'/emergency/manage/posts/{post.pk}/').status_code,404)
    def test_optional_email_and_non_object_api_payload(self):
        form=RegisterForm({'full_name':'Demo','phone_number':'09912345679','nrc':'Demo','email':'citizen@example.test','password':'StrongDemo2026!','confirmation':'StrongDemo2026!'})
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.save().email,'citizen@example.test')
        self.auth(self.citizen)
        self.assertEqual(self.client.post('/emergency/api/incidents/',data='[]',content_type='application/json').status_code,400)
    def test_notification_read_is_not_acceptance(self):
        deployment=self.send();self.auth(self.station_admin);notice=Notice.objects.filter(recipient=self.station_admin).first()
        self.client.post('/emergency/api/poll/',{'notice':notice.pk})
        notice.refresh_from_db();deployment.refresh_from_db();self.assertIsNotNone(notice.read_at);self.assertEqual(deployment.state,'Ordered')
    def test_closed_incident_is_read_only(self):
        deployment=self.send()
        self.incident.closed_at=timezone.now();self.incident.save()
        self.auth(self.admin)
        response=self.client.get(f'/emergency/incidents/{self.incident.pk}/')
        self.assertNotContains(response,'Admin အတည်ပြုပြီး စေလွှတ်ရန်')
        self.client.post(f'/emergency/incidents/{self.incident.pk}/update/',{'message':'Closed mutation'})
        self.client.post(f'/emergency/deployments/{deployment.pk}/state/',{'state':'Accepted'})
        self.assertFalse(IncidentUpdate.objects.filter(message='Closed mutation').exists())
        deployment.refresh_from_db();self.assertEqual(deployment.state,'Ordered')
    def test_inactive_session_cannot_access_console(self):
        self.auth(self.citizen)
        self.citizen.status='Inactive';self.citizen.save()
        self.assertEqual(self.client.get('/emergency/').status_code,302)
    def test_escalation_after_departure_creates_a_new_wave(self):
        deployment=self.send();deployment_state(self.station_admin,deployment.pk,'Accepted')
        assign_staff(self.station_admin,deployment.pk,[self.firefighter.pk])
        deployment_state(self.station_admin,deployment.pk,'Departed')
        plan=ResponsePlan.objects.create(home_station=self.station,lead_station=self.station,level=2)
        PlanRequirement.objects.create(plan=plan,station=self.station,kind=self.kind,quantity=3)
        self.incident.fire_scale=2;self.incident.save()
        with patch('Emergency.services.route_between',return_value={'coordinates':[[21.97,96.08],[21.98,96.09]],'metres':1000,'instructions':[]}):
            dispatch(self.admin,self.incident.pk,[self.vehicles[2].pk])
        self.assertEqual(Deployment.objects.filter(incident=self.incident).count(),2)
        self.assertEqual(deployment.vehicles.count(),2)
        self.assertEqual(preview(self.incident)[1][0]['needed'],0)
        self.incident.fire_scale=1;self.incident.save()
        self.assertEqual(VehicleParticipation.objects.filter(deployment__incident=self.incident,active=True).count(),3)
    def test_seed_does_not_reset_password(self):
        call_command('seed_emergency_demo',stdout=BytesIO() if False else None)
        user=User.objects.get(username='demo_citizen');user.set_password('ChangedPassword2026!');user.save()
        call_command('seed_emergency_demo');user.refresh_from_db();self.assertTrue(user.check_password('ChangedPassword2026!'))
    def test_filter_pagination(self):
        for i in range(22):FireReport.objects.create(user_id=self.citizen.pk,address='pagination',fire_scale=0)
        self.auth(self.citizen);response=self.client.get('/emergency/incidents/?q=pagination')
        self.assertEqual(len(response.context['page_obj']),20)
        self.assertContains(response,'q=pagination')
        self.assertEqual(len(self.client.get('/emergency/incidents/?q=pagination&page=2').context['page_obj']),2)
    def test_management_pages_render(self):
        self.auth(self.admin)
        for kind in ['stations','staff','vehicle-types','vehicles','plans','requirements','duties','leaves','posts']:
            self.assertEqual(self.client.get(f'/emergency/manage/{kind}/').status_code,200,kind)
            if kind!='leaves':self.assertEqual(self.client.get(f'/emergency/manage/{kind}/new/').status_code,200,kind)
        for path in ['/emergency/','/emergency/map/','/emergency/reports/','/emergency/incidents/']:
            self.assertEqual(self.client.get(path).status_code,200,path)
    def test_pdf_contains_embedded_font_and_route_diagram(self):
        self.send();self.auth(self.admin);response=self.client.get(f'/emergency/incidents/{self.incident.pk}/pdf/')
        self.assertEqual(response.status_code,200);self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertIn(b'/FontFile2',response.content)
        from pypdf import PdfReader
        reader=PdfReader(BytesIO(response.content))
        self.assertGreater(len(reader.pages),0)
        streams=b''.join(page.get_contents().get_data() for page in reader.pages)
        logical=(b'\xfe\xff'+'မီးလောင်ဖြစ်စဉ်'.encode('utf-16-be')).hex().encode()
        self.assertIn(b'/ActualText',streams)
        self.assertIn(logical,streams)
        from fontTools.ttLib import TTFont
        from pathlib import Path
        font=TTFont(Path(__file__).parent/'fonts'/'NotoEmergency-Regular.ttf')
        self.assertTrue(all(ord(c) in font.getBestCmap() for c in 'မီးလောင်ဖြစ်စဉ် Demo #30 © 250.00'))


class DijkstraTests(TestCase):
    def test_import_preserves_oneway_and_private_access(self):
        import tempfile
        from pathlib import Path
        payload={'elements':[
            {'type':'node','id':1,'lat':21.97,'lon':96.08},
            {'type':'node','id':2,'lat':21.98,'lon':96.08},
            {'type':'node','id':3,'lat':21.99,'lon':96.08},
            {'type':'way','id':10,'nodes':[1,2],'tags':{'highway':'residential','oneway':'-1','name':'Demo Road'}},
            {'type':'way','id':11,'nodes':[2,3],'tags':{'highway':'service','access':'private'}}]}
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'roads.json';source.write_text(json.dumps(payload),encoding='utf-8')
            call_command('import_roads',file=str(source))
        self.assertEqual(list(RoadEdge.objects.values_list('source__osm_id','target__osm_id')),[(2,1)])
        self.assertGreater(RoadEdge.objects.get().metres,0)
    def test_shortest_distance_not_fewest_edges(self):
        path,cost=dijkstra({1:[(2,1),(3,10)],2:[(3,2)],3:[]},1,3)
        self.assertEqual(path,[1,2,3]);self.assertEqual(cost,3)
    def test_one_way_and_disconnected(self):
        self.assertEqual(dijkstra({1:[(2,1)]},2,1),([],None))
        self.assertEqual(dijkstra({1:[(2,1)],3:[]},1,3),([],None))
    def test_same_node(self):self.assertEqual(dijkstra({},1,1),([1],0))


class ConcurrentReservationTests(TransactionTestCase):
    """Use independent database connections to exercise real row locks."""
    def setUp(self):
        from django.db import connection
        if connection.vendor != 'mysql':self.skipTest('Requires MySQL row locking')
        self.station=FireStation.objects.create(name='Concurrent',address='Mandalay',contact_number='1',latitude=21.97,longitude=96.08)
        admin_role,_=Role.objects.get_or_create(role_name='Administrator')
        ff_role,_=Role.objects.get_or_create(role_name='Firefighter')
        self.admin=User.objects.create(username='concurrent_admin',role=admin_role,email=None)
        self.person=User.objects.create(username='concurrent_ff',role=ff_role,station=self.station,email=None)
        now=timezone.now()
        Duty.objects.create(employee=self.person,starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=1),task='Respond')
        kind,_=VehicleType.objects.get_or_create(name='Concurrent engine')
        self.vehicle=Vehicle.objects.create(registration='CONCURRENT',station=self.station,kind=kind)
        self.incidents=[FireReport.objects.create(user_id=self.admin.pk,status='Confirmed',fire_scale=0,address='Concurrency demo',home_station=self.station,lead_station=self.station,latitude=21.98,longitude=96.09,coordinates_confirmed=True) for _ in range(2)]

    def race(self,operation):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections,connections
        barrier=Barrier(2)
        def attempt(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                operation(index)
                return 'reserved'
            except ValidationError:return 'unavailable'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,range(2)))
        self.assertCountEqual(results,['reserved','unavailable'])

    def test_two_incidents_cannot_reserve_the_same_vehicle_concurrently(self):
        with patch('Emergency.services.route_between',return_value={'coordinates':[[21.97,96.08],[21.98,96.09]],'metres':1000,'instructions':[]}):
            self.race(lambda index:dispatch(self.admin,self.incidents[index].pk,[self.vehicle.pk],reason='Concurrency test'))
        self.assertEqual(VehicleParticipation.objects.filter(vehicle=self.vehicle,active=True).count(),1)

    def test_two_deployments_cannot_select_the_same_employee_concurrently(self):
        deployments=[Deployment.objects.create(incident=incident,station=self.station,state='Accepted') for incident in self.incidents]
        self.race(lambda index:assign_staff(self.admin,deployments[index].pk,[self.person.pk]))
        self.assertEqual(StaffParticipation.objects.filter(employee=self.person,active=True).count(),1)

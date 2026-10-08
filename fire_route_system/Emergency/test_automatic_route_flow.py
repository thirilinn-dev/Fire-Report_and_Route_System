from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from DataAccess.models import User, Role, FireStation, FireReport, Dispatch, Tbl_Notification
from Emergency.models import Vehicle, VehicleType, Deployment, VehicleParticipation, RoadNode, RoadEdge
from Emergency.services import calculate_all_routes_and_dispatch


class AutomaticRouteFlowTests(TestCase):
    def setUp(self):
        # Setup roles
        self.admin_role = Role.objects.get_or_create(role_name='Administrator')[0]
        self.operator_role = Role.objects.get_or_create(role_name='Dispatcher')[0]
        self.citizen_role = Role.objects.get_or_create(role_name='Citizen')[0]
        self.firefighter_role = Role.objects.get_or_create(role_name='Firefighter')[0]

        # Setup stations
        # Station A: lat 21.980, lon 96.080 (Mandalay center)
        self.station_a = FireStation.objects.create(
            name='Station A (Chanayethazan)',
            address='Chanayethazan, Mandalay',
            contact_number='02-11111',
            latitude=21.980,
            longitude=96.080,
            status='Active'
        )
        # Station B: lat 21.950, lon 96.085 (further south)
        self.station_b = FireStation.objects.create(
            name='Station B (Mahaaungmye)',
            address='Mahaaungmye, Mandalay',
            contact_number='02-22222',
            latitude=21.950,
            longitude=96.085,
            status='Active'
        )

        # Vehicle type & engines
        self.engine_type = VehicleType.objects.get_or_create(name='Pumper Fire Engine')[0]
        self.engine_a = Vehicle.objects.create(
            registration='MDY-01-ENGINE',
            station=self.station_a,
            kind=self.engine_type,
            status='Available'
        )
        self.engine_b = Vehicle.objects.create(
            registration='MDY-02-ENGINE',
            station=self.station_b,
            kind=self.engine_type,
            status='Available'
        )

        # Users
        self.admin = User.objects.create(
            username='flow_admin_01',
            role=self.admin_role,
            phone_number='09111111111'
        )
        self.admin.set_password('FlowPass2026!')
        self.admin.save()

        self.operator = User.objects.create(
            username='flow_operator_01',
            role=self.operator_role,
            station=self.station_a,
            phone_number='09222222222'
        )
        self.operator.set_password('FlowPass2026!')
        self.operator.save()

        self.citizen = User.objects.create(
            username='flow_citizen_01',
            role=self.citizen_role,
            phone_number='09333333333'
        )
        self.citizen.set_password('FlowPass2026!')
        self.citizen.save()

        # Build interconnected road graph for real Dijkstra
        # Node 1: near Station A (21.980, 96.080)
        # Node 2: midway (21.975, 96.080)
        # Node 3: Incident location (21.970, 96.082)
        # Node 4: near Station B (21.950, 96.085)
        self.n1 = RoadNode.objects.create(osm_id=101, latitude=21.980, longitude=96.080)
        self.n2 = RoadNode.objects.create(osm_id=102, latitude=21.975, longitude=96.080)
        self.n3 = RoadNode.objects.create(osm_id=103, latitude=21.970, longitude=96.082)
        self.n4 = RoadNode.objects.create(osm_id=104, latitude=21.950, longitude=96.085)

        # Edges (bidirectional)
        # N1 <-> N2 (550m)
        RoadEdge.objects.create(source=self.n1, target=self.n2, metres=550.0, name='78th Street')
        RoadEdge.objects.create(source=self.n2, target=self.n1, metres=550.0, name='78th Street')
        # N2 <-> N3 (580m)
        RoadEdge.objects.create(source=self.n2, target=self.n3, metres=580.0, name='30th Street')
        RoadEdge.objects.create(source=self.n3, target=self.n2, metres=580.0, name='30th Street')
        # N3 <-> N4 (2250m)
        RoadEdge.objects.create(source=self.n3, target=self.n4, metres=2250.0, name='73rd Street')
        RoadEdge.objects.create(source=self.n4, target=self.n3, metres=2250.0, name='73rd Street')

    def test_01_normal_flow_complete(self):
        """
        Test 1 — Normal Flow:
        Citizen report -> Triage Queue -> Operator confirms -> Incident Management ->
        Admin selects Level ONLY -> Auto Dijkstra calculates ALL stations ->
        Selects shortest valid route -> Selects responding station ->
        Assigns engine -> Auto Dispatch created.
        """
        # 1. Citizen submits report
        report = FireReport.objects.create(
            user_id=self.citizen.pk,
            reporter_phone=self.citizen.phone_number,
            latitude=21.970,
            longitude=96.082,
            address='Near 30th & 73rd Street',
            fire_scale=0,
            status='Pending'
        )
        notif = Tbl_Notification.objects.filter(report=report).first()
        self.assertIsNotNone(notif, "Notification must be generated for Pending report in Triage Queue")

        # 2. Operator confirms report in Triage Queue
        client = Client()
        client.force_login(self.operator, backend='DataAccess.backends.RoleAuthBackend')
        confirm_resp = client.post(reverse('confirm_incident', args=[notif.id]))
        self.assertEqual(confirm_resp.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.status, 'Confirmed')
        self.assertTrue(report.coordinates_confirmed)

        # 3. Admin selects Fire Level ONLY (e.g. Level 3) in Incident Management
        admin_client = Client()
        admin_client.force_login(self.admin, backend='DataAccess.backends.RoleAuthBackend')

        # Admin POSTs ConfirmForm with ONLY fire_scale
        action_resp = admin_client.post(
            reverse('emergency:action', args=[report.pk, 'confirm']),
            data={'fire_scale': 3}
        )
        self.assertEqual(action_resp.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.fire_scale, 3)
        self.assertEqual(report.status, 'Dispatched')

        # Station A is closer (~1130m) than Station B (~2250m)
        self.assertEqual(report.home_station, self.station_a)

        # 4. Verify Deployment created automatically
        deployment = Deployment.objects.filter(incident=report, station=self.station_a).first()
        self.assertIsNotNone(deployment)
        self.assertEqual(deployment.state, 'Ordered')
        self.assertIn('coordinates', deployment.route)
        self.assertIn('all_routes', deployment.route)
        self.assertGreater(len(deployment.route['all_routes']), 0)

        # 5. Verify Engine reserved
        self.engine_a.refresh_from_db()
        self.assertEqual(self.engine_a.status, 'Reserved')
        self.assertTrue(deployment.vehicles.filter(vehicle=self.engine_a, active=True).exists())

        # 6. Verify Dispatch record created automatically
        dispatch = Dispatch.objects.filter(report=report).first()
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch.station, self.station_a)

    def test_02_fake_report_rejection(self):
        """
        Test 2 — Fake Report:
        Citizen report -> Operator rejects -> Status becomes False Alarm -> No dispatch
        """
        report = FireReport.objects.create(
            user_id=self.citizen.pk,
            reporter_phone=self.citizen.phone_number,
            latitude=21.970,
            longitude=96.082,
            address='Fake fire report',
            fire_scale=0,
            status='Pending'
        )
        notif = Tbl_Notification.objects.filter(report=report).first()

        client = Client()
        client.force_login(self.operator, backend='DataAccess.backends.RoleAuthBackend')
        reject_resp = client.post(reverse('reject_incident', args=[notif.id]))
        self.assertEqual(reject_resp.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.status, 'False Alarm')
        self.assertIsNotNone(report.closed_at)

        # Ensure NO deployment or dispatch was created
        self.assertFalse(Deployment.objects.filter(incident=report).exists())
        self.assertFalse(Dispatch.objects.filter(report=report).exists())

    def test_03_nearest_station_has_no_engine(self):
        """
        Test 3 — Nearest Station Has No Engine:
        Station A is closest, but its engine is Maintenance/unavailable.
        Station B has available engine.
        System must skip Station A and select Station B!
        """
        # Make Station A engine unavailable
        self.engine_a.status = 'Maintenance'
        self.engine_a.save()

        report = FireReport.objects.create(
            user_id=self.citizen.pk,
            latitude=21.970,
            longitude=96.082,
            address='Fire test location',
            fire_scale=1,
            status='Confirmed',
            coordinates_confirmed=True
        )

        res = calculate_all_routes_and_dispatch(report, actor=self.admin, fire_scale=1)
        self.assertTrue(res['success'])

        # Selected responding station must be Station B!
        self.assertEqual(res['selected_station'], self.station_b)
        self.assertEqual(res['selected_engine'], self.engine_b)

        report.refresh_from_db()
        self.assertEqual(report.home_station, self.station_b)
        self.assertEqual(report.status, 'Dispatched')

    def test_04_no_available_engine_anywhere(self):
        """
        Test 4 — No Available Engine:
        All stations have no available engines -> Clear error, no dispatch created.
        """
        self.engine_a.status = 'Deployed'
        self.engine_a.save()
        self.engine_b.status = 'Maintenance'
        self.engine_b.save()

        report = FireReport.objects.create(
            user_id=self.citizen.pk,
            latitude=21.970,
            longitude=96.082,
            address='Fire test location',
            fire_scale=1,
            status='Confirmed',
            coordinates_confirmed=True
        )

        res = calculate_all_routes_and_dispatch(report, actor=self.admin, fire_scale=2)
        self.assertFalse(res['success'])
        self.assertIn('No available fire engine', res['error'])

        # No deployment or dispatch created
        self.assertFalse(Deployment.objects.filter(incident=report).exists())
        self.assertFalse(Dispatch.objects.filter(report=report).exists())
        report.refresh_from_db()
        self.assertEqual(report.status, 'Confirmed')

    def test_05_no_road_route_error(self):
        """
        Test 5 — No Road Route:
        Incident is far outside road network where no path can be calculated.
        -> Clear error, no dispatch created.
        """
        report = FireReport.objects.create(
            user_id=self.citizen.pk,
            latitude=15.000,  # Far away from Mandalay road nodes
            longitude=90.000,
            address='Island in sea',
            fire_scale=1,
            status='Confirmed',
            coordinates_confirmed=True
        )

        res = calculate_all_routes_and_dispatch(report, actor=self.admin, fire_scale=1)
        self.assertFalse(res['success'])
        self.assertIn('No valid road route', res['error'])

        self.assertFalse(Deployment.objects.filter(incident=report).exists())
        self.assertFalse(Dispatch.objects.filter(report=report).exists())

    def test_06_idempotent_duplicate_prevention(self):
        """
        Test 6 — Duplicate Prevention:
        Recalculating or re-submitting route calculation for the same incident
        must NOT create duplicate Deployment or Dispatch records.
        """
        report = FireReport.objects.create(
            user_id=self.citizen.pk,
            latitude=21.970,
            longitude=96.082,
            address='Idempotency test location',
            fire_scale=1,
            status='Confirmed',
            coordinates_confirmed=True
        )

        # Run 1
        res1 = calculate_all_routes_and_dispatch(report, actor=self.admin, fire_scale=1)
        self.assertTrue(res1['success'])
        dep_count_1 = Deployment.objects.filter(incident=report).count()
        disp_count_1 = Dispatch.objects.filter(report=report).count()
        part_count_1 = VehicleParticipation.objects.filter(deployment__incident=report).count()

        self.assertEqual(dep_count_1, 1)
        self.assertEqual(disp_count_1, 1)
        self.assertEqual(part_count_1, 1)

        # Run 2 (Simulating page refresh or recalculation)
        res2 = calculate_all_routes_and_dispatch(report, actor=self.admin, fire_scale=2)
        self.assertTrue(res2['success'])
        dep_count_2 = Deployment.objects.filter(incident=report).count()
        disp_count_2 = Dispatch.objects.filter(report=report).count()
        part_count_2 = VehicleParticipation.objects.filter(deployment__incident=report).count()

        self.assertEqual(dep_count_2, 1, "Must NOT create duplicate Deployment on recalculation")
        self.assertEqual(disp_count_2, 1, "Must NOT create duplicate Dispatch on recalculation")
        self.assertEqual(part_count_2, 1, "Must NOT create duplicate VehicleParticipation")

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from DataAccess.models import FireReport, FireStation, Dispatch, User, Role
import json

class DashboardViewTests(TestCase):
    def setUp(self):
        # Create a Role and User for test setup
        self.role = Role.objects.create(role_name="Operator", description="Operator role")
        self.operator = User.objects.create(
            role=self.role,
            username="test_operator",
            email="operator@test.com",
            password_hash="hashed_pw",
            status="Active"
        )
        
        # Create dummy stations
        self.station1 = FireStation.objects.create(
            name="Mandalay Central Station",
            address="Mandalay Cent",
            contact_number="123456",
            latitude=21.9750,
            longitude=96.0830,
            status="Active"
        )
        self.station2 = FireStation.objects.create(
            name="Mandalay North Station",
            address="Mandalay North",
            contact_number="654321",
            latitude=22.0500,
            longitude=96.1000,
            status="Inactive"
        )

        # Create dummy fire reports
        self.report_pending = FireReport.objects.create(
            reporter_phone="091111111",
            latitude=21.9600,
            longitude=96.0900,
            fire_scale=3,
            status="Pending"
        )
        self.report_dispatched = FireReport.objects.create(
            reporter_phone="092222222",
            latitude=21.9800,
            longitude=96.0700,
            fire_scale=2,
            status="Dispatched"
        )
        self.report_resolved = FireReport.objects.create(
            reporter_phone="093333333",
            latitude=21.9900,
            longitude=96.0500,
            fire_scale=1,
            status="Resolved"
        )

        # Create dummy dispatch
        self.dispatch = Dispatch.objects.create(
            report=self.report_dispatched,
            station=self.station1,
            operator=self.operator,
            resources_deployed="2 fire trucks"
        )

    def test_dashboard_url_status_code(self):
        """
        Requesting the dashboard URL returns 200 OK status code.
        """
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_uses_correct_template(self):
        """
        Requesting the dashboard uses dashboard/dashboard.html.
        """
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')

    def test_dashboard_aggregates_kpis_correctly(self):
        """
        Dashboard context contains correct aggregated counts for KPIs.
        """
        response = self.client.get(reverse('dashboard'))
        
        # Active fires count should be 2 (Pending + Dispatched)
        self.assertEqual(response.context['total_active_fires'], 2)
        
        # High severity fires count should be 1 (Pending report has scale 3)
        self.assertEqual(response.context['high_severity_fires'], 1)
        
        # Available stations count should be 1 (station1 is Active, station2 is Inactive)
        self.assertEqual(response.context['available_stations'], 1)
        
        # Total dispatches today should be 1
        self.assertEqual(response.context['total_dispatches_today'], 1)

    def test_dashboard_lists_pending_reports_correctly(self):
        """
        Dashboard lists pending reports needing immediate operator action.
        """
        response = self.client.get(reverse('dashboard'))
        pending_list = response.context['pending_reports']
        
        self.assertEqual(pending_list.count(), 1)
        self.assertEqual(pending_list[0].id, self.report_pending.id)

    def test_dashboard_lists_active_dispatches_correctly(self):
        """
        Dashboard lists active dispatches (resolved_at is null).
        """
        response = self.client.get(reverse('dashboard'))
        active_dispatches = response.context['active_dispatches']
        
        self.assertEqual(active_dispatches.count(), 1)
        self.assertEqual(active_dispatches[0].id, self.dispatch.id)

    def test_dashboard_coordinates_serialized_to_json(self):
        """
        Active fire and station coordinates are serialized to JSON string in context.
        """
        response = self.client.get(reverse('dashboard'))
        
        # Verify fire pins JSON
        self.assertIn('fire_pins_json', response.context)
        fire_pins = json.loads(response.context['fire_pins_json'])
        self.assertEqual(len(fire_pins), 2)  # pending + dispatched
        
        # Verify active station pins JSON
        self.assertIn('station_pins_json', response.context)
        station_pins = json.loads(response.context['station_pins_json'])
        self.assertEqual(len(station_pins), 1)  # only station1 is Active
        self.assertEqual(station_pins[0]['name'], "Mandalay Central Station")


class DashboardReportPortalTests(TestCase):
    def setUp(self):
        # Create fire reports of different levels
        FireReport.objects.create(
            reporter_phone="091000001",
            latitude=21.9750,
            longitude=96.0830,
            fire_scale=1,
            status="Confirmed"
        )
        FireReport.objects.create(
            reporter_phone="091000002",
            latitude=21.9760,
            longitude=96.0840,
            fire_scale=2,
            status="Dispatched"
        )
        FireReport.objects.create(
            reporter_phone="091000003",
            latitude=21.9770,
            longitude=96.0855,
            fire_scale=3,
            status="Resolved"
        )

    def test_report_portal_preview_renders(self):
        response = self.client.get(reverse('report_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/report_preview.html')
        self.assertContains(response, "Command Report Portal")
        
        # Default all reports in view
        self.assertEqual(response.context['reports'].count(), 3)

    def test_report_portal_filter_by_level(self):
        response = self.client.get(reverse('report_portal'), {'level': '3'})
        self.assertEqual(response.status_code, 200)
        reports = response.context['reports']
        self.assertEqual(reports.count(), 1)
        self.assertEqual(reports[0].fire_scale, 3)

    def test_export_csv_download(self):
        response = self.client.get(reverse('export_csv'), {'level': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8-sig')
        self.assertIn('attachment;', response['Content-Disposition'])
        
        # Decode and verify content
        content = response.content.decode('utf-8-sig')
        self.assertIn("Level 2", content)
        self.assertNotIn("Level 3", content)

    def test_export_pdf_download(self):
        response = self.client.get(reverse('export_pdf'), {'level': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])


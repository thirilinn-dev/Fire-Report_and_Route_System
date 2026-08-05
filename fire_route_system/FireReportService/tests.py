import json
from django.test import TestCase, Client
from django.urls import reverse
from DataAccess.models import FireReport

class FireReportServiceAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.report1 = FireReport.objects.create(
            user_id=1,
            reporter_phone="09111222333",
            latitude=16.80,
            longitude=96.16,
            fire_scale=2,
            photo_url="http://example.com/fire1.jpg",
            status="Pending"
        )
        self.report2 = FireReport.objects.create(
            user_id=None,
            reporter_phone="09444555666",
            latitude=16.82,
            longitude=96.18,
            fire_scale=3,
            photo_url=None,
            status="Dispatched"
        )

    def test_firereport_list(self):
        url = reverse('api_firereport_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['reporter_phone'], "09111222333")
        self.assertEqual(data[1]['fire_scale'], 3)

    def test_firereport_create(self):
        url = reverse('api_firereport_list_create')
        payload = {
            'user_id': 2,
            'reporter_phone': '09888777666',
            'latitude': 16.84,
            'longitude': 96.22,
            'fire_scale': 1,
            'photo_url': 'http://example.com/fire3.jpg',
            'status': 'Pending'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['fire_scale'], 1)
        self.assertTrue(FireReport.objects.filter(reporter_phone="09888777666").exists())

    def test_firereport_create_invalid_scale(self):
        url = reverse('api_firereport_list_create')
        payload = {
            'latitude': 16.84,
            'longitude': 96.22,
            'fire_scale': 5 # Invalid scale
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_firereport_retrieve(self):
        url = reverse('api_firereport_detail', kwargs={'pk': self.report1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['reporter_phone'], "09111222333")

    def test_firereport_update(self):
        url = reverse('api_firereport_detail', kwargs={'pk': self.report1.pk})
        payload = {
            'user_id': 1,
            'reporter_phone': '09111222333-updated',
            'latitude': 16.805,
            'longitude': 96.165,
            'fire_scale': 3,
            'photo_url': 'http://example.com/fire1_new.jpg',
            'status': 'Under Control'
        }
        response = self.client.put(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['reporter_phone'], "09111222333-updated")
        self.assertEqual(data['status'], "Under Control")

    def test_firereport_delete(self):
        url = reverse('api_firereport_detail', kwargs={'pk': self.report2.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FireReport.objects.filter(pk=self.report2.pk).exists())


from DataAccess.models import Tbl_Notification

class FireReportTriageWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_notification_created_on_pending_report(self):
        """
        When a new report is created as 'Pending', a notification is created automatically.
        """
        initial_count = Tbl_Notification.objects.filter(is_read=False).count()

        # Create report
        report = FireReport.objects.create(
            latitude=21.9750,
            longitude=96.0830,
            fire_scale=2,
            status='Pending'
        )

        # Count should increment
        self.assertEqual(Tbl_Notification.objects.filter(is_read=False).count(), initial_count + 1)

        # Check association
        notification = Tbl_Notification.objects.filter(report=report).first()
        self.assertIsNotNone(notification)
        self.assertFalse(notification.is_read)

    def test_notification_not_created_on_other_statuses(self):
        """
        No notification is created if status is not 'Pending'.
        """
        initial_count = Tbl_Notification.objects.count()
        FireReport.objects.create(
            latitude=21.9750,
            longitude=96.0830,
            fire_scale=1,
            status='Resolved'
        )
        self.assertEqual(Tbl_Notification.objects.count(), initial_count)

    def test_triage_queue_displays_unread_notifications(self):
        # Create unconfirmed report
        report = FireReport.objects.create(
            latitude=21.9750,
            longitude=96.0830,
            fire_scale=3,
            status='Pending'
        )
        url = reverse('triage_queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#{report.id}")
        self.assertContains(response, "Confirm Incident")

    def test_confirm_incident_action(self):
        report = FireReport.objects.create(
            latitude=21.9750,
            longitude=96.0830,
            fire_scale=3,
            status='Pending'
        )
        notif = Tbl_Notification.objects.get(report=report)

        # Post confirmation action
        url = reverse('confirm_incident', kwargs={'notification_id': notif.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('triage_queue'))

        # Check database updates
        notif.refresh_from_db()
        report.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertEqual(report.status, 'Confirmed')

    def test_incident_list_excludes_pending_reports(self):
        # Pending report
        report_pending = FireReport.objects.create(
            latitude=21.97,
            longitude=96.08,
            fire_scale=3,
            status='Pending'
        )
        # Confirmed report
        report_confirmed = FireReport.objects.create(
            latitude=21.975,
            longitude=96.085,
            fire_scale=2,
            status='Confirmed'
        )
        url = reverse('fire_report_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context['reports']
        self.assertIn(report_confirmed, reports_in_context)
        self.assertNotIn(report_pending, reports_in_context)


from django.core.exceptions import ValidationError

class FireReportFlexibleReportingTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_validation_gps_only_is_valid(self):
        """
        A report with GPS coordinates and no address is valid.
        """
        report = FireReport(
            latitude=21.9750,
            longitude=96.0830,
            fire_scale=2,
            status='Pending'
        )
        try:
            report.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for GPS-only report!")

    def test_validation_address_only_is_valid(self):
        """
        A report with an address and no GPS coordinates is valid.
        """
        report = FireReport(
            address="Mandalay Palace, Mandalay",
            fire_scale=2,
            status='Pending'
        )
        try:
            report.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for Address-only report!")

    def test_validation_neither_raises_error(self):
        """
        A report with neither GPS coordinates nor address raises ValidationError.
        """
        report = FireReport(
            fire_scale=2,
            status='Pending'
        )
        with self.assertRaises(ValidationError):
            report.full_clean()

    def test_submission_without_phone_number(self):
        """
        Submitting report fire form without phone number and fire scale defaults scale to 1.
        """
        url = reverse('report_fire')
        payload = {
            'latitude': '21.9928',
            'longitude': '96.0964',
            'address': '',
            'reporter_phone': ''
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)
        
        # Verify saved properties in database
        report = FireReport.objects.filter(latitude=21.9928, longitude=96.0964).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.fire_scale, 1)
        self.assertIsNone(report.reporter_phone)
        self.assertIsNone(report.address)





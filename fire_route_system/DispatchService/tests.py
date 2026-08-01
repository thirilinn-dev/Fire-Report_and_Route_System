import json
from django.test import TestCase, Client
from django.urls import reverse
from DataAccess.models import Role, User, FireReport, FireStation, Dispatch

class DispatchServiceAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role = Role.objects.create(role_name="Operator", description="Operator")
        self.operator = User.objects.create(
            role=self.role,
            username="op_user",
            email="op@fireapp.com",
            password_hash="pw1",
            phone_number="09111",
            status="Active"
        )
        self.report = FireReport.objects.create(
            user_id=None,
            reporter_phone="09222",
            latitude=16.8,
            longitude=96.1,
            fire_scale=2,
            status="Pending"
        )
        self.station = FireStation.objects.create(
            name="Station 1",
            address="Address 1",
            contact_number="123",
            latitude=16.85,
            longitude=96.15,
            status="Active"
        )
        self.dispatch1 = Dispatch.objects.create(
            report=self.report,
            station=self.station,
            operator=self.operator,
            resources_deployed="2 fire engines, 5 firefighters"
        )

    def test_dispatch_list(self):
        url = reverse('api_dispatch_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['resources_deployed'], "2 fire engines, 5 firefighters")

    def test_dispatch_create(self):
        # Create another report to associate with the new dispatch
        new_report = FireReport.objects.create(
            user_id=None,
            reporter_phone="09333",
            latitude=16.9,
            longitude=96.2,
            fire_scale=1,
            status="Pending"
        )
        url = reverse('api_dispatch_list_create')
        payload = {
            'report_id': new_report.pk,
            'station_id': self.station.pk,
            'operator_id': self.operator.pk,
            'resources_deployed': '1 water tanker'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['resources_deployed'], "1 water tanker")
        self.assertTrue(Dispatch.objects.filter(resources_deployed="1 water tanker").exists())

    def test_dispatch_create_invalid_report(self):
        url = reverse('api_dispatch_list_create')
        payload = {
            'report_id': 999, # Non-existent report
            'station_id': self.station.pk,
            'operator_id': self.operator.pk,
            'resources_deployed': 'Error case'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_dispatch_retrieve(self):
        url = reverse('api_dispatch_detail', kwargs={'pk': self.dispatch1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['resources_deployed'], "2 fire engines, 5 firefighters")

    def test_dispatch_update(self):
        url = reverse('api_dispatch_detail', kwargs={'pk': self.dispatch1.pk})
        payload = {
            'report_id': self.report.pk,
            'station_id': self.station.pk,
            'operator_id': self.operator.pk,
            'resources_deployed': 'Updated resources description',
            'resolved_at': '2026-07-11T12:00:00Z'
        }
        response = self.client.put(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['resources_deployed'], "Updated resources description")
        self.assertIsNotNone(data['resolved_at'])

    def test_dispatch_delete(self):
        url = reverse('api_dispatch_detail', kwargs={'pk': self.dispatch1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Dispatch.objects.filter(pk=self.dispatch1.pk).exists())

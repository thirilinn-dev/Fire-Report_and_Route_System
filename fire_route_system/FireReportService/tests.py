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

import json
from django.test import TestCase, Client
from django.urls import reverse
from DataAccess.models import WaterSource

class WaterSourcesServiceAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.source1 = WaterSource.objects.create(
            source_type="Hydrant",
            description="Near town hall",
            latitude=16.81,
            longitude=96.17,
            status="Operational"
        )
        self.source2 = WaterSource.objects.create(
            source_type="Pond",
            description="Behind the garden",
            latitude=16.83,
            longitude=96.19,
            status="Unavailable"
        )

    def test_watersource_list(self):
        url = reverse('api_watersource_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['source_type'], "Hydrant")
        self.assertEqual(data[1]['status'], "Unavailable")

    def test_watersource_create(self):
        url = reverse('api_watersource_list_create')
        payload = {
            'source_type': 'River',
            'description': 'Main river access point',
            'latitude': 16.79,
            'longitude': 96.13,
            'status': 'Operational'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['source_type'], "River")
        self.assertTrue(WaterSource.objects.filter(source_type="River").exists())

    def test_watersource_create_missing_field(self):
        url = reverse('api_watersource_list_create')
        payload = {
            'source_type': 'Hydrant'
            # Missing latitude and longitude
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_watersource_retrieve(self):
        url = reverse('api_watersource_detail', kwargs={'pk': self.source1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['source_type'], "Hydrant")

    def test_watersource_update(self):
        url = reverse('api_watersource_detail', kwargs={'pk': self.source1.pk})
        payload = {
            'source_type': 'Hydrant',
            'description': 'Near town hall - updated location',
            'latitude': 16.812,
            'longitude': 96.172,
            'status': 'Under Maintenance'
        }
        response = self.client.put(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['description'], "Near town hall - updated location")
        self.assertEqual(data['status'], "Under Maintenance")

    def test_watersource_delete(self):
        url = reverse('api_watersource_detail', kwargs={'pk': self.source2.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WaterSource.objects.filter(pk=self.source2.pk).exists())

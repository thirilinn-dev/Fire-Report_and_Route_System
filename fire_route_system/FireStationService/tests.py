import json
from django.test import TestCase, Client
from django.urls import reverse
from DataAccess.models import FireStation

class FireStationServiceAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.station1 = FireStation.objects.create(
            name="Central Station",
            address="123 Main St",
            contact_number="111-222",
            latitude=16.82,
            longitude=96.15,
            status="Active"
        )
        self.station2 = FireStation.objects.create(
            name="North Station",
            address="456 Oak Rd",
            contact_number="333-444",
            latitude=16.89,
            longitude=96.12,
            status="Maintenance"
        )

    def test_firestation_list(self):
        url = reverse('api_firestation_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], "Central Station")
        self.assertEqual(data[1]['name'], "North Station")

    def test_firestation_create(self):
        url = reverse('api_firestation_list_create')
        payload = {
            'name': 'East Station',
            'address': '789 East Ave',
            'contact_number': '555-666',
            'latitude': 16.85,
            'longitude': 96.20,
            'status': 'Active'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['name'], "East Station")
        self.assertTrue(FireStation.objects.filter(name="East Station").exists())

    def test_firestation_create_missing_field(self):
        url = reverse('api_firestation_list_create')
        payload = {
            'name': 'East Station',
            # address and contact_number are missing
            'latitude': 16.85,
            'longitude': 96.20
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_firestation_retrieve(self):
        url = reverse('api_firestation_detail', kwargs={'station_id': self.station1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], "Central Station")

    def test_firestation_update(self):
        url = reverse('api_firestation_detail', kwargs={'station_id': self.station1.pk})
        payload = {
            'name': 'Central Station Renamed',
            'address': '123 New Main St',
            'contact_number': '111-222-updated',
            'latitude': 16.825,
            'longitude': 96.155,
            'status': 'Inactive'
        }
        response = self.client.put(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], "Central Station Renamed")
        self.assertEqual(data['status'], "Inactive")

    def test_firestation_delete(self):
        url = reverse('api_firestation_detail', kwargs={'station_id': self.station2.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FireStation.objects.filter(pk=self.station2.pk).exists())

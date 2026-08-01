from django.test import TestCase
from django.urls import reverse
from DataAccess.models import Location
import json

class MapViewTests(TestCase):
    def test_map_view_status_code(self):
        """
        Requesting the map view URL returns 200 OK status code.
        """
        response = self.client.get(reverse('map_view'))
        self.assertEqual(response.status_code, 200)

    def test_map_view_template_used(self):
        """
        Requesting the map view uses the correct template.
        """
        response = self.client.get(reverse('map_view'))
        self.assertTemplateUsed(response, 'maps/map.html')

    def test_map_view_auto_seeds_locations(self):
        """
        When there are no locations in the database, the view auto-seeds them.
        """
        # Ensure database starts empty of locations
        Location.objects.all().delete()
        self.assertEqual(Location.objects.count(), 0)

        # Trigger view
        response = self.client.get(reverse('map_view'))

        # Check database now contains the auto-seeded locations
        self.assertTrue(Location.objects.count() > 0)
        self.assertIn('locations', response.context)
        self.assertEqual(len(response.context['locations']), Location.objects.count())

    def test_map_view_serializes_locations_to_json(self):
        """
        Locations are correctly serialized to a JSON string in the context.
        """
        # Delete existing and create 2 specific locations
        Location.objects.all().delete()
        loc1 = Location.objects.create(name="Test Station A", latitude=16.1, longitude=96.1, description="Desc A")
        loc2 = Location.objects.create(name="Test Station B", latitude=16.2, longitude=96.2, description="Desc B")

        response = self.client.get(reverse('map_view'))

        self.assertIn('locations_json', response.context)
        locations_data = json.loads(response.context['locations_json'])

        self.assertEqual(len(locations_data), 2)
        
        # Checking first sorted location (Test Station A)
        self.assertEqual(locations_data[0]['name'], "Test Station A")
        self.assertEqual(locations_data[0]['latitude'], 16.1)
        self.assertEqual(locations_data[0]['longitude'], 96.1)
        self.assertEqual(locations_data[0]['description'], "Desc A")

        # Checking second sorted location (Test Station B)
        self.assertEqual(locations_data[1]['name'], "Test Station B")
        self.assertEqual(locations_data[1]['latitude'], 16.2)
        self.assertEqual(locations_data[1]['longitude'], 96.2)
        self.assertEqual(locations_data[1]['description'], "Desc B")

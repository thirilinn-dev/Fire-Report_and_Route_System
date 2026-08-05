from django.test import TestCase
from django.urls import reverse
from DataAccess.models import FireStation
import json

class MapViewTests(TestCase):
    def setUp(self):
        self.station1 = FireStation.objects.create(
            name="Central Fire Station",
            address="85th Street, Mandalay",
            contact_number="085-12345",
            latitude=21.9750,
            longitude=96.0830,
            status="Active"
        )
        self.station2 = FireStation.objects.create(
            name="North Fire Station",
            address="22nd Street, Mandalay",
            contact_number="085-67890",
            latitude=22.0100,
            longitude=96.0900,
            status="Inactive"
        )

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

    def test_map_view_passes_stations_to_context(self):
        """
        The map view should pass fire stations to the context.
        """
        response = self.client.get(reverse('map_view'))
        self.assertIn('stations', response.context)
        self.assertEqual(response.context['stations'].count(), 2)

    def test_map_view_serializes_stations_to_json(self):
        """
        Stations with coordinates are correctly serialized to JSON in the context.
        """
        response = self.client.get(reverse('map_view'))
        self.assertIn('stations_json', response.context)
        stations_data = json.loads(response.context['stations_json'])

        self.assertEqual(len(stations_data), 2)

        # Verify station fields present
        names = [s['name'] for s in stations_data]
        self.assertIn("Central Fire Station", names)
        self.assertIn("North Fire Station", names)

        central = next(s for s in stations_data if s['name'] == "Central Fire Station")
        self.assertEqual(central['latitude'], 21.9750)
        self.assertEqual(central['longitude'], 96.0830)
        self.assertEqual(central['status'], "Active")



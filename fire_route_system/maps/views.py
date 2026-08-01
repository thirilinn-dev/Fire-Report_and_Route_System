import json
from django.shortcuts import render
from .models import Location

def map_view(request):
    # Clear old Yangon seeds if present to ensure proper Mandalay display
    if Location.objects.filter(name="Shwedagon Pagoda").exists():
        Location.objects.all().delete()

    # Auto-seed if empty
    if not Location.objects.exists():
        Location.objects.create(
            name="Mandalay Palace",
            latitude=21.9928,
            longitude=96.0964,
            description="A royal palace built in the late 1850s, walled by a scenic moat, serving as the primary residence of the last Burmese monarchy."
        )
        Location.objects.create(
            name="Mandalay Hill",
            latitude=22.0161,
            longitude=96.1114,
            description="A 240-meter hill located to the northeast of the city center, known for its abundance of pagodas, monasteries, and panoramic sunset views."
        )
        Location.objects.create(
            name="Mahamuni Buddha Temple",
            latitude=21.9519,
            longitude=96.0786,
            description="A highly revered Buddhist pilgrimage site housing the famous Mahamuni Buddha image, coated in thick layers of gold leaf by devotees."
        )
        Location.objects.create(
            name="Kuthodaw Pagoda",
            latitude=22.0072,
            longitude=96.1133,
            description="A Buddhist stupa that houses the 'World's Largest Book', consisting of 729 stone-inscribed shrines containing the Tipitaka scriptures."
        )
        Location.objects.create(
            name="U Bein Bridge",
            latitude=21.8944,
            longitude=96.0586,
            description="A historic 1.2-kilometer crossing built around 1850, constructed from reclaimed teakwood and recognized as the oldest teak bridge in the world."
        )
        Location.objects.create(
            name="Zay Cho Market",
            latitude=21.9734,
            longitude=96.0792,
            description="The oldest and most important market in Mandalay, offering local goods, textiles, spices, and gemstones."
        )
        Location.objects.create(
            name="Shwenandaw Monastery",
            latitude=22.0033,
            longitude=96.1139,
            description="A historic Buddhist monastery built of teak wood, famous for its intricate wood carvings of Buddhist myths."
        )

    locations = Location.objects.all().order_by('name')
    
    # Serialize to JSON list
    locations_list = []
    for loc in locations:
        locations_list.append({
            'id': loc.id,
            'name': loc.name,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'description': loc.description or ""
        })
    
    locations_json = json.dumps(locations_list)
    
    context = {
        'locations': locations,
        'locations_json': locations_json,
    }
    return render(request, 'maps/map.html', context)

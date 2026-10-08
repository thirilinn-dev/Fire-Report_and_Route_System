from django.core.management.base import BaseCommand, CommandError
from DataAccess.models import FireStation, FireReport, User
from Emergency.routing import distance, route_between


class Command(BaseCommand):
    help = 'Create labelled demo incidents with verified road routes of at least 3 km.'

    def handle(self, *args, **options):
        stations=list(FireStation.objects.filter(status='Active',source_key__isnull=True))
        if not stations:raise CommandError('An active demo station is required.')
        station=min(stations,key=lambda s:distance((s.latitude,s.longitude),(21.975,96.083)))
        citizen=User.objects.filter(username='demo_citizen').first()
        if citizen is None:raise CommandError('Run seed_emergency_demo first.')
        cases=[('DEMO-ROUTE-SOUTH — တောင်ပိုင်း လမ်းကြောင်း စမ်းသပ်ဖြစ်စဉ်',21.91,96.09),
               ('DEMO-ROUTE-NORTH — မြောက်ပိုင်း လမ်းကြောင်း စမ်းသပ်ဖြစ်စဉ်',22.04,96.09),
               ('DEMO-ROUTE-EAST — အရှေ့ပိုင်း လမ်းကြောင်း စမ်းသပ်ဖြစ်စဉ်',21.975,96.16)]
        for address,latitude,longitude in cases:
            incident=FireReport.objects.filter(address=address).first()
            if incident is not None:
                self.stdout.write(f'Existing incident {incident.pk}; preserved.')
                continue
            incident=FireReport(user_id=citizen.pk,address=address,latitude=latitude,longitude=longitude,
                coordinates_confirmed=True,home_station=station,lead_station=station,fire_scale=1,status='Confirmed')
            route=route_between(station,incident)
            if route.get('error'):raise CommandError(route['error'])
            if route['metres']<3000:raise CommandError('Demo route must be at least 3 km; no distance inflation applied.')
            incident.save()
            self.stdout.write(self.style.SUCCESS(f'Added demo incident {incident.pk}: {route["metres"]/1000:.2f} km road distance.'))
        self.stdout.write('Demo events only; no dispatches, vehicles, or historical incidents changed.')

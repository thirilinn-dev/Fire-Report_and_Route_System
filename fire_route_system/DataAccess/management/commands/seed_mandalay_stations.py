from django.core.management.base import BaseCommand
from DataAccess.models import FireStation


MANDALAY_FIRE_STATIONS = [
    {
        "name": "မန္တလေးမြို့နယ် မီးသတ်ဌာနချုပ် (Mandalay Central Fire Station No. 1)",
        "address": "၈၄ လမ်းနှင့် ၂၆ လမ်းထောင့်၊ မဟာအောင်မြေမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-72355",
        "latitude": 21.9742,
        "longitude": 96.0835,
        "status": "Active",
    },
    {
        "name": "အောင်မြေသာဇံမြို့နယ် မီးသတ်ဌာန (Chanayethazan Fire Station No. 2)",
        "address": "၆၉ လမ်းနှင့် ၃၅ လမ်းထောင့်၊ ချမ်းအေးသာဇံမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-72203",
        "latitude": 21.9615,
        "longitude": 96.0760,
        "status": "Active",
    },
    {
        "name": "ချမ်းမြသာစည်မြို့နယ် မီးသတ်ဌာန (Chanmyathazi Fire Station No. 3)",
        "address": "ကန်တော်ကြီးလမ်းမ၊ ချမ်းမြသာစည်မြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-39205",
        "latitude": 21.9880,
        "longitude": 96.0680,
        "status": "Active",
    },
    {
        "name": "ပြည်ကြီးတံခွန်မြို့နယ် မီးသတ်ဌာန (Pyigyidagun Fire Station No. 4)",
        "address": "မန္တလေး-လားရှိုးလမ်းမ၊ ပြည်ကြီးတံခွန်မြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-57025",
        "latitude": 21.9500,
        "longitude": 96.1200,
        "status": "Active",
    },
    {
        "name": "မဟာအောင်မြေမြို့နယ် မီးသတ်ဌာန (Mahaaungmye Fire Station No. 5)",
        "address": "၃၅ လမ်းနှင့် ၇၈ လမ်းထောင့်၊ မဟာအောင်မြေမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-72299",
        "latitude": 21.9780,
        "longitude": 96.0900,
        "status": "Active",
    },
    {
        "name": "ပသိုင်းကျေးရွာ မီးသတ်ဌာန (Patheingyi Township Fire Station No. 6)",
        "address": "မန္တလေး-မတ္တရာလမ်းမ၊ ပသိုင်းမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-55138",
        "latitude": 21.9250,
        "longitude": 96.0550,
        "status": "Active",
    },
    {
        "name": "အမရပူရမြို့နယ် မီးသတ်ဌာန (Amarapura Fire Station No. 7)",
        "address": "မန္တလေး-အမရပူရလမ်းမ၊ အမရပူရမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-50144",
        "latitude": 21.8970,
        "longitude": 96.0490,
        "status": "Active",
    },
    {
        "name": "မြောက်ပိုင်းဒေသကြီး မီးသတ်ဌာန (Aungmyaethazan Fire Station No. 8)",
        "address": "၃၅ လမ်းနှင့် ၈၅ လမ်းထောင့်၊ အောင်မြေသာဇံမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "02-34822",
        "latitude": 22.0080,
        "longitude": 96.0820,
        "status": "Active",
    },
    {
        "name": "တံတားဦးမြို့နယ် မီးသတ်ဌာန (Tada-U Township Fire Station No. 9)",
        "address": "မန္တလေး-မုံရွာလမ်းမ၊ တံတားဦးမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "075-40222",
        "latitude": 22.0640,
        "longitude": 96.0980,
        "status": "Active",
    },
    {
        "name": "ဆင်ဖြူကျွန်းမြို့နယ် မီးသတ်ဌာန (Sintgaing Township Fire Station No. 10)",
        "address": "မန္တလေး-တောင်တွင်းကြီးလမ်းမ၊ ဆင်ဖြူကျွန်းမြို့နယ်၊ မန္တလေးတိုင်းဒေသကြီး",
        "contact_number": "075-50133",
        "latitude": 21.8400,
        "longitude": 96.0200,
        "status": "Active",
    },
]


class Command(BaseCommand):
    help = "Seed all Mandalay city area fire stations into the database."

    def handle(self, *args, **options):
        added = 0
        skipped = 0

        for data in MANDALAY_FIRE_STATIONS:
            station, created = FireStation.objects.get_or_create(
                name=data["name"],
                defaults={
                    "address": data["address"],
                    "contact_number": data["contact_number"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "status": data["status"],
                },
            )
            if created:
                added += 1
                self.stdout.write(self.style.SUCCESS(f"  [ADDED] Station ID={station.station_id}"))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"  [SKIP]  Station ID={station.station_id} (already exists)"))


        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {added} station(s) added, {skipped} station(s) already existed."
            )
        )

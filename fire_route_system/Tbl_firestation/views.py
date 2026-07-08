from django.shortcuts import render, redirect, get_object_or_404
from .models import FireStation

# ==========================
# READ (Display All)
# ==========================
def firestation_list(request):
    stations = FireStation.objects.all()

    context = {
        "stations": stations
    }

    return render(request, "firestation/list.html", context)


# ==========================
# CREATE
# ==========================
def firestation_create(request):

    if request.method == "POST":

        FireStation.objects.create(
            name=request.POST.get("name"),
            address=request.POST.get("address"),
            contact_number=request.POST.get("contact_number"),
            latitude=request.POST.get("latitude"),
            longitude=request.POST.get("longitude"),
            status=request.POST.get("status")
        )

        return redirect("firestation_list")

    return render(request, "firestation/create.html")


# ==========================
# UPDATE
# ==========================
def firestation_update(request, station_id):

    station = get_object_or_404(FireStation, pk=station_id)

    if request.method == "POST":

        station.name = request.POST.get("name")
        station.address = request.POST.get("address")
        station.contact_number = request.POST.get("contact_number")
        station.latitude = request.POST.get("latitude")
        station.longitude = request.POST.get("longitude")
        station.status = request.POST.get("status")

        station.save()

        return redirect("firestation_list")

    context = {
        "station": station
    }

    return render(request, "firestation/update.html", context)


# ==========================
# DELETE
# ==========================
def firestation_delete(request, station_id):

    station = get_object_or_404(FireStation, pk=station_id)

    if request.method == "POST":
        station.delete()
        return redirect("firestation_list")

    context = {
        "station": station
    }

    return render(request, "firestation/delete.html", context)
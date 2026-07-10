from django.shortcuts import render, redirect, get_object_or_404
from .models import WaterSource
from .forms import WaterSourceForm


# Read
def water_list(request):
    waters = WaterSource.objects.all()
    return render(request, 'water_sources/list.html', {'waters': waters})


# Create
def water_add(request):
    if request.method == "POST":
        form = WaterSourceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('water_list')
    else:
        form = WaterSourceForm()

    return render(request, 'water_sources/add.html', {'form': form})


# Update
def water_edit(request, pk):
    water = get_object_or_404(WaterSource, pk=pk)

    if request.method == "POST":
        form = WaterSourceForm(request.POST, instance=water)
        if form.is_valid():
            form.save()
            return redirect('water_list')
    else:
        form = WaterSourceForm(instance=water)

    return render(request, 'water_sources/edit.html', {'form': form})


# Delete
def water_delete(request, pk):
    water = get_object_or_404(WaterSource, pk=pk)

    if request.method == "POST":
        water.delete()
        return redirect('water_list')

    return render(request, 'water_sources/delete.html', {'water': water})
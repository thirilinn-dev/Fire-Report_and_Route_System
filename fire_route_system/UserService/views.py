from django.shortcuts import render, redirect, get_object_or_404
from .models import Role, User
from .forms import RoleForm, UserForm


# ROLE CRUD


def role_list(request):
    roles = Role.objects.all()
    return render(request, 'role/list.html', {'roles': roles})


def role_create(request):
    form = RoleForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('role_list')

    return render(request, 'role/form.html', {'form': form})


def role_update(request, pk):
    role = get_object_or_404(Role, pk=pk)

    form = RoleForm(request.POST or None, instance=role)

    if form.is_valid():
        form.save()
        return redirect('role_list')

    return render(request, 'role/form.html', {'form': form})


def role_delete(request, pk):
    role = get_object_or_404(Role, pk=pk)

    if request.method == 'POST':
        role.delete()
        return redirect('role_list')

    return render(request, 'role/delete.html', {'role': role})


# USER CRUD


def user_list(request):
    users = User.objects.all()
    return render(request, 'user/list.html', {'users': users})


def user_create(request):
    form = UserForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('user_list')

    return render(request, 'user/form.html', {'form': form})


def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)

    form = UserForm(request.POST or None, instance=user)

    if form.is_valid():
        form.save()
        return redirect('user_list')

    return render(request, 'user/form.html', {'form': form})


def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.delete()
        return redirect('user_list')

    return render(request, 'user/delete.html', {'user': user})

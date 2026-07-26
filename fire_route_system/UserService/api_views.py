import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from DataAccess.models import Role, User

def serialize_role(role):
    return {
        'id': role.id,
        'role_name': role.role_name,
        'description': role.description,
        'created_at': role.created_at.isoformat() if role.created_at else None,
    }

def serialize_user(user):
    return {
        'id': user.id,
        'role_id': user.role_id,
        'role_name': user.role.role_name if user.role else None,
        'username': user.username,
        'email': user.email,
        'password_hash': user.password_hash,
        'phone_number': user.phone_number,
        'status': user.status,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }

@csrf_exempt
def role_list_create(request):
    if request.method == 'GET':
        roles = Role.objects.all()
        return JsonResponse([serialize_role(r) for r in roles], safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        role_name = data.get('role_name')
        if not role_name:
            return JsonResponse({'error': 'role_name is required'}, status=400)

        try:
            role = Role.objects.create(
                role_name=role_name,
                description=data.get('description')
            )
            return JsonResponse(serialize_role(role), status=201)
        except IntegrityError:
            return JsonResponse({'error': 'Role with this name already exists'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def role_detail(request, pk):
    try:
        role = Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Role not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_role(role))

    elif request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if request.method == 'PUT':
            role_name = data.get('role_name')
            if not role_name:
                return JsonResponse({'error': 'role_name is required for PUT'}, status=400)
            role.role_name = role_name
            role.description = data.get('description')
        else: # PATCH
            if 'role_name' in data:
                role.role_name = data['role_name']
            if 'description' in data:
                role.description = data['description']

        try:
            role.save()
            return JsonResponse(serialize_role(role))
        except IntegrityError:
            return JsonResponse({'error': 'Role with this name already exists'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            role.delete()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def user_list_create(request):
    if request.method == 'GET':
        users = User.objects.all()
        return JsonResponse([serialize_user(u) for u in users], safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        required_fields = ['role_id', 'username', 'email', 'password_hash']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)

        role_id = data.get('role_id')
        try:
            role = Role.objects.get(pk=role_id)
        except Role.DoesNotExist:
            return JsonResponse({'error': f'Role with id {role_id} does not exist'}, status=400)

        try:
            user = User.objects.create(
                role=role,
                username=data.get('username'),
                email=data.get('email'),
                password_hash=data.get('password_hash'),
                phone_number=data.get('phone_number'),
                status=data.get('status', 'Active')
            )
            return JsonResponse(serialize_user(user), status=201)
        except IntegrityError:
            return JsonResponse({'error': 'Username or email already exists'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_user(user))

    elif request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        if request.method == 'PUT':
            required_fields = ['role_id', 'username', 'email', 'password_hash']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'error': f'{field} is required for PUT'}, status=400)
            
            role_id = data.get('role_id')
            try:
                role = Role.objects.get(pk=role_id)
            except Role.DoesNotExist:
                return JsonResponse({'error': f'Role with id {role_id} does not exist'}, status=400)

            user.role = role
            user.username = data.get('username')
            user.email = data.get('email')
            user.password_hash = data.get('password_hash')
            user.phone_number = data.get('phone_number')
            user.status = data.get('status', 'Active')
        else: # PATCH
            if 'role_id' in data:
                role_id = data['role_id']
                try:
                    role = Role.objects.get(pk=role_id)
                    user.role = role
                except Role.DoesNotExist:
                    return JsonResponse({'error': f'Role with id {role_id} does not exist'}, status=400)
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'password_hash' in data:
                user.password_hash = data['password_hash']
            if 'phone_number' in data:
                user.phone_number = data['phone_number']
            if 'status' in data:
                user.status = data['status']

        try:
            user.save()
            return JsonResponse(serialize_user(user))
        except IntegrityError:
            return JsonResponse({'error': 'Username or email already exists'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            user.delete()
            return JsonResponse({'success': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

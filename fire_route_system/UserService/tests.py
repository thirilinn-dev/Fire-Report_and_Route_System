import json
from django.test import TestCase, Client
from django.urls import reverse
from DataAccess.models import Role, User

class UserServiceAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role1 = Role.objects.create(role_name="Admin", description="Administrator")
        self.role2 = Role.objects.create(role_name="Operator", description="Dispatch Operator")
        self.user1 = User.objects.create(
            role=self.role1,
            username="admin_user",
            email="admin@fireapp.com",
            password_hash="hashed_pw_1",
            phone_number="091234567",
            status="Active"
        )

    def test_role_list(self):
        url = reverse('api_role_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['role_name'], "Admin")
        self.assertEqual(data[1]['role_name'], "Operator")

    def test_role_create(self):
        url = reverse('api_role_list_create')
        payload = {
            'role_name': 'Citizen',
            'description': 'Reporter / Citizen User'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['role_name'], "Citizen")
        self.assertTrue(Role.objects.filter(role_name="Citizen").exists())

    def test_role_create_duplicate(self):
        url = reverse('api_role_list_create')
        payload = {
            'role_name': 'Admin',
            'description': 'Duplicate'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_role_retrieve(self):
        url = reverse('api_role_detail', kwargs={'pk': self.role1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['role_name'], "Admin")

    def test_role_update(self):
        url = reverse('api_role_detail', kwargs={'pk': self.role1.pk})
        payload = {
            'role_name': 'SuperAdmin',
            'description': 'Updated description'
        }
        response = self.client.put(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['role_name'], "SuperAdmin")
        self.assertEqual(data['description'], "Updated description")

    def test_role_delete(self):
        url = reverse('api_role_detail', kwargs={'pk': self.role2.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Role.objects.filter(pk=self.role2.pk).exists())

    def test_user_list(self):
        url = reverse('api_user_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['username'], "admin_user")

    def test_user_create(self):
        url = reverse('api_user_list_create')
        payload = {
            'role_id': self.role2.pk,
            'username': 'operator_1',
            'email': 'op1@fireapp.com',
            'password_hash': 'hashed_op_pw',
            'phone_number': '097776665',
            'status': 'Active'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['username'], "operator_1")
        self.assertTrue(User.objects.filter(username="operator_1").exists())

    def test_user_create_missing_field(self):
        url = reverse('api_user_list_create')
        payload = {
            'role_id': self.role2.pk,
            'username': 'operator_2'
            # Missing email and password_hash
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_user_retrieve(self):
        url = reverse('api_user_detail', kwargs={'pk': self.user1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['username'], "admin_user")

    def test_user_update(self):
        url = reverse('api_user_detail', kwargs={'pk': self.user1.pk})
        payload = {
            'role_id': self.role1.pk,
            'username': 'admin_user_updated',
            'email': 'admin_new@fireapp.com',
            'password_hash': 'new_hash_pw',
            'phone_number': '090000000',
            'status': 'Suspended'
        }
        response = self.client.put(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['username'], "admin_user_updated")
        self.assertEqual(data['status'], "Suspended")

    def test_user_delete(self):
        url = reverse('api_user_detail', kwargs={'pk': self.user1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=self.user1.pk).exists())
